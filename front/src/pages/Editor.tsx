import { useState, useEffect, useRef } from 'react';
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
  FileText,
  Camera,
  Download
} from 'lucide-react';
import { useProject } from '@/hooks/useProjects';
import { useUpdateFile } from '@/hooks/useFiles';
import { useQueryClient } from '@tanstack/react-query';
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
import { GitHistoryModal } from '@/components/editor/GitHistoryModal';
import { GitConfigModal } from '@/components/editor/GitConfigModal';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { useToast } from '@/hooks/use-toast';

const Editor = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const { data: project, isLoading: projectLoading } = useProject(Number(projectId));
  const updateFileMutation = useUpdateFile();

  const [selectedFile, setSelectedFile] = useState<{ name: string; id: number; content: string; filepath: string } | null>(null);
  const [editedContent, setEditedContent] = useState<string>('');
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [activeView, setActiveView] = useState<'code' | 'preview' | 'split'>('split');
  const [showExplorer, setShowExplorer] = useState(true);
  const [showChat, setShowChat] = useState(true);
  const [isPreviewLoading, setIsPreviewLoading] = useState(true);
  const [isTyping, setIsTyping] = useState(false);
  const [tabs, setTabs] = useState<Array<{ id: string; name: string; isActive: boolean; fileId?: number }>>([]);
  const [showGitHistory, setShowGitHistory] = useState(false);
  const [showGitConfig, setShowGitConfig] = useState(false);
  const [currentBranch, setCurrentBranch] = useState('main');
  const [isSyncing, setIsSyncing] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string>('');
  const chatPanelRef = useRef<{ sendMessage: (message: string) => void }>(null);
  const previewPanelRef = useRef<{ reload: () => void }>(null);

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

  // Fetch current branch on mount
  useEffect(() => {
    const fetchBranch = async () => {
      if (!projectId) return;
      try {
        const response = await fetch(`http://localhost:8000/api/v1/projects/${projectId}/git/branch`);
        if (response.ok) {
          const data = await response.json();
          setCurrentBranch(data.branch);
        }
      } catch (error) {
        console.error('Error fetching branch:', error);
      }
    };
    fetchBranch();
  }, [projectId]);

  // Keyboard shortcut for saving (Ctrl+S)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        if (hasUnsavedChanges && selectedFile) {
          handleSaveFile();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [hasUnsavedChanges, selectedFile, editedContent]);

  const handleFileSelect = (file: { name: string; id: number; content: string; filepath: string }) => {
    setSelectedFile(file);
    setEditedContent(file.content);
    setHasUnsavedChanges(false);
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

  const handleContentChange = (newContent: string) => {
    setEditedContent(newContent);
    setHasUnsavedChanges(newContent !== selectedFile?.content);
  };

  const handleSaveFile = async () => {
    if (!selectedFile || !hasUnsavedChanges) return;

    try {
      await updateFileMutation.mutateAsync({
        projectId: Number(projectId),
        fileId: selectedFile.id,
        data: {
          content: editedContent,
          filepath: selectedFile.filepath
        }
      });

      setSelectedFile({ ...selectedFile, content: editedContent });
      setHasUnsavedChanges(false);

      // Reload WebContainer to reflect changes
      if (previewPanelRef.current) {
        previewPanelRef.current.reload();
      }

      toast({
        title: "File saved",
        description: `${selectedFile.name} has been saved successfully.`,
      });
    } catch (error) {
      toast({
        title: "Error saving file",
        description: "There was an error saving the file. Please try again.",
        variant: "destructive",
      });
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

    // Refetch files to update the file explorer
    if (projectId) {
      queryClient.invalidateQueries({ queryKey: ['project', Number(projectId)] });
    }
  };

  const handleReportError = (errorMessage: string) => {
    if (chatPanelRef.current) {
      chatPanelRef.current.sendMessage(errorMessage);
    }
  };

  const handleRunProject = () => {
    // Trigger a reload of the preview to run the project
    handleCodeChange();
    toast({
      title: "Running project",
      description: "Reloading preview to run the latest code...",
    });
  };

  const handleShowGitHistory = () => {
    setShowGitHistory(true);
  };

  const handleGitSync = async () => {
    if (!projectId) return;

    setIsSyncing(true);
    try {
      const response = await fetch(`http://localhost:8000/api/v1/projects/${projectId}/git/sync`, {
        method: 'POST',
      });

      if (!response.ok) throw new Error('Sync failed');

      const data = await response.json();

      if (data.success) {
        toast({
          title: "✅ Sync completed",
          description: (
            <div className="text-xs space-y-1">
              <div>{data.fetch}</div>
              <div>{data.pull}</div>
              <div>{data.commit}</div>
              <div>{data.push}</div>
            </div>
          ),
          duration: 5000,
        });
      } else {
        toast({
          title: "⚠️ Sync incomplete",
          description: data.message,
          variant: "destructive",
          duration: 5000,
        });
      }
    } catch (error) {
      toast({
        title: "Error syncing",
        description: "Failed to sync with remote repository",
        variant: "destructive",
      });
    } finally {
      setIsSyncing(false);
    }
  };

  const handleGitConfig = () => {
    setShowGitConfig(true);
  };

  const handlePreviewReady = (url: string) => {
    console.log('[Editor] Preview ready with URL:', url);
    setPreviewUrl(url);
  };

  const captureScreenshot = async (showToastOnSuccess = true) => {
    if (!previewUrl) {
      toast({
        title: "Preview not ready",
        description: "Please wait for the preview to load before capturing screenshot",
        variant: "destructive",
      });
      return;
    }

    try {
      console.log('[Screenshot] Sending URL to backend:', previewUrl);

      // Send preview URL to backend for screenshot capture
      const response = await fetch(`http://localhost:8000/api/v1/projects/${projectId}/thumbnail`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: previewUrl }),
      });

      if (response.ok) {
        console.log('[Screenshot] Thumbnail saved successfully');

        // Invalidate queries to refresh the project data
        queryClient.invalidateQueries({ queryKey: ['projects'] });
        queryClient.invalidateQueries({ queryKey: ['projects', 'detail', Number(projectId)] });

        if (showToastOnSuccess) {
          toast({
            title: "📸 Screenshot saved",
            description: "Project thumbnail has been captured",
            duration: 3000,
          });
        }
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to capture screenshot');
      }
    } catch (error) {
      console.error('[Screenshot] Failed to capture:', error);
      toast({
        title: "Screenshot failed",
        description: error instanceof Error ? error.message : "There was an error capturing the screenshot. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handleManualScreenshot = () => {
    captureScreenshot(true);
  };

  const handleDownloadProject = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/projects/${projectId}/download`);

      if (!response.ok) {
        throw new Error('Failed to download project');
      }

      // Get the filename from Content-Disposition header or use default
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = 'project.zip';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      // Create blob from response
      const blob = await response.blob();

      // Create download link and trigger download
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();

      // Cleanup
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast({
        title: "Download started",
        description: `${filename} is being downloaded`,
        duration: 3000,
      });
    } catch (error) {
      console.error('[Download] Failed:', error);
      toast({
        title: "Download failed",
        description: "There was an error downloading the project. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handleReloadPreview = (data: { message: string }) => {
    console.log('[Editor] Reload preview requested:', data);

    // Refetch files to update the file explorer
    if (projectId) {
      queryClient.invalidateQueries({ queryKey: ['project', Number(projectId)] });
    }

    // Trigger WebContainer reload via ref
    if (previewPanelRef.current) {
      previewPanelRef.current.reload();
    }
  };

  const handleGitCommit = async (data: { success: boolean; error?: string; message?: string }) => {
    // Only capture screenshot on successful commit if project doesn't have a thumbnail yet
    if (!data.success || !previewUrl) return;

    // Check if project already has a thumbnail
    if (project?.thumbnail) return;

    try {
      // Wait a bit for the preview to be fully rendered
      await new Promise(resolve => setTimeout(resolve, 2000));
      await captureScreenshot(false);
    } catch (error) {
      console.error('[Screenshot] Failed to capture:', error);
    }
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
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-muted/20 rounded-lg border border-border/30">
            <Cloud className="w-4 h-4 text-primary" />
            <span className="text-xs font-medium">Cloud</span>
          </div>

          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon" onClick={handleManualScreenshot}>
                <Camera className="w-4 h-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              Capture project thumbnail
            </TooltipContent>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon" onClick={handleDownloadProject}>
                <Download className="w-4 h-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              Download project as ZIP
            </TooltipContent>
          </Tooltip>

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
              <div className="h-full relative">
                <ChatPanel
                  ref={chatPanelRef}
                  projectId={Number(projectId)}
                  onCodeChange={handleCodeChange}
                  onGitCommit={handleGitCommit}
                  onReloadPreview={handleReloadPreview}
                />
                {/* Toggle Chat Button - positioned at right edge of chat panel */}
                <div className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-full z-10">
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        onClick={() => setShowChat(false)}
                        className="p-1.5 bg-background border border-border/50 rounded-r-lg hover:bg-muted/20 transition-colors shadow-sm"
                      >
                        <PanelLeftClose className="w-4 h-4 text-muted-foreground" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="right">
                      Hide chat
                    </TooltipContent>
                  </Tooltip>
                </div>
              </div>
            </ResizablePanel>
            <ResizableHandle withHandle />
          </>
        )}

        {/* File Explorer + Editor + Preview */}
        <ResizablePanel defaultSize={showChat ? 75 : 100}>
          <div className="h-full flex flex-col">
            {/* Toggle Chat Button - Show when chat is hidden */}
            {!showChat && (
              <div className="absolute left-0 top-1/2 -translate-y-1/2 z-10">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      onClick={() => setShowChat(true)}
                      className="p-1.5 bg-background border border-border/50 rounded-r-lg hover:bg-muted/20 transition-colors shadow-sm"
                    >
                      <PanelLeft className="w-4 h-4 text-muted-foreground" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="right">
                    Show chat
                  </TooltipContent>
                </Tooltip>
              </div>
            )}

            <ResizablePanelGroup direction="horizontal" className="flex-1">
              {/* File Explorer */}
              {showExplorer && activeView !== 'preview' && (
                <>
                  <ResizablePanel defaultSize={18} minSize={15} maxSize={30}>
                    <FileExplorer
                      projectId={Number(projectId)}
                      selectedFile={selectedFile?.name || ''}
                      onSelectFile={handleFileSelect}
                      hasUnsavedChanges={hasUnsavedChanges}
                      onSaveFile={handleSaveFile}
                      isSaving={updateFileMutation.isPending}
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
                    onRunProject={handleRunProject}
                    onShowGitHistory={handleShowGitHistory}
                    currentBranch={currentBranch}
                    onGitSync={handleGitSync}
                    onGitConfig={handleGitConfig}
                    isSyncing={isSyncing}
                  />

                  <ResizablePanelGroup direction="horizontal" className="flex-1">
                    {/* Code Editor */}
                    {(activeView === 'code' || activeView === 'split') && (
                      <ResizablePanel defaultSize={activeView === 'split' ? 50 : 100}>
                        <CodeEditor
                          selectedFile={selectedFile ? { ...selectedFile, content: editedContent } : null}
                          isTyping={isTyping}
                          onContentChange={handleContentChange}
                        />
                      </ResizablePanel>
                    )}

                    {activeView === 'split' && <ResizableHandle withHandle />}

                    {/* Preview */}
                    {(activeView === 'preview' || activeView === 'split') && (
                      <ResizablePanel defaultSize={activeView === 'split' ? 50 : 100}>
                        <PreviewPanel
                          ref={previewPanelRef}
                          projectId={Number(projectId)}
                          isLoading={isPreviewLoading}
                          onReload={handleCodeChange}
                          onReportError={handleReportError}
                          onPreviewReady={handlePreviewReady}
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

      {/* Git History Modal */}
      <GitHistoryModal
        projectId={Number(projectId)}
        isOpen={showGitHistory}
        onClose={() => setShowGitHistory(false)}
      />

      {/* Git Config Modal */}
      <GitConfigModal
        projectId={Number(projectId)}
        isOpen={showGitConfig}
        onClose={() => setShowGitConfig(false)}
      />
    </div>
  );
};

export default Editor;
