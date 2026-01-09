import { Button } from "@/components/ui/button";
import { ArrowRight, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";

const HeroSection = () => {
  return (
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
          <h1 className="text-5xl md:text-7xl font-extrabold leading-tight mb-6 animate-fade-in-up">
            Build software with{" "}
            <span className="text-gradient">superhuman</span>{" "}
            speed
          </h1>

          {/* Subheadline */}
          <p className="text-xl md:text-2xl text-muted-foreground max-w-2xl mx-auto mb-10 animate-fade-in-up delay-200">
            Describe what you want to build, and watch AI transform your ideas into 
            production-ready applications in minutes.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-fade-in-up delay-300">
            <Link to="/editor">
              <Button variant="hero" size="xl">
                Start Building Free
                <ArrowRight className="w-5 h-5" />
              </Button>
            </Link>
            <Button variant="heroOutline" size="xl">
              Watch Demo
            </Button>
          </div>

          {/* Social Proof */}
          <div className="mt-16 animate-fade-in delay-500">
            <p className="text-sm text-muted-foreground mb-4">
              Trusted by 100,000+ developers and teams
            </p>
            <div className="flex flex-wrap items-center justify-center gap-8 opacity-50">
              {["Google", "Microsoft", "Stripe", "Vercel", "Notion"].map((company) => (
                <span key={company} className="text-lg font-semibold text-muted-foreground">
                  {company}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Floating Preview Window */}
        <div className="mt-20 relative max-w-5xl mx-auto animate-fade-in-up delay-400">
          <div className="glass rounded-2xl overflow-hidden glow-accent">
            {/* Window Header */}
            <div className="flex items-center gap-2 px-4 py-3 border-b border-border/30">
              <div className="flex gap-2">
                <div className="w-3 h-3 rounded-full bg-destructive/70" />
                <div className="w-3 h-3 rounded-full bg-yellow-500/70" />
                <div className="w-3 h-3 rounded-full bg-green-500/70" />
              </div>
              <div className="flex-1 text-center">
                <span className="text-xs text-muted-foreground">dlovable.daveplanet.com</span>
              </div>
            </div>
            
            {/* Preview Content */}
            <div className="p-8 bg-card/30">
              <div className="grid md:grid-cols-2 gap-8">
                {/* Chat Panel */}
                <div className="space-y-4">
                  <div className="glass rounded-lg p-4">
                    <p className="text-sm text-muted-foreground">You:</p>
                    <p className="text-foreground mt-1">Create a dashboard with analytics charts and user management</p>
                  </div>
                  <div className="glass rounded-lg p-4 border-primary/30">
                    <p className="text-sm text-primary">DaveLovable:</p>
                    <p className="text-foreground mt-1">Building your dashboard with interactive charts, user table with search, and role management...</p>
                  </div>
                </div>
                
                {/* Code Preview */}
                <div className="glass rounded-lg p-4 font-mono text-xs">
                  <div className="text-muted-foreground">// Generated component</div>
                  <div className="mt-2">
                    <span className="text-primary">export</span> <span className="text-accent">function</span> <span className="text-foreground">Dashboard</span>() {"{"}
                  </div>
                  <div className="pl-4 text-foreground">
                    <span className="text-primary">return</span> (
                  </div>
                  <div className="pl-8 text-muted-foreground">{"<div className=\"...\">"}</div>
                  <div className="pl-8 text-muted-foreground">  {"<AnalyticsChart />"}</div>
                  <div className="pl-8 text-muted-foreground">  {"<UserTable />"}</div>
                  <div className="pl-8 text-muted-foreground">{"</div>"}</div>
                  <div className="text-foreground">{"}"}</div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Decorative floating elements */}
          <div className="absolute -top-4 -right-4 w-20 h-20 bg-gradient-primary rounded-xl rotate-12 opacity-20 animate-float" />
          <div className="absolute -bottom-4 -left-4 w-16 h-16 bg-accent/30 rounded-lg -rotate-12 animate-float delay-300" />
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
