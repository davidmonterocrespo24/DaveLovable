import { Link } from 'react-router-dom';
import { useProjects, useCreateProject } from '@/hooks/useProjects';
import { Button } from '@/components/ui/button';
import { Plus, Folder, Calendar } from 'lucide-react';
import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

const Projects = () => {
  const { data: projects, isLoading } = useProjects();
  const createProject = useCreateProject();
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [projectName, setProjectName] = useState('');
  const [projectDescription, setProjectDescription] = useState('');

  const handleCreateProject = async () => {
    if (!projectName.trim()) {
      return;
    }

    try {
      await createProject.mutateAsync({
        name: projectName,
        description: projectDescription || 'A new project',
      });
      setShowCreateDialog(false);
      setProjectName('');
      setProjectDescription('');
    } catch (error) {
      console.error('Failed to create project:', error);
    }
  };

  const openCreateDialog = () => {
    setShowCreateDialog(true);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading projects...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold">My Projects</h1>
            <p className="text-muted-foreground mt-2">
              Manage and access your development projects
            </p>
          </div>
          <Button onClick={handleCreateProject} disabled={creating}>
            <Plus className="w-4 h-4 mr-2" />
            {creating ? 'Creating...' : 'New Project'}
          </Button>
        </div>

        {!projects || projects.length === 0 ? (
          <div className="text-center py-12">
            <Folder className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
            <h2 className="text-xl font-semibold mb-2">No projects yet</h2>
            <p className="text-muted-foreground mb-6">
              Create your first project to get started
            </p>
            <Button onClick={handleCreateProject} disabled={creating}>
              <Plus className="w-4 h-4 mr-2" />
              Create Your First Project
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <Link
                key={project.id}
                to={`/editor/${project.id}`}
                className="block p-6 rounded-lg border border-border bg-card hover:border-primary transition-colors"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center">
                    <Folder className="w-6 h-6 text-primary-foreground" />
                  </div>
                  <span className="text-xs text-muted-foreground capitalize">
                    {project.status}
                  </span>
                </div>
                <h3 className="text-lg font-semibold mb-2">{project.name}</h3>
                <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
                  {project.description || 'No description'}
                </p>
                <div className="flex items-center text-xs text-muted-foreground">
                  <Calendar className="w-3 h-3 mr-1" />
                  {new Date(project.created_at).toLocaleDateString()}
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Projects;
