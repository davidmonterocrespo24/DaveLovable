import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, ArrowUp, Sparkles, Loader2 } from "lucide-react";
import { useCreateProject } from "@/hooks/useProjects";
import { useProjects } from "@/hooks/useProjects";
import { useToast } from "@/hooks/use-toast";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import FeaturesSection from "@/components/FeaturesSection";
import HowItWorksSection from "@/components/HowItWorksSection";
import DocsSection from "@/components/DocsSection";

const Index = () => {
  const [message, setMessage] = useState("");
  const [showGallery, setShowGallery] = useState(false);
  const [displayedProjects, setDisplayedProjects] = useState(16);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const galleryRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const { toast } = useToast();
  const createProject = useCreateProject();
  const { data: projects } = useProjects();

  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY;
      if (scrollPosition > 300 && !showGallery) {
        setShowGallery(true);
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [showGallery]);

  const handleSubmit = async () => {
    if (!message.trim()) {
      toast({
        title: "Empty message",
        description: "Please describe what you want to build",
        variant: "destructive",
      });
      return;
    }

    if (isSubmitting) {
      return;
    }

    setIsSubmitting(true);

    try {
      // Call the new endpoint that uses AI to generate project metadata
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/projects/from-message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message.substring(0, 1000),
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create project');
      }

      const data = await response.json();
      const project = data.project;
      const initialMessage = data.initial_message;

      toast({
        title: "Project created!",
        description: "Redirecting to editor...",
      });

      // Navigate to editor with the initial message in state
      setTimeout(() => {
        navigate(`/editor/${project.id}`, {
          state: { initialMessage }
        });
      }, 500);
    } catch (error) {
      toast({
        title: "Error creating project",
        description: "Please try again",
        variant: "destructive",
      });
      setIsSubmitting(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const loadMoreProjects = () => {
    setDisplayedProjects(prev => prev + 16);
  };

  return (
    <main className="min-h-screen bg-background">
      <Navbar />

      {/* Hero Section with Input */}
      <section className="relative min-h-screen flex items-center justify-center pt-20 overflow-hidden">
        {/* Background Effects */}
        <div className="absolute inset-0 bg-gradient-subtle" />
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-3xl animate-pulse-glow" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-accent/15 rounded-full blur-3xl animate-pulse-glow delay-500" />

        {/* Grid Pattern */}
        <div
          className="absolute inset-0 opacity-[0.02]"
          style={{
            backgroundImage: `linear-gradient(hsl(var(--foreground)) 1px, transparent 1px), linear-gradient(90deg, hsl(var(--foreground)) 1px, transparent 1px)`,
            backgroundSize: '60px 60px',
          }}
        />

        <div className="container mx-auto px-6 relative z-10">
          <div className="max-w-4xl mx-auto text-center">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass mb-8 animate-fade-in">
              <Sparkles className="w-4 h-4 text-primary" />
              <span className="text-sm text-muted-foreground">Powered by AI</span>
            </div>

            {/* Headline */}
            <h1 className="text-4xl md:text-5xl font-extrabold leading-tight mb-6 animate-fade-in-up">
              What can I{" "}
              <span className="text-gradient">build</span>{" "}
              for you?
            </h1>

            {/* Subheadline */}
            <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-10 animate-fade-in-up delay-200">
              Describe what you want to build, and watch AI transform your ideas into
              production-ready applications in minutes.
            </p>

            {/* Input Box */}
            <div className="w-full max-w-5xl mx-auto mb-8 animate-fade-in-up delay-300">
              <div className="glass rounded-3xl glow-accent flex items-start gap-4 p-6 hover:border-primary/50 transition-all">
                <button
                  className="w-11 h-11 rounded-full border border-border bg-background hover:bg-muted flex items-center justify-center transition-colors shrink-0 mt-1"
                  onClick={() => {/* Add attachment functionality */}}
                >
                  <Plus className="w-6 h-6 text-muted-foreground" />
                </button>

                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Describe your project or ask anything..."
                  rows={4}
                  disabled={isSubmitting}
                  className="flex-1 bg-transparent border-none outline-none text-lg text-foreground placeholder:text-muted-foreground resize-none disabled:opacity-50 disabled:cursor-not-allowed"
                />

                <div className="flex flex-col items-center gap-3 shrink-0 mt-1">
                  <div className="w-2.5 h-2.5 rounded-full bg-primary animate-pulse" />

                  <button
                    onClick={handleSubmit}
                    disabled={!message.trim() || isSubmitting}
                    className="w-11 h-11 rounded-full bg-gradient-primary hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 flex items-center justify-center transition-all glow-primary"
                  >
                    {isSubmitting ? (
                      <Loader2 className="w-6 h-6 text-primary-foreground animate-spin" />
                    ) : (
                      <ArrowUp className="w-6 h-6 text-primary-foreground" />
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Social Proof */}
            <div className="mt-12 animate-fade-in delay-500">
              <p className="text-sm text-muted-foreground mb-4">
                Join thousands of developers building faster with AI
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Project Gallery */}
      {showGallery && (
        <section ref={galleryRef} className="py-20 px-4 bg-muted/20">
          <div className="max-w-7xl mx-auto">
            <h2 className="text-3xl font-semibold text-center mb-12">
              Recent Projects
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {projects?.slice(0, displayedProjects).map((project) => (
                <div
                  key={project.id}
                  onClick={() => navigate(`/editor/${project.id}`)}
                  className="group relative bg-background border border-border rounded-lg overflow-hidden cursor-pointer hover:border-primary/50 hover:shadow-xl transition-all duration-300"
                >
                  {project.thumbnail ? (
                    <img
                      src={project.thumbnail}
                      alt={project.name}
                      className="w-full h-48 object-cover"
                    />
                  ) : (
                    <div className="w-full h-48 bg-gradient-to-br from-primary/20 to-purple-500/20 flex items-center justify-center">
                      <Sparkles className="w-12 h-12 text-primary/40" />
                    </div>
                  )}

                  <div className="p-4">
                    <h3 className="font-semibold text-foreground truncate mb-1">
                      {project.name}
                    </h3>
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {project.description || "No description"}
                    </p>
                    <p className="text-xs text-muted-foreground mt-2">
                      {new Date(project.created_at).toLocaleDateString()}
                    </p>
                  </div>

                  <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              ))}
            </div>

            {projects && projects.length > displayedProjects && (
              <div className="flex justify-center">
                <button
                  onClick={loadMoreProjects}
                  className="px-8 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-medium"
                >
                  Load More
                </button>
              </div>
            )}
          </div>
        </section>
      )}

      {/* Features Section */}
      <FeaturesSection />

      {/* How It Works Section */}
      <HowItWorksSection />

      {/* Docs Section */}
      <DocsSection />

      <Footer />
    </main>
  );
};

export default Index;
