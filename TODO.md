# 🔥 TODO: Firebase Integration - Client-Side Persistence

## 📋 OBJETIVO

Integrar Firebase al sistema multi-agente de DaveLovable para que el agente pueda **detectar automáticamente** cuando el usuario necesita persistencia y ofrezca activar Firebase con un botón de confirmación en el chat.

---

## 🎯 COMPORTAMIENTO ESPERADO

### Flujo de Usuario:

1. **Usuario pide algo simple:**
   ```
   Usuario: "Crea un formulario HTML para crear un cliente"
   Agente: Genera formulario con campos name, email, phone
   ```

2. **Usuario pide persistencia/CRUD:**
   ```
   Usuario: "Quiero poder guardar múltiples clientes"
   ó "Quiero crear un CRUD completo"
   ó "Necesito cargar datos en el formulario"
   ```

3. **Agente detecta necesidad de DB:**
   ```
   Chat muestra mensaje:

   ┌─────────────────────────────────────────────────────┐
   │ 📊 Detección de Persistencia                        │
   ├─────────────────────────────────────────────────────┤
   │ Para guardar múltiples clientes necesitas una       │
   │ base de datos. ¿Quieres activar Firebase?          │
   │                                                     │
   │ Esto agregará:                                      │
   │ • Firestore Database (NoSQL)                        │
   │ • Firebase Authentication                           │
   │ • Firebase Storage (opcional)                       │
   │                                                     │
   │ [✅ Activar Firebase]  [❌ No, usar mock data]      │
   └─────────────────────────────────────────────────────┘
   ```

4. **Si usuario acepta:**
   ```
   Agente:
   - Crea configuración Firebase en proyecto
   - Genera servicios de persistencia
   - Implementa CRUD con Firestore
   - Muestra mensaje: "Firebase activado ✅"
   ```

5. **Si usuario rechaza:**
   ```
   Agente: Crea versión con mock data (localStorage o arrays)
   ```

---

## 🏗️ ARQUITECTURA DE LA SOLUCIÓN

### Componentes a Modificar/Crear:

```
backend/
├── app/
│   ├── agents/
│   │   ├── prompts.py                    # ✏️ MODIFICAR
│   │   └── orchestrator.py               # ✏️ MODIFICAR
│   ├── api/
│   │   └── chat.py                       # ✏️ MODIFICAR
│   └── services/
│       ├── chat_service.py               # ✏️ MODIFICAR
│       └── filesystem_service.py         # ✏️ MODIFICAR (template)

front/
├── src/
│   └── components/
│       └── editor/
│           └── ChatPanel.tsx             # ✏️ MODIFICAR
```

---

## 📝 TAREAS DETALLADAS

### FASE 1: Modificar Prompts del Agente

**Archivo:** `backend/app/agents/prompts.py`

#### ✅ Tarea 1.1: Agregar Detección de Persistencia al Prompt

**Ubicación:** Después de línea 110 (MOCK-FIRST DEVELOPMENT)

**Código a agregar:**

```python
**FIREBASE PERSISTENCE DETECTION:**
- If the user asks for features that require PERSISTENT STORAGE (database, multiple records, CRUD operations), you must DETECT this and PROPOSE Firebase.
- **TRIGGERS for Firebase detection:**
  - User says: "save", "store", "persist", "database", "CRUD", "load data", "multiple records", "fetch data"
  - User asks to create/read/update/delete multiple items
  - User wants data to survive page reloads

- **DETECTION RESPONSE FORMAT:**
  When you detect need for persistence, respond with EXACTLY this JSON:
  ```json
  {
    "type": "FIREBASE_ACTIVATION_REQUEST",
    "reason": "User requested [feature] which requires persistent storage",
    "features": ["firestore", "auth", "storage"],
    "message": "Para [feature] necesitas una base de datos. ¿Quieres activar Firebase?"
  }
  ```

- **After user APPROVES Firebase:**
  - Firebase configuration will be automatically added to the project template
  - You will receive a signal: `FIREBASE_ENABLED: true`
  - From that point, generate code using Firebase SDK (firestore, auth, storage)
  - Create services in `src/services/` for database operations
  - Use `src/lib/firebase.ts` for Firebase initialization

- **If user DECLINES Firebase:**
  - Use mock data with localStorage or in-memory arrays
  - Keep mock-first development pattern

**FIREBASE CODE PATTERNS:**
Once Firebase is enabled, use these patterns:

1. **Firestore CRUD:**
```typescript
// src/services/clientService.ts
import { db } from '@/lib/firebase';
import { collection, addDoc, getDocs, updateDoc, deleteDoc, doc } from 'firebase/firestore';

export const clientService = {
  async create(data: Client) {
    return await addDoc(collection(db, 'clients'), data);
  },
  async getAll() {
    const snapshot = await getDocs(collection(db, 'clients'));
    return snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
  },
  async update(id: string, data: Partial<Client>) {
    await updateDoc(doc(db, 'clients', id), data);
  },
  async delete(id: string) {
    await deleteDoc(doc(db, 'clients', id));
  }
};
```

2. **React Query Integration:**
```typescript
// src/hooks/useClients.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { clientService } from '@/services/clientService';

export function useClients() {
  const queryClient = useQueryClient();

  const { data: clients = [], isLoading } = useQuery({
    queryKey: ['clients'],
    queryFn: clientService.getAll
  });

  const createClient = useMutation({
    mutationFn: clientService.create,
    onSuccess: () => queryClient.invalidateQueries(['clients'])
  });

  return { clients, isLoading, createClient: createClient.mutate };
}
```

3. **Component Usage:**
```typescript
// src/components/ClientList.tsx
import { useClients } from '@/hooks/useClients';

export function ClientList() {
  const { clients, isLoading, createClient } = useClients();

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      {clients.map(client => <div key={client.id}>{client.name}</div>)}
    </div>
  );
}
```

**IMPORTANT:** Only use Firebase patterns AFTER receiving `FIREBASE_ENABLED: true` signal.
```

---

### FASE 2: Modificar Backend para Detectar y Procesar Request

**Archivo:** `backend/app/services/chat_service.py`

#### ✅ Tarea 2.1: Detector de Firebase Activation Request

**Ubicación:** Dentro de `process_chat_streaming()`, después de recibir mensaje del agente

**Código a agregar:**

```python
import json
import re

def detect_firebase_request(message_content: str) -> dict | None:
    """
    Detecta si el agente está solicitando activar Firebase
    """
    try:
        # Pattern 1: JSON directo
        if "FIREBASE_ACTIVATION_REQUEST" in message_content:
            # Extraer JSON del mensaje
            json_match = re.search(r'\{[^}]*"type"\s*:\s*"FIREBASE_ACTIVATION_REQUEST"[^}]*\}', message_content, re.DOTALL)
            if json_match:
                firebase_request = json.loads(json_match.group())
                return firebase_request

        # Pattern 2: Palabras clave en español
        persistence_keywords = [
            "necesitas una base de datos",
            "activar firebase",
            "persistir los datos",
            "guardar en base de datos"
        ]
        if any(keyword in message_content.lower() for keyword in persistence_keywords):
            return {
                "type": "FIREBASE_ACTIVATION_REQUEST",
                "reason": "Agent detected need for persistence",
                "message": message_content
            }

        return None
    except:
        return None
```

**Modificar streaming loop:**

```python
# En process_chat_streaming(), dentro del loop de mensajes del agente:

for message in response.messages:
    if message["role"] == "assistant":
        content = message.get("content", "")

        # NUEVA LÓGICA: Detectar Firebase request
        firebase_request = detect_firebase_request(content)

        if firebase_request:
            # Enviar evento especial al frontend
            yield {
                "type": "firebase_activation_request",
                "data": {
                    "message": firebase_request.get("message", ""),
                    "features": firebase_request.get("features", ["firestore", "auth"]),
                    "reason": firebase_request.get("reason", "")
                }
            }
            continue  # No enviar el mensaje raw, solo la request

        # Mensaje normal del agente
        yield {
            "type": "agent_message",
            "content": content
        }
```

#### ✅ Tarea 2.2: Endpoint para Confirmar Activación

**Archivo:** `backend/app/api/chat.py`

**Agregar nuevo endpoint:**

```python
@router.post("/{project_id}/activate-firebase")
async def activate_firebase(
    project_id: int,
    data: dict = Body(...),
    db: Session = Depends(get_db)
):
    """
    Activa Firebase en un proyecto específico

    Body:
    {
        "enabled": true/false,
        "features": ["firestore", "auth", "storage"]
    }
    """
    enabled = data.get("enabled", False)
    features = data.get("features", ["firestore"])

    if not enabled:
        return {"success": True, "message": "Firebase not enabled"}

    # Marcar proyecto como usando Firebase
    project = ProjectService.get_project(db, project_id, MOCK_USER_ID)

    # Activar Firebase en el proyecto
    result = await FileSystemService.activate_firebase(project_id, features)

    return {
        "success": True,
        "message": "Firebase activated",
        "files_created": result.get("files_created", []),
        "config_needed": result.get("config_needed", {})
    }
```

---

### FASE 3: Modificar Filesystem Service para Agregar Firebase Template

**Archivo:** `backend/app/services/filesystem_service.py`

#### ✅ Tarea 3.1: Template Firebase

**Agregar después de `create_project_structure()`:**

```python
FIREBASE_TEMPLATE_FILES = {
    ".env.local": """# Firebase Configuration
VITE_FIREBASE_API_KEY=your_api_key_here
VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your_project_id
VITE_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789
VITE_FIREBASE_APP_ID=1:123456789:web:abc123
VITE_FIREBASE_MEASUREMENT_ID=G-XXXXXXXXXX
""",

    "src/lib/firebase.ts": """import { initializeApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';
import { getAuth } from 'firebase/auth';
import { getStorage } from 'firebase/storage';
import { getAnalytics } from 'firebase/analytics';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID
};

// Initialize Firebase
export const app = initializeApp(firebaseConfig);

// Initialize services
export const db = getFirestore(app);
export const auth = getAuth(app);
export const storage = getStorage(app);
export const analytics = typeof window !== 'undefined' ? getAnalytics(app) : null;

export default app;
""",

    "src/types/firebase.ts": """import { Timestamp } from 'firebase/firestore';

export interface FirebaseDocument {
  id: string;
  createdAt: Timestamp | Date;
  updatedAt: Timestamp | Date;
}

export interface QueryOptions {
  limit?: number;
  orderBy?: string;
  direction?: 'asc' | 'desc';
}
""",

    "README.firebase.md": """# Firebase Setup Instructions

## 1. Create Firebase Project

1. Go to https://console.firebase.google.com/
2. Click "Add project"
3. Enter project name
4. Enable Google Analytics (recommended)
5. Click "Create project"

## 2. Enable Services

### Firestore Database
1. Build → Firestore Database
2. Click "Create database"
3. Start in: **Test mode** (for development)
4. Location: Select closest region
5. Click "Enable"

### Authentication (Optional)
1. Build → Authentication
2. Click "Get started"
3. Enable Email/Password
4. Enable Google Sign-In

### Storage (Optional)
1. Build → Storage
2. Click "Get started"
3. Start in: **Test mode**

## 3. Get Configuration

1. Project Overview → Project Settings (⚙️ icon)
2. Scroll to "Your apps"
3. Click Web icon (</>)
4. Register app with nickname
5. **Copy the firebaseConfig object**

## 4. Add to Your Project

Paste the config values in `.env.local` file.

## 5. Security Rules (Production)

**Firestore Rules:**
\`\`\`javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read: if true;
      allow write: if request.auth != null;
    }
  }
}
\`\`\`

**Storage Rules:**
\`\`\`javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /{allPaths=**} {
      allow read: if true;
      allow write: if request.auth != null;
    }
  }
}
\`\`\`
"""
}

@staticmethod
async def activate_firebase(project_id: int, features: list[str]) -> dict:
    """
    Activa Firebase en un proyecto existente
    """
    project_dir = os.path.join(PROJECTS_DIR, f"project_{project_id}")

    if not os.path.exists(project_dir):
        raise FileNotFoundError(f"Project {project_id} not found")

    files_created = []

    # Crear archivos base de Firebase
    for filepath, content in FIREBASE_TEMPLATE_FILES.items():
        full_path = os.path.join(project_dir, filepath)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

        files_created.append(filepath)

    # Actualizar package.json para incluir Firebase
    package_json_path = os.path.join(project_dir, "package.json")
    with open(package_json_path, 'r', encoding='utf-8') as f:
        package_data = json.load(f)

    # Agregar dependencias de Firebase
    if "dependencies" not in package_data:
        package_data["dependencies"] = {}

    package_data["dependencies"]["firebase"] = "^10.8.0"

    with open(package_json_path, 'w', encoding='utf-8') as f:
        json.dump(package_data, f, indent=2)

    files_created.append("package.json (updated)")

    # Crear archivo de estado
    firebase_state = {
        "enabled": True,
        "features": features,
        "activated_at": datetime.now().isoformat()
    }

    state_path = os.path.join(project_dir, ".firebase-state.json")
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(firebase_state, f, indent=2)

    return {
        "files_created": files_created,
        "config_needed": {
            "message": "Firebase activated! Please configure your .env.local with your Firebase credentials.",
            "instructions_file": "README.firebase.md"
        }
    }
```

---

### FASE 4: Modificar Frontend - Chat Panel

**Archivo:** `front/src/components/editor/ChatPanel.tsx`

#### ✅ Tarea 4.1: Agregar Modal de Confirmación Firebase

**Agregar estado:**

```typescript
const [firebaseRequest, setFirebaseRequest] = useState<{
  message: string;
  features: string[];
  reason: string;
} | null>(null);
```

**Agregar listener en SSE:**

```typescript
eventSource.addEventListener('firebase_activation_request', (e) => {
  const data = JSON.parse(e.data);
  setFirebaseRequest({
    message: data.message,
    features: data.features || ['firestore', 'auth'],
    reason: data.reason
  });
});
```

**Agregar componente de modal:**

```typescript
{firebaseRequest && (
  <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
      <div className="flex items-start gap-3 mb-4">
        <div className="w-10 h-10 rounded-full bg-orange-100 flex items-center justify-center flex-shrink-0">
          <Database className="w-5 h-5 text-orange-600" />
        </div>
        <div>
          <h3 className="font-semibold text-lg">📊 Detección de Persistencia</h3>
          <p className="text-sm text-gray-600 mt-1">
            {firebaseRequest.message}
          </p>
        </div>
      </div>

      <div className="bg-blue-50 rounded-lg p-4 mb-4">
        <p className="text-sm font-medium text-blue-900 mb-2">
          Esto agregará:
        </p>
        <ul className="text-sm text-blue-800 space-y-1">
          {firebaseRequest.features.includes('firestore') && (
            <li className="flex items-center gap-2">
              <Check className="w-4 h-4" />
              Firestore Database (NoSQL)
            </li>
          )}
          {firebaseRequest.features.includes('auth') && (
            <li className="flex items-center gap-2">
              <Check className="w-4 h-4" />
              Firebase Authentication
            </li>
          )}
          {firebaseRequest.features.includes('storage') && (
            <li className="flex items-center gap-2">
              <Check className="w-4 h-4" />
              Firebase Storage
            </li>
          )}
        </ul>
      </div>

      <div className="flex gap-3">
        <button
          onClick={() => handleFirebaseDecision(true)}
          className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 font-medium transition-colors"
        >
          ✅ Activar Firebase
        </button>
        <button
          onClick={() => handleFirebaseDecision(false)}
          className="flex-1 bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 font-medium transition-colors"
        >
          ❌ Usar mock data
        </button>
      </div>

      <p className="text-xs text-gray-500 mt-3 text-center">
        Necesitarás configurar Firebase en console.firebase.google.com
      </p>
    </div>
  </div>
)}
```

**Handler para decisión:**

```typescript
const handleFirebaseDecision = async (enabled: boolean) => {
  try {
    // Enviar decisión al backend
    const response = await fetch(`${API_URL}/chat/${projectId}/activate-firebase`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        enabled,
        features: firebaseRequest?.features || ['firestore']
      })
    });

    const result = await response.json();

    if (enabled) {
      // Mostrar mensaje de éxito
      toast.success('Firebase activado ✅', {
        description: 'El agente ahora puede usar Firebase para persistencia'
      });

      // Enviar mensaje al agente confirmando activación
      const confirmMessage = `FIREBASE_ENABLED: true. Firebase has been activated with features: ${firebaseRequest?.features.join(', ')}. You can now create Firebase services and use Firestore for data persistence.`;

      // Agregar mensaje al chat
      setMessages(prev => [...prev, {
        role: 'system',
        content: confirmMessage
      }]);

      // Reenviar request original del usuario para que el agente continúe
      sendMessage(lastUserMessage, false);
    } else {
      toast.info('Usando mock data', {
        description: 'El agente usará datos locales en lugar de Firebase'
      });

      // Informar al agente que use mock data
      const mockMessage = `FIREBASE_ENABLED: false. User declined Firebase. Please implement the feature using localStorage or in-memory arrays for mock data.`;

      setMessages(prev => [...prev, {
        role: 'system',
        content: mockMessage
      }]);

      sendMessage(lastUserMessage, false);
    }

    // Cerrar modal
    setFirebaseRequest(null);

  } catch (error) {
    console.error('Error handling Firebase decision:', error);
    toast.error('Error al procesar la decisión');
    setFirebaseRequest(null);
  }
};
```

---

### FASE 5: Modificar Template Default del Proyecto

**Archivo:** `backend/app/services/filesystem_service.py`

#### ✅ Tarea 5.1: Pre-incluir Firebase en package.json

**Modificar PACKAGE_JSON_CONTENT:**

```json
{
  "name": "vite-react-app",
  "private": true,
  "version": "0.0.1",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.26.0",
    "lucide-react": "^0.263.1",
    "clsx": "^2.1.0",
    "date-fns": "^2.30.0",
    "framer-motion": "^11.0.0",
    "zustand": "^4.5.0",
    "@tanstack/react-query": "^5.0.0",
    "axios": "^1.7.0",
    "react-hook-form": "^7.51.0",
    "zod": "^3.22.0",
    "firebase": "^10.8.0"  // ⭐ AGREGADO POR DEFECTO
  },
  "devDependencies": {
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@typescript-eslint/eslint-plugin": "^8.15.0",
    "@typescript-eslint/parser": "^8.15.0",
    "@vitejs/plugin-react": "^4.3.4",
    "autoprefixer": "^10.4.20",
    "eslint": "^9.15.0",
    "eslint-plugin-react-hooks": "^5.0.0",
    "eslint-plugin-react-refresh": "^0.4.14",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.17",
    "typescript": "^5.8.0",
    "vite": "^5.4.11"
  }
}
```

#### ✅ Tarea 5.2: Agregar .gitignore para Firebase

**Modificar GITIGNORE_CONTENT:**

```
# Firebase
.env.local
.firebase-state.json
firebase-debug.log
firestore-debug.log
ui-debug.log
```

---

## 🧪 TESTING DEL FLUJO

### Test Case 1: Detección Automática

**Input:**
```
Usuario: "Crea un formulario de clientes"
Agente: [genera formulario]

Usuario: "Quiero guardar múltiples clientes"
```

**Expected Output:**
```
Chat muestra modal:
"Para guardar múltiples clientes necesitas una base de datos. ¿Quieres activar Firebase?"
[Botones: Activar Firebase / Usar mock data]
```

### Test Case 2: Activación Exitosa

**Actions:**
1. Usuario click "Activar Firebase"
2. Backend crea archivos Firebase
3. package.json se actualiza
4. Agente recibe señal `FIREBASE_ENABLED: true`

**Expected Result:**
```
Agente genera:
- src/lib/firebase.ts
- src/services/clientService.ts (con Firestore)
- src/hooks/useClients.ts (con React Query)
- Componentes usando hooks
```

### Test Case 3: Decline Firebase

**Actions:**
1. Usuario click "Usar mock data"
2. Agente recibe `FIREBASE_ENABLED: false`

**Expected Result:**
```
Agente genera:
- src/services/mockClientService.ts (con localStorage)
- src/hooks/useClients.ts (con mock data)
```

---

## 📊 PALABRAS CLAVE DE DETECCIÓN

### Triggers Positivos (Activar Firebase):

- "guardar", "save", "persist", "persistir"
- "base de datos", "database", "DB"
- "CRUD", "crear/leer/actualizar/eliminar"
- "múltiples registros", "multiple records"
- "cargar datos", "load data", "fetch"
- "almacenar", "store"
- "formulario + submit/enviar"

### Context Negativo (NO activar):

- "ejemplo", "demo", "mockup"
- "temporal", "por ahora"
- "solo mostrar", "display only"

---

## 🎯 CRITERIOS DE ÉXITO

- [ ] Agente detecta automáticamente necesidad de persistencia
- [ ] Modal aparece en chat con botones claros
- [ ] Activación crea archivos Firebase correctamente
- [ ] package.json se actualiza automáticamente
- [ ] Agente genera código Firebase válido después de activación
- [ ] Opción de decline usa mock data alternativo
- [ ] No hay cambios en Python backend después de setup inicial

---

## 🚀 DEPLOYMENT

### Orden de Implementación:

1. ✅ FASE 1: Modificar prompts (agente entiende Firebase)
2. ✅ FASE 2: Backend detector (SSE + endpoint)
3. ✅ FASE 3: Filesystem service (template Firebase)
4. ✅ FASE 4: Frontend modal (UI confirmación)
5. ✅ FASE 5: Template default (pre-incluir Firebase)
6. ✅ Testing end-to-end

### Rollout:

- **Día 1-2:** Implementar FASE 1, 2, 3
- **Día 3:** Implementar FASE 4
- **Día 4:** Implementar FASE 5 + Testing
- **Día 5:** Ajustes y optimizaciones

---

## 📝 NOTAS ADICIONALES

### Configuración Firebase del Usuario:

El usuario deberá:
1. Ir a https://console.firebase.google.com/
2. Crear proyecto
3. Habilitar Firestore/Auth/Storage
4. Copiar config
5. Pegar en `.env.local`

### Seguridad:

- **Test Mode:** Inicialmente usar reglas permisivas
- **Production:** Agregar autenticación obligatoria
- **Validación:** El agente debe generar reglas de seguridad

### Mejoras Futuras:

- [ ] Auto-configurar Firebase desde API (requiere OAuth)
- [ ] Template wizard para elegir features específicas
- [ ] Migración automática de mock data → Firebase
- [ ] Dashboard de uso de Firebase en UI

---

## 🔗 REFERENCIAS

- [Firebase Web Setup](https://firebase.google.com/docs/web/setup)
- [Firestore Get Started](https://firebase.google.com/docs/firestore/quickstart)
- [React Query + Firebase](https://tanstack.com/query/latest/docs/framework/react/guides/queries)

---

**ESTADO:** 📋 TODO - Listo para implementación
**PRIORIDAD:** 🔥 ALTA (para hackathon)
**ESTIMADO:** 4-5 días de desarrollo
