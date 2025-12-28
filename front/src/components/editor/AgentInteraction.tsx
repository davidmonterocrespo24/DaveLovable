import { useState } from 'react';
import { ChevronDown, ChevronRight, Wrench, Brain, CheckCircle, XCircle } from 'lucide-react';

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
        return 'bg-blue-50 border-blue-200';
      case 'tool_call':
        return 'bg-purple-50 border-purple-200';
      case 'tool_response':
        return content.toLowerCase().includes('error') ?
          'bg-red-50 border-red-200' :
          'bg-green-50 border-green-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className={`border rounded-lg overflow-hidden transition-all ${getBgColor()}`}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-2 flex items-center gap-3 hover:bg-black/5 transition-colors text-left"
      >
        <div className="shrink-0">
          {isExpanded ? (
            <ChevronDown className="w-4 h-4 text-gray-600" />
          ) : (
            <ChevronRight className="w-4 h-4 text-gray-600" />
          )}
        </div>
        <div className="shrink-0">
          {getIcon()}
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-gray-900 truncate">
            {getTitle()}
          </div>
          {!isExpanded && (
            <div className="text-xs text-gray-600 truncate">
              {content.substring(0, 60)}
              {content.length > 60 && '...'}
            </div>
          )}
        </div>
        <div className="text-xs text-gray-500 shrink-0">
          {new Date(timestamp).toLocaleTimeString()}
        </div>
      </button>

      {isExpanded && (
        <div className="px-4 py-3 border-t border-gray-200 bg-white/50">
          <div className="space-y-2">
            <div className="text-sm text-gray-800 whitespace-pre-wrap break-words">
              {content}
            </div>

            {toolName && (
              <div className="mt-3 pt-3 border-t border-gray-200">
                <div className="text-xs font-semibold text-gray-700 mb-2">
                  Tool: {toolName}
                </div>
                {toolArguments && Object.keys(toolArguments).length > 0 && (
                  <div className="mt-2">
                    <div className="text-xs font-semibold text-gray-700 mb-1">
                      Arguments:
                    </div>
                    <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto">
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
