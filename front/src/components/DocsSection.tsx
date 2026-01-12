import { Book, FileCode, Video, MessageCircle, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

const DocsSection = () => {
  const resources = [
    {
      icon: MessageCircle,
      title: "AI Agents System",
      description: "Understand how the Orchestrator and Coder agents collaborate to transform your natural language prompts into production-ready code.",
      link: "#",
      linkText: "Learn about Agents",
    },
    {
      icon: FileCode,
      title: "Modern Architecture",
      description: "Built on a robust stack: React + Vite frontend for a responsive UI, and FastAPI backend for high-performance agent processing.",
      link: "#",
      linkText: "View Architecture",
    },
    {
      icon: Book,
      title: "Project Workflow",
      description: "From idea to deployment: 1. You Prompt -> 2. Orchestrator Plans -> 3. Coder Implements -> 4. Live Preview.",
      link: "#",
      linkText: "See Workflow",
    },
    {
      icon: Video,
      title: "Developer Guide",
      description: "Dive deep into the codebase. Learn how to extend the agents, add new tools, or customize the UI components.",
      link: "#",
      linkText: "Read Developer Docs",
    },
  ];

  const quickLinks = [
    { title: "Getting Started", href: "#" },
    { title: "AI Chat Commands", href: "#" },
    { title: "Project Structure", href: "#" },
    { title: "Deployment Guide", href: "#" },
    { title: "Best Practices", href: "#" },
    { title: "Troubleshooting", href: "#" },
  ];

  return (
    <section id="docs" className="py-24 relative overflow-hidden bg-muted/30">
      {/* Background Effects */}
      <div className="absolute inset-0 bg-gradient-subtle opacity-30" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl" />

      <div className="container mx-auto px-6 relative z-10">
        {/* Section Header */}
        <div className="max-w-3xl mx-auto text-center mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass mb-6">
            <Book className="w-4 h-4 text-primary" />
            <span className="text-sm text-muted-foreground">Documentation</span>
          </div>
          <h2 className="text-4xl md:text-5xl font-extrabold mb-6">
            Understand the <span className="text-gradient">DaveLovable System</span>
          </h2>
          <p className="text-xl text-muted-foreground">
            A powerful multi-agent architecture designed to build software autonomously.
          </p>
        </div>

        {/* System Architecture Section */}
        <div className="mb-20 text-center">
          <div className="glass p-12 rounded-3xl glow-accent max-w-4xl mx-auto">
            <h3 className="text-3xl font-bold mb-6">Master the System</h3>
            <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
              Dive deep into the architecture, learn about the AI agents, and master the workflow with our comprehensive documentation.
            </p>

            <div className="grid md:grid-cols-3 gap-6 text-left mb-8">
              <div className="p-4 rounded-xl bg-background/50">
                <h4 className="font-semibold mb-2 flex items-center gap-2"><MessageCircle className="w-4 h-4 text-blue-500" /> AI Agents</h4>
                <p className="text-sm text-muted-foreground">Detailed breakdown of Planner and Coder agents.</p>
              </div>
              <div className="p-4 rounded-xl bg-background/50">
                <h4 className="font-semibold mb-2 flex items-center gap-2"><ArrowRight className="w-4 h-4 text-green-500" /> Workflow</h4>
                <p className="text-sm text-muted-foreground">Step-by-step guide from prompt to production.</p>
              </div>
              <div className="p-4 rounded-xl bg-background/50">
                <h4 className="font-semibold mb-2 flex items-center gap-2"><FileCode className="w-4 h-4 text-purple-500" /> API Reference</h4>
                <p className="text-sm text-muted-foreground">Complete backend and frontend technical docs.</p>
              </div>
            </div>

            <Button asChild size="lg" className="bg-gradient-primary glow-primary">
              <a href="/docs">
                Read Full Documentation
                <ArrowRight className="ml-2 w-5 h-5" />
              </a>
            </Button>
          </div>
        </div>

        {/* Resources Grid (Original Content Summarized) */}
        <div className="grid md:grid-cols-2 gap-6 max-w-5xl mx-auto mb-16">
          {resources.map((resource, index) => (
            <div
              key={index}
              className="glass rounded-2xl p-8 hover:glow-accent transition-all duration-300 group"
            >
              <div className="w-12 h-12 rounded-xl bg-gradient-primary flex items-center justify-center mb-6">
                <resource.icon className="w-6 h-6 text-primary-foreground" />
              </div>
              <h3 className="text-xl font-bold mb-3 text-foreground">
                {resource.title}
              </h3>
              <p className="text-muted-foreground mb-6">
                {resource.description}
              </p>
              <a
                href={resource.link}
                className="inline-flex items-center gap-2 text-primary hover:text-primary/80 transition-colors font-medium group-hover:gap-3"
              >
                {resource.linkText}
                <ArrowRight className="w-4 h-4" />
              </a>
            </div>
          ))}
        </div>

        {/* Quick Links */}
        <div className="max-w-5xl mx-auto">
          <div className="glass rounded-2xl p-8">
            <h3 className="text-2xl font-bold mb-6 text-foreground">
              Quick Links
            </h3>
            <div className="grid md:grid-cols-3 gap-4">
              {quickLinks.map((link, index) => (
                <a
                  key={index}
                  href={link.href}
                  className="flex items-center gap-2 px-4 py-3 rounded-lg hover:bg-accent/10 transition-colors text-muted-foreground hover:text-foreground"
                >
                  <ArrowRight className="w-4 h-4 text-primary" />
                  <span className="font-medium">{link.title}</span>
                </a>
              ))}
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="max-w-3xl mx-auto text-center mt-16">
          <div className="glass rounded-2xl p-10">
            <h3 className="text-2xl font-bold mb-4 text-foreground">
              Ready to start building?
            </h3>
            <p className="text-muted-foreground mb-6">
              Create your first project in minutes. No credit card required.
            </p>
            <Button variant="hero" size="lg" asChild>
              <a href="/">
                Get Started Free
                <ArrowRight className="w-5 h-5" />
              </a>
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
};

export default DocsSection;
