import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  chatApi,
  type ChatSession,
  type SendChatMessageRequest,
} from '@/services/api';
import { fileKeys } from './useFiles';
import { projectKeys } from './useProjects';

// Query keys
export const chatKeys = {
  all: ['chat'] as const,
  sessions: (projectId: number) => [...chatKeys.all, 'sessions', projectId] as const,
  session: (projectId: number, sessionId: number) =>
    [...chatKeys.all, 'session', projectId, sessionId] as const,
};

// Get chat sessions for a project
export function useChatSessions(projectId: number, enabled = true) {
  return useQuery({
    queryKey: chatKeys.sessions(projectId),
    queryFn: () => chatApi.listSessions(projectId),
    enabled,
  });
}

// Get a specific chat session
export function useChatSession(
  projectId: number,
  sessionId: number,
  enabled = true
) {
  return useQuery({
    queryKey: chatKeys.session(projectId, sessionId),
    queryFn: () => chatApi.getSession(projectId, sessionId),
    enabled,
  });
}

// Send a chat message
export function useSendChatMessage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      projectId,
      data,
    }: {
      projectId: number;
      data: SendChatMessageRequest;
    }) => chatApi.sendMessage(projectId, data),
    onSuccess: (response, { projectId }) => {
      // Invalidate chat sessions to get new messages
      queryClient.invalidateQueries({ queryKey: chatKeys.sessions(projectId) });

      // If there's a session_id in the response, invalidate that session
      if (response.session_id) {
        queryClient.invalidateQueries({
          queryKey: chatKeys.session(projectId, response.session_id),
        });
      }

      // If code changes were made, invalidate files and project
      if (response.code_changes && response.code_changes.length > 0) {
        queryClient.invalidateQueries({ queryKey: fileKeys.list(projectId) });
        queryClient.invalidateQueries({ queryKey: projectKeys.detail(projectId) });
      }
    },
  });
}

// Delete a chat session
export function useDeleteChatSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      projectId,
      sessionId,
    }: {
      projectId: number;
      sessionId: number;
    }) => chatApi.deleteSession(projectId, sessionId),
    onSuccess: (_, { projectId, sessionId }) => {
      // Remove session from cache
      queryClient.removeQueries({
        queryKey: chatKeys.session(projectId, sessionId),
      });
      // Invalidate sessions list
      queryClient.invalidateQueries({ queryKey: chatKeys.sessions(projectId) });
    },
  });
}
