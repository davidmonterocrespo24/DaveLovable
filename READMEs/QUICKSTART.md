# 🚀 Guía de Inicio Rápido

Esta guía te ayudará a tener el backend funcionando en menos de 5 minutos.

## ⚡ Instalación Rápida

### 1. Prerrequisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Una API key de OpenAI ([obtener aquí](https://platform.openai.com/api-keys))

### 2. Instalación en 3 pasos

```bash
# Paso 1: Navegar al directorio backend
cd backend

# Paso 2: Crear entorno virtual e instalar dependencias
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt

# Paso 3: Configurar variables de entorno
cp .env.example .env
# Edita .env y agrega tu OPENAI_API_KEY
```

### 3. Inicializar y Ejecutar

```bash
# Inicializar base de datos
python init_db.py

# Ejecutar servidor
python run.py
```

¡Listo! La API estará corriendo en http://localhost:8000

## 🧪 Probar la API

### Opción 1: Swagger UI (Recomendado)

Abre tu navegador en: http://localhost:8000/docs

Aquí puedes:
- Ver todos los endpoints
- Probar requests directamente
- Ver ejemplos de request/response

### Opción 2: cURL

```bash
# 1. Crear un proyecto
curl -X POST "http://localhost:8000/api/v1/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mi Primer Proyecto",
    "description": "Proyecto de prueba",
    "template": "react-vite"
  }'

# 2. Listar proyectos
curl "http://localhost:8000/api/v1/projects"

# 3. Enviar mensaje al chat
curl -X POST "http://localhost:8000/api/v1/chat/1" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Crea un componente Button con variantes primary y secondary"
  }'
```

### Opción 3: Python Requests

```python
import requests

# Base URL
BASE_URL = "http://localhost:8000/api/v1"

# Crear proyecto
response = requests.post(f"{BASE_URL}/projects", json={
    "name": "Mi Proyecto",
    "description": "Proyecto de prueba",
    "template": "react-vite"
})
project = response.json()
print(f"Proyecto creado: {project['id']}")

# Enviar mensaje al chat
response = requests.post(f"{BASE_URL}/chat/{project['id']}", json={
    "message": "Añade un componente Card con sombra y hover effect"
})
chat_response = response.json()
print(f"Respuesta: {chat_response['message']['content']}")
print(f"Cambios en código: {len(chat_response['code_changes'])} archivos")
```

## 📱 Integración con Frontend

Si estás usando el frontend de este proyecto:

1. Asegúrate que el backend esté corriendo en `http://localhost:8000`
2. El frontend debe estar configurado para usar esta URL
3. CORS ya está configurado para `localhost:5173` (Vite)

## 🎯 Flujo de Trabajo Típico

### Crear un proyecto y generar código con IA

```bash
# 1. Crear proyecto
POST /api/v1/projects
{
  "name": "Mi App",
  "template": "react-vite"
}
# Respuesta: { "id": 1, "name": "Mi App", ... }

# 2. Iniciar chat con IA
POST /api/v1/chat/1
{
  "message": "Crea un dashboard con gráficos y tarjetas"
}
# Respuesta: Código generado y guardado automáticamente

# 3. Obtener archivos generados
GET /api/v1/projects/1/files
# Respuesta: Lista de archivos con su contenido

# 4. Ver el proyecto completo
GET /api/v1/projects/1
# Respuesta: Proyecto con todos sus archivos
```

## 🔑 Configuración de OpenAI API Key

### Obtener tu API Key

1. Ve a https://platform.openai.com/api-keys
2. Inicia sesión o crea una cuenta
3. Clic en "Create new secret key"
4. Copia la key (empieza con `sk-...`)

### Configurar en el proyecto

Edita el archivo `.env`:

```env
OPENAI_API_KEY="sk-tu-api-key-aqui"
OPENAI_MODEL="gpt-4"  # o "gpt-3.5-turbo" para ahorrar costos
```

### Modelos Recomendados

- **gpt-4**: Mejor calidad, más costoso (recomendado para producción)
- **gpt-3.5-turbo**: Buena calidad, más económico (bueno para desarrollo)
- **gpt-4-turbo**: Balance entre calidad y costo

## 🐛 Solución de Problemas

### Error: "Module not found"

```bash
# Asegúrate de tener el entorno virtual activado
pip install -r requirements.txt
```

### Error: "OPENAI_API_KEY not configured"

```bash
# Verifica que el archivo .env existe y tiene la key
cat .env  # Linux/Mac
type .env  # Windows

# Debe contener:
OPENAI_API_KEY="sk-..."
```

### Error: "Port 8000 already in use"

```bash
# Cambia el puerto en run.py o usa:
uvicorn app.main:app --port 8001
```

### Base de datos no se crea

```bash
# Elimina la BD existente y reinicializa
rm lovable_dev.db  # Linux/Mac
del lovable_dev.db  # Windows

python init_db.py
```

## 📊 Endpoints Principales

### Proyectos

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/projects` | Crear proyecto |
| GET | `/api/v1/projects` | Listar proyectos |
| GET | `/api/v1/projects/{id}` | Obtener proyecto |
| PUT | `/api/v1/projects/{id}` | Actualizar proyecto |
| DELETE | `/api/v1/projects/{id}` | Eliminar proyecto |

### Chat con IA

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/chat/{project_id}` | Enviar mensaje |
| GET | `/api/v1/chat/{project_id}/sessions` | Listar sesiones |
| GET | `/api/v1/chat/{project_id}/sessions/{id}` | Ver sesión |

### Archivos

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/projects/{id}/files` | Listar archivos |
| POST | `/api/v1/projects/{id}/files` | Crear archivo |
| PUT | `/api/v1/projects/{id}/files/{file_id}` | Actualizar archivo |
| DELETE | `/api/v1/projects/{id}/files/{file_id}` | Eliminar archivo |

## 💡 Ejemplos de Prompts para el Chat

### Crear componentes

```
"Crea un componente Button con variantes primary, secondary y outline"
"Añade un componente Card con imagen, título, descripción y botón"
"Genera un Header responsive con logo y navegación"
```

### Modificar estilos

```
"Cambia los colores del tema a azul y amarillo"
"Añade animaciones hover a todos los botones"
"Haz el diseño más moderno con glassmorphism"
```

### Añadir funcionalidad

```
"Añade un formulario de contacto con validación"
"Crea un sistema de pestañas para organizar el contenido"
"Implementa un carrusel de imágenes"
```

### Crear páginas completas

```
"Crea una landing page con hero, features y CTA"
"Genera un dashboard con gráficos y métricas"
"Diseña una página de pricing con 3 planes"
```

## 🎓 Próximos Pasos

1. **Explora la API**: Usa Swagger UI en `/docs`
2. **Lee la arquitectura**: Consulta `ARCHITECTURE.md`
3. **Experimenta con agentes**: Prueba diferentes prompts
4. **Integra con frontend**: Conecta con tu aplicación React

## 📚 Recursos Adicionales

- [Documentación completa](README.md)
- [Arquitectura del sistema](ARCHITECTURE.md)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [AutoGen Docs](https://microsoft.github.io/autogen/)

## 🆘 ¿Necesitas Ayuda?

- Revisa los logs en la consola donde corre el servidor
- Consulta la documentación de cada componente
- Verifica que todas las dependencias estén instaladas
- Asegúrate que la API key de OpenAI sea válida

---

**¡Feliz coding! 🚀**
