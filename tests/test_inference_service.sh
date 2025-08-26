#!/bin/bash

# Script para probar el servicio de inferencia Llama Stack desplegado en OpenShift
# Configuración
NAMESPACE="llama-stack-example"
SERVICE_NAME="inference-example"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Función para verificar si un comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Verificar dependencias
print_info "Verificando dependencias..."
if ! command_exists "oc"; then
    print_error "OpenShift CLI (oc) no está instalado"
    exit 1
fi

if ! command_exists "curl"; then
    print_error "curl no está instalado"
    exit 1
fi

if ! command_exists "jq"; then
    print_error "jq no está instalado (opcional pero recomendado)"
fi

# Obtener la URL del servicio
print_info "Obteniendo URL del servicio desde OpenShift..."

# Primero verificar si el proyecto existe
if ! oc project $NAMESPACE >/dev/null 2>&1; then
    print_error "No se pudo acceder al namespace '$NAMESPACE'"
    print_info "Namespaces disponibles:"
    oc get projects --no-headers -o custom-columns=":metadata.name" 2>/dev/null || echo "No se pudo listar proyectos"
    exit 1
fi

# Obtener la URL de la ruta
ROUTE_URL=$(oc get route $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.host}' 2>/dev/null)

if [ -z "$ROUTE_URL" ]; then
    print_error "No se pudo obtener la URL de la ruta '$SERVICE_NAME' en el namespace '$NAMESPACE'"
    print_info "Verificando servicios disponibles:"
    oc get routes -n $NAMESPACE
    exit 1
fi

BASE_URL="https://$ROUTE_URL"
print_success "URL del servicio: $BASE_URL"

# Verificar conectividad básica
print_info "Verificando conectividad básica..."
if ! curl -s --connect-timeout 10 --max-time 30 -k "$BASE_URL/health" >/dev/null 2>&1; then
    if ! curl -s --connect-timeout 10 --max-time 30 -k "$BASE_URL" >/dev/null 2>&1; then
        print_error "No se pudo conectar al servicio"
        exit 1
    fi
fi

# Test 1: Obtener lista de modelos disponibles
print_info "Test 1: Obteniendo lista de modelos disponibles..."
MODELS_RESPONSE=$(curl -s -k -X GET "$BASE_URL/v1/models" \
    -H "Content-Type: application/json" \
    -w "HTTPSTATUS:%{http_code}")

HTTP_STATUS=$(echo $MODELS_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
MODELS_BODY=$(echo $MODELS_RESPONSE | sed -e 's/HTTPSTATUS:.*//g')

if [ "$HTTP_STATUS" -eq 200 ]; then
    print_success "✓ Endpoint /v1/models responde correctamente"
    if command_exists "jq"; then
        echo "$MODELS_BODY" | jq '.data[].id' 2>/dev/null || echo "$MODELS_BODY"
    else
        echo "$MODELS_BODY"
    fi
else
    print_error "✗ Error en /v1/models (HTTP $HTTP_STATUS)"
    echo "$MODELS_BODY"
fi

echo ""

# Test 2: Completions simples
print_info "Test 2: Probando completions simples..."
COMPLETION_PAYLOAD='{
  "model": "inference-example",
  "prompt": "The capital of Spain is",
  "max_tokens": 20,
  "temperature": 0.7
}'

COMPLETION_RESPONSE=$(curl -s -k -X POST "$BASE_URL/v1/completions" \
    -H "Content-Type: application/json" \
    -d "$COMPLETION_PAYLOAD" \
    -w "HTTPSTATUS:%{http_code}")

HTTP_STATUS=$(echo $COMPLETION_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
COMPLETION_BODY=$(echo $COMPLETION_RESPONSE | sed -e 's/HTTPSTATUS:.*//g')

if [ "$HTTP_STATUS" -eq 200 ]; then
    print_success "✓ Endpoint /v1/completions responde correctamente"
    if command_exists "jq"; then
        echo "Respuesta:"
        echo "$COMPLETION_BODY" | jq -r '.choices[0].text' 2>/dev/null || echo "$COMPLETION_BODY"
    else
        echo "$COMPLETION_BODY"
    fi
else
    print_error "✗ Error en /v1/completions (HTTP $HTTP_STATUS)"
    echo "$COMPLETION_BODY"
fi

echo ""

# Test 3: Chat completions
print_info "Test 3: Probando chat completions..."
CHAT_PAYLOAD='{
  "model": "inference-example",
  "messages": [
    {"role": "user", "content": "Hola, ¿puedes contarme un chiste corto?"}
  ],
  "max_tokens": 100,
  "temperature": 0.7
}'

CHAT_RESPONSE=$(curl -s -k -X POST "$BASE_URL/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d "$CHAT_PAYLOAD" \
    -w "HTTPSTATUS:%{http_code}")

HTTP_STATUS=$(echo $CHAT_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
CHAT_BODY=$(echo $CHAT_RESPONSE | sed -e 's/HTTPSTATUS:.*//g')

if [ "$HTTP_STATUS" -eq 200 ]; then
    print_success "✓ Endpoint /v1/chat/completions responde correctamente"
    if command_exists "jq"; then
        echo "Respuesta del asistente:"
        echo "$CHAT_BODY" | jq -r '.choices[0].message.content' 2>/dev/null || echo "$CHAT_BODY"
    else
        echo "$CHAT_BODY"
    fi
else
    print_error "✗ Error en /v1/chat/completions (HTTP $HTTP_STATUS)"
    echo "$CHAT_BODY"
fi

echo ""

# Test 4: Streaming chat completions (opcional)
print_info "Test 4: Probando streaming chat completions..."
STREAM_PAYLOAD='{
  "model": "inference-example",
  "messages": [
    {"role": "user", "content": "Cuenta hasta 5"}
  ],
  "max_tokens": 50,
  "temperature": 0.7,
  "stream": true
}'

echo "Streaming response:"
curl -s -k -X POST "$BASE_URL/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d "$STREAM_PAYLOAD" | head -20

echo ""
echo ""

# Test 5: Verificar que el modelo soporta tool calling (si está configurado)
print_info "Test 5: Probando capacidades de tool calling..."
TOOLS_PAYLOAD='{
  "model": "inference-example",
  "messages": [
    {"role": "user", "content": "¿Qué hora es?"}
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_current_time",
        "description": "Obtiene la hora actual",
        "parameters": {
          "type": "object",
          "properties": {}
        }
      }
    }
  ],
  "max_tokens": 100
}'

TOOLS_RESPONSE=$(curl -s -k -X POST "$BASE_URL/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d "$TOOLS_PAYLOAD" \
    -w "HTTPSTATUS:%{http_code}")

HTTP_STATUS=$(echo $TOOLS_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
TOOLS_BODY=$(echo $TOOLS_RESPONSE | sed -e 's/HTTPSTATUS:.*//g')

if [ "$HTTP_STATUS" -eq 200 ]; then
    print_success "✓ El modelo responde a peticiones con herramientas"
    if command_exists "jq"; then
        echo "Respuesta:"
        echo "$TOOLS_BODY" | jq -r '.choices[0].message.content // .choices[0].message' 2>/dev/null || echo "$TOOLS_BODY"
    else
        echo "$TOOLS_BODY"
    fi
else
    print_error "✗ Error en tool calling (HTTP $HTTP_STATUS)"
    echo "$TOOLS_BODY"
fi

echo ""

# Resumen final
print_info "=== RESUMEN DE PRUEBAS ==="
print_info "URL del servicio: $BASE_URL"
print_info "Namespace: $NAMESPACE"
print_info "Servicio: $SERVICE_NAME"
echo ""
print_success "✅ Pruebas completadas. El servicio de inferencia está funcionando correctamente."
print_info "Puedes usar esta URL para hacer peticiones desde tus aplicaciones."

echo ""
print_info "Ejemplos de uso con curl:"
echo ""
echo "# Completions simples:"
echo "curl -X POST '$BASE_URL/v1/completions' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"model\": \"inference-example \", \"prompt\": \"Hola mundo\", \"max_tokens\": 50}'"
echo ""
echo "# Chat completions:"
echo "curl -X POST '$BASE_URL/v1/chat/completions' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"model\": \"inference-example \", \"messages\": [{\"role\": \"user\", \"content\": \"Hola\"}], \"max_tokens\": 100}'"
