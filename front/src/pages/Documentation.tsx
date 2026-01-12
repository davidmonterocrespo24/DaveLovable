import { useState } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { Book, FileCode, MessageCircle, ArrowRight, Menu, ChevronRight, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

const Documentation = () => {
    const [activeSection, setActiveSection] = useState("introduction");
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    const sections = [
        {
            id: "introduction",
            title: "Introduction",
            items: [
                { id: "welcome", title: "Welcome" },
                { id: "overview", title: "System Overview" },
            ]
        },
        {
            id: "architecture",
            title: "System Architecture",
            items: [
                { id: "agents", title: "AI Agents System" },
                { id: "orchestrator", title: "Orchestrator" },
                { id: "tech-stack", title: "Tech Stack" },
            ]
        },
        {
            id: "guides",
            title: "User Guides",
            items: [
                { id: "getting-started", title: "Getting Started" },
                { id: "first-project", title: "Creating a Project" },
            ]
        }
    ];

    const scrollToSection = (id: string) => {
        const element = document.getElementById(id);
        if (element) {
            element.scrollIntoView({ behavior: "smooth" });
            setActiveSection(id);
            setMobileMenuOpen(false);
        }
    };

    return (
        <div className="min-h-screen bg-background flex flex-col">
            <Navbar />

            <div className="flex-1 container mx-auto px-6 pt-24 pb-12 flex relative">
                {/* Mobile Menu Toggle */}
                <button
                    className="lg:hidden fixed bottom-6 right-6 z-50 p-4 bg-primary text-primary-foreground rounded-full shadow-lg"
                    onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                >
                    <Menu />
                </button>

                {/* Sidebar Navigation */}
                <aside className={cn(
                    "fixed inset-y-0 left-0 z-40 w-64 bg-background border-r border-border transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:h-[calc(100vh-6rem)] lg:overflow-y-auto lg:pb-10 pt-24 lg:pt-0 pl-6",
                    mobileMenuOpen ? "translate-x-0" : "-translate-x-full"
                )}>
                    <div className="space-y-6">
                        <h3 className="font-bold text-lg mb-4 px-2">Documentation</h3>
                        {sections.map((section) => (
                            <div key={section.id} className="space-y-2">
                                <h4 className="font-semibold text-sm text-muted-foreground uppercase tracking-wider px-2">
                                    {section.title}
                                </h4>
                                <div className="space-y-1">
                                    {section.items.map((item) => (
                                        <button
                                            key={item.id}
                                            onClick={() => scrollToSection(item.id)}
                                            className={cn(
                                                "w-full text-left px-2 py-1.5 text-sm rounded-md transition-colors flex items-center gap-2",
                                                activeSection === item.id
                                                    ? "bg-primary/10 text-primary font-medium"
                                                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                                            )}
                                        >
                                            {activeSection === item.id && <ChevronRight className="w-3 h-3" />}
                                            {item.title}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                </aside>

                {/* Main Content */}
                <main className="flex-1 lg:pl-12 w-full max-w-4xl">
                    <div className="space-y-16 py-8">
                        {/* Introduction */}
                        <section id="welcome" className="space-y-6">
                            <h1 className="text-4xl font-extrabold mb-4">Documentation</h1>
                            <p className="text-xl text-muted-foreground leading-relaxed">
                                Welcome to the official documentation for DaveLovable. This guide will help you understand the architecture,
                                set up your environment, and start building AI-powered software autonomously.
                            </p>
                        </section>

                        <section id="overview" className="space-y-6">
                            <h2 className="text-3xl font-bold flex items-center gap-2">
                                <span className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary">#</span>
                                System Overview
                            </h2>
                            <div className="p-6 glass rounded-xl border-l-4 border-primary">
                                <p className="text-lg">
                                    DaveLovable is a multi-agent system designed to act as an autonomous software engineer.
                                    It takes high-level natural language prompts and converts them into full-stack applications.
                                </p>
                            </div>
                        </section>

                        <div className="border-t border-border/50 my-10" />

                        {/* Architecture */}
                        <section id="agents" className="space-y-6">
                            <h2 className="text-3xl font-bold mb-6">AI Agents System</h2>
                            <p className="text-muted-foreground mb-6">
                                The core of the system relies on specialized agents communicating to solve complex tasks.
                            </p>

                            <div className="grid md:grid-cols-2 gap-6">
                                <div className="glass p-6 rounded-xl">
                                    <div className="flex items-center gap-3 mb-4">
                                        <div className="bg-blue-500/10 p-2 rounded-lg"><MessageCircle className="text-blue-500 w-5 h-5" /></div>
                                        <h3 className="text-lg font-bold">Planner Agent</h3>
                                    </div>
                                    <p className="text-sm text-muted-foreground">
                                        Responsible for understanding requirements, creating tasks, and validating the output.
                                        It acts as the project manager, ensuring the solution matches the user's intent.
                                    </p>
                                </div>

                                <div className="glass p-6 rounded-xl">
                                    <div className="flex items-center gap-3 mb-4">
                                        <div className="bg-purple-500/10 p-2 rounded-lg"><FileCode className="text-purple-500 w-5 h-5" /></div>
                                        <h3 className="text-lg font-bold">Coder Agent</h3>
                                    </div>
                                    <p className="text-sm text-muted-foreground">
                                        The execution engine. It has access to file system tools, terminal, and search.
                                        It writes the code, runs tests, and applies fixes based on the Planner's feedback.
                                    </p>
                                </div>
                            </div>
                        </section>

                        <section id="orchestrator" className="space-y-6">
                            <h2 className="text-3xl font-bold">Orchestrator</h2>
                            <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                                The orchestration layer is built on <strong>Microsoft AutoGen 0.4</strong>. It manages the conversation history,
                                routes messages between agents, and handles termination conditions (e.g., when the task is complete or if a loop is detected).
                            </p>
                            <div className="bg-muted/50 p-4 rounded-lg font-mono text-sm leading-relaxed">
                User Prompt → [Orchestrator] → Planner (Plan) → Coder (Execute) → Planner (Review) → Output
                            </div>
                        </section>

                        <section id="tech-stack" className="space-y-6">
                            <h2 className="text-3xl font-bold">Tech Stack</h2>
                            <div className="overflow-hidden rounded-xl border border-border">
                                <table className="w-full text-left text-sm">
                                    <thead className="bg-muted/50">
                                        <tr>
                                            <th className="p-4 font-semibold">Component</th>
                                            <th className="p-4 font-semibold">Technology</th>
                                            <th className="p-4 font-semibold">Purpose</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-border/50">
                                        <tr><td className="p-4 font-medium">Backend</td><td className="p-4">FastAPI (Python)</td><td className="p-4">API & Agent Runtime</td></tr>
                                        <tr><td className="p-4 font-medium">AI Framework</td><td className="p-4">Microsoft AutoGen 0.4</td><td className="p-4">Multi-agent Orchestration</td></tr>
                                        <tr><td className="p-4 font-medium">LLM</td><td className="p-4">Gemini Flash</td><td className="p-4">Intelligence Engine</td></tr>
                                        <tr><td className="p-4 font-medium">Frontend</td><td className="p-4">React + Vite</td><td className="p-4">User Interface</td></tr>
                                        <tr><td className="p-4 font-medium">Styling</td><td className="p-4">TailwindCSS</td><td className="p-4">Components & Layouts</td></tr>
                                    </tbody>
                                </table>
                            </div>
                        </section>

                        <div className="border-t border-border/50 my-10" />

                        {/* Guides */}
                        <section id="getting-started" className="space-y-6">
                            <h2 className="text-3xl font-bold">Getting Started</h2>
                            <p className="text-muted-foreground">
                                Prerequisites: Python 3.10+, Node.js 18+, and a Gemini API Key.
                            </p>
                            <div className="bg-black/80 text-white p-4 rounded-xl font-mono text-sm">
                                npm install<br />
                                npm run dev
                            </div>
                        </section>

                        <section id="first-project" className="space-y-6">
                            <h2 className="text-3xl font-bold">Creating Your First Project</h2>
                            <ol className="list-decimal pl-6 space-y-4 text-muted-foreground">
                                <li>Go to the <strong>Projects</strong> page.</li>
                                <li>Click on "New Project".</li>
                                <li>Describe what you want to build (e.g., "A todo app with local storage").</li>
                                <li>Watch the agents generate the code in real-time.</li>
                            </ol>
                        </section>

                    </div>
                </main>
            </div>

            <Footer />
        </div>
    );
};

export default Documentation;
