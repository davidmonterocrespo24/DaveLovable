import { useState } from 'react';
import { ChevronDown, ChevronRight, Wrench, Brain, CheckCircle, XCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github-dark.css';

interface AgentInteractionProps {
  agentName: string;
  messageType: 'thought' | 'tool_call' | 'tool_response';
  content: string;
  toolName?: string;
  toolArguments?: Record<string, any>;
  timestamp: string;
}

export const AgentInteraction: React.FC<AgentInteractionProps> = ({
  agentName,
  messageType,
  content,
  toolName,
  toolArguments,
  timestamp,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getIcon = () => {
    switch (messageType) {
      case 'thought':
        return <Brain className="w-4 h-4" />;
      case 'tool_call':
        return <Wrench className="w-4 h-4" />;
      case 'tool_response':
        return content.toLowerCase().includes('error') ?
          <XCircle className="w-4 h-4 text-red-500" /> :
          <CheckCircle className="w-4 h-4 text-green-500" />;
      default:
        return <Brain className="w-4 h-4" />;
    }
  };

  const getTitle = () => {
    switch (messageType) {
      case 'thought':
        return `${agentName} is thinking`;
      case 'tool_call':
        return `${agentName} is using ${toolName}`;
      case 'tool_response':
        return `Tool response`;
      default:
        return `${agentName}`;
    }
  };

  const getBgColor = () => {
    switch (messageType) {
      case 'thought':
        // Different colors for Planner vs Coder
        if (agentName === 'Planner') {
          return 'bg-indigo-500/10 border-indigo-500/30';
        }
        return 'bg-blue-500/10 border-blue-500/30';
      case 'tool_call':
        return 'bg-purple-500/10 border-purple-500/30';
      case 'tool_response':
        return content.toLowerCase().includes('error') ?
          'bg-red-500/10 border-red-500/30' :
          'bg-green-500/10 border-green-500/30';
      default:
        return 'bg-muted/20 border-border/30';
    }
  };

  return (
    <div className={`border rounded-lg overflow-hidden transition-all ${getBgColor()}`}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-2 flex items-center gap-3 hover:bg-muted/40 transition-colors text-left"
      >
        <div className="shrink-0">
          {isExpanded ? (
            <ChevronDown className="w-4 h-4 text-muted-foreground" />
          ) : (
            <ChevronRight className="w-4 h-4 text-muted-foreground" />
          )}
        </div>
        <div className="shrink-0">
          {getIcon()}
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-foreground truncate">
            {getTitle()}
          </div>
          {!isExpanded && (
            <div className="text-xs text-muted-foreground truncate">
              {content.substring(0, 60)}
              {content.length > 60 && '...'}
            </div>
          )}
        </div>
        <div className="text-xs text-muted-foreground shrink-0">
          {new Date(timestamp).toLocaleTimeString()}
        </div>
      </button>

      {isExpanded && (
        <div className="px-4 py-2 border-t border-border/30 bg-background/50">
          <div className="space-y-1">
            <div className="text-xs prose prose-xs prose-invert max-w-none
                          prose-headings:text-gray-100 prose-headings:text-xs prose-headings:my-1
                          prose-p:text-gray-200 prose-p:text-xs prose-p:my-0.5 prose-p:leading-tight
                          prose-strong:text-gray-100
                          prose-code:text-gray-200 prose-code:text-[10px]
                          prose-pre:bg-gray-800 prose-pre:text-gray-100 prose-pre:text-[10px] prose-pre:my-1
                          prose-li:text-gray-200 prose-li:text-xs prose-li:my-0
                          prose-ul:my-1 prose-ol:my-1
                          prose-a:text-blue-400">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeHighlight]}
              >
                {content}
              </ReactMarkdown>
            </div>

            {toolName && (
              <div className="mt-3 pt-3 border-t border-border/30">
                <div className="text-xs font-semibold text-foreground mb-2">
                  Tool: {toolName}
                </div>
                {toolArguments && Object.keys(toolArguments).length > 0 && (
                  <div className="mt-2">
                    <div className="text-xs font-semibold text-foreground mb-1">
                      Arguments:
                    </div>
                    <pre className="text-xs bg-muted/30 text-foreground p-2 rounded overflow-x-auto border border-border/20">
                      {JSON.stringify(toolArguments, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
