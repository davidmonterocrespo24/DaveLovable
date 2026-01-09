import { useState, useEffect } from 'react';
import { X, GitBranch, Globe, Save } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import { API_URL } from '@/services/api';

interface GitConfigModalProps {
  projectId: number;
  isOpen: boolean;
  onClose: () => void;
}

export const GitConfigModal: React.FC<GitConfigModalProps> = ({ projectId, isOpen, onClose }) => {
  const [remoteUrl, setRemoteUrl] = useState('');
  const [remoteName, setRemoteName] = useState('origin');
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    if (isOpen) {
      loadGitConfig();
    }
  }, [isOpen, projectId]);

  const loadGitConfig = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_URL}/projects/${projectId}/git/config`);
      if (!response.ok) throw new Error('Failed to load git config');

      const data = await response.json();
      setRemoteUrl(data.remote_url || '');
      setRemoteName(data.remote_name || 'origin');
    } catch (error) {
      console.error('Error loading git config:', error);
      toast({
        title: "Error loading config",
        description: "Failed to load git configuration",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!remoteUrl.trim()) {
      toast({
        title: "Invalid URL",
        description: "Please enter a valid remote repository URL",
        variant: "destructive",
      });
      return;
    }

    setIsSaving(true);
    try {
      const response = await fetch(`${API_URL}/projects/${projectId}/git/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          remote_url: remoteUrl,
          remote_name: remoteName,
        }),
      });

      if (!response.ok) throw new Error('Failed to save git config');

      const data = await response.json();

      toast({
        title: "✅ Configuration saved",
        description: data.message || "Git remote configuration updated successfully",
      });

      onClose();
    } catch (error) {
      console.error('Error saving git config:', error);
      toast({
        title: "Error saving config",
        description: "Failed to save git configuration",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-background border border-border rounded-lg shadow-2xl w-full max-w-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <div className="flex items-center gap-2">
            <Globe className="w-5 h-5 text-primary" />
            <h2 className="text-lg font-semibold">Git Remote Configuration</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-muted rounded transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : (
            <>
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Remote Name
                </label>
                <input
                  type="text"
                  value={remoteName}
                  onChange={(e) => setRemoteName(e.target.value)}
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary text-sm"
                  placeholder="origin"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  The name of the remote repository (usually "origin")
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Remote URL
                </label>
                <input
                  type="text"
                  value={remoteUrl}
                  onChange={(e) => setRemoteUrl(e.target.value)}
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary text-sm font-mono"
                  placeholder="https://github.com/username/repo.git"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  HTTPS or SSH URL of your remote Git repository
                </p>
              </div>

              <div className="bg-muted/20 border border-border/30 rounded-lg p-4">
                <div className="flex items-start gap-2">
                  <GitBranch className="w-4 h-4 text-primary mt-0.5 shrink-0" />
                  <div className="text-xs text-muted-foreground">
                    <p className="font-medium text-foreground mb-1">Examples:</p>
                    <ul className="list-disc list-inside space-y-0.5">
                      <li>HTTPS: <code className="text-[10px] bg-background px-1 py-0.5 rounded">https://github.com/username/repo.git</code></li>
                      <li>SSH: <code className="text-[10px] bg-background px-1 py-0.5 rounded">git@github.com:username/repo.git</code></li>
                      <li>GitLab: <code className="text-[10px] bg-background px-1 py-0.5 rounded">https://gitlab.com/username/repo.git</code></li>
                    </ul>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 px-6 py-4 border-t border-border">
          <Button variant="outline" onClick={onClose} disabled={isSaving}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSaving || isLoading} className="gap-2">
            <Save className="w-4 h-4" />
            {isSaving ? 'Saving...' : 'Save Configuration'}
          </Button>
        </div>
      </div>
    </div>
  );
};
