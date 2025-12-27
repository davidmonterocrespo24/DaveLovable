# Lovable Dev Clone - Backend

Backend completo para un clon de lovable.dev construido con FastAPI, SQLite y Microsoft AutoGen para orquestación de agentes LLM.

## 🚀 Características

- **FastAPI**: Framework web moderno y rápido
- **SQLite**: Base de datos ligera y fácil de configurar
- **Microsoft AutoGen**: Orquestación de múltiples agentes LLM para generación de código
- **Arquitectura Modular**: Separación clara de responsabilidades
- **API RESTful**: Endpoints bien documentados con OpenAPI/Swagger
- **Sistema de Agentes**:
  - **Coding Agent**: Genera código de alta calidad
  - **UI Designer**: Especializado en diseño de interfaces
  - **Code Reviewer**: Revisa y mejora el código
  - **Architect**: Diseña la arquitectura del sistema

## 📋 Requisitos Previos

- Python 3.8+
- pip
- Una API key de OpenAI (para usar los agentes LLM)

## 🛠️ Instalación

### 1. Clonar el repositorio y navegar al directorio backend

```bash
cd backend
```

### 2. Crear un entorno virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia el archivo `.env.example` a `.env`:

```bash
cp .env.example .env
```

Edita el archivo `.env` y configura tus credenciales:

```env
OPENAI_API_KEY="tu-api-key-de-openai"
SECRET_KEY="genera-una-clave-secreta-segura"
```

Para generar una clave secreta segura:

```bash
# En Python
python -c "import secrets; print(secrets.token_hex(32))"

# O con OpenSSL
openssl rand -hex 32
```

## 🚀 Ejecutar la Aplicación

### Opción 1: Usando el script run.py

```bash
python run.py
```

### Opción 2: Usando uvicorn directamente

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

La API estará disponible en:
- **API**: http://localhost:8000
- **Documentación Interactiva (Swagger)**: http://localhost:8000/docs
- **Documentación Alternativa (ReDoc)**: http://localhost:8000/redoc

## 📚 Estructura del Proyecto

```
backend/
├── app/
│   ├── agents/              # Sistema de agentes AutoGen
│   │   ├── __init__.py
│   │   ├── config.py        # Configuración de agentes
│   │   └── orchestrator.py  # Orquestador de agentes
│   ├── api/                 # Endpoints de la API
│   │   ├── __init__.py
│   │   ├── projects.py      # CRUD de proyectos
│   │   └── chat.py          # Chat con agentes LLM
│   ├── core/                # Configuración central
│   │   ├── __init__.py
│   │   ├── config.py        # Settings de la app
│   │   └── security.py      # Seguridad y autenticación
│   ├── db/                  # Configuración de base de datos
│   │   ├── __init__.py
│   │   └── database.py      # Setup de SQLAlchemy
│   ├── models/              # Modelos SQLAlchemy
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── file.py
│   │   └── chat.py
│   ├── schemas/             # Schemas Pydantic
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── file.py
│   │   └── chat.py
│   ├── services/            # Lógica de negocio
│   │   ├── __init__.py
│   │   ├── project_service.py
│   │   └── chat_service.py
│   ├── __init__.py
│   └── main.py              # Aplicación FastAPI principal
├── .env.example             # Ejemplo de variables de entorno
├── .gitignore
├── requirements.txt         # Dependencias Python
├── run.py                   # Script para ejecutar la app
└── README.md
```

## 🔌 API Endpoints

### Proyectos

- `POST /api/v1/projects` - Crear un nuevo proyecto
- `GET /api/v1/projects` - Listar todos los proyectos
- `GET /api/v1/projects/{project_id}` - Obtener un proyecto específico con sus archivos
- `PUT /api/v1/projects/{project_id}` - Actualizar un proyecto
- `DELETE /api/v1/projects/{project_id}` - Eliminar un proyecto

### Archivos de Proyecto

- `GET /api/v1/projects/{project_id}/files` - Listar archivos del proyecto
- `POST /api/v1/projects/{project_id}/files` - Agregar archivo al proyecto
- `PUT /api/v1/projects/{project_id}/files/{file_id}` - Actualizar archivo
- `DELETE /api/v1/projects/{project_id}/files/{file_id}` - Eliminar archivo

### Chat con Agentes LLM

- `POST /api/v1/chat/{project_id}` - Enviar mensaje y obtener respuesta de IA
- `POST /api/v1/chat/{project_id}/sessions` - Crear nueva sesión de chat
- `GET /api/v1/chat/{project_id}/sessions` - Listar sesiones de chat
- `GET /api/v1/chat/{project_id}/sessions/{session_id}` - Obtener sesión con mensajes
- `GET /api/v1/chat/{project_id}/sessions/{session_id}/messages` - Obtener mensajes
- `DELETE /api/v1/chat/{project_id}/sessions/{session_id}` - Eliminar sesión

## 🤖 Sistema de Agentes AutoGen

El backend utiliza Microsoft AutoGen para orquestar múltiples agentes especializados:

### Agentes Disponibles

1. **Coding Agent**: Genera código TypeScript/React de alta calidad
2. **UI Designer**: Se enfoca en diseño UI/UX y componentes visuales
3. **Code Reviewer**: Revisa código en busca de bugs y mejoras
4. **Architect**: Diseña la arquitectura y estructura del sistema

### Flujo de Trabajo

1. Usuario envía un mensaje/prompt
2. El orquestador distribuye la tarea entre los agentes
3. Los agentes colaboran en modo "group chat"
4. Se genera código basado en las contribuciones de todos
5. El código se guarda automáticamente en los archivos del proyecto

### Ejemplo de Uso

```python
from app.agents import get_orchestrator

orchestrator = get_orchestrator()

# Generar código
result = orchestrator.generate_code(
    "Crea un componente Button con variantes primary y secondary",
    context={"framework": "react"}
)

# Revisar código
review = orchestrator.review_code(
    code="function MyComponent() { ... }",
    context="React component"
)
```

## 🗄️ Base de Datos

El proyecto usa SQLite con SQLAlchemy ORM. La base de datos se crea automáticamente al iniciar la aplicación.

### Modelos Principales

- **User**: Usuarios del sistema
- **Project**: Proyectos de desarrollo
- **ProjectFile**: Archivos de código de cada proyecto
- **ChatSession**: Sesiones de chat con el asistente IA
- **ChatMessage**: Mensajes individuales del chat

### Migrar la Base de Datos (Alembic)

```bash
# Crear una migración
alembic revision --autogenerate -m "descripción"

# Aplicar migraciones
alembic upgrade head

# Revertir migración
alembic downgrade -1
```

## 🔒 Seguridad

- Autenticación JWT (configuración lista, endpoints de auth pendientes)
- Hash de contraseñas con bcrypt
- CORS configurado para desarrollo
- Validación de datos con Pydantic

## 🧪 Testing

```bash
# Instalar dependencias de testing
pip install pytest pytest-asyncio httpx

# Ejecutar tests
pytest
```

## 📝 Notas Importantes

1. **API Key de OpenAI**: Es necesaria para que funcione el sistema de agentes
2. **Modo Desarrollo**: El usuario está mockeado (MOCK_USER_ID = 1)
3. **Base de Datos**: SQLite es ideal para desarrollo, considera PostgreSQL para producción
4. **CORS**: Configurado para localhost:5173 (Vite) y localhost:3000

## 🚧 Próximos Pasos

- [ ] Implementar autenticación completa con JWT
- [ ] Agregar tests unitarios y de integración
- [ ] Implementar WebSockets para actualizaciones en tiempo real
- [ ] Agregar rate limiting
- [ ] Implementar caché con Redis
- [ ] Migrar a PostgreSQL para producción
- [ ] Implementar CI/CD
- [ ] Agregar métricas y logging avanzado

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es un prototipo educativo.

## 🙏 Agradecimientos

- FastAPI por el excelente framework
- Microsoft AutoGen por la orquestación de agentes
- OpenAI por los modelos LLM
- La comunidad de código abierto

---

**¿Necesitas ayuda?** Abre un issue en el repositorio.
