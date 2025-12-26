import { MessageSquare, Wand2, Rocket } from "lucide-react";

const steps = [
  {
    icon: MessageSquare,
    number: "01",
    title: "Describe Your Vision",
    description: "Simply tell us what you want to build in plain English. Be as specific or as vague as you like - our AI adapts to your style.",
  },
  {
    icon: Wand2,
    number: "02", 
    title: "Watch It Come to Life",
    description: "See your application materialize in real-time. Make adjustments, add features, and refine your vision through natural conversation.",
  },
  {
    icon: Rocket,
    number: "03",
    title: "Ship with Confidence",
    description: "Deploy to production with one click. Your app is fully functional, secure, and ready for users from day one.",
  },
];

const HowItWorksSection = () => {
  return (
    <section id="how-it-works" className="py-32 relative bg-gradient-subtle">
      <div className="container mx-auto px-6">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-20">
          <span className="text-primary font-semibold text-sm uppercase tracking-wider">How It Works</span>
          <h2 className="text-4xl md:text-5xl font-bold mt-4 mb-6">
            Three steps to{" "}
            <span className="text-gradient">production</span>
          </h2>
          <p className="text-xl text-muted-foreground">
            Building software has never been simpler. No coding experience required.
          </p>
        </div>

        {/* Steps */}
        <div className="grid md:grid-cols-3 gap-8 relative">
          {/* Connection Line */}
          <div className="hidden md:block absolute top-20 left-1/6 right-1/6 h-0.5 bg-gradient-to-r from-transparent via-primary/30 to-transparent" />
          
          {steps.map((step, index) => (
            <div key={step.number} className="relative">
              <div className="text-center">
                {/* Icon Container */}
                <div className="relative inline-flex mb-8">
                  <div className="w-20 h-20 rounded-2xl bg-gradient-primary flex items-center justify-center glow-primary">
                    <step.icon className="w-8 h-8 text-primary-foreground" />
                  </div>
                  <span className="absolute -top-2 -right-2 w-8 h-8 rounded-full bg-card border-2 border-primary flex items-center justify-center text-sm font-bold text-primary">
                    {step.number}
                  </span>
                </div>
                
                <h3 className="text-2xl font-bold mb-4 text-foreground">
                  {step.title}
                </h3>
                <p className="text-muted-foreground leading-relaxed max-w-sm mx-auto">
                  {step.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default HowItWorksSection;
