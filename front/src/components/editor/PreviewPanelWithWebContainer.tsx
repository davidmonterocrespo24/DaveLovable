import { useState, useEffect, forwardRef, useImperativeHandle, useRef } from 'react';
import {
  RefreshCw,
  Smartphone,
  Tablet,
  Monitor,
  ExternalLink,
  Maximize2,
  Terminal,
  X,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Send,
  Copy,
  Check
} from 'lucide-react';
import { loadProject, reloadProjectFiles } from '@/services/webcontainer';
import { initializeLogCapture } from '@/services/browserLogs';

interface PreviewPanelProps {
  projectId: number;
  isLoading?: boolean;
  onReload?: () => void;
  onReportError?: (errorMessage: string) => void;
  onPreviewReady?: (url: string) => void;
}

interface ConsoleLog {
  type: 'info' | 'log' | 'warn' | 'error';
  message: string;
  timestamp: string;
}

export interface PreviewPanelRef {
  reload: () => void;
}

export const PreviewPanel = forwardRef<PreviewPanelRef, PreviewPanelProps>(
  ({ projectId, isLoading: externalLoading, onReload, onReportError, onPreviewReady }, ref) => {
    const [device, setDevice] = useState<'mobile' | 'tablet' | 'desktop'>('desktop');
    const [showConsole, setShowConsole] = useState(true);
    const [previewUrl, setPreviewUrl] = useState<string>('');
    const [isInitializing, setIsInitializing] = useState(true);
    const [initError, setInitError] = useState<string>('');
    const [consoleLogs, setConsoleLogs] = useState<ConsoleLog[]>([]);
    const [urlCopied, setUrlCopied] = useState(false);
    const iframeRef = useRef<HTMLIFrameElement>(null);

    const deviceWidths = {
      mobile: 'max-w-[375px]',
      tablet: 'max-w-[768px]',
      desktop: 'w-full',
    };

    const addLog = (type: ConsoleLog['type'], message: string) => {
      const timestamp = new Date().toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        fractionalSecondDigits: 3
      });

      setConsoleLogs(prev => [...prev, { type, message, timestamp }]);
    };

    // Listen for browser logs from the iframe via postMessage
    useEffect(() => {
      const handleMessage = (event: MessageEvent) => {
        // Security: verify the message is from our WebContainer
        if (event.data?.type === 'console-log') {
          const { logType, message } = event.data;
          // Add browser console logs to our log display
          addLog(logType as ConsoleLog['type'], message);
        }
      };

      window.addEventListener('message', handleMessage);
      return () => window.removeEventListener('message', handleMessage);
    }, []);

    const initializeWebContainer = async () => {
      setIsInitializing(true);
      setInitError('');
      setConsoleLogs([]);
      setPreviewUrl('');

      addLog('info', '[WebContainer] Initializing...');

      try {
        const result = await loadProject(
          projectId,
          (msg) => {
            // Determine log type from message
            if (msg.includes('ERROR') || msg.includes('error')) {
              addLog('error', msg);
            } else if (msg.includes('WARN') || msg.includes('warn')) {
              addLog('warn', msg);
            } else {
              addLog('info', msg);
            }
          },
          (msg) => {
            addLog('error', msg);
          }
        );

        setPreviewUrl(result.url);
        addLog('log', `✓ Application ready at ${result.url}`);
        setIsInitializing(false);

        // Notify parent component that preview is ready
        if (onPreviewReady) {
          onPreviewReady(result.url);
        }
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : 'Unknown error';
        setInitError(errorMsg);
        addLog('error', `✗ Failed to initialize: ${errorMsg}`);
        setIsInitializing(false);
      }
    };

    useEffect(() => {
      initializeWebContainer();
    }, [projectId]);

    // Initialize browser log capture when component mounts
    useEffect(() => {
      console.log('[PreviewPanel] Initializing browser log capture listener');
      initializeLogCapture();
    }, []);

    // Lightweight reload: only update files without reinstalling or restarting
    const reloadFiles = async () => {
      if (!previewUrl) {
        // If not initialized yet, do full initialization
        initializeWebContainer();
        return;
      }

      addLog('info', '[WebContainer] Reloading files...');

      try {
        await reloadProjectFiles(
          projectId,
          (msg) => {
            addLog('info', msg);
          }
        );
        addLog('log', '✓ Files reloaded successfully');
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : 'Unknown error';
        addLog('error', `✗ Failed to reload files: ${errorMsg}`);
      }
    };

    // Expose reload method to parent via ref (uses lightweight reload)
    useImperativeHandle(ref, () => ({
      reload: () => {
        if (onReload) {
          onReload();
        }
        reloadFiles();
      },
    }));

    const handleRefresh = () => {
      if (onReload) {
        onReload();
      }
      initializeWebContainer();
    };

    const getLogIcon = (type: ConsoleLog['type']) => {
      switch (type) {
        case 'error':
          return <AlertCircle className="w-3 h-3 text-red-400" />;
        case 'warn':
          return <AlertCircle className="w-3 h-3 text-yellow-400" />;
        case 'info':
          return <CheckCircle2 className="w-3 h-3 text-blue-400" />;
        default:
          return <span className="text-muted-foreground">›</span>;
      }
    };

    const handleReportErrors = () => {
      const errors = consoleLogs.filter(log => log.type === 'error');
      if (errors.length === 0) {
        return;
      }

      const errorReport = errors.map(err => `[${err.timestamp}] ${err.message}`).join('\n');
      const fullReport = `I found ${errors.length} error(s) in the console:\n\n${errorReport}\n\nPlease help me fix these errors.`;

      if (onReportError) {
        onReportError(fullReport);
      }
    };

    const handleCopyUrl = async () => {
      if (!previewUrl) return;

      try {
        await navigator.clipboard.writeText(previewUrl);
        setUrlCopied(true);
        setTimeout(() => setUrlCopied(false), 2000);
      } catch (err) {
        console.error('Failed to copy URL:', err);
      }
    };

    const handleFullscreen = () => {
      if (!ref || typeof ref === 'function') return;

      const element = ref.current;
      if (!element) return;

      if (!document.fullscreenElement) {
        element.requestFullscreen().catch(err => {
          console.error('Error attempting to enable fullscreen:', err);
        });
      } else {
        document.exitFullscreen();
      }
    };

    const isLoading = externalLoading || isInitializing;

    return (
      <div ref={ref} className="h-full flex flex-col bg-[#0d1117]">
        {/* Toolbar */}
        <div className="flex items-center justify-between px-3 py-2 border-b border-border/50 bg-background/50">
          <div className="flex items-center gap-2">
            <button
              onClick={handleRefresh}
              disabled={isLoading}
              className="p-1.5 hover:bg-muted/20 rounded transition-colors text-muted-foreground hover:text-foreground disabled:opacity-50"
              title="Refresh"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>

            <div className="flex items-center bg-muted/20 rounded-lg p-0.5">
              <button
                onClick={() => setDevice('mobile')}
                className={`p-1.5 rounded transition-colors ${
                  device === 'mobile' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'
                }`}
                title="Mobile view"
              >
                <Smartphone className="w-4 h-4" />
              </button>
              <button
                onClick={() => setDevice('tablet')}
                className={`p-1.5 rounded transition-colors ${
                  device === 'tablet' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'
                }`}
                title="Tablet view"
              >
                <Tablet className="w-4 h-4" />
              </button>
              <button
                onClick={() => setDevice('desktop')}
                className={`p-1.5 rounded transition-colors ${
                  device === 'desktop' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'
                }`}
                title="Desktop view"
              >
                <Monitor className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* URL Bar */}
          <div className="flex-1 mx-4">
            <div className="flex items-center gap-2 bg-muted/20 rounded-lg px-3 py-1.5 max-w-md mx-auto border border-border/30">
              <div className={`w-2 h-2 rounded-full ${
                previewUrl ? 'bg-green-500 animate-pulse' : 'bg-gray-500'
              }`} />
              <span className="text-xs text-muted-foreground truncate">
                {previewUrl || 'Initializing...'}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={() => setShowConsole(!showConsole)}
              className={`p-1.5 rounded transition-colors relative ${
                showConsole ? 'bg-primary text-primary-foreground' : 'hover:bg-muted/20 text-muted-foreground hover:text-foreground'
              }`}
              title="Toggle console"
            >
              <Terminal className="w-4 h-4" />
              {consoleLogs.some(l => l.type === 'error') && (
                <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-red-500 rounded-full" />
              )}
            </button>
            <button
              disabled={!previewUrl}
              onClick={handleCopyUrl}
              className={`p-1.5 rounded transition-colors disabled:opacity-50 ${
                urlCopied
                  ? 'bg-green-500/20 text-green-400'
                  : 'hover:bg-muted/20 text-muted-foreground hover:text-foreground'
              }`}
              title={urlCopied ? "URL copied!" : "Copy preview URL"}
            >
              {urlCopied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
            </button>
            <button
              onClick={handleFullscreen}
              className="p-1.5 hover:bg-muted/20 rounded transition-colors text-muted-foreground hover:text-foreground"
              title="Toggle fullscreen"
            >
              <Maximize2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Preview Area */}
        <div className="flex-1 overflow-auto p-4 flex justify-center bg-[#1a1a2e]">
          <div
            className={`${deviceWidths[device]} w-full h-full bg-white
                        rounded-lg overflow-hidden shadow-2xl border border-border/30 transition-all duration-300`}
          >
            {isLoading ? (
              <div className="h-full flex flex-col items-center justify-center gap-4 bg-gradient-to-br from-slate-900 to-slate-800">
                <div className="relative">
                  <Loader2 className="w-12 h-12 text-primary animate-spin" />
                </div>
                <p className="text-sm text-muted-foreground">
                  {isInitializing ? 'Starting WebContainer...' : 'Loading preview...'}
                </p>
                <div className="flex items-center gap-2 text-xs text-muted-foreground/60">
                  <span className="w-1.5 h-1.5 bg-primary rounded-full animate-pulse" />
                  {isInitializing ? 'Installing dependencies...' : 'Preparing...'}
                </div>
              </div>
            ) : initError ? (
              <div className="h-full flex flex-col items-center justify-center gap-4 bg-gradient-to-br from-red-900/20 to-slate-800 p-8">
                <AlertCircle className="w-12 h-12 text-red-400" />
                <p className="text-sm text-red-400 font-medium">Failed to start preview</p>
                <p className="text-xs text-muted-foreground text-center max-w-md">
                  {initError}
                </p>
                <button
                  onClick={handleRefresh}
                  className="mt-4 px-4 py-2 bg-primary hover:bg-primary/90 text-primary-foreground rounded-lg text-sm font-medium transition-colors"
                >
                  Retry
                </button>
              </div>
            ) : previewUrl ? (
              <iframe
                ref={iframeRef}
                src={previewUrl}
                className="w-full h-full border-0"
                title="Preview"
                allow="cross-origin-isolated"
                sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals"
              />
            ) : (
              <div className="h-full flex items-center justify-center bg-gradient-to-br from-slate-900 to-slate-800">
                <p className="text-sm text-muted-foreground">No preview available</p>
              </div>
            )}
          </div>
        </div>

        {/* Console */}
        {showConsole && (
          <div className="h-64 border-t border-border/50 bg-[#0d1117] flex flex-col">
            <div className="flex items-center justify-between px-3 py-2 border-b border-border/50">
              <div className="flex items-center gap-4">
                <span className="text-xs font-medium text-foreground">Console</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs px-2 py-0.5 rounded bg-muted/30 text-muted-foreground">
                    All ({consoleLogs.length})
                  </span>
                  {consoleLogs.filter(l => l.type === 'error').length > 0 && (
                    <span className="text-xs px-2 py-0.5 rounded bg-red-500/20 text-red-400">
                      {consoleLogs.filter(l => l.type === 'error').length} errors
                    </span>
                  )}
                  {consoleLogs.filter(l => l.type === 'warn').length > 0 && (
                    <span className="text-xs px-2 py-0.5 rounded bg-yellow-500/20 text-yellow-400">
                      {consoleLogs.filter(l => l.type === 'warn').length} warnings
                    </span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                {consoleLogs.filter(l => l.type === 'error').length > 0 && (
                  <button
                    onClick={handleReportErrors}
                    className="text-xs px-3 py-1 bg-red-500/20 hover:bg-red-500/30 rounded transition-colors text-red-400 flex items-center gap-1.5 border border-red-500/30 animate-pulse"
                    title="Send browser errors to AI for fixing"
                  >
                    <Send className="w-3 h-3" />
                    Report Browser Errors to AI
                  </button>
                )}
                <button
                  onClick={() => setConsoleLogs([])}
                  className="text-xs px-2 py-1 hover:bg-muted/20 rounded transition-colors text-muted-foreground"
                >
                  Clear
                </button>
                <button
                  onClick={() => setShowConsole(false)}
                  className="p-1 hover:bg-muted/20 rounded transition-colors"
                >
                  <X className="w-3 h-3 text-muted-foreground" />
                </button>
              </div>
            </div>
            <div className="flex-1 p-3 font-mono text-xs space-y-1 overflow-auto">
              {consoleLogs.length === 0 ? (
                <div className="flex items-center justify-center h-full text-muted-foreground/50">
                  No console output
                </div>
              ) : (
                consoleLogs.map((log, i) => (
                  <div key={i} className="flex items-start gap-2 hover:bg-muted/10 px-1 rounded">
                    <span className="text-muted-foreground/50 w-20 shrink-0 font-mono">{log.timestamp}</span>
                    <span className="shrink-0">{getLogIcon(log.type)}</span>
                    <span className={`flex-1 break-all ${
                      log.type === 'error' ? 'text-red-400' :
                      log.type === 'warn' ? 'text-yellow-400' :
                      'text-foreground/80'
                    }`}>{log.message}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    );
  }
);

PreviewPanel.displayName = 'PreviewPanel';
