import { useState, useEffect, forwardRef, useMemo } from 'react';

interface CodeEditorProps {
  selectedFile: {
    name: string;
    id: number;
    content: string;
  } | null;
  isTyping: boolean;
  onContentChange?: (content: string) => void;
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
  ({ selectedFile, isTyping, onContentChange }, ref) => {
    const [displayedCode, setDisplayedCode] = useState('');
    const [editableContent, setEditableContent] = useState('');
    const code = selectedFile?.content || '// Select a file to view its contents';

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
        setEditableContent(code);
      }
    }, [code, isTyping]);

    const handleContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const newContent = e.target.value;
      setEditableContent(newContent);
      setDisplayedCode(newContent);
      onContentChange?.(newContent);
    };

    const lines = displayedCode.split('\n');

    return (
      <div ref={ref} className="h-full bg-[#0d1117] overflow-auto font-mono text-sm relative">
        <div className="flex min-h-full">
          {/* Line Numbers */}
          <div className="py-4 px-2 text-right text-muted-foreground/40 select-none border-r border-border/30 sticky left-0 bg-[#0d1117] z-10">
            {lines.map((_, i) => (
              <div key={i} className="leading-6 text-xs px-2">
                {i + 1}
              </div>
            ))}
          </div>

          {/* Editable Textarea (invisible but functional) */}
          <textarea
            value={editableContent}
            onChange={handleContentChange}
            disabled={!selectedFile || isTyping}
            className="absolute inset-0 p-4 pl-[60px] bg-transparent text-transparent caret-white resize-none outline-none font-mono text-sm leading-6 z-20"
            spellCheck={false}
            style={{
              caretColor: 'white',
              WebkitTextFillColor: 'transparent'
            }}
          />

          {/* Code Content (syntax highlighted, read-only display) */}
          <pre className="p-4 overflow-x-auto flex-1 pointer-events-none">
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
