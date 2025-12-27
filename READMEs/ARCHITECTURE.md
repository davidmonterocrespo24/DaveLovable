# Arquitectura del Backend - Lovable Dev Clone

## 🏗️ Visión General

Este backend está diseñado como un sistema modular que utiliza Microsoft AutoGen para orquestar agentes LLM que generan código automáticamente. La arquitectura sigue principios SOLID y patrones de diseño modernos.

## 📐 Arquitectura de Capas

```
┌─────────────────────────────────────────┐
│          API Layer (FastAPI)            │
│  - REST Endpoints                       │
│  - Request/Response Handling            │
│  - Validation (Pydantic)                │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│         Service Layer                   │
│  - Business Logic                       │
│  - Transaction Management               │
│  - Agent Orchestration                  │
└──────────────┬──────────────────────────┘
               │
      ┌────────┴────────┐
      │                 │
┌─────▼──────┐   ┌─────▼──────────────────┐
│  Database  │   │   Agent Layer          │
│  (SQLite)  │   │   (AutoGen)            │
│            │   │  - Coding Agent        │
│  Models    │   │  - UI Designer         │
│  CRUD Ops  │   │  - Code Reviewer       │
└────────────┘   │  - Architect           │
                 └────────────────────────┘
```

## 🔄 Flujo de Datos

### 1. Creación de Proyecto

```
User Request (POST /projects)
    │
    ▼
ProjectController.create_project()
    │
    ▼
ProjectService.create_project()
    │
    ├──► Create Project in DB
    │
    └──► Initialize project files
         (App.tsx, main.tsx, etc.)
    │
    ▼
Return Project with Files
```

### 2. Chat con Agentes LLM

```
User Message (POST /chat/{project_id})
    │
    ▼
ChatController.send_message()
    │
    ▼
ChatService.process_chat_message()
    │
    ├──► Save user message to DB
    │
    ├──► Get project context (files)
    │
    ▼
AgentOrchestrator.generate_code()
    │
    ├──► Initialize AutoGen Agents
    │    ├─ Architect (plans structure)
    │    ├─ UI Designer (designs UI)
    │    ├─ Coding Agent (writes code)
    │    └─ Code Reviewer (reviews)
    │
    ├──► Group Chat Discussion
    │
    ▼
Extract Code from Conversation
    │
    ▼
Update/Create Project Files in DB
    │
    ▼
Save Assistant Response
    │
    ▼
Return Response + Code Changes
```

## 🗂️ Estructura de Módulos

### `/app/api` - API Endpoints

Controladores REST que manejan requests HTTP.

**Responsabilidades:**
- Validación de entrada (via Pydantic)
- Autenticación y autorización
- Orquestación de servicios
- Formateo de respuestas

**Archivos:**
- `projects.py` - CRUD de proyectos y archivos
- `chat.py` - Interacción con agentes LLM

### `/app/services` - Lógica de Negocio

Servicios que implementan las reglas de negocio.

**Responsabilidades:**
- Transacciones de base de datos
- Validaciones de negocio
- Coordinación entre modelos
- Integración con agentes

**Archivos:**
- `project_service.py` - Gestión de proyectos
- `chat_service.py` - Gestión de chat y agentes

### `/app/agents` - Sistema de Agentes AutoGen

Orquestación de agentes LLM para generación de código.

**Responsabilidades:**
- Configuración de agentes
- Coordinación de conversaciones
- Extracción de código generado
- Distribución de tareas

**Componentes:**

#### AgentOrchestrator

Clase principal que gestiona todos los agentes:

```python
class AgentOrchestrator:
    - coding_agent: AssistantAgent
    - ui_designer: AssistantAgent
    - code_reviewer: AssistantAgent
    - architect: AssistantAgent
    - user_proxy: UserProxyAgent
```

**Métodos principales:**

1. `generate_code(request, context)` - Generación colaborativa
2. `quick_code_generation(request, agent_type)` - Generación rápida
3. `review_code(code, context)` - Revisión de código

#### Agentes Especializados

1. **Coding Agent**
   - Genera código TypeScript/React
   - Sigue best practices
   - Usa TypeScript para type safety

2. **UI Designer**
   - Diseña componentes visuales
   - Aplica principios de diseño
   - Usa Tailwind CSS

3. **Code Reviewer**
   - Revisa calidad de código
   - Detecta bugs y problemas
   - Sugiere mejoras

4. **Architect**
   - Diseña estructura de componentes
   - Planifica data flow
   - Asegura escalabilidad

### `/app/models` - Modelos de Base de Datos

Definiciones de tablas SQLAlchemy.

**Modelos principales:**

```python
User
├── id: int
├── email: str
├── username: str
└── projects: List[Project]

Project
├── id: int
├── name: str
├── owner_id: int
├── files: List[ProjectFile]
└── chat_sessions: List[ChatSession]

ProjectFile
├── id: int
├── project_id: int
├── filename: str
├── filepath: str
└── content: str

ChatSession
├── id: int
├── project_id: int
└── messages: List[ChatMessage]

ChatMessage
├── id: int
├── session_id: int
├── role: MessageRole
├── content: str
└── metadata: str (JSON)
```

### `/app/schemas` - Validación de Datos

Schemas Pydantic para request/response.

**Tipos de Schemas:**

1. **Base** - Campos comunes
2. **Create** - Para crear registros
3. **Update** - Para actualizar (campos opcionales)
4. **InDB** - Representación en BD
5. **Response** - Para respuestas API

### `/app/db` - Configuración de Base de Datos

Setup de SQLAlchemy y gestión de sesiones.

**Componentes:**
- `engine` - Motor de base de datos
- `SessionLocal` - Factory de sesiones
- `Base` - Base declarativa
- `get_db()` - Dependency injection

### `/app/core` - Configuración Central

Settings y utilidades core.

**Archivos:**
- `config.py` - Settings de la app (Pydantic Settings)
- `security.py` - JWT, hashing, autenticación

## 🔐 Seguridad

### Autenticación (Preparada)

```python
# Hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"])

# JWT Tokens
create_access_token(data: dict) -> str
decode_access_token(token: str) -> dict
```

### CORS

Configurado para permitir requests desde:
- http://localhost:5173 (Vite dev server)
- http://localhost:3000 (React dev server)

## 🚀 Patrones de Diseño Utilizados

### 1. Repository Pattern

Los servicios actúan como repositories:

```python
class ProjectService:
    @staticmethod
    def get_project(db, project_id, owner_id)
    @staticmethod
    def create_project(db, project_data, owner_id)
```

### 2. Dependency Injection

FastAPI DI para database sessions:

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/projects")
def get_projects(db: Session = Depends(get_db)):
    ...
```

### 3. Singleton Pattern

Orchestrator de agentes es singleton:

```python
_orchestrator = None

def get_orchestrator() -> AgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
```

### 4. Strategy Pattern

Diferentes agentes para diferentes estrategias:

```python
orchestrator.quick_code_generation(
    request,
    agent_type="coding"  # or "ui_designer", "architect"
)
```

## 📊 Diagrama de Secuencia - Generación de Código

```
User    API    Service    Agent    DB
 │       │        │         │       │
 │──1──>│        │         │       │  POST /chat/{project_id}
 │       │──2──>│         │       │  process_chat_message()
 │       │       │──3───>│        │  Get project files
 │       │       │<──4────│        │  Files context
 │       │       │──5────────>│    │  generate_code(msg, ctx)
 │       │       │         │   │   │
 │       │       │         │   │   │  [AutoGen Group Chat]
 │       │       │         │   │   │  Architect -> plans
 │       │       │         │   │   │  UIDesigner -> designs
 │       │       │         │   │   │  CodingAgent -> codes
 │       │       │         │   │   │  CodeReviewer -> reviews
 │       │       │         │   │   │
 │       │       │<──6───────<│    │  Generated code
 │       │       │──7────────────>│  Update files
 │       │       │<──8────────────│  Saved
 │       │<──9──│         │       │  Response + changes
 │<─10──│       │         │       │  JSON response
```

## 🔧 Extensibilidad

### Agregar Nuevo Agente

```python
# 1. Crear mensaje de sistema en agents/config.py
NEW_AGENT_SYSTEM_MESSAGE = """..."""

# 2. Inicializar en orchestrator.py
self.new_agent = AssistantAgent(
    name="NewAgent",
    system_message=NEW_AGENT_SYSTEM_MESSAGE,
    llm_config=self.llm_config
)

# 3. Agregar a group chat
groupchat = GroupChat(
    agents=[..., self.new_agent],
    ...
)
```

### Agregar Nuevo Endpoint

```python
# 1. Crear schema en schemas/
class NewResource(BaseModel):
    ...

# 2. Crear modelo en models/
class NewModel(Base):
    ...

# 3. Crear servicio en services/
class NewService:
    @staticmethod
    def create(...):
        ...

# 4. Crear endpoint en api/
@router.post("/new")
def create_new(data: NewResource):
    return NewService.create(data)
```

## 🎯 Consideraciones de Performance

1. **Connection Pooling**: SQLAlchemy maneja pool de conexiones
2. **Lazy Loading**: Relaciones cargadas bajo demanda
3. **Agent Singleton**: Un solo orchestrator reutilizado
4. **Async Support**: FastAPI async-ready

## 🚦 Próximas Mejoras

1. **Caché**: Redis para respuestas frecuentes
2. **Queue**: Celery para procesamiento async de agentes
3. **WebSockets**: Updates en tiempo real
4. **Métricas**: Prometheus/Grafana
5. **Rate Limiting**: Limitar requests por usuario
6. **Testing**: Unit tests, integration tests

## 📚 Referencias

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [AutoGen Docs](https://microsoft.github.io/autogen/)
- [Pydantic Docs](https://docs.pydantic.dev/)
