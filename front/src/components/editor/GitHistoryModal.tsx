import { useState, useEffect } from 'react';
import { X, GitBranch, Calendar, User, Hash, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';

interface GitCommit {
  hash: string;
  author: string;
  date: string;
  message: string;
}

interface GitHistoryModalProps {
  projectId: number;
  isOpen: boolean;
  onClose: () => void;
}

export const GitHistoryModal: React.FC<GitHistoryModalProps> = ({ projectId, isOpen, onClose }) => {
  const [commits, setCommits] = useState<GitCommit[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedCommit, setSelectedCommit] = useState<string | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    if (isOpen) {
      loadGitHistory();
    }
  }, [isOpen, projectId]);

  const loadGitHistory = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/api/v1/projects/${projectId}/git/history?limit=50`);
      if (!response.ok) throw new Error('Failed to load git history');

      const data = await response.json();
      setCommits(data.commits || []);
    } catch (error) {
      console.error('Error loading git history:', error);
      toast({
        title: "Error loading history",
        description: "Failed to load git commit history",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRestore = async (commitHash: string) => {
    if (!confirm(`Are you sure you want to restore to commit ${commitHash.substring(0, 7)}? This will create a new commit.`)) {
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/api/v1/projects/${projectId}/git/restore/${commitHash}`, {
        method: 'POST',
      });

      if (!response.ok) throw new Error('Failed to restore commit');

      const data = await response.json();

      toast({
        title: "✅ Restored successfully",
        description: data.message,
      });

      // Reload history to show new commit
      loadGitHistory();

      // Reload page after 2 seconds to reflect changes
      setTimeout(() => {
        window.location.reload();
      }, 2000);
    } catch (error) {
      console.error('Error restoring commit:', error);
      toast({
        title: "Error restoring commit",
        description: "Failed to restore to the selected commit",
        variant: "destructive",
      });
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-background border border-border rounded-lg shadow-2xl w-full max-w-3xl max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <div className="flex items-center gap-2">
            <GitBranch className="w-5 h-5 text-primary" />
            <h2 className="text-lg font-semibold">Git Commit History</h2>
            {commits.length > 0 && (
              <span className="text-sm text-muted-foreground">({commits.length} commits)</span>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-muted rounded transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : commits.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <GitBranch className="w-12 h-12 mb-4 opacity-50" />
              <p>No commits found</p>
            </div>
          ) : (
            <div className="space-y-3">
              {commits.map((commit) => (
                <div
                  key={commit.hash}
                  className={`border rounded-lg p-4 transition-all ${
                    selectedCommit === commit.hash
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/50 hover:bg-muted/30'
                  }`}
                  onClick={() => setSelectedCommit(commit.hash)}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      {/* Commit Message */}
                      <div className="font-medium text-foreground mb-2 break-words">
                        {commit.message}
                      </div>

                      {/* Commit Info */}
                      <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
                        <div className="flex items-center gap-1.5">
                          <Hash className="w-3 h-3" />
                          <span className="font-mono">{commit.hash.substring(0, 7)}</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <User className="w-3 h-3" />
                          <span>{commit.author}</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <Calendar className="w-3 h-3" />
                          <span>{new Date(commit.date).toLocaleString()}</span>
                        </div>
                      </div>
                    </div>

                    {/* Restore Button */}
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRestore(commit.hash);
                      }}
                      className="gap-1.5 shrink-0"
                    >
                      <RotateCcw className="w-3 h-3" />
                      Restore
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 px-6 py-4 border-t border-border">
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </div>
  );
};
