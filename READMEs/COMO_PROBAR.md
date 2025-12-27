# Cómo Probar la Implementación Completa

## Pasos para Probar

### 1. Asegúrate de que el Backend está corriendo

En una terminal:
```bash
cd backend
python run.py
```

**Deberías ver:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Application startup complete.
```

**Verifica en el navegador:**
- http://localhost:8000 → Debe mostrar mensaje de bienvenida
- http://localhost:8000/docs → Debe mostrar Swagger UI

### 2. Asegúrate de que el Frontend está corriendo

En otra terminal:
```bash
cd front
npm run dev
```

**Deberías ver:**
```
VITE v5.4.11  ready in XXX ms

➜  Local:   http://[::]:8080/
➜  Network: use --host to expose
```

**Importante:** Asegúrate de que está en el puerto **8080** (no 8081)

### 3. Abre el Editor en el Navegador

**Navegador recomendado:** Chrome o Edge (Firefox y Safari NO soportan WebContainers)

Abre: **http://localhost:8080/editor/3**

### 4. Observa la Inicialización

**En el PreviewPanel (panel derecho) deberías ver:**

#### Paso 1: Inicializando (2-3 segundos)
```
[WebContainer] Initializing...
[WebContainer] Getting instance...
[WebContainer] Booting...
```

#### Paso 2: Cargando archivos (< 1 segundo)
```
[WebContainer] Ready
[WebContainer] Fetching project files...
[WebContainer] Received 9 files
[WebContainer] Converting file structure...
[WebContainer] Mounting files...
[WebContainer] Files mounted successfully
```

#### Paso 3: Instalando dependencias (5-15 segundos)
```
[WebContainer] Installing dependencies...
[npm] npm WARN deprecated inflight@1.0.6: This module is not supported...
[npm]
[npm] added 234 packages, and audited 235 packages in 8s
[npm]
[npm] 78 packages are looking for funding
```

#### Paso 4: Iniciando dev server (< 1 segundo)
```
[WebContainer] Dependencies installed successfully
[WebContainer] Starting dev server...
[dev]
[dev] VITE v5.4.11  ready in 523 ms
[dev]
[dev] ➜  Local:   http://localhost:5173/
```

#### Paso 5: Listo ✓
```
✓ Application ready at http://localhost:5173/
```

**El iframe debe mostrar la aplicación corriendo:**
- Título: "Welcome to Your App"
- Botón: "Count is: 0"
- 3 Cards con imágenes
- Diseño con gradientes oscuros

### 5. Verifica el FileExplorer

**En el panel izquierdo deberías ver:**

```
📁 src
  📄 App.tsx
  📄 main.tsx
  📄 index.css
  📁 components
    📄 CardProps.tsx
```

**Si no ves los archivos:**
1. Abre la consola del navegador (F12)
2. Ve a la pestaña Network
3. Busca el request a `/api/v1/projects/3/files`
4. Verifica que devuelve un array con 4 archivos

### 6. Prueba la Generación de Código

**En el ChatPanel (panel izquierdo), escribe:**
```
Create a simple ContactForm component with name, email and message fields
```

**Deberías ver:**
1. **Loading:** Spinner girando mientras el AI procesa
2. **Respuesta:** El AI muestra el código generado en su mensaje
3. **FileExplorer actualizado:** Aparece `ContactForm.tsx` en `src/components/`
4. **Console del Preview:** Puede mostrar "HMR update" si el archivo se usa

**Click en el nuevo archivo:**
- CodeEditor debe mostrar el código del ContactForm
- Deberías ver campos de formulario, inputs, botón de submit, etc.

### 7. Prueba el Refresh del Preview

**Click en el botón de Refresh (icono de refresh en toolbar del preview):**
1. Console se limpia
2. Se muestra "Initializing..."
3. El proceso de npm install se repite (más rápido porque está cacheado)
4. Dev server se reinicia
5. Preview se actualiza

## Verificaciones de Funcionamiento

### ✅ Backend

**Test 1: Health Check**
```bash
curl http://localhost:8000/health
```
**Esperado:** `{"status":"healthy"}`

**Test 2: Get Project**
```bash
curl http://localhost:8000/api/v1/projects/3
```
**Esperado:** JSON con el proyecto y sus archivos

**Test 3: Get Bundle**
```bash
curl http://localhost:8000/api/v1/projects/3/bundle
```
**Esperado:** JSON con `{"files": { "package.json": "...", ... }}`

**Test 4: Archivos Físicos**
```bash
ls backend/projects/project_3/
```
**Esperado:**
```
index.html
package.json
postcss.config.js
src/
tailwind.config.js
tsconfig.json
vite.config.ts
```

### ✅ Frontend

**Test 1: Página Principal**
- Abre: http://localhost:8080
- **Esperado:** Landing page o redirect

**Test 2: Editor**
- Abre: http://localhost:8080/editor/3
- **Esperado:** Editor con FileExplorer, CodeEditor, ChatPanel, PreviewPanel

**Test 3: Consola del Navegador**
- Abre DevTools (F12)
- Ve a Console
- **NO deberías ver errores en rojo**
- Puede haber warnings (amarillo) de React DevTools - es normal

**Test 4: Network**
- Abre DevTools (F12) → Network tab
- Recarga la página
- **Deberías ver requests exitosos:**
  - `GET /api/v1/projects/3` → 200 OK
  - `GET /api/v1/projects/3/files` → 200 OK
  - `GET /api/v1/projects/3/bundle` → 200 OK (cuando preview carga)

### ✅ WebContainers

**Test 1: Boot**
- Console del preview debe mostrar: `[WebContainer] Ready`
- **Si falla:** Verifica que estás usando Chrome/Edge

**Test 2: Install**
- Console debe mostrar: `[npm] added XXX packages`
- **Si falla:** Verifica conexión a internet

**Test 3: Dev Server**
- Console debe mostrar: `[dev] VITE v5.4.11 ready`
- URL bar debe mostrar: `http://localhost:5173/`
- **Si falla:** Revisa console por errores de Vite

**Test 4: Preview**
- Iframe debe mostrar la app corriendo
- App debe ser interactiva (botón de counter funciona)
- **Si está en blanco:** Abre console del iframe (click derecho en iframe → Inspect)

## Problemas Comunes

### Problema: "Cannot GET /api/v1/..."

**Síntoma:** Errores 404 en requests al backend

**Causa:** Backend no está corriendo

**Solución:**
```bash
cd backend
python run.py
```

### Problema: "Failed to boot WebContainer"

**Síntoma:** Error en console del preview

**Causa:** Navegador no soportado o headers incorrectos

**Solución:**
1. Usa Chrome o Edge (NO Firefox/Safari)
2. Verifica vite.config.ts tiene headers COOP/COEP
3. Recarga la página con Ctrl+F5 (hard reload)

### Problema: FileExplorer vacío

**Síntoma:** Panel de archivos dice "No files found"

**Causa:** Proyecto no tiene archivos en DB

**Solución:**
```bash
# Crear proyecto nuevo
curl -X POST http://localhost:8000/api/v1/projects/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","description":"Test","template":"react-vite"}'

# Usar el ID que devuelve
# Ejemplo: http://localhost:8080/editor/4
```

### Problema: "npm install failed"

**Síntoma:** Error en console del preview

**Causa:** Problema con package.json o red

**Solución:**
1. Verifica conexión a internet
2. Verifica package.json es válido
3. Intenta refresh
4. Si persiste, crea proyecto nuevo

### Problema: Preview muestra error de TypeScript

**Síntoma:** Pantalla roja con error de TS en el preview

**Causa:** Código generado tiene error de tipos

**Solución:**
1. No es un bug del sistema, es el código generado
2. Pide al AI que corrija: "Fix the TypeScript error in the last component"
3. O edita manualmente en CodeEditor

## Comandos Útiles

### Ver logs del backend
```bash
# En la terminal donde corre el backend, deberías ver:
INFO:     127.0.0.1:XXXXX - "GET /api/v1/projects/3/files HTTP/1.1" 200 OK
INFO:     127.0.0.1:XXXXX - "GET /api/v1/projects/3/bundle HTTP/1.1" 200 OK
```

### Ver archivos generados
```bash
# Windows
dir backend\projects\project_3\src\components\

# Linux/Mac
ls -la backend/projects/project_3/src/components/
```

### Limpiar cache de npm (si hay problemas)
```bash
# En el preview, ejecuta desde terminal (si implementaste)
# O simplemente haz refresh del preview
```

### Verificar DB
```bash
cd backend
python -c "
from app.db import SessionLocal
from app.models import ProjectFile
db = SessionLocal()
files = db.query(ProjectFile).filter(ProjectFile.project_id == 3).all()
for f in files:
    print(f'{f.id}: {f.filepath}')
"
```

## Checklist Final

Antes de dar por terminado, verifica:

- [ ] Backend corriendo en puerto 8000
- [ ] Frontend corriendo en puerto 8080
- [ ] Editor carga en http://localhost:8080/editor/3
- [ ] FileExplorer muestra al menos 4 archivos
- [ ] ChatPanel acepta mensajes
- [ ] CodeEditor muestra código con syntax highlighting
- [ ] PreviewPanel inicia WebContainer
- [ ] Console del preview muestra logs
- [ ] Preview iframe muestra app funcionando
- [ ] Botón de counter incrementa al hacer click
- [ ] AI genera código nuevo al enviar mensaje
- [ ] Archivo nuevo aparece en FileExplorer
- [ ] Refresh del preview funciona

## Resultado Esperado Final

Deberías tener un **editor funcional completo** donde:

1. ✅ Puedes chatear con AI para generar código
2. ✅ El código se guarda en DB y filesystem
3. ✅ Los archivos aparecen en FileExplorer
4. ✅ Puedes ver/editar código en CodeEditor
5. ✅ El preview ejecuta la app en el navegador (sin backend!)
6. ✅ Todo funciona en tiempo real

**¡Felicitaciones!** 🎉 Tienes un clon funcional de Lovable.dev con WebContainers.
