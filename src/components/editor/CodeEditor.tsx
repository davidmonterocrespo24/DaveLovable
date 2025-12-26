import { useState, useEffect } from 'react';

const mockCode: Record<string, string> = {
  'App.tsx': `import { Header } from './components/Header';
import { Card } from './components/Card';
import { Button } from './components/Button';

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800">
      <Header />
      <main className="container mx-auto px-4 py-12">
        <h1 className="text-4xl font-bold text-white mb-8">
          Welcome to My App
        </h1>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card title="Feature 1" description="Amazing feature" />
          <Card title="Feature 2" description="Another feature" />
          <Card title="Feature 3" description="Best feature" />
        </div>
        <Button>Get Started</Button>
      </main>
    </div>
  );
}

export default App;`,
  'Button.tsx': `interface ButtonProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary';
  onClick?: () => void;
}

export const Button = ({ 
  children, 
  variant = 'primary', 
  onClick 
}: ButtonProps) => {
  return (
    <button
      onClick={onClick}
      className={\`px-6 py-3 rounded-lg font-medium transition-all
        \${variant === 'primary' 
          ? 'bg-purple-600 hover:bg-purple-700 text-white' 
          : 'bg-white/10 hover:bg-white/20 text-white'
        }\`}
    >
      {children}
    </button>
  );
};`,
  'Card.tsx': `interface CardProps {
  title: string;
  description: string;
}

export const Card = ({ title, description }: CardProps) => {
  return (
    <div className="p-6 rounded-xl bg-white/5 border border-white/10 
                    hover:border-purple-500/50 transition-all">
      <h3 className="text-xl font-semibold text-white mb-2">
        {title}
      </h3>
      <p className="text-gray-400">{description}</p>
    </div>
  );
};`,
  'Header.tsx': `import { Menu } from 'lucide-react';

export const Header = () => {
  return (
    <header className="border-b border-white/10 px-6 py-4">
      <nav className="flex items-center justify-between">
        <span className="text-xl font-bold text-white">MyApp</span>
        <div className="hidden md:flex gap-6">
          <a href="#" className="text-gray-300 hover:text-white">Home</a>
          <a href="#" className="text-gray-300 hover:text-white">Features</a>
          <a href="#" className="text-gray-300 hover:text-white">Pricing</a>
        </div>
        <Menu className="md:hidden text-white" />
      </nav>
    </header>
  );
};`,
};

interface CodeEditorProps {
  selectedFile: string;
  isTyping: boolean;
}

export const CodeEditor = ({ selectedFile, isTyping }: CodeEditorProps) => {
  const [displayedCode, setDisplayedCode] = useState('');
  const code = mockCode[selectedFile] || '// Select a file to view its contents';

  useEffect(() => {
    if (isTyping) {
      setDisplayedCode('');
      let index = 0;
      const interval = setInterval(() => {
        if (index < code.length) {
          setDisplayedCode(code.slice(0, index + 1));
          index++;
        } else {
          clearInterval(interval);
        }
      }, 5);
      return () => clearInterval(interval);
    } else {
      setDisplayedCode(code);
    }
  }, [code, isTyping]);

  const lines = displayedCode.split('\n');

  return (
    <div className="h-full bg-[#0d1117] overflow-auto font-mono text-sm">
      <div className="flex">
        <div className="py-4 px-2 text-right text-muted-foreground/50 select-none border-r border-white/5">
          {lines.map((_, i) => (
            <div key={i} className="leading-6 text-xs">
              {i + 1}
            </div>
          ))}
        </div>
        <pre className="p-4 overflow-x-auto flex-1">
          <code className="text-gray-300">
            {displayedCode.split('\n').map((line, i) => (
              <div key={i} className="leading-6">
                {highlightSyntax(line)}
              </div>
            ))}
            {isTyping && (
              <span className="inline-block w-2 h-4 bg-primary animate-pulse ml-0.5" />
            )}
          </code>
        </pre>
      </div>
    </div>
  );
};

const highlightSyntax = (line: string) => {
  // Simple syntax highlighting
  const keywords = ['import', 'export', 'const', 'function', 'return', 'from', 'interface', 'type'];
  const reactKeywords = ['div', 'span', 'button', 'header', 'nav', 'main', 'h1', 'h3', 'p', 'a'];
  
  let result = line;
  
  // Highlight strings
  result = result.replace(/(["'`])(.*?)\1/g, '<span class="text-green-400">$&</span>');
  
  // Highlight keywords
  keywords.forEach(kw => {
    const regex = new RegExp(`\\b${kw}\\b`, 'g');
    result = result.replace(regex, `<span class="text-purple-400">${kw}</span>`);
  });
  
  // Highlight JSX tags
  reactKeywords.forEach(tag => {
    const regex = new RegExp(`<(/?)${tag}`, 'g');
    result = result.replace(regex, `<span class="text-blue-400">&lt;$1${tag}</span>`);
  });
  
  // Highlight component names (PascalCase)
  result = result.replace(/<([A-Z][a-zA-Z]*)/g, '<span class="text-cyan-400">&lt;$1</span>');
  result = result.replace(/<\/([A-Z][a-zA-Z]*)/g, '<span class="text-cyan-400">&lt;/$1</span>');
  
  // Highlight comments
  result = result.replace(/(\/\/.*$)/g, '<span class="text-gray-500">$1</span>');
  
  return <span dangerouslySetInnerHTML={{ __html: result }} />;
};
