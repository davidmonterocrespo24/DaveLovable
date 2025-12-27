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

export interface ChatMessage {
  id: number;
  session_id: number;
  role: 'user' | 'assistant';
  content: string;
  message_metadata?: string;
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

// Chat API
export const chatApi = {
  // Send a message to AI
  sendMessage: async (
    projectId: number,
    data: SendChatMessageRequest
  ): Promise<SendChatMessageResponse> => {
    return fetchApi<SendChatMessageResponse>(`/chat/${projectId}`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
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
