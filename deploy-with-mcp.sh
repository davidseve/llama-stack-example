#!/bin/bash

# Script para desplegar Llama Stack con servidor MCP de Kubernetes en OpenShift
# Este script despliega primero el servidor MCP y luego Llama Stack

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración por defecto
NAMESPACE=${NAMESPACE:-llama-stack}
TARGET_NAMESPACE=${TARGET_NAMESPACE:-""}  # Si está vacío, usa NAMESPACE
MCP_RELEASE_NAME=${MCP_RELEASE_NAME:-kubernetes-mcp-server}
LLAMA_RELEASE_NAME=${LLAMA_RELEASE_NAME:-llama-stack}
VALUES_FILE=${VALUES_FILE:-values-production.yaml}
TIMEOUT=${TIMEOUT:-300s}

# Función para mostrar ayuda
show_help() {
    cat << EOF
Desplegador de Llama Stack con MCP Server

USO:
    $0 [OPCIONES]

OPCIONES:
    -n, --namespace NAME        Namespace de OpenShift (default: llama-stack)
    --target-namespace NAME     Namespace objetivo para los recursos (sobrescribe global.namespace)
    -m, --mcp-release NAME      Nombre del release MCP (default: kubernetes-mcp-server)
    -l, --llama-release NAME    Nombre del release Llama Stack (default: llama-stack)
    -f, --values-file FILE      Archivo de valores para MCP (default: values-production.yaml)
    -t, --timeout DURATION     Timeout para el despliegue (default: 300s)
    --skip-mcp                  Solo desplegar Llama Stack (asumir MCP ya existe)
    --skip-llama                Solo desplegar MCP Server
    --dry-run                   Mostrar comandos sin ejecutar
    -h, --help                  Mostrar esta ayuda

VARIABLES DE ENTORNO:
    NAMESPACE                   Namespace de destino
    MCP_RELEASE_NAME           Nombre del release MCP
    LLAMA_RELEASE_NAME         Nombre del release Llama Stack
    VALUES_FILE                Archivo de valores MCP
    TIMEOUT                    Timeout de despliegue

EJEMPLOS:
    # Despliegue completo
    $0 -n my-namespace

    # Solo MCP Server
    $0 --skip-llama -f values-development.yaml

    # Despliegue en dry-run
    $0 --dry-run -n test-env

EOF
}

# Función para logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# Función para verificar dependencias
check_dependencies() {
    log "Verificando dependencias..."
    
    local deps=("helm" "oc" "kubectl")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log_error "$dep no está instalado o no está en PATH"
            exit 1
        fi
    done
    
    # Verificar conexión a OpenShift/Kubernetes
    if ! kubectl auth can-i create deployments &> /dev/null; then
        log_error "No tienes permisos suficientes en el cluster"
        exit 1
    fi
    
    log_success "Todas las dependencias están disponibles"
}

# Función para crear namespace si no existe
ensure_namespace() {
    log "Verificando namespace '$NAMESPACE'..."
    
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log "Creando namespace '$NAMESPACE'..."
        if [ "$DRY_RUN" = true ]; then
            echo "kubectl create namespace $NAMESPACE"
        else
            kubectl create namespace "$NAMESPACE"
        fi
    fi
    
    log_success "Namespace '$NAMESPACE' está disponible"
}

# Función para desplegar MCP Server
deploy_mcp_server() {
    log "Desplegando servidor MCP de Kubernetes..."
    
    local mcp_chart_path="./charts/kubernetes-mcp-server"
    local values_path="$mcp_chart_path/$VALUES_FILE"
    
    # Verificar que el chart existe
    if [ ! -d "$mcp_chart_path" ]; then
        log_error "Chart de MCP no encontrado en $mcp_chart_path"
        exit 1
    fi
    
    # Verificar archivo de valores
    if [ ! -f "$values_path" ]; then
        log_warning "Archivo de valores '$values_path' no encontrado, usando valores por defecto"
        values_path=""
    fi
    
    # Construir comando helm
    local helm_cmd="helm upgrade --install $MCP_RELEASE_NAME $mcp_chart_path"
    helm_cmd="$helm_cmd --namespace $NAMESPACE"
    helm_cmd="$helm_cmd --timeout $TIMEOUT"
    helm_cmd="$helm_cmd --wait"
    
    # Añadir namespace objetivo si está especificado
    if [ -n "$TARGET_NAMESPACE" ]; then
        helm_cmd="$helm_cmd --set global.namespace=$TARGET_NAMESPACE"
    fi
    
    if [ -n "$values_path" ]; then
        helm_cmd="$helm_cmd --values $values_path"
    fi
    
    log "Ejecutando: $helm_cmd"
    
    if [ "$DRY_RUN" = true ]; then
        echo "$helm_cmd"
    else
        eval "$helm_cmd"
        
        # Verificar que el deployment está listo
        log "Esperando a que el servidor MCP esté listo..."
        kubectl wait --for=condition=available --timeout=$TIMEOUT \
            deployment/$MCP_RELEASE_NAME -n "$NAMESPACE"
        
        # Mostrar información del servicio
        local service_info
        service_info=$(kubectl get service "$MCP_RELEASE_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}:{.spec.ports[0].port}')
        log_success "Servidor MCP desplegado correctamente en: $service_info"
    fi
}

# Función para desplegar Llama Stack
deploy_llama_stack() {
    log "Desplegando Llama Stack..."
    
    local llama_chart_path="./charts/llama-stack"
    
    # Verificar que el chart existe
    if [ ! -d "$llama_chart_path" ]; then
        log_error "Chart de Llama Stack no encontrado en $llama_chart_path"
        exit 1
    fi
    
    # Configurar variables de entorno para MCP
    local mcp_service_url="http://$MCP_RELEASE_NAME:8080"
    
    # Construir comando helm
    local helm_cmd="helm upgrade --install $LLAMA_RELEASE_NAME $llama_chart_path"
    helm_cmd="$helm_cmd --namespace $NAMESPACE"
    helm_cmd="$helm_cmd --timeout $TIMEOUT"
    helm_cmd="$helm_cmd --wait"
    helm_cmd="$helm_cmd --set env.KUBERNETES_MCP_URL=$mcp_service_url"
    
    log "Ejecutando: $helm_cmd"
    
    if [ "$DRY_RUN" = true ]; then
        echo "$helm_cmd"
    else
        eval "$helm_cmd"
        
        log_success "Llama Stack desplegado correctamente"
    fi
}

# Función para mostrar status
show_status() {
    log "Estado del despliegue:"
    echo
    
    if [ "$SKIP_MCP" != true ]; then
        echo "=== Servidor MCP ==="
        kubectl get deployment,service,route "$MCP_RELEASE_NAME" -n "$NAMESPACE" 2>/dev/null || true
        echo
    fi
    
    if [ "$SKIP_LLAMA" != true ]; then
        echo "=== Llama Stack ==="
        kubectl get deployment,service,route "$LLAMA_RELEASE_NAME" -n "$NAMESPACE" 2>/dev/null || true
        echo
    fi
    
    # Mostrar URLs de acceso
    log "URLs de acceso:"
    if [ "$SKIP_MCP" != true ]; then
        local mcp_route
        mcp_route=$(kubectl get route "$MCP_RELEASE_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.host}' 2>/dev/null || echo "No disponible")
        echo "  MCP Server: https://$mcp_route"
    fi
    
    if [ "$SKIP_LLAMA" != true ]; then
        local llama_route
        llama_route=$(kubectl get route "$LLAMA_RELEASE_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.host}' 2>/dev/null || echo "No disponible")
        echo "  Llama Stack: https://$llama_route"
    fi
}

# Parsear argumentos
SKIP_MCP=false
SKIP_LLAMA=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        --target-namespace)
            TARGET_NAMESPACE="$2"
            shift 2
            ;;
        -m|--mcp-release)
            MCP_RELEASE_NAME="$2"
            shift 2
            ;;
        -l|--llama-release)
            LLAMA_RELEASE_NAME="$2"
            shift 2
            ;;
        -f|--values-file)
            VALUES_FILE="$2"
            shift 2
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --skip-mcp)
            SKIP_MCP=true
            shift
            ;;
        --skip-llama)
            SKIP_LLAMA=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Opción desconocida: $1"
            show_help
            exit 1
            ;;
    esac
done

# Función principal
main() {
    log "🚀 Iniciando despliegue de Llama Stack con MCP Server"
    log "Configuración:"
    echo "  Namespace: $NAMESPACE"
    if [ -n "$TARGET_NAMESPACE" ]; then
        echo "  Target Namespace: $TARGET_NAMESPACE"
    fi
    echo "  MCP Release: $MCP_RELEASE_NAME"
    echo "  Llama Release: $LLAMA_RELEASE_NAME"
    echo "  Values File: $VALUES_FILE"
    echo "  Timeout: $TIMEOUT"
    echo "  Skip MCP: $SKIP_MCP"
    echo "  Skip Llama: $SKIP_LLAMA"
    echo "  Dry Run: $DRY_RUN"
    echo
    
    # Verificaciones previas
    check_dependencies
    ensure_namespace
    
    # Despliegues
    if [ "$SKIP_MCP" != true ]; then
        deploy_mcp_server
    fi
    
    if [ "$SKIP_LLAMA" != true ]; then
        deploy_llama_stack
    fi
    
    # Mostrar estado final
    if [ "$DRY_RUN" != true ]; then
        show_status
        log_success "¡Despliegue completado exitosamente! 🎉"
    else
        log "Dry run completado - no se realizaron cambios"
    fi
}

# Ejecutar función principal
main "$@"
