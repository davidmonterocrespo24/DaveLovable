from io import BytesIO
import logging
from datetime import datetime
from typing import Dict, List

from autogen_core import CancellationToken
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.agents import get_orchestrator
from app.models import ChatMessage, ChatSession, MessageRole, ProjectFile
from app.schemas import ChatMessageCreate, ChatRequest, ChatSessionCreate
from app.services.commit_message_service import CommitMessageService
from app.services.filesystem_service import FileSystemService
from app.services.git_service import GitService

# Configure logging for agent interactions
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ChatService:
    """Service for managing chat sessions and AI interactions"""

    @staticmethod
    def detect_firebase_request(message_content: str) -> Dict | None:
        """
        Detects if the agent is requesting to activate Firebase

        Returns:
            dict with Firebase activation request details if detected, None otherwise
        """
        import json
        import re

        # Method 1: Look for exact JSON format from agent
        if "FIREBASE_ACTIVATION_REQUEST" in message_content:
            # Try to extract JSON object
            json_match = re.search(
                r'\{[^}]*"type"\s*:\s*"FIREBASE_ACTIVATION_REQUEST"[^}]*\}',
                message_content,
                re.DOTALL
            )
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    logger.warning("Failed to parse FIREBASE_ACTIVATION_REQUEST JSON")

        # Method 2: Look for persistence-related keywords (fallback detection)
        persistence_keywords = [
            # Spanish keywords
            "necesitas una base de datos",
            "activar firebase",
            "persistir los datos",
            "base de datos",
            "guardar",
            "crud",
            # English keywords
            "need a database",
            "activate firebase",
            "persist the data",
            "persist",
            "database",
            "save multiple",
            "store multiple",
            "load data",
        ]

        if any(keyword in message_content.lower() for keyword in persistence_keywords):
            logger.info(f"🔥 Firebase activation keywords detected in message")
            return {
                "type": "FIREBASE_ACTIVATION_REQUEST",
                "message": message_content,
                "features": ["firestore"],  # Default to Firestore
                "reason": "Persistence keywords detected"
            }

        return None

    @staticmethod
    def create_session(db: Session, session_data: ChatSessionCreate) -> ChatSession:
        """Create a new chat session"""

        db_session = ChatSession(**session_data.model_dump())
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        return db_session

    @staticmethod
    def get_session(db: Session, session_id: int, project_id: int) -> ChatSession:
        """Get a chat session by ID"""

        session = (
            db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.project_id == project_id).first()
        )

        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")

        return session

    @staticmethod
    def get_sessions(db: Session, project_id: int) -> List[ChatSession]:
        """Get all chat sessions for a project"""

        return (
            db.query(ChatSession)
            .filter(ChatSession.project_id == project_id)
            .order_by(ChatSession.updated_at.desc())
            .all()
        )

    @staticmethod
    def add_message(db: Session, message_data: ChatMessageCreate) -> ChatMessage:
        """Add a message to a chat session"""

        db_message = ChatMessage(**message_data.model_dump())
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        return db_message

    @staticmethod
    def get_messages(db: Session, session_id: int, limit: int = 100) -> List[ChatMessage]:
        """Get messages for a session"""

        return (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
            .limit(limit)
            .all()
        )

    @staticmethod
    async def process_chat_message(db: Session, project_id: int, chat_request: ChatRequest) -> Dict:
        """
        Process a chat message and generate AI response

        Args:
            db: Database session
            project_id: Project ID
            chat_request: Chat request with message and optional session_id

        Returns:
            Dict with session_id, message, and code_changes
        """

        # Get or create chat session
        if chat_request.session_id:
            session = ChatService.get_session(db, chat_request.session_id, project_id)
        else:
            session = ChatService.create_session(db, ChatSessionCreate(project_id=project_id))

        # Save user message
        user_message = ChatService.add_message(
            db, ChatMessageCreate(session_id=session.id, role=MessageRole.USER, content=chat_request.message)
        )

        # Get project context (existing files from filesystem)
        project_files = db.query(ProjectFile).filter(ProjectFile.project_id == project_id).all()

        context = {
            "project_id": project_id,
            "files": [
                {
                    "filename": f.filename,
                    "filepath": f.filepath,
                    "language": f.language,
                    "content": (FileSystemService.read_file(project_id, f.filepath) or "")[
                        :500
                    ],  # First 500 chars for context
                }
                for f in project_files
            ],
        }

        # Generate AI response using agents
        try:
            orchestrator = await get_orchestrator(project_id)
        except ValueError as e:
            # API key not configured
            error_message = ChatService.add_message(
                db, ChatMessageCreate(session_id=session.id, role=MessageRole.ASSISTANT, content=str(e))
            )
            return {
                "session_id": session.id,
                "message": error_message,
                "code_changes": [],
            }

        try:
            # Set working directory to the project directory so agent tools work correctly
            import os
            from pathlib import Path

            from app.core.config import settings

            project_dir = Path(settings.PROJECTS_BASE_DIR) / f"project_{project_id}"
            original_cwd = os.getcwd()

            try:
                os.chdir(project_dir)
                logger.info(f"📂 Changed working directory to: {project_dir}")

                # Check if Firebase was activated (check session history)
                firebase_context = ""
                firebase_activated = "FIREBASE_ACTIVATED" in chat_request.message

                # Also check session history for FIREBASE_ACTIVATED
                if not firebase_activated:
                    session_messages = ChatService.get_messages(db, session.id, limit=100)
                    for msg in session_messages:
                        if "FIREBASE_ACTIVATED" in msg.content:
                            firebase_activated = True
                            break

                if firebase_activated:
                    # Read Firebase state to get project info
                    firebase_state_path = project_dir / ".firebase-state.json"
                    if firebase_state_path.exists():
                        import json
                        with open(firebase_state_path, 'r', encoding='utf-8') as f:
                            firebase_state = json.load(f)

                        firebase_context = f"""

**FIREBASE ACTIVATED - Technical Context:**
This project uses a SHARED Firebase database with automatic collection prefixing.

- **Your project prefix**: `{firebase_state.get('collection_prefix', 'proj_')}`
- **Project unique ID**: `{firebase_state.get('project_unique_id', 'unknown')}`
- **How it works**: The wrapper at `src/lib/firestore.ts` automatically adds/removes prefixes transparently

**CRITICAL RULES:**
1. **ALWAYS import from `@/lib/firestore`** (NOT from `firebase/firestore`)
2. **Just use normal Firestore syntax** - prefixing is automatic!
3. The wrapper handles everything behind the scenes

Configuration files ready:
- .env.local (with VITE_PROJECT_ID={firebase_state.get('project_unique_id', 'unknown')})
- src/lib/firebase.ts (Firebase app, auth, storage initialized)
- src/lib/firestore.ts (Firestore wrapper with auto-prefixing)

**Example service pattern:**
```typescript
//  CORRECT - Import from @/lib/firestore wrapper
import {{ db }} from '@/lib/firestore';
import {{ collection, addDoc, getDocs, doc, updateDoc }} from '@/lib/firestore';

export const createItem = async (data) => {{
  const docRef = await addDoc(collection(db, 'items'), data);
  return {{ id: docRef.id, ...data }};
}};

export const getItems = async () => {{
  const snapshot = await getDocs(collection(db, 'items'));
  return snapshot.docs.map(doc => ({{ id: doc.id, ...doc.data() }}));
}};

//  WRONG - Don't import from firebase/firestore
// import {{ collection }} from 'firebase/firestore'; // DON'T DO THIS
```
"""

                # Build task description with context for the agents
                task_description = f"""User Request: {chat_request.message}

Project Context:
- Project ID: {project_id}
- Working Directory: {project_dir}
- Existing Files: {len(context["files"])} files
- Files: {", ".join([f["filepath"] for f in context["files"]])}
{firebase_context}
IMPORTANT: You are working in the project directory. All file operations will be relative to this directory.
Please analyze the request, create a plan if needed, and implement the solution."""

                logger.info("=" * 80)
                logger.info("🤖 STARTING MULTI-AGENT TEAM EXECUTION")
                logger.info("=" * 80)
                logger.info(f"📝 User Request: {chat_request.message}")
                logger.info(f"📁 Project Files: {len(context['files'])}")
                logger.info("=" * 80)

                # List to collect agent interactions as events stream in
                agent_interactions = []

                # Run the agent team using run_stream to capture events in real-time
                async for message in orchestrator.main_team.run_stream(
                    task=task_description, cancellation_token=CancellationToken()
                ):
                    # Get event type
                    event_type = type(message).__name__
                    msg_source = message.source if hasattr(message, "source") else "Unknown"
                    msg_timestamp = message.created_at if hasattr(message, "created_at") else datetime.now()

                    logger.info(f"📨 Event: {event_type} from {msg_source}")

                    # TextMessage - Agent thoughts/responses
                    if event_type == "TextMessage":
                        content_preview = message.content[:200] if len(message.content) > 200 else message.content
                        logger.info(f"💭 {msg_source}: {content_preview}")

                        # Skip user messages and filter out system/control messages
                        skip_patterns = ["TASK_COMPLETED", "TERMINATE", "DELEGATE_TO_PLANNER", "SUBTASK_DONE"]
                        should_skip = (
                            msg_source == "user"
                            or any(pattern in message.content for pattern in skip_patterns)
                            or len(message.content.strip()) < 10  # Skip very short messages
                        )

                        if not should_skip:
                            agent_interactions.append(
                                {
                                    "agent_name": msg_source,
                                    "message_type": "thought",
                                    "content": message.content,
                                    "tool_name": None,
                                    "tool_arguments": None,
                                    "timestamp": msg_timestamp,
                                }
                            )

                    # ToolCallRequestEvent - Tool calls
                    elif event_type == "ToolCallRequestEvent":
                        for tool_call in message.content:
                            logger.info(f"🔧 Tool: {tool_call.name}")
                            tool_args = {}
                            try:
                                import json

                                if isinstance(tool_call.arguments, str):
                                    tool_args = json.loads(tool_call.arguments)
                                elif isinstance(tool_call.arguments, dict):
                                    tool_args = tool_call.arguments
                                else:
                                    tool_args = {"raw": str(tool_call.arguments)}
                            except json.JSONDecodeError as e:
                                # Try to fix common JSON issues
                                logger.warning(f"⚠️  Failed to parse tool arguments as JSON: {e}")
                                logger.warning(f"Arguments: {tool_call.arguments[:200]}...")
                                # Store as raw but log the error for debugging
                                tool_args = {"raw": str(tool_call.arguments)}
                            except Exception as e:
                                logger.error(f"❌ Unexpected error parsing tool arguments: {e}")
                                tool_args = {"raw": str(tool_call.arguments)}

                            agent_interactions.append(
                                {
                                    "agent_name": msg_source,
                                    "message_type": "tool_call",
                                    "content": f"Calling: {tool_call.name}",
                                    "tool_name": tool_call.name,
                                    "tool_arguments": tool_args,
                                    "timestamp": msg_timestamp,
                                }
                            )

                    # ToolCallExecutionEvent - Tool results
                    elif event_type == "ToolCallExecutionEvent":
                        for tool_result in message.content:
                            result_preview = str(tool_result.content)[:200]
                            logger.info(f"✅ Result ({tool_result.name}): {result_preview}")

                            agent_interactions.append(
                                {
                                    "agent_name": "System",
                                    "message_type": "tool_response",
                                    "content": tool_result.content,
                                    "tool_name": tool_result.name,
                                    "tool_arguments": None,
                                    "timestamp": msg_timestamp,
                                }
                            )

                    # TaskResult - Final
                    elif event_type == "TaskResult":
                        result = message
                        logger.info("=" * 80)
                        logger.info("✅ EXECUTION COMPLETED")
                        logger.info("=" * 80)
            finally:
                # Always restore original working directory
                os.chdir(original_cwd)
                logger.info(f"📂 Restored working directory to: {original_cwd}")

            # Extract the final response from the result
            response_content = ""
            agent_name = "Team"

            # Get the final response from the last message
            if result.messages:
                # Get the last message from the team
                last_message = result.messages[-1]
                response_content = last_message.content if hasattr(last_message, "content") else str(last_message)
                agent_name = last_message.source if hasattr(last_message, "source") else "Team"

                logger.info("=" * 80)
                logger.info(f"📤 FINAL RESPONSE (from {agent_name}):")
                logger.info("=" * 80)
                logger.info(response_content[:1000])
                logger.info("=" * 80)
            else:
                response_content = "I processed your request successfully."
                logger.warning("⚠️  No messages in result, using default response")

            # Note: File changes are now handled by the Coder agent's tools
            # We don't need to manually create/update files anymore
            # The agent uses write_file, edit_file tools directly

            # Save assistant message with the team's response
            assistant_message = ChatService.add_message(
                db,
                ChatMessageCreate(
                    session_id=session.id, role=MessageRole.ASSISTANT, content=response_content, agent_name=agent_name
                ),
            )

            return {
                "session_id": session.id,
                "message": assistant_message,
                "code_changes": [],  # Changes are handled by agent tools, not tracked here
                "agent_interactions": agent_interactions,
            }

        except Exception as e:
            logger.error("=" * 80)
            logger.error("❌ ERROR DURING AGENT EXECUTION")
            logger.error("=" * 80)
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {e!s}")
            logger.error("=" * 80)

            # Log full traceback
            import traceback

            logger.error("Full traceback:")
            logger.error(traceback.format_exc())

            # Save error message
            error_message = ChatService.add_message(
                db,
                ChatMessageCreate(
                    session_id=session.id,
                    role=MessageRole.ASSISTANT,
                    content=f"I encountered an error: {e!s}. Please try again.",
                    agent_name="System",
                ),
            )

            return {
                "session_id": session.id,
                "message": error_message,
                "code_changes": [],
            }

    @staticmethod
    async def process_chat_message_stream(db: Session, project_id: int, chat_request: ChatRequest):
        """
        Process a chat message and stream AI response events in real-time

        Yields events for:
        - Agent thoughts (thought)
        - Tool calls (tool_call)
        - Tool execution results (tool_response)
        - Final response (complete)
        """

        # Get or create chat session
        if chat_request.session_id:
            session = ChatService.get_session(db, chat_request.session_id, project_id)
        else:
            session = ChatService.create_session(db, ChatSessionCreate(project_id=project_id))

        # Process attachments if present
        processed_attachments = []
        if chat_request.attachments:
            from app.utils.multimodal import process_attachment

            for attachment in chat_request.attachments:
                is_valid, error, processed_data, processed_mime = process_attachment(
                    attachment.type, attachment.mime_type, attachment.data, attachment.name
                )

                if not is_valid:
                    yield {"type": "error", "data": {"message": f"Invalid attachment {attachment.name}: {error}"}}
                    return

                processed_attachments.append({
                    "type": attachment.type,
                    "mime_type": processed_mime,
                    "data": processed_data,
                    "name": attachment.name
                })

        # Save user message with attachments in metadata
        user_message_metadata = None
        if processed_attachments:
            import json
            user_message_metadata = json.dumps({"attachments": processed_attachments})

        user_message = ChatService.add_message(
            db, ChatMessageCreate(
                session_id=session.id,
                role=MessageRole.USER,
                content=chat_request.message,
                message_metadata=user_message_metadata
            )
        )

        # Yield initial event
        yield {"type": "start", "data": {"session_id": session.id, "user_message_id": user_message.id}}

        # Flag to track if Firebase activation was already requested
        firebase_activation_sent = False

        # Get project context
        project_files = db.query(ProjectFile).filter(ProjectFile.project_id == project_id).all()

        # Check if this is the first message in the session (optimize for speed)
        message_count = db.query(ChatMessage).filter(ChatMessage.session_id == session.id).count()
        is_first_message = message_count <= 1  # Only user message exists

        # Files to exclude from LLM context (internal use only)
        EXCLUDED_FILES = {".agent_state.json", ".gitignore"}

        # Filter out internal files that should never be sent to the LLM
        user_files = [f for f in project_files if f.filename not in EXCLUDED_FILES]

        # For first message: provide FULL file content to avoid wasteful read_file calls
        # For subsequent messages: provide only preview (first 500 chars)
        context = {
            "project_id": project_id,
            "files": [
                {
                    "filename": f.filename,
                    "filepath": f.filepath,
                    "language": f.language,
                    "content": (FileSystemService.read_file(project_id, f.filepath) or "")
                    if is_first_message
                    else (FileSystemService.read_file(project_id, f.filepath) or "")[:500],
                }
                for f in user_files  # Use filtered list instead of all project_files
            ],
        }

        # Generate AI response using agents
        try:
            orchestrator = await get_orchestrator(project_id)
        except ValueError as e:
            # API key not configured
            yield {"type": "error", "data": {"message": str(e)}}
            return

        try:
            import os
            from pathlib import Path

            from app.core.config import settings

            project_dir = Path(settings.PROJECTS_BASE_DIR) / f"project_{project_id}"
            original_cwd = os.getcwd()

            try:
                os.chdir(project_dir)
                logger.info(f"📂 Changed working directory to: {project_dir}")

                # Prepare multimodal content if attachments present
                task_input = None  # Will be either string or MultiModalMessage

                if processed_attachments:
                    # Build multimodal message using AutoGen format
                    from autogen_agentchat.messages import MultiModalMessage
                    from autogen_core import Image as AGImage
                    from PIL import Image
                    import base64

                    content_parts = []

                    # Add images to content
                    for attachment in processed_attachments:
                        if attachment["type"] == "image":
                            # Decode base64 to PIL Image
                            img_data = base64.b64decode(attachment["data"])
                            pil_img = Image.open(BytesIO(img_data))
                            ag_image = AGImage(pil_img)
                            content_parts.append(ag_image)

                # Check if Firebase was activated (check session history)
                firebase_context = ""
                firebase_activated = "FIREBASE_ACTIVATED" in chat_request.message

                # Also check session history for FIREBASE_ACTIVATED
                if not firebase_activated:
                    session_messages = ChatService.get_messages(db, session.id, limit=100)
                    for msg in session_messages:
                        if "FIREBASE_ACTIVATED" in msg.content:
                            firebase_activated = True
                            break

                if firebase_activated:
                    # Read Firebase state to get project info
                    firebase_state_path = project_dir / ".firebase-state.json"
                    if firebase_state_path.exists():
                        import json
                        with open(firebase_state_path, 'r', encoding='utf-8') as f:
                            firebase_state = json.load(f)

                        firebase_context = f"""

**🔥 FIREBASE ACTIVATED - Technical Context:**
This project uses a SHARED Firebase database with automatic collection prefixing.

- **Your project prefix**: `{firebase_state.get('collection_prefix', 'proj_')}`
- **Project unique ID**: `{firebase_state.get('project_unique_id', 'unknown')}`
- **How it works**: The wrapper at `src/lib/firestore.ts` automatically adds/removes prefixes

**CRITICAL RULES:**
1. **ALWAYS import from `@/lib/firestore`** (NOT from `firebase/firestore`)
2. **Just use normal Firestore syntax** - prefixing is automatic!

Configuration files ready:
- .env.local (VITE_PROJECT_ID={firebase_state.get('project_unique_id', 'unknown')})
- src/lib/firebase.ts (auth, storage)
- src/lib/firestore.ts (wrapper with auto-prefixing)

**Example:**
```typescript
import {{ db }} from '@/lib/firestore';
import {{ collection, addDoc, getDocs }} from '@/lib/firestore';

const docRef = await addDoc(collection(db, 'items'), data);
const snapshot = await getDocs(collection(db, 'items'));
```
"""

                # Build task description with optimizations for first message
                if is_first_message:
                    # FIRST MESSAGE: Provide complete file structure and content to avoid wasteful tool calls
                    file_contents_section = "\n\n".join(
                        [
                            f"File: {f['filepath']}\nLanguage: {f['language']}\nContent:\n```{f['language']}\n{f['content']}\n```"
                            for f in context["files"]
                        ]
                    )

                    # Build file tree
                    file_tree = "\n".join([f"  {f['filepath']}" for f in context["files"]])

                    task_description = f"""User Request: {chat_request.message}

⚡ FIRST MESSAGE OPTIMIZATION - ATOMIC EXECUTION STRATEGY:
- This is the FIRST user request for this project
- Your goal: Get a working prototype visible in the preview panel as FAST as possible
- Use PARALLEL TOOL CALLING: Call write_file up to 5 times in ONE response to create multiple files at once
- Build a simple but WORKING UI first, then refactor in subsequent iterations

Project Context:
- Project ID: {project_id}
- Working Directory: {project_dir}
- Existing Files: {len(context["files"])} files

📂 COMPLETE FILE TREE (provided in context - NEVER use list_dir):
{file_tree}

📁 COMPLETE FILE STRUCTURE AND CONTENT (no need to use list_dir or read_file):

{file_contents_section}

🔧 ENVIRONMENT ASSUMPTIONS (already configured, no need to verify):
- Vite + React + TypeScript project (package.json already configured)
- Tailwind CSS installed and configured (tailwind.config.js, postcss.config.js ready)
- All dependencies in package.json are installed (lucide-react, date-fns, clsx, react-router-dom, axios, zustand, @tanstack/react-query, framer-motion, react-hook-form, zod)
- Entry point: index.html → main.tsx → App.tsx
- Base styles: index.css with Tailwind directives
- Dev server runs automatically in WebContainer - NEVER run npm run dev or npm start
{firebase_context}
⚡ CRITICAL OPTIMIZATION RULES:
1. 🚫 **NEVER use list_dir** - The file tree is provided above in your context
2. 🚫 **NEVER use read_file** - All file contents are provided above
3. 🚫 **NEVER use mkdir** - write_file automatically creates parent directories
4. ⚡ **USE PARALLEL TOOL CALLING**: Call write_file up to 5 times in ONE response to create multiple files
5. 🎭 **MOCK-FIRST**: If task needs external API/backend, create mock service with fake data first
6. 🎯 **KEEP IT SIMPLE**: Start with code in base files (App.tsx, index.css), add components only if needed
7. 🚀 **SPEED IS CRITICAL**: Fewer turns = faster results. Batch file creation into one response!

IMPORTANT: You are working in the project directory. All file operations will be relative to this directory.
Please implement the solution QUICKLY and EFFICIENTLY using parallel write_file calls."""
                else:
                    # SUBSEQUENT MESSAGES: Standard prompt with file previews
                    task_description = f"""User Request: {chat_request.message}

Project Context:
- Project ID: {project_id}
- Working Directory: {project_dir}
- Existing Files: {len(context["files"])} files
- Files: {", ".join([f["filepath"] for f in context["files"]])}
{firebase_context}
⚡ OPTIMIZATION REMINDER:
- **write_file AUTOMATICALLY creates parent directories** - NEVER use mkdir

IMPORTANT: You are working in the project directory. All file operations will be relative to this directory.
Please analyze the request, create a plan if needed, and implement the solution."""

                # Create multimodal message if attachments are present
                if processed_attachments:
                    from autogen_agentchat.messages import MultiModalMessage

                    # Prepend text description
                    content_parts.insert(0, task_description)

                    # Create multimodal message
                    task_input = MultiModalMessage(content=content_parts, source="User")
                else:
                    # Use simple text task
                    task_input = task_description

                logger.info("=" * 80)
                logger.info("🤖 STARTING MULTI-AGENT TEAM EXECUTION (STREAMING)")
                logger.info("=" * 80)

                # Note: Agent state is automatically loaded in get_orchestrator(project_id)

                # List to collect all agent interactions for database storage
                agent_interactions = []
                
                # Dictionary to store pending tool calls to retrieve arguments later
                # Format: {call_id: {name: str, arguments: dict}}
                pending_tool_calls = {}

                # Track assistant message for incremental updates
                assistant_message_id = None

                # Helper function to save state incrementally
                async def save_incremental_state():
                    """Save agent interactions and state to database incrementally"""
                    nonlocal assistant_message_id
                    try:
                        # Update or create assistant message with current interactions
                        if assistant_message_id:
                            # Update existing message
                            db_message = db.query(ChatMessage).filter(ChatMessage.id == assistant_message_id).first()
                            if db_message:
                                db_message.message_metadata = json.dumps({"agent_interactions": agent_interactions})
                                db.commit()
                                logger.info(
                                    f"💾 Updated message {assistant_message_id} with {len(agent_interactions)} interactions"
                                )
                        else:
                            # Create initial assistant message
                            new_message = ChatService.add_message(
                                db,
                                ChatMessageCreate(
                                    session_id=session.id,
                                    role=MessageRole.ASSISTANT,
                                    content="Processing...",
                                    agent_name="Team",
                                    message_metadata=json.dumps({"agent_interactions": agent_interactions}),
                                ),
                            )
                            assistant_message_id = new_message.id
                            logger.info(f"💾 Created assistant message {assistant_message_id}")

                        # Save agent state
                        await orchestrator.save_state(project_id)
                        logger.info(f"💾 Saved agent state for project {project_id}")
                    except Exception as e:
                        logger.error(f"❌ Error saving incremental state: {e}")

                # Stream agent events in real-time
                async for message in orchestrator.main_team.run_stream(
                    task=task_input, cancellation_token=CancellationToken()
                ):
                    event_type = type(message).__name__
                    msg_source = message.source if hasattr(message, "source") else "Unknown"
                    msg_timestamp = message.created_at if hasattr(message, "created_at") else datetime.now()

                    logger.info(f"📨 Event: {event_type} from {msg_source}")

                    # TextMessage - Agent thoughts/responses
                    if event_type == "TextMessage":
                        # Check for Firebase activation request FIRST (before skipping)
                        # Only send once per session execution
                        firebase_request = ChatService.detect_firebase_request(message.content)
                        if firebase_request and not firebase_activation_sent:
                            logger.info(f"🔥 FIREBASE ACTIVATION REQUEST DETECTED (first time)")
                            logger.info(f"🔥 Features: {firebase_request.get('features', [])}")
                            logger.info(f"🔥 Reason: {firebase_request.get('reason', 'N/A')}")

                            # Mark as sent to prevent duplicates
                            firebase_activation_sent = True

                            # Send special event to frontend to show modal
                            yield {
                                "type": "firebase_activation_request",
                                "data": {
                                    "message": firebase_request.get("message", "Para esta funcionalidad necesitas una base de datos. ¿Quieres activar Firebase?"),
                                    "features": firebase_request.get("features", ["firestore"]),
                                    "reason": firebase_request.get("reason", "Persistence required")
                                }
                            }

                            # Save a message indicating we're waiting for approval
                            waiting_message = ChatService.add_message(
                                db,
                                ChatMessageCreate(
                                    session_id=session.id,
                                    role=MessageRole.ASSISTANT,
                                    content=firebase_request.get("message", "Para esta funcionalidad necesitas una base de datos. ¿Quieres activar Firebase?")
                                )
                            )

                            # Yield the complete event with the waiting message
                            yield {
                                "type": "complete",
                                "data": {
                                    "session_id": session.id,
                                    "message": {
                                        "id": waiting_message.id,
                                        "session_id": waiting_message.session_id,
                                        "role": waiting_message.role.value,
                                        "content": waiting_message.content,
                                        "agent_name": "System",
                                        "created_at": waiting_message.created_at.isoformat()
                                    },
                                    "code_changes": []
                                }
                            }

                            # TERMINATE the agent execution immediately
                            # This prevents further messages and waits for user's decision
                            logger.info(f"🔥 Stopping agent execution to wait for Firebase approval")
                            return  # Exit the generator completely
                        elif firebase_request and firebase_activation_sent:
                            # Already requested, skip subsequent detections
                            logger.info(f"🔥 Firebase already requested in this execution, skipping duplicate")
                            continue

                        # Skip user messages and filter out system/control messages
                        skip_patterns = ["TASK_COMPLETED", "TERMINATE", "DELEGATE_TO_PLANNER", "SUBTASK_DONE"]
                        should_skip = (
                            msg_source == "user"
                            or any(pattern in message.content for pattern in skip_patterns)
                            or len(message.content.strip()) < 10  # Skip very short messages
                        )

                        if not should_skip:
                            interaction_data = {
                                "agent_name": msg_source,
                                "message_type": "thought",
                                "content": message.content,
                                "tool_name": None,
                                "tool_arguments": None,
                                "timestamp": msg_timestamp.isoformat()
                                if hasattr(msg_timestamp, "isoformat")
                                else str(msg_timestamp),
                            }
                            # Add to list for database storage
                            agent_interactions.append(interaction_data)
                            # Stream to frontend
                            yield {"type": "agent_interaction", "data": interaction_data}
                            # Save state incrementally every 3 interactions
                            if len(agent_interactions) % 3 == 0:
                                await save_incremental_state()

                    # ToolCallRequestEvent - Tool calls
                    elif event_type == "ToolCallRequestEvent":
                        for tool_call in message.content:
                            tool_args = {}
                            try:
                                import json

                                if isinstance(tool_call.arguments, str):
                                    tool_args = json.loads(tool_call.arguments)
                                elif isinstance(tool_call.arguments, dict):
                                    tool_args = tool_call.arguments
                                else:
                                    tool_args = {"raw": str(tool_call.arguments)}
                            except json.JSONDecodeError as e:
                                # Try to fix common JSON issues
                                logger.warning(f"⚠️  Failed to parse tool arguments as JSON: {e}")
                                logger.warning(f"Arguments: {tool_call.arguments[:200]}...")
                                # Store as raw but log the error for debugging
                                tool_args = {"raw": str(tool_call.arguments)}
                            except Exception as e:
                                logger.error(f"❌ Unexpected error parsing tool arguments: {e}")
                                tool_args = {"raw": str(tool_call.arguments)}

                            interaction_data = {
                                "agent_name": msg_source,
                                "message_type": "tool_call",
                                "content": f"Calling: {tool_call.name}",
                                "tool_name": tool_call.name,
                                "tool_arguments": tool_args,
                                "timestamp": msg_timestamp.isoformat()
                                if hasattr(msg_timestamp, "isoformat")
                                else str(msg_timestamp),
                            }
                            # Add to list for database storage
                            agent_interactions.append(interaction_data)
                            # Stream to frontend
                            yield {"type": "agent_interaction", "data": interaction_data}

                            # Store tool call arguments for later use in execution event
                            # We need this to get the 'content' argument for write_file/update_file tools
                            try:
                                pending_tool_calls[tool_call.id] = {
                                    "name": tool_call.name,
                                    "arguments": tool_args
                                }
                            except Exception as e:
                                logger.warning(f"⚠️ Failed to store pending tool call: {e}")

                    # ToolCallExecutionEvent - Tool results
                    elif event_type == "ToolCallExecutionEvent":
                        for tool_result in message.content:
                            interaction_data = {
                                "agent_name": "System",
                                "message_type": "tool_response",
                                "content": str(tool_result.content),
                                "tool_name": tool_result.name,
                                "tool_arguments": None,
                                "timestamp": msg_timestamp.isoformat()
                                if hasattr(msg_timestamp, "isoformat")
                                else str(msg_timestamp),
                            }
                            # Add to list for database storage
                            agent_interactions.append(interaction_data)
                            # Stream to frontend
                            yield {"type": "agent_interaction", "data": interaction_data}
                        # Save state after every tool execution
                        await save_incremental_state()

                        # Check if tool was a file modification tool
                        file_mod_tools = {
                            "write_file",
                            "replace_file_content", 
                            "edit_file", 
                            "multi_replace_file_content"
                        }
                        
                        tool_names = [r.name for r in message.content]
                        if any(name in file_mod_tools for name in tool_names):
                            logger.info(f"📁 [Files Update] Detected file modification tools: {tool_names}")
                            
                            # Extract file updates from tool arguments
                            updated_files = []
                            
                            for tool_result in message.content:
                                if tool_result.name in file_mod_tools:
                                    # Try to find original call arguments
                                    call_id = tool_result.call_id
                                    if call_id and call_id in pending_tool_calls:
                                        args = pending_tool_calls[call_id]["arguments"]
                                        
                                        # Extract file path and content based on tool type
                                        if tool_result.name == "write_file":
                                            if "filepath" in args and "content" in args:
                                                updated_files.append({
                                                    "path": args["filepath"],
                                                    "content": args["content"]
                                                })
                                        # Note: other tools like replace_file_content are partial edits
                                        # We can't push partial content easily to WebContainer
                                        # For those, we might still need to rely on the side-effect (or read from disk)
                                        # BUT: WebContainers filesystem operations are fast. 
                                        # If replace_file_content was used, the file on disk IS updated. 
                                        # We can read it back and push it.
                                        elif tool_result.name in ["replace_file_content", "edit_file", "multi_replace_file_content"]:
                                            # For edits, we need the TargetFile/filepath
                                            target_file = args.get("TargetFile") or args.get("filepath") or args.get("file_path")
                                            
                                            if target_file:
                                                # Read the FULL updated content from disk to ensure correctness
                                                # This is safe because the tool has already executed (we are in execution event)
                                                content = FileSystemService.read_file(project_id, target_file)
                                                if content:
                                                    updated_files.append({
                                                        "path": target_file,
                                                        "content": content
                                                    })
                            
                            # Construct payload
                            data_payload = {
                                "message": "File updated",
                                "project_id": project_id,
                            }
                            
                            if updated_files:
                                data_payload["files"] = updated_files
                                logger.info(f"🚀 [Files Push] Pushing {len(updated_files)} files directly to frontend")

                            yield {
                                "type": "files_ready",
                                "data": data_payload,
                            }

                    # TaskResult - Final
                    elif event_type == "TaskResult":
                        result = message
                        logger.info("=" * 80)
                        logger.info("✅ EXECUTION COMPLETED")
                        logger.info("=" * 80)

            finally:
                os.chdir(original_cwd)
                logger.info(f"📂 Restored working directory to: {original_cwd}")

            # Extract final response
            response_content = ""
            agent_name = "Team"

            if result.messages:
                last_message = result.messages[-1]
                response_content = last_message.content if hasattr(last_message, "content") else str(last_message)
                agent_name = last_message.source if hasattr(last_message, "source") else "Team"
            else:
                response_content = "I processed your request successfully."

            # Update final assistant message with completion status
            if assistant_message_id:
                # Update existing message with final content
                db_message = db.query(ChatMessage).filter(ChatMessage.id == assistant_message_id).first()
                if db_message:
                    db_message.content = response_content
                    db_message.agent_name = agent_name
                    db_message.message_metadata = json.dumps({"agent_interactions": agent_interactions})
                    db.commit()
                    db.refresh(db_message)
                    assistant_message = db_message
                    logger.info(f"✅ Updated final message {assistant_message_id}")
            else:
                # Create message if it wasn't created incrementally
                import json

                assistant_message = ChatService.add_message(
                    db,
                    ChatMessageCreate(
                        session_id=session.id,
                        role=MessageRole.ASSISTANT,
                        content=response_content,
                        agent_name=agent_name,
                        message_metadata=json.dumps({"agent_interactions": agent_interactions}),
                    ),
                )

            # Final save of agent state
            logger.info("📦 [Save State] Saving agent state to filesystem...")
            await orchestrator.save_state(project_id)
            logger.info("📦 [Save State] ✅ Agent state saved successfully")

            # IMPORTANT: Send files_ready event BEFORE git commit starts
            # Files are already written to filesystem and ready for download
            logger.info("📁 [Files Ready] 🚀 About to send files_ready event...")
            yield {
                "type": "files_ready",
                "data": {
                    "message": "Files ready for download",
                    "project_id": project_id,
                },
            }
            logger.info(f"📁 [Files Ready] ✅ files_ready event SENT - Files written to filesystem, ready for frontend download")

            # AUTO-COMMIT: Create Git commit synchronously so we can send the result to frontend
            commit_hash = None
            commit_message_title = None
            try:
                logger.info("🔄 Creating automatic Git commit...")

                # Get the git diff to see what changed
                diff_output = GitService.get_diff(project_id)

                if diff_output and diff_output.strip():
                    # Generate commit message using LLM
                    commit_info = await CommitMessageService.generate_commit_message(
                        diff=diff_output, user_request=chat_request.message
                    )

                    # Combine title and body for full commit message
                    full_commit_message = f"{commit_info['title']}\n\n{commit_info['body']}"
                    commit_message_title = commit_info['title']

                    # Create the commit (synchronous git operation)
                    commit_success = GitService.commit_changes(
                        project_id=project_id,
                        message=full_commit_message,
                        files=None,  # Commit all changes
                    )

                    if commit_success:
                        logger.info(f"✅ Git commit created: {commit_info['title']}")

                        # Get the latest commit hash
                        commits = GitService.get_commit_history(project_id, limit=1)
                        if commits:
                            commit_hash = commits[0]['hash']
                            logger.info(f"📝 Commit hash: {commit_hash}")

                        # Get commit count
                        all_commits = GitService.get_commit_history(project_id, limit=100)
                        commit_count = len(all_commits)
                        logger.info(f"📊 Total commits in project: {commit_count}")

                        # Send commit success event to frontend
                        yield {
                            "type": "git_commit",
                            "data": {
                                "success": True,
                                "message": commit_message_title,
                                "commit_hash": commit_hash,
                                "commit_count": commit_count,
                            },
                        }

                        # Check if this is the first commit for screenshot
                        if commit_count == 2:
                            logger.info("=" * 80)
                            logger.info("📸 FIRST COMMIT DETECTED")
                            logger.info("📸 Screenshot will be captured by frontend from WebContainer")
                            logger.info("=" * 80)
                    else:
                        logger.warning("⚠️ Git commit failed or no changes to commit")
                        yield {
                            "type": "git_commit",
                            "data": {
                                "success": False,
                                "message": "No changes to commit",
                            },
                        }
                else:
                    logger.info("ℹ️ No changes detected for Git commit")
                    yield {
                        "type": "git_commit",
                        "data": {
                            "success": False,
                            "message": "No changes to commit",
                        },
                    }
            except Exception as e:
                logger.error(f"❌ Error creating auto-commit: {e}")
                yield {
                    "type": "git_commit",
                    "data": {
                        "success": False,
                        "message": f"Error: {str(e)}",
                    },
                }

            # Trigger WebContainer reload after agent completes
            logger.info("🔄 Triggering WebContainer reload (agent finished)")
            yield {"type": "reload_preview", "data": {"message": "Reloading preview to show final changes"}}

            # Yield final completion event
            yield {
                "type": "complete",
                "data": {
                    "session_id": session.id,
                    "message": {
                        "id": assistant_message.id,
                        "session_id": assistant_message.session_id,
                        "role": assistant_message.role.value,
                        "content": assistant_message.content,
                        "agent_name": assistant_message.agent_name,
                        "created_at": assistant_message.created_at.isoformat(),
                    },
                    "code_changes": [],
                },
            }

        except Exception as e:
            logger.error("=" * 80)
            logger.error("❌ ERROR DURING AGENT EXECUTION")
            logger.error("=" * 80)
            logger.error(f"Error: {e!s}")
            logger.error("=" * 80)

            import traceback

            logger.error(traceback.format_exc())

            yield {"type": "error", "data": {"message": str(e)}}

    @staticmethod
    def delete_session(db: Session, session_id: int, project_id: int) -> bool:
        """Delete a chat session"""

        session = ChatService.get_session(db, session_id, project_id)
        db.delete(session)
        db.commit()
        return True
