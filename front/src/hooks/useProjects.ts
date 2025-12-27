import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  projectApi,
  type Project,
  type CreateProjectRequest,
  type UpdateProjectRequest,
} from '@/services/api';

// Query keys
export const projectKeys = {
  all: ['projects'] as const,
  lists: () => [...projectKeys.all, 'list'] as const,
  list: () => [...projectKeys.lists()] as const,
  details: () => [...projectKeys.all, 'detail'] as const,
  detail: (id: number) => [...projectKeys.details(), id] as const,
};

// Get all projects
export function useProjects() {
  return useQuery({
    queryKey: projectKeys.list(),
    queryFn: () => projectApi.list(),
  });
}

// Get a specific project
export function useProject(projectId: number, enabled = true) {
  return useQuery({
    queryKey: projectKeys.detail(projectId),
    queryFn: () => projectApi.get(projectId),
    enabled,
  });
}

// Create project
export function useCreateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateProjectRequest) => projectApi.create(data),
    onSuccess: (newProject) => {
      // Invalidate and refetch projects list
      queryClient.invalidateQueries({ queryKey: projectKeys.list() });
      // Set the new project in cache
      queryClient.setQueryData(projectKeys.detail(newProject.id), newProject);
    },
  });
}

// Update project
export function useUpdateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      projectId,
      data,
    }: {
      projectId: number;
      data: UpdateProjectRequest;
    }) => projectApi.update(projectId, data),
    onSuccess: (updatedProject) => {
      // Update the project in cache
      queryClient.setQueryData(
        projectKeys.detail(updatedProject.id),
        updatedProject
      );
      // Invalidate list to reflect changes
      queryClient.invalidateQueries({ queryKey: projectKeys.list() });
    },
  });
}

// Delete project
export function useDeleteProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (projectId: number) => projectApi.delete(projectId),
    onSuccess: (_, projectId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: projectKeys.detail(projectId) });
      // Invalidate list
      queryClient.invalidateQueries({ queryKey: projectKeys.list() });
    },
  });
}
