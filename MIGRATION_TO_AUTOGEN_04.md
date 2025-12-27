# Migración a AutoGen 0.4

Este proyecto ha sido actualizado para usar AutoGen 0.4, que introduce una arquitectura completamente nueva basada en eventos asíncronos.

## Cambios Principales

### 1. Librerías Actualizadas

```txt
# AutoGen 0.4+ (nueva arquitectura asíncrona)
autogen-agentchat==0.4.0.dev14
autogen-core==0.4.0.dev14
autogen-ext[openai]==0.4.0.dev14

# FastAPI actualizado
fastapi==0.115.5
uvicorn[standard]==0.32.1

# Pydantic v2 actualizado
pydantic==2.10.3
pydantic-settings==2.7.0

# SQLAlchemy actualizado
sqlalchemy==2.0.36
```

### 2. Cambios en la API de AutoGen

#### Antes (v0.2):
```python
from autogen import AssistantAgent, UserProxyAgent

llm_config = {
    "config_list": [{"model": "gpt-4o", "api_key": "sk-xxx"}],
    "temperature": 0.7,
}

agent = AssistantAgent(
    name="assistant",
    llm_config=llm_config,
)
```

#### Ahora (v0.4):
```python
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

model_client = OpenAIChatCompletionClient(
    model="deepseek-chat",
    api_key="sk-xxx",
    base_url="https://api.deepseek.com",
    temperature=0.7,
)

agent = AssistantAgent(
    name="assistant",
    model_client=model_client,
    tools=[function1, function2],  # Las funciones se pasan directamente
    reflect_on_tool_use=True,
)
```

### 3. Cambios en Herramientas (Tools)

En v0.4, las herramientas se pasan directamente al agente como funciones Python normales. No se necesita `register_function` ni `UserProxyAgent` para ejecutar herramientas.

```python
async def get_weather(city: str) -> str:
    """Get the weather for a given city."""
    return f"The weather in {city} is 73 degrees and Sunny."

agent = AssistantAgent(
    name="weather_agent",
    model_client=model_client,
    tools=[get_weather],  # Función directamente
    reflect_on_tool_use=True,
)
```

### 4. Ejecución Asíncrona

Todos los métodos ahora son asíncronos:

```python
# Conversación simple
response = await agent.on_messages(
    [TextMessage(content="Hello!", source="user")],
    CancellationToken()
)

# Group Chat (RoundRobinGroupChat)
team = RoundRobinGroupChat([agent1, agent2], termination_condition=termination)
result = await team.run(task="Your task here", cancellation_token=CancellationToken())
```

## Pasos de Instalación

### 1. Desinstalar versiones anteriores

```bash
cd backend
pip uninstall pyautogen openai -y
```

### 2. Instalar nuevas dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

El archivo `.env` ahora soporta configuración de API base URL:

```env
# OpenAI Configuration
OPENAI_API_KEY="sk-8cb1f4fc5bd74bd3a83f31204b942d60"
OPENAI_API_BASE_URL="https://api.deepseek.com"
OPENAI_MODEL="deepseek-chat"
```

Puedes usar cualquier API compatible con OpenAI:
- OpenAI: `https://api.openai.com/v1`
- DeepSeek: `https://api.deepseek.com`
- Azure OpenAI: `https://your-resource.openai.azure.com/`
- Ollama (local): `http://localhost:11434/v1`
- LM Studio (local): `http://localhost:1234/v1`

### 4. Probar el backend

```bash
cd backend
python -c "from app.agents.orchestrator import get_orchestrator; print('OK')"
```

### 5. Ejecutar el servidor

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Características Nuevas

### 1. Soporte para Múltiples Proveedores de LLM

Ahora puedes cambiar fácilmente entre diferentes proveedores de LLM simplemente cambiando la configuración en `.env`.

### 2. Arquitectura Asíncrona

Mejor rendimiento y capacidad de manejar múltiples solicitudes concurrentes.

### 3. Mejor Manejo de Herramientas

Las herramientas se ejecutan directamente dentro del agente, sin necesidad de un UserProxy.

### 4. Streaming de Respuestas

Posibilidad de hacer streaming de las respuestas del agente (pendiente de implementar en el frontend).

## Solución de Problemas

### Error: "Client.__init__() got an unexpected keyword argument 'proxies'"

Esto significa que aún tienes la versión antigua de OpenAI instalada. Solución:

```bash
pip uninstall openai -y
pip install -r requirements.txt
```

### Error: "No module named 'autogen_agentchat'"

Asegúrate de instalar las nuevas dependencias:

```bash
pip install autogen-agentchat==0.4.0.dev14 autogen-core==0.4.0.dev14 autogen-ext[openai]==0.4.0.dev14
```

### Error de API Key

Verifica que tu API key esté correctamente configurada en `.env` y que coincida con el proveedor configurado en `OPENAI_API_BASE_URL`.

## Referencias

- [AutoGen 0.4 Documentation](https://microsoft.github.io/autogen/)
- [Migration Guide v0.2 to v0.4](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/migration-guide.html)
- [AgentChat Tutorial](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/index.html)
