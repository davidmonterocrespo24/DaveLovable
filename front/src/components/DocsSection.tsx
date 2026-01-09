import { Book, FileCode, Video, MessageCircle, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

const DocsSection = () => {
  const resources = [
    {
      icon: Book,
      title: "Documentation",
      description: "Complete guides and API references to help you make the most of DaveLovable.",
      link: "#",
      linkText: "Read the docs",
    },
    {
      icon: Video,
      title: "Video Tutorials",
      description: "Step-by-step video guides covering everything from basics to advanced features.",
      link: "#",
      linkText: "Watch tutorials",
    },
    {
      icon: FileCode,
      title: "Code Examples",
      description: "Real-world examples and starter templates to kickstart your projects.",
      link: "#",
      linkText: "Browse examples",
    },
    {
      icon: MessageCircle,
      title: "Community",
      description: "Join our active community of developers to get help and share your creations.",
      link: "#",
      linkText: "Join community",
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
    <section id="docs" className="py-24 relative overflow-hidden">
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
            Learn how to build with{" "}
            <span className="text-gradient">DaveLovable</span>
          </h2>
          <p className="text-xl text-muted-foreground">
            Everything you need to master AI-powered development.
          </p>
        </div>

        {/* Resources Grid */}
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
