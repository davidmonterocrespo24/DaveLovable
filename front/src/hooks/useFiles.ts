import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fileApi,
  type ProjectFile,
  type CreateFileRequest,
  type UpdateFileRequest,
} from '@/services/api';
import { projectKeys } from './useProjects';

// Query keys
export const fileKeys = {
  all: ['files'] as const,
  lists: () => [...fileKeys.all, 'list'] as const,
  list: (projectId: number) => [...fileKeys.lists(), projectId] as const,
  details: () => [...fileKeys.all, 'detail'] as const,
  detail: (projectId: number, fileId: number) =>
    [...fileKeys.details(), projectId, fileId] as const,
};

// Get all files for a project
export function useFiles(projectId: number, enabled = true) {
  return useQuery({
    queryKey: fileKeys.list(projectId),
    queryFn: () => fileApi.list(projectId),
    enabled,
  });
}

// Create file
export function useCreateFile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      projectId,
      data,
    }: {
      projectId: number;
      data: CreateFileRequest;
    }) => fileApi.create(projectId, data),
    onSuccess: (newFile, { projectId }) => {
      // Invalidate files list
      queryClient.invalidateQueries({ queryKey: fileKeys.list(projectId) });
      // Also invalidate project detail to get updated files
      queryClient.invalidateQueries({ queryKey: projectKeys.detail(projectId) });
    },
  });
}

// Update file
export function useUpdateFile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      projectId,
      fileId,
      data,
    }: {
      projectId: number;
      fileId: number;
      data: UpdateFileRequest;
    }) => fileApi.update(projectId, fileId, data),
    onSuccess: (updatedFile, { projectId }) => {
      // Update file in cache
      queryClient.setQueryData(
        fileKeys.detail(projectId, updatedFile.id),
        updatedFile
      );
      // Invalidate files list
      queryClient.invalidateQueries({ queryKey: fileKeys.list(projectId) });
      // Also invalidate project detail
      queryClient.invalidateQueries({ queryKey: projectKeys.detail(projectId) });
    },
  });
}

// Delete file
export function useDeleteFile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      projectId,
      fileId,
    }: {
      projectId: number;
      fileId: number;
    }) => fileApi.delete(projectId, fileId),
    onSuccess: (_, { projectId, fileId }) => {
      // Remove from cache
      queryClient.removeQueries({
        queryKey: fileKeys.detail(projectId, fileId),
      });
      // Invalidate files list
      queryClient.invalidateQueries({ queryKey: fileKeys.list(projectId) });
      // Also invalidate project detail
      queryClient.invalidateQueries({ queryKey: projectKeys.detail(projectId) });
    },
  });
}
