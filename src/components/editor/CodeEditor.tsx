import { useState, useEffect, forwardRef, useMemo } from 'react';

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
  'index.css': `@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
}

body {
  @apply bg-background text-foreground;
}`,
  'main.tsx': `import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);`,
};

interface CodeEditorProps {
  selectedFile: string;
  isTyping: boolean;
}

// Token types for syntax highlighting
type TokenType = 'keyword' | 'string' | 'comment' | 'component' | 'tag' | 'attribute' | 'operator' | 'number' | 'function' | 'plain';

interface Token {
  type: TokenType;
  value: string;
}

const tokenColors: Record<TokenType, string> = {
  keyword: 'text-purple-400',
  string: 'text-green-400',
  comment: 'text-muted-foreground/60',
  component: 'text-cyan-400',
  tag: 'text-blue-400',
  attribute: 'text-orange-300',
  operator: 'text-pink-400',
  number: 'text-orange-400',
  function: 'text-yellow-300',
  plain: 'text-foreground/90',
};

const tokenize = (line: string): Token[] => {
  const tokens: Token[] = [];
  let remaining = line;

  const patterns: [RegExp, TokenType][] = [
    [/^(\/\/.*)/, 'comment'],
    [/^(import|export|from|const|let|var|function|return|if|else|interface|type|default|async|await)\b/, 'keyword'],
    [/^(<\/?)([A-Z][a-zA-Z]*)/, 'component'],
    [/^(<\/?)([a-z][a-z0-9]*)\b/, 'tag'],
    [/^([a-zA-Z_][a-zA-Z0-9_]*)\s*(?=\()/, 'function'],
    [/^(["'`])(?:(?!\1)[^\\]|\\.)*\1/, 'string'],
    [/^(\d+\.?\d*)/, 'number'],
    [/^([=<>!&|+\-*/%{}()[\];:,.?]+)/, 'operator'],
    [/^([a-zA-Z_][a-zA-Z0-9_]*)/, 'plain'],
    [/^(\s+)/, 'plain'],
  ];

  while (remaining.length > 0) {
    let matched = false;

    for (const [pattern, type] of patterns) {
      const match = remaining.match(pattern);
      if (match) {
        if (type === 'component' || type === 'tag') {
          // Handle JSX tags specially
          tokens.push({ type: 'operator', value: match[1] });
          tokens.push({ type, value: match[2] });
        } else {
          tokens.push({ type, value: match[0] });
        }
        remaining = remaining.slice(match[0].length);
        matched = true;
        break;
      }
    }

    if (!matched) {
      tokens.push({ type: 'plain', value: remaining[0] });
      remaining = remaining.slice(1);
    }
  }

  return tokens;
};

const SyntaxHighlightedLine = ({ line }: { line: string }) => {
  const tokens = useMemo(() => tokenize(line), [line]);
  
  return (
    <span>
      {tokens.map((token, i) => (
        <span key={i} className={tokenColors[token.type]}>
          {token.value}
        </span>
      ))}
    </span>
  );
};

export const CodeEditor = forwardRef<HTMLDivElement, CodeEditorProps>(
  ({ selectedFile, isTyping }, ref) => {
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
      <div ref={ref} className="h-full bg-[#0d1117] overflow-auto font-mono text-sm">
        <div className="flex min-h-full">
          {/* Line Numbers */}
          <div className="py-4 px-2 text-right text-muted-foreground/40 select-none border-r border-border/30 sticky left-0 bg-[#0d1117]">
            {lines.map((_, i) => (
              <div key={i} className="leading-6 text-xs px-2">
                {i + 1}
              </div>
            ))}
          </div>
          
          {/* Code Content */}
          <pre className="p-4 overflow-x-auto flex-1">
            <code>
              {lines.map((line, i) => (
                <div key={i} className="leading-6">
                  <SyntaxHighlightedLine line={line} />
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
  }
);

CodeEditor.displayName = 'CodeEditor';
