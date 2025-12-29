import { useState } from 'react';
import { ChevronDown, ChevronRight, Wrench, CheckCircle, XCircle } from 'lucide-react';

interface ToolExecution {
  toolName: string;
  agentName: string;
  arguments: Record<string, any>;
  response: string;
  timestamp: string;
  hasError?: boolean;
}

interface ToolExecutionBlockProps {
  executions: ToolExecution[];
}

const ArgumentField: React.FC<{ name: string; value: any }> = ({ name, value }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const isLongValue = typeof value === 'string' && value.length > 100;
  const isObject = typeof value === 'object' && value !== null;

  if (isLongValue) {
    return (
      <div className="mb-2">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-1 text-[10px] font-medium text-purple-400 hover:text-purple-300"
        >
          {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
          <span className="font-mono">{name}</span>
          <span className="text-muted-foreground">({value.length} chars)</span>
        </button>
        {isExpanded && (
          <pre className="mt-1 text-[10px] bg-muted/40 text-foreground p-2 rounded overflow-x-auto border border-border/20 max-h-96">
            {value}
          </pre>
        )}
      </div>
    );
  }

  return (
    <div className="mb-1">
      <span className="text-[10px] font-mono text-purple-400">{name}</span>
      <span className="text-muted-foreground">: </span>
      <span className="text-[10px] text-foreground font-mono">
        {isObject ? JSON.stringify(value) : String(value)}
      </span>
    </div>
  );
};

const ToolExecutionItem: React.FC<{ execution: ToolExecution; index: number }> = ({ execution, index }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="border border-border/20 rounded overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-2 py-1 flex items-center gap-1.5 hover:bg-muted/30 transition-colors text-left"
      >
        <div className="shrink-0">
          {isExpanded ? (
            <ChevronDown className="w-3 h-3 text-muted-foreground" />
          ) : (
            <ChevronRight className="w-3 h-3 text-muted-foreground" />
          )}
        </div>
        <div className="shrink-0">
          <Wrench className="w-3 h-3 text-purple-400" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-[10px] font-semibold text-foreground truncate">
            {execution.agentName} → {execution.toolName}
          </div>
        </div>
        <div className="shrink-0">
          {execution.hasError ? (
            <XCircle className="w-3 h-3 text-red-400" />
          ) : (
            <CheckCircle className="w-3 h-3 text-green-400" />
          )}
        </div>
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="px-2 py-1.5 border-t border-border/20 bg-background/30 space-y-1.5">
          {/* Arguments */}
          {execution.arguments && Object.keys(execution.arguments).length > 0 && (
            <div>
              <div className="text-[9px] font-medium text-muted-foreground mb-1">
                Arguments:
              </div>
              <div className="bg-muted/20 p-1.5 rounded border border-border/20">
                {Object.entries(execution.arguments).map(([key, value]) => (
                  <ArgumentField key={key} name={key} value={value} />
                ))}
              </div>
            </div>
          )}

          {/* Response */}
          <div>
            <div className="text-[9px] font-medium text-muted-foreground mb-0.5">
              {execution.hasError ? 'Error Response:' : 'Response:'}
            </div>
            <div className={`text-[10px] p-1.5 rounded border ${
              execution.hasError
                ? 'bg-red-500/10 border-red-500/30 text-red-200'
                : 'bg-muted/30 border-border/20 text-foreground'
            } whitespace-pre-wrap break-words max-h-48 overflow-y-auto`}>
              {execution.response}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export const ToolExecutionBlock: React.FC<ToolExecutionBlockProps> = ({ executions }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (executions.length === 0) return null;

  const firstExecution = executions[0];
  const hasAnyError = executions.some(e => e.hasError);

  return (
    <div className="border border-border/30 rounded overflow-hidden transition-all bg-purple-500/10">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-3 py-1.5 flex items-center gap-2 hover:bg-muted/40 transition-colors text-left"
      >
        <div className="shrink-0">
          {isExpanded ? (
            <ChevronDown className="w-3.5 h-3.5 text-muted-foreground" />
          ) : (
            <ChevronRight className="w-3.5 h-3.5 text-muted-foreground" />
          )}
        </div>
        <div className="shrink-0">
          {hasAnyError ? (
            <XCircle className="w-3.5 h-3.5 text-red-400" />
          ) : (
            <Wrench className="w-3.5 h-3.5 text-purple-400" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-xs font-medium text-foreground truncate">
            Tool Executions ({executions.length})
          </div>
          {!isExpanded && (
            <div className="text-[10px] text-muted-foreground truncate">
              {executions.map(e => e.toolName).join(', ')}
            </div>
          )}
        </div>
        <div className="text-[10px] text-muted-foreground shrink-0">
          {new Date(firstExecution.timestamp).toLocaleTimeString()}
        </div>
      </button>

      {isExpanded && (
        <div className="px-3 py-2 border-t border-border/30 bg-background/50">
          <div className="space-y-1">
            {executions.map((execution, idx) => (
              <ToolExecutionItem key={idx} execution={execution} index={idx} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
