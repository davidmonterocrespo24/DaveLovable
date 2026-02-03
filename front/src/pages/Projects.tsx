import { Link, useNavigate } from 'react-router-dom';
import { useProjects, useCreateProject, useDeleteProject } from '@/hooks/useProjects';
import { Button } from '@/components/ui/button';
import { Plus, Folder, ArrowRight, Sparkles } from 'lucide-react';
import { ProjectCard } from '@/components/ProjectCard';
import { useState } from 'react';
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
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

const Projects = () => {
  const navigate = useNavigate();
  const { data: projects, isLoading } = useProjects();
  const createProject = useCreateProject();
  const deleteProject = useDeleteProject();
  const { toast } = useToast();
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [projectName, setProjectName] = useState('');
  const [projectDescription, setProjectDescription] = useState('');
  const [deleteProjectId, setDeleteProjectId] = useState<number | null>(null);
  const [deleteProjectName, setDeleteProjectName] = useState('');

  // Sort projects by created_at descending (newest first)
  const sortedProjects = projects?.slice().sort((a, b) => {
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });

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
    } catch (error: any) {
      // If 404, project doesn't exist (already deleted or never existed)
      if (error.response?.status === 404) {
        toast({
          title: "Project not found",
          description: `${deleteProjectName} no longer exists. Refreshing project list...`,
        });
        setDeleteProjectId(null);
        setDeleteProjectName('');
      } else {
        toast({
          title: "Error deleting project",
          description: "There was an error deleting the project. Please try again.",
          variant: "destructive",
        });
      }
    }
  };

  // Show skeleton UI during loading for better UX
  const showSkeleton = isLoading && !projects;

  return (
    <main className="min-h-screen bg-background">
      <Navbar />

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 overflow-hidden">
        {/* Background Effects */}
        <div className="absolute inset-0 bg-gradient-subtle" />
        <div className="absolute top-20 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-3xl animate-pulse-glow" />
        <div className="absolute bottom-0 right-1/4 w-80 h-80 bg-accent/15 rounded-full blur-3xl animate-pulse-glow delay-500" />

        {/* Grid Pattern */}
        <div
          className="absolute inset-0 opacity-[0.02]"
          style={{
            backgroundImage: `linear-gradient(hsl(var(--foreground)) 1px, transparent 1px), linear-gradient(90deg, hsl(var(--foreground)) 1px, transparent 1px)`,
            backgroundSize: '60px 60px',
          }}
        />

        <div className="container mx-auto px-6 relative z-10">
          <div className="max-w-6xl mx-auto">
            {/* Header */}
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-12 animate-fade-in-up">
              <div>
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass mb-4">
                  <Sparkles className="w-4 h-4 text-primary" />
                  <span className="text-sm text-muted-foreground">Your Workspace</span>
                </div>
                <h1 className="text-4xl md:text-5xl font-extrabold mb-3">
                  My <span className="text-gradient">Projects</span>
                </h1>
                <p className="text-lg text-muted-foreground">
                  Manage and access all your AI-powered development projects
                </p>
              </div>
              <Button
                onClick={() => navigate('/')}
                size="lg"
                className="mt-6 md:mt-0 bg-gradient-primary hover:scale-105 transition-all glow-primary"
              >
                <Plus className="w-5 h-5 mr-2" />
                New Project
              </Button>
            </div>

            {/* Projects Grid */}
            {showSkeleton ? (
              /* Skeleton Loading State */
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-fade-in">
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <div key={i} className="glass rounded-2xl overflow-hidden">
                    <div className="h-48 bg-muted/50 animate-pulse" />
                    <div className="p-6 space-y-3">
                      <div className="h-6 bg-muted/50 rounded animate-pulse w-3/4" />
                      <div className="h-4 bg-muted/30 rounded animate-pulse w-full" />
                      <div className="h-4 bg-muted/30 rounded animate-pulse w-2/3" />
                      <div className="h-3 bg-muted/20 rounded animate-pulse w-1/2 mt-4" />
                    </div>
                  </div>
                ))}
              </div>
            ) : !projects || projects.length === 0 ? (
              <div className="text-center py-20 animate-fade-in">
                <div className="glass rounded-3xl p-12 max-w-2xl mx-auto glow-accent">
                  <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-primary/10 flex items-center justify-center">
                    <Folder className="w-10 h-10 text-primary" />
                  </div>
                  <h2 className="text-2xl font-bold mb-3">No projects yet</h2>
                  <p className="text-muted-foreground mb-8 text-lg">
                    Create your first project and start building with AI assistance
                  </p>
                  <Button
                    onClick={() => navigate('/')}
                    size="lg"
                    className="bg-gradient-primary hover:scale-105 transition-all glow-primary"
                  >
                    <Plus className="w-5 h-5 mr-2" />
                    Create Your First Project
                    <ArrowRight className="w-5 h-5 ml-2" />
                  </Button>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-fade-in-up delay-200">
                {sortedProjects?.map((project, index) => (
                  <ProjectCard
                    key={project.id}
                    project={project}
                    index={index}
                    onDelete={handleDeleteProject}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </section>

      <Footer />

      {/* Create Project Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="text-2xl">Create New Project</DialogTitle>
            <DialogDescription className="text-base">
              Enter the details for your new AI-powered development project
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-6 py-4">
            <div className="grid gap-3">
              <Label htmlFor="name" className="text-base">Project Name</Label>
              <Input
                id="name"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                placeholder="My Awesome App"
                className="h-11"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && projectName.trim()) {
                    handleCreateProject();
                  }
                }}
              />
            </div>
            <div className="grid gap-3">
              <Label htmlFor="description" className="text-base">Description (Optional)</Label>
              <Textarea
                id="description"
                value={projectDescription}
                onChange={(e) => setProjectDescription(e.target.value)}
                placeholder="A brief description of your project..."
                rows={4}
                className="resize-none"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)} size="lg">
              Cancel
            </Button>
            <Button
              onClick={handleCreateProject}
              disabled={!projectName.trim() || createProject.isPending}
              size="lg"
              className="bg-gradient-primary glow-primary"
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
            <AlertDialogTitle className="text-2xl">Are you sure?</AlertDialogTitle>
            <AlertDialogDescription className="text-base">
              This will permanently delete <strong className="text-foreground">{deleteProjectName}</strong> and all its files. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="h-11">Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDeleteProject}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90 h-11"
            >
              {deleteProject.isPending ? 'Deleting...' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </main>
  );
};

export default Projects;
