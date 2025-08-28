# Discounts Platform - Ejemplos y Demos

## 🛍️ Resumen

Esta sección contiene ejemplos prácticos y demos de la plataforma **Discounts**, mostrando cómo implementar diferentes funcionalidades de búsqueda de descuentos, comparación de precios, y alertas inteligentes usando agentes de IA.

## 🚀 Demos Disponibles

### 1. Chatbot de Descuentos Básico
```bash
python tests/agent-chatbot/llama_agent_chatbot-simple.py
```
Un chatbot básico que puede responder preguntas sobre descuentos y encontrar ofertas simples.

### 2. Agente RAG con Herramientas MCP
```bash
python tests/agent-chatbot/llama_agent_chatbot-rag-mcp.py
```
Agente avanzado que combina:
- **RAG**: Base de conocimiento de ofertas y estrategias de ahorro
- **MCP Tools**: Herramientas en tiempo real para scraping de precios
- **Análisis Predictivo**: Predicciones de cambios de precio

### 3. Sistema Completo de Descuentos
```bash
python tests/agent-chatbot/llama_agent_chatbot.py
```
Implementación completa con todas las funcionalidades:
- Búsqueda multi-tienda
- Validación de cupones
- Alertas de precio
- Cashback tracking
- Historial de ahorros

## 🛠️ Configuración

### Helm Charts

#### Servicio de Inferencia
```bash
helm install discount-inference charts/inference/
```
Despliega los modelos de IA necesarios para análisis de precios y procesamiento de lenguaje natural.

#### Servidor MCP de Descuentos  
```bash
helm install discount-mcp charts/kubernetes-mcp-server/
```
Despliega las herramientas MCP específicas para web scraping de ofertas y APIs de tiendas.

#### Stack Completo de Discounts
```bash
helm install discounts-stack charts/llama-stack/
```
Despliega toda la plataforma incluyendo:
- Agentes de IA especializados
- Base de datos vectorial
- APIs de comparación
- Sistema de notificaciones

### Variables de Configuración

#### values-common.yaml
```yaml
discounts:
  enableScrapingTools: true
  storeApis:
    amazon: 
      enabled: true
      apiKey: "${AMAZON_API_KEY}"
    walmart:
      enabled: true
      apiKey: "${WALMART_API_KEY}"
  thresholds:
    minimumDiscount: 0.15  # 15%
    priceDropAlert: 0.10   # 10%
```

## 🧪 Testing y Validación

### Scripts de Validación
```bash
# Validación básica de funcionalidad
./tests/run_validation.sh

# Test de servicios de inferencia
./tests/test_inference_service.sh

# Validación completa de la plataforma
python tests/validate_discounts_platform.py
```

### Tests Específicos

#### 1. Test de APIs de Tiendas
```bash
python tests/validate_basic.py --test-stores
```

#### 2. Test de Agentes RAG
```bash
python tests/validate_llamastack_enhanced.py --test-rag
```

#### 3. Test de Herramientas MCP
```bash
python tests/validate_llamastack_enhanced.py --test-mcp
```

## 🔧 Desarrollo

### Estructura del Proyecto
```
tests/
├── agent-chatbot/           # Demos de chatbots
│   ├── llama_agent_chatbot-simple.py
│   ├── llama_agent_chatbot-rag-mcp.py
│   └── llama_agent_chatbot.py
├── validate_basic.py        # Tests básicos
├── validate_llamastack_enhanced.py  # Tests avanzados
└── requirements.txt         # Dependencias
```

### Setup para Desarrollo
```bash
cd tests/agent-chatbot
./setup.sh
source venv/bin/activate
pip install -r requirements.txt
```

## 📊 Funcionalidades Destacadas

### Búsqueda Inteligente de Productos
- Procesamiento de lenguaje natural para entender consultas de productos
- Búsqueda semántica usando embeddings
- Ranking inteligente de resultados por ahorro potencial

### Análisis de Precios en Tiempo Real
- Monitoreo continuo de precios en 15+ tiendas
- Alertas automáticas de bajadas de precio
- Predicciones basadas en histórico de precios

### Validación Automática de Cupones
- Verificación en tiempo real de códigos promocionales
- Base de datos actualizada de cupones válidos
- Combinación inteligente de ofertas para maximizar ahorros

### Dashboard de Ahorros
- Tracking personalizado de ahorros acumulados
- Análisis de patrones de compra
- Recomendaciones basadas en historial

## 🤖 Casos de Uso

### Para Usuarios Finales
- "¿Cuál es el mejor precio para iPhone 15 Pro?"
- "Avísame cuando los AirPods bajen de $150"
- "Encuentra cupones para Nike"
- "¿Cuánto he ahorrado este mes?"

### Para Desarrolladores
- Integración de APIs de descuentos en aplicaciones existentes
- Implementación de alertas de precio personalizadas
- Desarrollo de bots de Slack/Discord para equipos
- Automatización de procesos de compra corporativa

## 📈 Métricas y Observabilidad

La plataforma incluye métricas integradas para monitorear:

- **Ahorros generados**: Total de dinero ahorrado por usuarios
- **Precisión de cupones**: Porcentaje de cupones válidos encontrados
- **Latencia de búsqueda**: Tiempo de respuesta de consultas
- **Cobertura de tiendas**: Número de tiendas monitoreadas activamente
- **Satisfacción del usuario**: Feedback y ratings de recomendaciones

## 🚀 Próximas Funcionalidades

- [ ] Integración con asistentes de voz (Alexa, Google)
- [ ] App móvil nativa con notificaciones push
- [ ] Sistema de recompensas por uso de la plataforma
- [ ] API pública para desarrolladores terceros
- [ ] Integración con carteras digitales para compras automáticas
