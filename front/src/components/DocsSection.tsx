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
        <div className="mb-20">
          <div className="text-center mb-12">
            <h3 className="text-3xl font-bold mb-4">How It Works</h3>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              DaveLovable uses a sophisticated orchestration of AI agents to plan, write, and verify code.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Planner Agent */}
            <div className="glass p-8 rounded-2xl relative overflow-hidden group hover:border-primary/50 transition-all">
              <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                <MessageCircle size={100} />
              </div>
              <div className="relative z-10">
                <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center mb-6">
                  <MessageCircle className="w-6 h-6 text-blue-500" />
                </div>
                <h4 className="text-xl font-bold mb-3">1. Planner Agent</h4>
                <p className="text-muted-foreground mb-4">
                  The strategic brain. It analyzes your request, breaks it down into actionable steps, and creates a detailed implementation plan.
                </p>
                <ul className="text-sm space-y-2 text-muted-foreground">
                  <li className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                    Requirement Analysis
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                    Step-by-step Planning
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                    Review & Strategy
                  </li>
                </ul>
              </div>
            </div>

            {/* Orchestrator */}
            <div className="glass p-8 rounded-2xl relative overflow-hidden group hover:border-primary/50 transition-all border-primary/30 shadow-lg shadow-primary/5">
              <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                <ArrowRight size={100} />
              </div>
              <div className="relative z-10">
                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-6">
                  <ArrowRight className="w-6 h-6 text-primary" />
                </div>
                <h4 className="text-xl font-bold mb-3">2. Orchestrator</h4>
                <p className="text-muted-foreground mb-4">
                  Powered by Microsoft AutoGen 0.4. It manages the conversation flow, delegating tasks between agents and ensuring the goal is met.
                </p>
                <ul className="text-sm space-y-2 text-muted-foreground">
                  <li className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-primary" />
                    Context Management
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-primary" />
                    Task Delegation
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-primary" />
                    Loop Prevention
                  </li>
                </ul>
              </div>
            </div>

            {/* Coder Agent */}
            <div className="glass p-8 rounded-2xl relative overflow-hidden group hover:border-primary/50 transition-all">
              <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                <FileCode size={100} />
              </div>
              <div className="relative z-10">
                <div className="w-12 h-12 rounded-xl bg-purple-500/10 flex items-center justify-center mb-6">
                  <FileCode className="w-6 h-6 text-purple-500" />
                </div>
                <h4 className="text-xl font-bold mb-3">3. Coder Agent</h4>
                <p className="text-muted-foreground mb-4">
                  The builder. Equipped with file system tools, terminal access, and search capabilities to execute the plan and write code.
                </p>
                <ul className="text-sm space-y-2 text-muted-foreground">
                  <li className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-500" />
                    File I/O & Editing
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-500" />
                    Terminal Execution
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-500" />
                    Semantic Search
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Tech Stack Table */}
        <div className="max-w-4xl mx-auto mb-20">
          <h3 className="text-2xl font-bold mb-8 text-center">Built on Modern Technology</h3>
          <div className="glass rounded-2xl overflow-hidden">
            <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-border/50">
              <div className="p-8">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 rounded-lg bg-green-500/10 flex items-center justify-center">
                    <span className="text-green-500 font-bold">BE</span>
                  </div>
                  <h4 className="text-xl font-semibold">Backend Core</h4>
                </div>
                <ul className="space-y-4">
                  {[
                    { name: "FastAPI", desc: "High-performance Python web framwork" },
                    { name: "Microsoft AutoGen 0.4", desc: "Agent orchestration runtime" },
                    { name: "Gemini Flash", desc: "Underlying intelligence model" },
                    { name: "SQLite", desc: "Lightweight project database" }
                  ].map((item) => (
                    <li key={item.name} className="flex justify-between items-start border-b border-border/30 last:border-0 pb-3 last:pb-0">
                      <span className="font-medium">{item.name}</span>
                      <span className="text-sm text-muted-foreground">{item.desc}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="p-8">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                    <span className="text-blue-500 font-bold">FE</span>
                  </div>
                  <h4 className="text-xl font-semibold">Frontend Interface</h4>
                </div>
                <ul className="space-y-4">
                  {[
                    { name: "React + Vite", desc: "Fast, modern UI library & bundler" },
                    { name: "Tailwind CSS", desc: "Utility-first styling framework" },
                    { name: "Lucide React", desc: "Beautiful, consistent icons" },
                    { name: "Shadcn UI", desc: "Accessible component primitives" }
                  ].map((item) => (
                    <li key={item.name} className="flex justify-between items-start border-b border-border/30 last:border-0 pb-3 last:pb-0">
                      <span className="font-medium">{item.name}</span>
                      <span className="text-sm text-muted-foreground">{item.desc}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
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
            <Button variant="hero" size="lg">
              Get Started Free
              <ArrowRight className="w-5 h-5" />
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
};

export default DocsSection;
