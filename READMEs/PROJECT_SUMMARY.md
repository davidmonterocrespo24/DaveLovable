# 📦 Lovable Dev Clone - Resumen del Proyecto

## 🎯 Descripción General

Un clon completo de lovable.dev que permite crear proyectos web con IA. El sistema incluye:

- **Frontend**: React + TypeScript + Vite con editor de código visual
- **Backend**: FastAPI + SQLite + Microsoft AutoGen para orquestación de agentes LLM
- **Preview en Navegador**: Usando WebContainers API de StackBlitz (integración pendiente)

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (React)                       │
│  - Landing Page                                             │
│  - Editor con Chat, Code Editor, Preview                   │
│  - File Explorer                                            │
│  - Resizable Panels                                         │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   BACKEND (FastAPI)                         │
│                                                             │
│  ┌──────────────────────────────────────────────┐          │
│  │          API Layer (FastAPI)                 │          │
│  │  - Projects CRUD                             │          │
│  │  - Chat with AI                              │          │
│  │  - File Management                           │          │
│  └──────────────┬───────────────────────────────┘          │
│                 │                                           │
│  ┌──────────────▼───────────────────────────────┐          │
│  │         Service Layer                        │          │
│  │  - ProjectService                            │          │
│  │  - ChatService                               │          │
│  └──────────────┬───────────────────────────────┘          │
│                 │                                           │
│        ┌────────┴─────────┐                                │
│        │                  │                                │
│  ┌─────▼──────┐   ┌──────▼──────────────────────┐         │
│  │  Database  │   │   Agent Orchestrator        │         │
│  │  (SQLite)  │   │   (Microsoft AutoGen)       │         │
│  │            │   │  - Coding Agent             │         │
│  │  Models:   │   │  - UI Designer              │         │
│  │  - User    │   │  - Code Reviewer            │         │
│  │  - Project │   │  - Architect                │         │
│  │  - File    │   │                             │         │
│  │  - Chat    │   └─────────────────────────────┘         │
│  └────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
```

## 📂 Estructura Completa del Proyecto

```
DaveLovable/
├── DaveLovable/                    # FRONTEND
│   ├── src/
│   │   ├── components/
│   │   │   ├── editor/            # Componentes del editor
│   │   │   │   ├── ChatPanel.tsx
│   │   │   │   ├── CodeEditor.tsx
│   │   │   │   ├── PreviewPanel.tsx
│   │   │   │   ├── FileExplorer.tsx
│   │   │   │   └── EditorTabs.tsx
│   │   │   ├── ui/                # Componentes UI (shadcn)
│   │   │   ├── HeroSection.tsx
│   │   │   ├── FeaturesSection.tsx
│   │   │   ├── HowItWorksSection.tsx
│   │   │   ├── CTASection.tsx
│   │   │   ├── Footer.tsx
│   │   │   └── Navbar.tsx
│   │   ├── pages/
│   │   │   ├── Index.tsx          # Landing page
│   │   │   ├── Editor.tsx         # Editor principal
│   │   │   └── NotFound.tsx
│   │   ├── hooks/
│   │   ├── lib/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── tailwind.config.ts
│
└── backend/                        # BACKEND
    ├── app/
    │   ├── agents/                # Sistema de Agentes AutoGen
    │   │   ├── config.py         # Configuración de agentes
    │   │   ├── orchestrator.py   # Orquestador principal
    │   │   └── __init__.py
    │   ├── api/                  # Endpoints REST
    │   │   ├── projects.py       # CRUD proyectos
    │   │   ├── chat.py          # Chat con IA
    │   │   └── __init__.py
    │   ├── core/                # Configuración central
    │   │   ├── config.py        # Settings
    │   │   ├── security.py      # JWT, hashing
    │   │   └── __init__.py
    │   ├── db/                  # Base de datos
    │   │   ├── database.py      # SQLAlchemy setup
    │   │   └── __init__.py
    │   ├── models/              # Modelos SQLAlchemy
    │   │   ├── user.py
    │   │   ├── project.py
    │   │   ├── file.py
    │   │   ├── chat.py
    │   │   └── __init__.py
    │   ├── schemas/             # Schemas Pydantic
    │   │   ├── user.py
    │   │   ├── project.py
    │   │   ├── file.py
    │   │   ├── chat.py
    │   │   └── __init__.py
    │   ├── services/            # Lógica de negocio
    │   │   ├── project_service.py
    │   │   ├── chat_service.py
    │   │   └── __init__.py
    │   ├── main.py             # App FastAPI principal
    │   └── __init__.py
    ├── requirements.txt        # Dependencias Python
    ├── .env.example           # Variables de entorno
    ├── .gitignore
    ├── run.py                 # Script para ejecutar
    ├── init_db.py            # Inicializar BD
    ├── README.md             # Documentación principal
    ├── ARCHITECTURE.md       # Documentación arquitectura
    └── QUICKSTART.md         # Guía rápida
```

## 🚀 Características Implementadas

### Frontend ✅

1. **Landing Page Completa**
   - Hero section con animaciones
   - Features section
   - How it works section
   - CTA section
   - Footer responsive

2. **Editor de Código**
   - Panel de chat con IA (UI completa)
   - Editor de código con syntax highlighting
   - Preview panel (UI preparado)
   - File Explorer
   - Tabs para múltiples archivos
   - Paneles redimensionables
   - Diseño responsivo

3. **UI/UX**
   - Diseño moderno con Tailwind CSS
   - Componentes shadcn/ui
   - Tema oscuro
   - Animaciones suaves
   - Iconos Lucide React

### Backend ✅

1. **API REST Completa**
   - CRUD de proyectos
   - Gestión de archivos
   - Sistema de chat con IA
   - Documentación automática (Swagger)

2. **Base de Datos**
   - SQLite con SQLAlchemy ORM
   - Modelos: User, Project, ProjectFile, ChatSession, ChatMessage
   - Relaciones bien definidas
   - Migraciones preparadas

3. **Sistema de Agentes IA (AutoGen)**
   - Coding Agent - Genera código
   - UI Designer - Diseña interfaces
   - Code Reviewer - Revisa código
   - Architect - Planifica arquitectura
   - Orquestación colaborativa

4. **Seguridad**
   - Hash de contraseñas con bcrypt
   - JWT tokens preparado
   - CORS configurado
   - Validación con Pydantic

5. **Documentación**
   - README completo
   - Arquitectura detallada
   - Guía de inicio rápido
   - Ejemplos de uso

## 🔧 Tecnologías Utilizadas

### Frontend
- React 18.3
- TypeScript 5.8
- Vite 5.4
- Tailwind CSS 3.4
- shadcn/ui (Radix UI)
- React Router 6.30
- TanStack Query 5.83
- Lucide React (iconos)

### Backend
- Python 3.8+
- FastAPI 0.109
- SQLAlchemy 2.0
- Pydantic 2.5
- Microsoft AutoGen 0.2.18
- OpenAI API
- Uvicorn (ASGI server)
- python-jose (JWT)
- passlib (hashing)

## 📋 Estado Actual

### ✅ Completado

- [x] Frontend completo (UI/UX)
- [x] Backend completo (API + DB)
- [x] Sistema de agentes AutoGen
- [x] Modelos de base de datos
- [x] API endpoints
- [x] Documentación completa
- [x] Scripts de inicialización

### 🔨 Pendiente de Integración

- [ ] Conectar frontend con backend
- [ ] Implementar llamadas API desde frontend
- [ ] Integrar WebContainers API
- [ ] Sistema de autenticación frontend
- [ ] Preview real en navegador
- [ ] Deploy del sistema completo

### 🚧 Mejoras Futuras

- [ ] WebSockets para updates en tiempo real
- [ ] Sistema de colaboración multi-usuario
- [ ] Historial de versiones (git integration)
- [ ] Export de proyectos
- [ ] Templates adicionales
- [ ] Caché con Redis
- [ ] Tests unitarios e integración
- [ ] CI/CD pipeline

## 🚀 Cómo Ejecutar

### Backend

```bash
cd backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar .env
cp .env.example .env
# Editar .env y agregar OPENAI_API_KEY

# Inicializar BD
python init_db.py

# Ejecutar servidor
python run.py
```

Backend corriendo en: http://localhost:8000
API Docs: http://localhost:8000/docs

### Frontend

```bash
cd DaveLovable

# Instalar dependencias
npm install

# Ejecutar dev server
npm run dev
```

Frontend corriendo en: http://localhost:5173

## 📊 API Endpoints

### Proyectos
- `POST /api/v1/projects` - Crear proyecto
- `GET /api/v1/projects` - Listar proyectos
- `GET /api/v1/projects/{id}` - Obtener proyecto
- `PUT /api/v1/projects/{id}` - Actualizar proyecto
- `DELETE /api/v1/projects/{id}` - Eliminar proyecto

### Archivos
- `GET /api/v1/projects/{id}/files` - Listar archivos
- `POST /api/v1/projects/{id}/files` - Crear archivo
- `PUT /api/v1/projects/{id}/files/{file_id}` - Actualizar archivo
- `DELETE /api/v1/projects/{id}/files/{file_id}` - Eliminar archivo

### Chat
- `POST /api/v1/chat/{project_id}` - Enviar mensaje y obtener respuesta IA
- `GET /api/v1/chat/{project_id}/sessions` - Listar sesiones
- `GET /api/v1/chat/{project_id}/sessions/{id}` - Obtener sesión

## 🔑 Configuración Requerida

### Variables de Entorno (.env)

```env
# OpenAI (REQUERIDO para agentes IA)
OPENAI_API_KEY="sk-..."
OPENAI_MODEL="gpt-4"

# App
DEBUG=True

# Database
DATABASE_URL="sqlite:///./lovable_dev.db"

# Security
SECRET_KEY="tu-clave-secreta"
```

## 📚 Documentación Completa

- [Backend README](backend/README.md) - Documentación completa del backend
- [Architecture](backend/ARCHITECTURE.md) - Arquitectura detallada
- [Quickstart](backend/QUICKSTART.md) - Guía de inicio rápido

## 🎯 Casos de Uso

### 1. Crear un proyecto nuevo
```
Usuario → Frontend → POST /api/v1/projects
Backend → Crea proyecto en BD
Backend → Inicializa archivos (App.tsx, main.tsx, etc.)
Backend → Retorna proyecto con archivos
```

### 2. Generar código con IA
```
Usuario escribe: "Crea un botón con gradiente"
Frontend → POST /api/v1/chat/{project_id}
Backend → Orquesta agentes AutoGen
Agents → Architect planifica, UIDesigner diseña, CodingAgent codifica
Backend → Guarda código en archivos
Backend → Retorna respuesta + cambios
Frontend → Actualiza vista de archivos
```

### 3. Editar código manualmente
```
Usuario edita archivo en CodeEditor
Frontend → PUT /api/v1/projects/{id}/files/{file_id}
Backend → Actualiza archivo en BD
Backend → Retorna archivo actualizado
```

## 💡 Notas Importantes

1. **El frontend es solo UI**: No hace llamadas reales al backend aún
2. **AutoGen requiere OpenAI**: Necesitas una API key válida
3. **SQLite para desarrollo**: Considera PostgreSQL para producción
4. **Usuario mockeado**: MOCK_USER_ID = 1 (auth pendiente en frontend)
5. **WebContainers pendiente**: Preview simulado por ahora

## 🎓 Próximos Pasos para Conectar

1. **Crear servicio API en frontend**:
   ```typescript
   // src/services/api.ts
   const API_URL = 'http://localhost:8000/api/v1';
   ```

2. **Implementar hooks para datos**:
   ```typescript
   // src/hooks/useProjects.ts
   const useProjects = () => {
     return useQuery(['projects'], fetchProjects);
   };
   ```

3. **Conectar ChatPanel con backend**:
   ```typescript
   const handleSend = async (message) => {
     await sendChatMessage(projectId, message);
   };
   ```

4. **Implementar actualización en tiempo real**:
   - WebSockets o polling
   - Actualizar CodeEditor cuando cambian archivos
   - Sincronizar Preview con cambios

## 🏆 Logros del Proyecto

✅ Backend completo y funcional con AutoGen
✅ Frontend moderno y responsive
✅ Arquitectura escalable y mantenible
✅ Documentación exhaustiva
✅ Sistema de agentes IA colaborativos
✅ API REST bien diseñada
✅ UI/UX profesional

## 📝 Licencia

Proyecto educativo - Prototipo

---

**Desarrollado como clon de lovable.dev con tecnologías modernas** 🚀
