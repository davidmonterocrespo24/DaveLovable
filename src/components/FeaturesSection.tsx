import { Code2, Zap, Shield, Palette, Database, Globe } from "lucide-react";

const features = [
  {
    icon: Zap,
    title: "Lightning Fast",
    description: "Build complete applications in minutes, not months. Our AI understands context and generates production-ready code.",
  },
  {
    icon: Code2,
    title: "Real Code Output",
    description: "Get clean, maintainable React and TypeScript code. No black boxes - full access to every line.",
  },
  {
    icon: Database,
    title: "Built-in Backend",
    description: "Database, authentication, and APIs included. No external setup required - just describe what you need.",
  },
  {
    icon: Palette,
    title: "Beautiful by Default",
    description: "Every component is designed to look stunning. Customizable design system with dark mode support.",
  },
  {
    icon: Shield,
    title: "Enterprise Security",
    description: "SOC 2 compliant with automatic security best practices. Your data is always protected.",
  },
  {
    icon: Globe,
    title: "Deploy Instantly",
    description: "One-click deployment to production. Custom domains, SSL, and global CDN included.",
  },
];

const FeaturesSection = () => {
  return (
    <section id="features" className="py-32 relative">
      <div className="container mx-auto px-6">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-20">
          <span className="text-primary font-semibold text-sm uppercase tracking-wider">Features</span>
          <h2 className="text-4xl md:text-5xl font-bold mt-4 mb-6">
            Everything you need to{" "}
            <span className="text-gradient">ship faster</span>
          </h2>
          <p className="text-xl text-muted-foreground">
            From idea to production in record time. No compromises on quality or control.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <div
              key={feature.title}
              className="group glass rounded-2xl p-8 hover:border-primary/50 transition-all duration-300 hover:-translate-y-1"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="w-12 h-12 rounded-xl bg-gradient-primary flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                <feature.icon className="w-6 h-6 text-primary-foreground" />
              </div>
              <h3 className="text-xl font-semibold mb-3 text-foreground">
                {feature.title}
              </h3>
              <p className="text-muted-foreground leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default FeaturesSection;
