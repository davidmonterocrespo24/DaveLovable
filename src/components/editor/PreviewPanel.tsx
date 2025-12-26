import { useState } from 'react';
import { 
  RefreshCw, 
  Smartphone, 
  Tablet, 
  Monitor, 
  ExternalLink, 
  Maximize2,
  Terminal,
  X,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

interface PreviewPanelProps {
  isLoading: boolean;
}

export const PreviewPanel = ({ isLoading }: PreviewPanelProps) => {
  const [device, setDevice] = useState<'mobile' | 'tablet' | 'desktop'>('desktop');
  const [showConsole, setShowConsole] = useState(false);
  const [url] = useState('my-awesome-app.lovable.app');

  const consoleLogs = [
    { type: 'info', message: '[vite] connecting...' },
    { type: 'info', message: '[vite] connected.' },
    { type: 'log', message: 'App mounted successfully' },
    { type: 'log', message: 'Rendering 3 Card components' },
  ];

  const deviceWidths = {
    mobile: 'w-[375px]',
    tablet: 'w-[768px]',
    desktop: 'w-full',
  };

  return (
    <div className="h-full flex flex-col bg-[#0d1117]">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-white/10 bg-background/50">
        <div className="flex items-center gap-2">
          <button className="p-1.5 hover:bg-white/10 rounded transition-colors text-muted-foreground hover:text-foreground">
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
          
          <div className="flex items-center bg-white/5 rounded-lg p-0.5">
            <button
              onClick={() => setDevice('mobile')}
              className={`p-1.5 rounded transition-colors ${
                device === 'mobile' ? 'bg-primary text-white' : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <Smartphone className="w-4 h-4" />
            </button>
            <button
              onClick={() => setDevice('tablet')}
              className={`p-1.5 rounded transition-colors ${
                device === 'tablet' ? 'bg-primary text-white' : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <Tablet className="w-4 h-4" />
            </button>
            <button
              onClick={() => setDevice('desktop')}
              className={`p-1.5 rounded transition-colors ${
                device === 'desktop' ? 'bg-primary text-white' : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <Monitor className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="flex-1 mx-4">
          <div className="flex items-center gap-2 bg-white/5 rounded-lg px-3 py-1.5 max-w-md mx-auto">
            <div className="w-2 h-2 rounded-full bg-green-500" />
            <span className="text-xs text-muted-foreground truncate">{url}</span>
          </div>
        </div>

        <div className="flex items-center gap-1">
          <button 
            onClick={() => setShowConsole(!showConsole)}
            className={`p-1.5 rounded transition-colors ${
              showConsole ? 'bg-primary text-white' : 'hover:bg-white/10 text-muted-foreground hover:text-foreground'
            }`}
          >
            <Terminal className="w-4 h-4" />
          </button>
          <button className="p-1.5 hover:bg-white/10 rounded transition-colors text-muted-foreground hover:text-foreground">
            <ExternalLink className="w-4 h-4" />
          </button>
          <button className="p-1.5 hover:bg-white/10 rounded transition-colors text-muted-foreground hover:text-foreground">
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Preview Area */}
      <div className="flex-1 overflow-auto p-4 flex justify-center bg-[#1a1a2e]">
        <div 
          className={`${deviceWidths[device]} h-full bg-gradient-to-br from-slate-900 to-slate-800 
                      rounded-lg overflow-hidden shadow-2xl border border-white/10 transition-all duration-300`}
        >
          {isLoading ? (
            <div className="h-full flex flex-col items-center justify-center gap-4">
              <div className="relative">
                <div className="w-12 h-12 border-4 border-primary/30 rounded-full" />
                <div className="w-12 h-12 border-4 border-transparent border-t-primary rounded-full animate-spin absolute inset-0" />
              </div>
              <p className="text-sm text-muted-foreground">Iniciando WebContainer...</p>
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
        <div className="h-48 border-t border-white/10 bg-[#0d1117]">
          <div className="flex items-center justify-between px-3 py-2 border-b border-white/10">
            <div className="flex items-center gap-4">
              <span className="text-xs font-medium text-muted-foreground">Console</span>
              <span className="text-xs px-2 py-0.5 rounded bg-white/10 text-muted-foreground">
                {consoleLogs.length}
              </span>
            </div>
            <div className="flex items-center gap-1">
              <button 
                onClick={() => setShowConsole(false)}
                className="p-1 hover:bg-white/10 rounded"
              >
                <X className="w-3 h-3 text-muted-foreground" />
              </button>
            </div>
          </div>
          <div className="p-3 font-mono text-xs space-y-1 overflow-auto h-[calc(100%-40px)]">
            {consoleLogs.map((log, i) => (
              <div key={i} className="flex items-start gap-2">
                <span className={`${
                  log.type === 'info' ? 'text-blue-400' : 'text-gray-400'
                }`}>
                  {log.type === 'info' ? 'ℹ' : '›'}
                </span>
                <span className="text-gray-300">{log.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
