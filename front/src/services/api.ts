// API service layer for backend communication

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Types matching backend schemas
export interface Project {
  id: number;
  name: string;
  description?: string;
  owner_id: number;
  created_at: string;
  updated_at: string;
  files?: ProjectFile[];
}

export interface ProjectFile {
  id: number;
  project_id: number;
  filename: string;
  filepath: string;
  content: string;
  language: string;
  created_at: string;
  updated_at: string;
}

export interface AgentInteraction {
  agent_name: string;
  message_type: 'thought' | 'tool_call' | 'tool_response';
  content: string;
  tool_name?: string;
  tool_arguments?: Record<string, any>;
  timestamp: string;
}

export interface ChatMessage {
  id: number;
  session_id: number;
  role: 'user' | 'assistant';
  content: string;
  message_metadata?: string;
  agent_interactions?: AgentInteraction[];
  created_at: string;
}

export interface ChatSession {
  id: number;
  project_id: number;
  created_at: string;
  messages?: ChatMessage[];
}

export interface CreateProjectRequest {
  name: string;
  description?: string;
}

export interface UpdateProjectRequest {
  name?: string;
  description?: string;
}

export interface CreateFileRequest {
  filename: string;
  filepath: string;
  content: string;
  language: string;
}

export interface UpdateFileRequest {
  content: string;
}

export interface SendChatMessageRequest {
  message: string;
  session_id?: number;
}

export interface SendChatMessageResponse {
  message: {
    role: string;
    content: string;
    agent_name: string | null;
    message_metadata: string | null;
    id: number;
    session_id: number;
    created_at: string;
  };
  session_id: number;
  code_changes?: Array<{
    filename: string;
    content: string;
    language: string;
  }>;
  agent_interactions?: AgentInteraction[];
}

// Error handling
class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

// Helper function for API requests
async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new ApiError(
      response.status,
      errorData.detail || `HTTP ${response.status}`
    );
  }

  return response.json();
}

// Project API
export const projectApi = {
  // Create a new project
  create: async (data: CreateProjectRequest): Promise<Project> => {
    return fetchApi<Project>('/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // List all projects
  list: async (): Promise<Project[]> => {
    return fetchApi<Project[]>('/projects');
  },

  // Get a specific project with files
  get: async (projectId: number): Promise<Project> => {
    return fetchApi<Project>(`/projects/${projectId}`);
  },

  // Update project
  update: async (
    projectId: number,
    data: UpdateProjectRequest
  ): Promise<Project> => {
    return fetchApi<Project>(`/projects/${projectId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  // Delete project
  delete: async (projectId: number): Promise<void> => {
    return fetchApi<void>(`/projects/${projectId}`, {
      method: 'DELETE',
    });
  },
};

// File API
export const fileApi = {
  // List files in a project
  list: async (projectId: number): Promise<ProjectFile[]> => {
    return fetchApi<ProjectFile[]>(`/projects/${projectId}/files`);
  },

  // Create a new file
  create: async (
    projectId: number,
    data: CreateFileRequest
  ): Promise<ProjectFile> => {
    return fetchApi<ProjectFile>(`/projects/${projectId}/files`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // Update file content
  update: async (
    projectId: number,
    fileId: number,
    data: UpdateFileRequest
  ): Promise<ProjectFile> => {
    return fetchApi<ProjectFile>(`/projects/${projectId}/files/${fileId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  // Delete file
  delete: async (projectId: number, fileId: number): Promise<void> => {
    return fetchApi<void>(`/projects/${projectId}/files/${fileId}`, {
      method: 'DELETE',
    });
  },
};

// SSE Event types
export interface SSEEvent {
  type: 'start' | 'agent_interaction' | 'complete' | 'error' | 'git_commit';
  data: any;
}

// Chat API
export const chatApi = {
  // Send a message to AI with streaming (SSE)
  sendMessageStream: async (
    projectId: number,
    data: SendChatMessageRequest,
    callbacks: {
      onStart?: (data: { session_id: number; user_message_id: number }) => void;
      onAgentInteraction?: (interaction: AgentInteraction) => void;
      onGitCommit?: (data: { success: boolean; message?: string; full_message?: string; error?: string }) => void;
      onComplete?: (data: SendChatMessageResponse) => void;
      onError?: (error: string) => void;
    }
  ): Promise<void> => {
    return new Promise((resolve, reject) => {
      // We can't use EventSource for POST requests, so we'll use fetch with streaming
      const url = `${API_URL}/chat/${projectId}/stream`;

      console.log('[SSE] Starting stream to:', url);

      fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })
        .then(async (response) => {
          console.log('[SSE] Response received:', response.status, response.statusText);

          if (!response.ok) {
            throw new ApiError(response.status, `HTTP ${response.status}`);
          }

          const reader = response.body?.getReader();
          if (!reader) {
            throw new Error('No response body');
          }

          const decoder = new TextDecoder();
          let buffer = '';

          console.log('[SSE] Starting to read stream...');

          while (true) {
            const { done, value } = await reader.read();

            if (done) {
              console.log('[SSE] Stream complete');
              resolve();
              break;
            }

            // Decode chunk and add to buffer
            const chunk = decoder.decode(value, { stream: true });
            buffer += chunk;
            console.log('[SSE] Received chunk:', chunk.substring(0, 100));

            // Process complete SSE messages (separated by \n\n)
            const lines = buffer.split('\n\n');
            buffer = lines.pop() || ''; // Keep incomplete message in buffer

            for (const line of lines) {
              if (line.trim().startsWith('data: ')) {
                try {
                  const jsonStr = line.replace(/^data: /, '').trim();
                  console.log('[SSE] Parsing event:', jsonStr.substring(0, 100));
                  const event: SSEEvent = JSON.parse(jsonStr);
                  console.log('[SSE] Event type:', event.type);

                  switch (event.type) {
                    case 'start':
                      console.log('[SSE] Start event:', event.data);
                      callbacks.onStart?.(event.data);
                      break;
                    case 'agent_interaction':
                      console.log('[SSE] Agent interaction:', event.data.message_type, event.data.agent_name);
                      callbacks.onAgentInteraction?.(event.data);
                      break;
                    case 'git_commit':
                      console.log('[SSE] Git commit event:', event.data);
                      callbacks.onGitCommit?.(event.data);
                      break;
                    case 'complete':
                      console.log('[SSE] Complete event');
                      callbacks.onComplete?.(event.data);
                      break;
                    case 'error':
                      console.error('[SSE] Error event:', event.data.message);
                      callbacks.onError?.(event.data.message);
                      reject(new ApiError(500, event.data.message));
                      return;
                  }
                } catch (err) {
                  console.error('[SSE] Failed to parse event:', err, line);
                }
              }
            }
          }
        })
        .catch((error) => {
          console.error('[SSE] Stream error:', error);
          callbacks.onError?.(error.message || 'Unknown error');
          reject(error);
        });
    });
  },

  // Send a message to AI (non-streaming, backward compatible)
  sendMessage: async (
    projectId: number,
    data: SendChatMessageRequest
  ): Promise<SendChatMessageResponse> => {
    // Use AbortController for timeout (5 minutes for AI processing)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5 * 60 * 1000); // 5 minutes

    try {
      const response = await fetchApi<SendChatMessageResponse>(`/chat/${projectId}`, {
        method: 'POST',
        body: JSON.stringify(data),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === 'AbortError') {
        throw new ApiError(408, 'Request timeout - AI is taking too long to respond');
      }
      throw error;
    }
  },

  // List chat sessions
  listSessions: async (projectId: number): Promise<ChatSession[]> => {
    return fetchApi<ChatSession[]>(`/chat/${projectId}/sessions`);
  },

  // Get a specific session with messages
  getSession: async (projectId: number, sessionId: number): Promise<ChatSession> => {
    return fetchApi<ChatSession>(`/chat/${projectId}/sessions/${sessionId}`);
  },

  // Delete a session
  deleteSession: async (projectId: number, sessionId: number): Promise<void> => {
    return fetchApi<void>(`/chat/${projectId}/sessions/${sessionId}`, {
      method: 'DELETE',
    });
  },
};

export { ApiError };
