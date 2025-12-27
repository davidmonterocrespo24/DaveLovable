import { useState, useEffect } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import {
  Sparkles,
  Settings,
  Share2,
  ChevronLeft,
  PanelLeftClose,
  PanelLeft,
  Cloud,
  Zap,
  History
} from 'lucide-react';
import { useProject } from '@/hooks/useProjects';
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { FileExplorer } from '@/components/editor/FileExplorer';
import { CodeEditor } from '@/components/editor/CodeEditor';
import { ChatPanel } from '@/components/editor/ChatPanel';
import { PreviewPanel } from '@/components/editor/PreviewPanelWithWebContainer';
import { EditorTabs } from '@/components/editor/EditorTabs';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';

const Editor = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { data: project, isLoading: projectLoading } = useProject(Number(projectId));

  const [selectedFile, setSelectedFile] = useState<{ name: string; id: number; content: string } | null>(null);
  const [activeView, setActiveView] = useState<'code' | 'preview' | 'split'>('split');
  const [showExplorer, setShowExplorer] = useState(true);
  const [showChat, setShowChat] = useState(true);
  const [isPreviewLoading, setIsPreviewLoading] = useState(true);
  const [isTyping, setIsTyping] = useState(false);
  const [tabs, setTabs] = useState<Array<{ id: string; name: string; isActive: boolean; fileId?: number }>>([]);

  useEffect(() => {
    if (!projectId || isNaN(Number(projectId))) {
      navigate('/projects');
    }
  }, [projectId, navigate]);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsPreviewLoading(false);
    }, 2000);
    return () => clearTimeout(timer);
  }, []);

  const handleFileSelect = (file: { name: string; id: number; content: string }) => {
    setSelectedFile(file);
    const existingTab = tabs.find(t => t.fileId === file.id);
    if (!existingTab) {
      setTabs(prev => [
        ...prev.map(t => ({ ...t, isActive: false })),
        { id: file.id.toString(), name: file.name, isActive: true, fileId: file.id }
      ]);
    } else {
      setTabs(prev => prev.map(t => ({ ...t, isActive: t.fileId === file.id })));
    }
  };

  const handleTabClose = (id: string) => {
    setTabs(prev => {
      const filtered = prev.filter(t => t.id !== id);
      if (filtered.length === 0) {
        setSelectedFile(null);
        return [];
      }
      if (prev.find(t => t.id === id)?.isActive && selectedFile) {
        filtered[filtered.length - 1].isActive = true;
      }
      return filtered;
    });
  };

  const handleTabSelect = (id: string) => {
    setTabs(prev => prev.map(t => ({ ...t, isActive: t.id === id })));
  };

  const handleCodeChange = () => {
    setIsPreviewLoading(true);
    setTimeout(() => {
      setIsPreviewLoading(false);
    }, 1000);
  };

  if (projectLoading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading project...</p>
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-lg font-semibold mb-2">Project not found</p>
          <Link to="/projects" className="text-primary hover:underline">
            Back to projects
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-background overflow-hidden">
      {/* Top Bar */}
      <header className="h-12 flex items-center justify-between px-4 border-b border-border/50 bg-background/80 backdrop-blur-sm shrink-0">
        <div className="flex items-center gap-3">
          <Link to="/projects" className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors">
            <ChevronLeft className="w-4 h-4" />
          </Link>
          <div className="w-px h-6 bg-border/50" />
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center shadow-lg shadow-primary/20">
              <Sparkles className="w-4 h-4 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-sm font-semibold">{project.name}</h1>
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                <span className="text-xs text-muted-foreground">Synced</span>
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="sm" className="gap-2">
                <History className="w-4 h-4" />
                <span className="hidden sm:inline">History</span>
              </Button>
            </TooltipTrigger>
            <TooltipContent>View version history</TooltipContent>
          </Tooltip>

          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-muted/20 rounded-lg border border-border/30">
            <Cloud className="w-4 h-4 text-primary" />
            <span className="text-xs font-medium">Cloud</span>
          </div>
          
          <Button variant="ghost" size="icon">
            <Settings className="w-4 h-4" />
          </Button>
          
          <Button size="sm" className="gap-2">
            <Share2 className="w-4 h-4" />
            Share
          </Button>
        </div>
      </header>

      {/* Main Content with Resizable Panels */}
      <ResizablePanelGroup direction="horizontal" className="flex-1">
        {/* Chat Panel */}
        {showChat && (
          <>
            <ResizablePanel defaultSize={25} minSize={20} maxSize={40}>
              <ChatPanel
                projectId={Number(projectId)}
                onCodeChange={handleCodeChange}
              />
            </ResizablePanel>
            <ResizableHandle withHandle />
          </>
        )}

        {/* File Explorer + Editor + Preview */}
        <ResizablePanel defaultSize={showChat ? 75 : 100}>
          <div className="h-full flex flex-col">
            {/* Toggle Chat Button */}
            <div className="absolute left-0 top-1/2 -translate-y-1/2 z-10" style={{ left: showChat ? 'calc(25% - 12px)' : '0' }}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    onClick={() => setShowChat(!showChat)}
                    className="p-1.5 bg-background border border-border/50 rounded-r-lg hover:bg-muted/20 transition-colors shadow-sm"
                  >
                    {showChat ? (
                      <PanelLeftClose className="w-4 h-4 text-muted-foreground" />
                    ) : (
                      <PanelLeft className="w-4 h-4 text-muted-foreground" />
                    )}
                  </button>
                </TooltipTrigger>
                <TooltipContent side="right">
                  {showChat ? 'Hide chat' : 'Show chat'}
                </TooltipContent>
              </Tooltip>
            </div>

            <ResizablePanelGroup direction="horizontal" className="flex-1">
              {/* File Explorer */}
              {showExplorer && activeView !== 'preview' && (
                <>
                  <ResizablePanel defaultSize={18} minSize={15} maxSize={30}>
                    <FileExplorer
                      projectId={Number(projectId)}
                      selectedFile={selectedFile?.name || ''}
                      onSelectFile={handleFileSelect}
                    />
                  </ResizablePanel>
                  <ResizableHandle />
                </>
              )}

              {/* Editor & Preview Area */}
              <ResizablePanel defaultSize={showExplorer && activeView !== 'preview' ? 82 : 100}>
                <div className="h-full flex flex-col">
                  <EditorTabs
                    activeView={activeView}
                    onViewChange={setActiveView}
                    tabs={tabs}
                    onTabClose={handleTabClose}
                    onTabSelect={handleTabSelect}
                  />

                  <ResizablePanelGroup direction="horizontal" className="flex-1">
                    {/* Code Editor */}
                    {(activeView === 'code' || activeView === 'split') && (
                      <ResizablePanel defaultSize={activeView === 'split' ? 50 : 100}>
                        <CodeEditor selectedFile={selectedFile} isTyping={isTyping} />
                      </ResizablePanel>
                    )}

                    {activeView === 'split' && <ResizableHandle withHandle />}

                    {/* Preview */}
                    {(activeView === 'preview' || activeView === 'split') && (
                      <ResizablePanel defaultSize={activeView === 'split' ? 50 : 100}>
                        <PreviewPanel
                          projectId={Number(projectId)}
                          isLoading={isPreviewLoading}
                          onReload={handleCodeChange}
                        />
                      </ResizablePanel>
                    )}
                  </ResizablePanelGroup>
                </div>
              </ResizablePanel>
            </ResizablePanelGroup>
          </div>
        </ResizablePanel>
      </ResizablePanelGroup>

      {/* Status Bar */}
      <footer className="h-6 flex items-center justify-between px-4 border-t border-border/50 bg-background/80 text-xs text-muted-foreground shrink-0">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <Zap className="w-3 h-3 text-yellow-500" />
            <span>WebContainer Ready</span>
          </div>
          <span className="text-muted-foreground/60">|</span>
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
