import { useState, forwardRef } from 'react';
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
  CheckCircle2
} from 'lucide-react';

interface PreviewPanelProps {
  isLoading: boolean;
}

interface ConsoleLog {
  type: 'info' | 'log' | 'warn' | 'error';
  message: string;
  timestamp: string;
}

export const PreviewPanel = forwardRef<HTMLDivElement, PreviewPanelProps>(
  ({ isLoading }, ref) => {
    const [device, setDevice] = useState<'mobile' | 'tablet' | 'desktop'>('desktop');
    const [showConsole, setShowConsole] = useState(false);
    const [url] = useState('my-awesome-app.lovable.app');

    const consoleLogs: ConsoleLog[] = [
      { type: 'info', message: '[vite] connecting...', timestamp: '00:00:01' },
      { type: 'info', message: '[vite] connected.', timestamp: '00:00:02' },
      { type: 'log', message: 'App mounted successfully', timestamp: '00:00:03' },
      { type: 'log', message: 'Rendering 3 Card components', timestamp: '00:00:03' },
      { type: 'warn', message: 'React DevTools not detected', timestamp: '00:00:04' },
    ];

    const deviceWidths = {
      mobile: 'max-w-[375px]',
      tablet: 'max-w-[768px]',
      desktop: 'w-full',
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

    return (
      <div ref={ref} className="h-full flex flex-col bg-[#0d1117]">
        {/* Toolbar */}
        <div className="flex items-center justify-between px-3 py-2 border-b border-border/50 bg-background/50">
          <div className="flex items-center gap-2">
            <button 
              className="p-1.5 hover:bg-muted/20 rounded transition-colors text-muted-foreground hover:text-foreground"
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
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-xs text-muted-foreground truncate">{url}</span>
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
              className="p-1.5 hover:bg-muted/20 rounded transition-colors text-muted-foreground hover:text-foreground"
              title="Open in new tab"
            >
              <ExternalLink className="w-4 h-4" />
            </button>
            <button 
              className="p-1.5 hover:bg-muted/20 rounded transition-colors text-muted-foreground hover:text-foreground"
              title="Fullscreen"
            >
              <Maximize2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Preview Area */}
        <div className="flex-1 overflow-auto p-4 flex justify-center bg-[#1a1a2e]">
          <div 
            className={`${deviceWidths[device]} w-full h-full bg-gradient-to-br from-slate-900 to-slate-800 
                        rounded-lg overflow-hidden shadow-2xl border border-border/30 transition-all duration-300`}
          >
            {isLoading ? (
              <div className="h-full flex flex-col items-center justify-center gap-4">
                <div className="relative">
                  <div className="w-12 h-12 border-4 border-primary/30 rounded-full" />
                  <div className="w-12 h-12 border-4 border-transparent border-t-primary rounded-full animate-spin absolute inset-0" />
                </div>
                <p className="text-sm text-muted-foreground">Iniciando WebContainer...</p>
                <div className="flex items-center gap-2 text-xs text-muted-foreground/60">
                  <span className="w-1.5 h-1.5 bg-primary rounded-full animate-pulse" />
                  Instalando dependencias...
                </div>
              </div>
            ) : (
              <div className="h-full overflow-auto">
                {/* Simulated App Preview */}
                <header className="border-b border-white/10 px-6 py-4">
                  <nav className="flex items-center justify-between">
                    <span className="text-xl font-bold text-white">MyApp</span>
                    <div className="hidden md:flex gap-6">
                      <a href="#" className="text-gray-300 hover:text-white transition-colors">Home</a>
                      <a href="#" className="text-gray-300 hover:text-white transition-colors">Features</a>
                      <a href="#" className="text-gray-300 hover:text-white transition-colors">Pricing</a>
                    </div>
                  </nav>
                </header>
                
                <main className="container mx-auto px-4 py-12">
                  <h1 className="text-4xl font-bold text-white mb-8">
                    Welcome to My App
                  </h1>
                  <div className={`grid gap-6 ${device === 'mobile' ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-3'}`}>
                    {['Feature 1', 'Feature 2', 'Feature 3'].map((title) => (
                      <div
                        key={title}
                        className="p-6 rounded-xl bg-white/5 border border-white/10 
                                  hover:border-purple-500/50 transition-all cursor-pointer
                                  hover:transform hover:scale-[1.02]"
                      >
                        <h3 className="text-xl font-semibold text-white mb-2">{title}</h3>
                        <p className="text-gray-400">Amazing feature description goes here</p>
                      </div>
                    ))}
                  </div>
                  <button className="mt-8 px-6 py-3 rounded-lg font-medium bg-purple-600 
                                   hover:bg-purple-700 text-white transition-all">
                    Get Started
                  </button>
                </main>
              </div>
            )}
          </div>
        </div>

        {/* Console */}
        {showConsole && (
          <div className="h-48 border-t border-border/50 bg-[#0d1117] flex flex-col">
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
              <button 
                onClick={() => setShowConsole(false)}
                className="p-1 hover:bg-muted/20 rounded transition-colors"
              >
                <X className="w-3 h-3 text-muted-foreground" />
              </button>
            </div>
            <div className="flex-1 p-3 font-mono text-xs space-y-1 overflow-auto">
              {consoleLogs.map((log, i) => (
                <div key={i} className="flex items-start gap-2 hover:bg-muted/10 px-1 rounded">
                  <span className="text-muted-foreground/50 w-16 shrink-0">{log.timestamp}</span>
                  <span className="shrink-0">{getLogIcon(log.type)}</span>
                  <span className={`${
                    log.type === 'error' ? 'text-red-400' :
                    log.type === 'warn' ? 'text-yellow-400' :
                    'text-foreground/80'
                  }`}>{log.message}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }
);

PreviewPanel.displayName = 'PreviewPanel';
