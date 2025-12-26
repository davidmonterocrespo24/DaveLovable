import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Sparkles, 
  Settings, 
  Share2, 
  ChevronLeft,
  PanelLeftClose,
  PanelLeft,
  Cloud,
  Zap
} from 'lucide-react';
import { FileExplorer } from '@/components/editor/FileExplorer';
import { CodeEditor } from '@/components/editor/CodeEditor';
import { ChatPanel } from '@/components/editor/ChatPanel';
import { PreviewPanel } from '@/components/editor/PreviewPanel';
import { EditorTabs } from '@/components/editor/EditorTabs';

const Editor = () => {
  const [selectedFile, setSelectedFile] = useState('App.tsx');
  const [activeView, setActiveView] = useState<'code' | 'preview' | 'split'>('split');
  const [showExplorer, setShowExplorer] = useState(true);
  const [showChat, setShowChat] = useState(true);
  const [isPreviewLoading, setIsPreviewLoading] = useState(true);
  const [isTyping, setIsTyping] = useState(false);
  const [tabs, setTabs] = useState([
    { id: '1', name: 'App.tsx', isActive: true },
  ]);

  useEffect(() => {
    // Simulate initial loading
    const timer = setTimeout(() => {
      setIsPreviewLoading(false);
    }, 2000);
    return () => clearTimeout(timer);
  }, []);

  const handleFileSelect = (fileName: string) => {
    setSelectedFile(fileName);
    const existingTab = tabs.find(t => t.name === fileName);
    if (!existingTab) {
      setTabs(prev => [
        ...prev.map(t => ({ ...t, isActive: false })),
        { id: Date.now().toString(), name: fileName, isActive: true }
      ]);
    } else {
      setTabs(prev => prev.map(t => ({ ...t, isActive: t.name === fileName })));
    }
  };

  const handleTabClose = (id: string) => {
    setTabs(prev => {
      const filtered = prev.filter(t => t.id !== id);
      if (filtered.length === 0) return prev;
      if (prev.find(t => t.id === id)?.isActive) {
        filtered[filtered.length - 1].isActive = true;
        setSelectedFile(filtered[filtered.length - 1].name);
      }
      return filtered;
    });
  };

  const handleTabSelect = (id: string) => {
    setTabs(prev => prev.map(t => ({ ...t, isActive: t.id === id })));
    const tab = tabs.find(t => t.id === id);
    if (tab) setSelectedFile(tab.name);
  };

  const handleSendMessage = (message: string) => {
    // Simulate code generation
    setIsTyping(true);
    setIsPreviewLoading(true);
    setTimeout(() => {
      setIsTyping(false);
      setIsPreviewLoading(false);
    }, 3000);
  };

  return (
    <div className="h-screen flex flex-col bg-background overflow-hidden">
      {/* Top Bar */}
      <header className="h-12 flex items-center justify-between px-4 border-b border-white/10 bg-background/80 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <Link to="/" className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors">
            <ChevronLeft className="w-4 h-4" />
          </Link>
          <div className="w-px h-6 bg-white/10" />
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-sm font-semibold">my-awesome-app</h1>
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
                <span className="text-xs text-muted-foreground">Synced</span>
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 px-3 py-1.5 bg-white/5 rounded-lg">
            <Cloud className="w-4 h-4 text-primary" />
            <span className="text-xs font-medium">Cloud</span>
          </div>
          <button className="p-2 hover:bg-white/10 rounded-lg transition-colors">
            <Settings className="w-4 h-4 text-muted-foreground" />
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary/90 
                           text-white text-sm font-medium rounded-lg transition-colors">
            <Share2 className="w-4 h-4" />
            Share
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chat Panel */}
        {showChat && (
          <div className="w-80 border-r border-white/10 flex flex-col">
            <ChatPanel onSendMessage={handleSendMessage} />
          </div>
        )}

        {/* Toggle Chat Button */}
        <button
          onClick={() => setShowChat(!showChat)}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-10 p-1.5 bg-background border border-white/10 
                   rounded-r-lg hover:bg-white/5 transition-colors"
          style={{ left: showChat ? '320px' : '0' }}
        >
          {showChat ? (
            <PanelLeftClose className="w-4 h-4 text-muted-foreground" />
          ) : (
            <PanelLeft className="w-4 h-4 text-muted-foreground" />
          )}
        </button>

        {/* File Explorer */}
        {showExplorer && activeView !== 'preview' && (
          <div className="w-56 border-r border-white/10">
            <FileExplorer selectedFile={selectedFile} onSelectFile={handleFileSelect} />
          </div>
        )}

        {/* Editor & Preview */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <EditorTabs
            activeView={activeView}
            onViewChange={setActiveView}
            tabs={tabs}
            onTabClose={handleTabClose}
            onTabSelect={handleTabSelect}
          />

          <div className="flex-1 flex overflow-hidden">
            {/* Code Editor */}
            {(activeView === 'code' || activeView === 'split') && (
              <div className={`${activeView === 'split' ? 'w-1/2 border-r border-white/10' : 'w-full'}`}>
                <CodeEditor selectedFile={selectedFile} isTyping={isTyping} />
              </div>
            )}

            {/* Preview */}
            {(activeView === 'preview' || activeView === 'split') && (
              <div className={`${activeView === 'split' ? 'w-1/2' : 'w-full'}`}>
                <PreviewPanel isLoading={isPreviewLoading} />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Status Bar */}
      <footer className="h-6 flex items-center justify-between px-4 border-t border-white/10 bg-background/80 text-xs text-muted-foreground">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <Zap className="w-3 h-3 text-yellow-500" />
            <span>WebContainer Ready</span>
          </div>
          <span>TypeScript</span>
          <span>UTF-8</span>
        </div>
        <div className="flex items-center gap-4">
          <span>Ln 24, Col 12</span>
          <span>Spaces: 2</span>
        </div>
      </footer>
    </div>
  );
};

export default Editor;
