import { Link } from 'react-router-dom';
import { useProjects, useCreateProject, useDeleteProject } from '@/hooks/useProjects';
import { Button } from '@/components/ui/button';
import { Plus, Folder, Calendar, Trash2, MoreVertical } from 'lucide-react';
import { useState } from 'react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { useToast } from '@/hooks/use-toast';
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
  const deleteProject = useDeleteProject();
  const { toast } = useToast();
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [projectName, setProjectName] = useState('');
  const [projectDescription, setProjectDescription] = useState('');
  const [deleteProjectId, setDeleteProjectId] = useState<number | null>(null);
  const [deleteProjectName, setDeleteProjectName] = useState('');

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

  const handleDeleteProject = (id: number, name: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDeleteProjectId(id);
    setDeleteProjectName(name);
  };

  const confirmDeleteProject = async () => {
    if (!deleteProjectId) return;

    try {
      await deleteProject.mutateAsync(deleteProjectId);
      toast({
        title: "Project deleted",
        description: `${deleteProjectName} has been deleted successfully.`,
      });
      setDeleteProjectId(null);
      setDeleteProjectName('');
    } catch (error) {
      toast({
        title: "Error deleting project",
        description: "There was an error deleting the project. Please try again.",
        variant: "destructive",
      });
    }
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
          <Button onClick={openCreateDialog}>
            <Plus className="w-4 h-4 mr-2" />
            New Project
          </Button>
        </div>

        {!projects || projects.length === 0 ? (
          <div className="text-center py-12">
            <Folder className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
            <h2 className="text-xl font-semibold mb-2">No projects yet</h2>
            <p className="text-muted-foreground mb-6">
              Create your first project to get started
            </p>
            <Button onClick={openCreateDialog}>
              <Plus className="w-4 h-4 mr-2" />
              Create Your First Project
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <div
                key={project.id}
                className="block rounded-lg border border-border bg-card hover:border-primary transition-colors overflow-hidden group relative"
              >
                <Link to={`/editor/${project.id}`}>
                  {/* Thumbnail or placeholder */}
                  <div className="relative h-48 bg-gradient-to-br from-primary/10 to-purple-600/10 overflow-hidden">
                    {project.thumbnail ? (
                      <img
                        src={project.thumbnail}
                        alt={project.name}
                        className="w-full h-full object-cover object-top"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <Folder className="w-16 h-16 text-primary/30" />
                      </div>
                    )}
                    <div className="absolute top-2 right-2 flex items-center gap-2">
                      <span className="text-xs px-2 py-1 rounded bg-background/80 backdrop-blur-sm text-foreground capitalize">
                        {project.status}
                      </span>
                    </div>
                  </div>

                  {/* Project details */}
                  <div className="p-6">
                    <h3 className="text-lg font-semibold mb-2 group-hover:text-primary transition-colors">
                      {project.name}
                    </h3>
                    <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
                      {project.description || 'No description'}
                    </p>
                    <div className="flex items-center text-xs text-muted-foreground">
                      <Calendar className="w-3 h-3 mr-1" />
                      {new Date(project.created_at).toLocaleDateString()}
                    </div>
                  </div>
                </Link>

                {/* Delete button - positioned absolutely */}
                <div className="absolute top-52 right-2">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                      <button className="p-2 bg-background/80 backdrop-blur-sm hover:bg-background rounded-lg border border-border/30 transition-all opacity-0 group-hover:opacity-100">
                        <MoreVertical className="w-4 h-4" />
                      </button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem
                        onClick={(e) => handleDeleteProject(project.id, project.name, e)}
                        className="text-destructive focus:text-destructive"
                      >
                        <Trash2 className="w-4 h-4 mr-2" />
                        Delete Project
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Create Project Dialog */}
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Project</DialogTitle>
              <DialogDescription>
                Enter the details for your new development project
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="name">Project Name</Label>
                <Input
                  id="name"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  placeholder="My Awesome App"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && projectName.trim()) {
                      handleCreateProject();
                    }
                  }}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="description">Description (Optional)</Label>
                <Textarea
                  id="description"
                  value={projectDescription}
                  onChange={(e) => setProjectDescription(e.target.value)}
                  placeholder="A brief description of your project..."
                  rows={3}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                Cancel
              </Button>
              <Button
                onClick={handleCreateProject}
                disabled={!projectName.trim() || createProject.isPending}
              >
                {createProject.isPending ? 'Creating...' : 'Create Project'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Delete Confirmation Dialog */}
        <AlertDialog open={deleteProjectId !== null} onOpenChange={() => setDeleteProjectId(null)}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Are you sure?</AlertDialogTitle>
              <AlertDialogDescription>
                This will permanently delete <strong>{deleteProjectName}</strong> and all its files. This action cannot be undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={confirmDeleteProject}
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              >
                {deleteProject.isPending ? 'Deleting...' : 'Delete'}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </div>
  );
};

export default Projects;
