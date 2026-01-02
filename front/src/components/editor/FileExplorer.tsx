import { forwardRef, useState, useMemo } from 'react';
import { ChevronRight, ChevronDown, File, Folder, Search, MoreHorizontal, Plus, Trash2, FilePlus, Save } from 'lucide-react';
import { useFiles, useCreateFile, useDeleteFile } from '@/hooks/useFiles';
import type { ProjectFile } from '@/services/api';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from '@/hooks/use-toast';

interface FileNode {
  name: string;
  type: 'file' | 'folder';
  children?: FileNode[];
  fileId?: number;
  content?: string;
  filepath?: string;
}

// Helper function to build a file tree from flat file list
function buildFileTree(files: ProjectFile[]): FileNode[] {
  const root: FileNode[] = [];

  files.forEach((file) => {
    const parts = file.filepath.split('/').filter(Boolean);
    let currentChildren = root;

    // Navigate through folders
    for (let i = 0; i < parts.length - 1; i++) {
      const folderName = parts[i];
      let folder = currentChildren.find(node => node.name === folderName && node.type === 'folder');

      if (!folder) {
        folder = {
          name: folderName,
          type: 'folder',
          children: [],
        };
        currentChildren.push(folder);
      }

      currentChildren = folder.children!;
    }

    // Add the file
    const fileName = parts[parts.length - 1];
    currentChildren.push({
      name: fileName,
      type: 'file',
      fileId: file.id,
      content: file.content,
      filepath: file.filepath,
    });
  });

  return root;
}

interface FileItemProps {
  node: FileNode;
  depth: number;
  selectedFile: string;
  onSelect: (file: { name: string; id: number; content: string; filepath: string }) => void;
  expandedFolders: Set<string>;
  onToggleFolder: (path: string) => void;
  path: string;
  onDeleteFile: (fileId: number, fileName: string) => void;
}

const getFileIcon = (fileName: string) => {
  if (fileName.endsWith('.tsx') || fileName.endsWith('.ts')) {
    return <span className="text-blue-400 text-xs font-mono">TS</span>;
  }
  if (fileName.endsWith('.css')) {
    return <span className="text-purple-400 text-xs font-mono">CSS</span>;
  }
  if (fileName.endsWith('.json')) {
    return <span className="text-yellow-400 text-xs font-mono">{'{}'}</span>;
  }
  return <File className="w-4 h-4 text-muted-foreground" />;
};

const FileItem = ({
  node,
  depth,
  selectedFile,
  onSelect,
  expandedFolders,
  onToggleFolder,
  path,
  onDeleteFile
}: FileItemProps) => {
  const currentPath = path ? `${path}/${node.name}` : node.name;
  const isOpen = expandedFolders.has(currentPath);

  const handleClick = () => {
    if (node.type === 'folder') {
      onToggleFolder(currentPath);
    } else if (node.fileId && node.content !== undefined && node.filepath) {
      onSelect({ name: node.name, id: node.fileId, content: node.content, filepath: node.filepath });
    }
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (node.type === 'file' && node.fileId) {
      onDeleteFile(node.fileId, node.name);
    }
  };

  return (
    <div>
      <div
        className={`group flex items-center gap-1 py-1.5 px-2 cursor-pointer rounded-md mx-1 transition-colors ${
          selectedFile === node.name
            ? 'bg-primary/20 text-primary'
            : 'text-muted-foreground hover:bg-muted/20 hover:text-foreground'
        }`}
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
        onClick={handleClick}
      >
        {node.type === 'folder' ? (
          <>
            <span className="w-4 h-4 flex items-center justify-center shrink-0">
              {isOpen ? (
                <ChevronDown className="w-3.5 h-3.5" />
              ) : (
                <ChevronRight className="w-3.5 h-3.5" />
              )}
            </span>
            <Folder className={`w-4 h-4 shrink-0 ${isOpen ? 'text-primary' : 'text-primary/70'}`} />
          </>
        ) : (
          <>
            <span className="w-4" />
            <span className="w-4 h-4 flex items-center justify-center shrink-0">
              {getFileIcon(node.name)}
            </span>
          </>
        )}
        <span className="text-sm truncate flex-1">{node.name}</span>
        {node.type === 'file' && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
              <button className="opacity-0 group-hover:opacity-100 p-0.5 hover:bg-muted/30 rounded transition-all">
                <MoreHorizontal className="w-3.5 h-3.5" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={handleDelete} className="text-destructive focus:text-destructive">
                <Trash2 className="w-4 h-4 mr-2" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>
      {node.type === 'folder' && isOpen && node.children && (
        <div>
          {node.children.map((child) => (
            <FileItem
              key={child.name}
              node={child}
              depth={depth + 1}
              selectedFile={selectedFile}
              onSelect={onSelect}
              expandedFolders={expandedFolders}
              onToggleFolder={onToggleFolder}
              path={currentPath}
              onDeleteFile={onDeleteFile}
            />
          ))}
        </div>
      )}
    </div>
  );
};

interface FileExplorerProps {
  projectId: number;
  selectedFile: string;
  onSelectFile: (file: { name: string; id: number; content: string; filepath: string }) => void;
  hasUnsavedChanges?: boolean;
  onSaveFile?: () => void;
  isSaving?: boolean;
}

export const FileExplorer = forwardRef<HTMLDivElement, FileExplorerProps>(
  ({ projectId, selectedFile, onSelectFile, hasUnsavedChanges = false, onSaveFile, isSaving = false }, ref) => {
    const [searchQuery, setSearchQuery] = useState('');
    const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set(['src', 'src/components']));
    const [showCreateDialog, setShowCreateDialog] = useState(false);
    const [newFileName, setNewFileName] = useState('');
    const [newFilePath, setNewFilePath] = useState('src/');
    const [deleteFileId, setDeleteFileId] = useState<number | null>(null);
    const [deleteFileName, setDeleteFileName] = useState('');

    const { toast } = useToast();

    // Fetch files from backend
    const { data: files = [], isLoading } = useFiles(projectId);
    const createFileMutation = useCreateFile();
    const deleteFileMutation = useDeleteFile();

    const handleToggleFolder = (path: string) => {
      setExpandedFolders(prev => {
        const next = new Set(prev);
        if (next.has(path)) {
          next.delete(path);
        } else {
          next.add(path);
        }
        return next;
      });
    };

    const handleCreateFile = async () => {
      if (!newFileName.trim()) {
        toast({
          title: "Error",
          description: "File name cannot be empty",
          variant: "destructive",
        });
        return;
      }

      const fullPath = newFilePath.endsWith('/')
        ? `${newFilePath}${newFileName}`
        : `${newFilePath}/${newFileName}`;

      const language = newFileName.endsWith('.tsx') || newFileName.endsWith('.ts')
        ? 'tsx'
        : newFileName.endsWith('.css')
        ? 'css'
        : newFileName.endsWith('.json')
        ? 'json'
        : 'tsx';

      try {
        await createFileMutation.mutateAsync({
          projectId,
          data: {
            project_id: projectId,
            filename: newFileName,
            filepath: fullPath,
            content: '',
            language,
          }
        });

        toast({
          title: "File created",
          description: `${newFileName} has been created successfully.`,
        });

        setShowCreateDialog(false);
        setNewFileName('');
        setNewFilePath('src/');
      } catch (error) {
        toast({
          title: "Error creating file",
          description: "There was an error creating the file. Please try again.",
          variant: "destructive",
        });
      }
    };

    const handleDeleteFile = (fileId: number, fileName: string) => {
      setDeleteFileId(fileId);
      setDeleteFileName(fileName);
    };

    const confirmDeleteFile = async () => {
      if (!deleteFileId) return;

      try {
        await deleteFileMutation.mutateAsync({
          projectId,
          fileId: deleteFileId,
        });

        toast({
          title: "File deleted",
          description: `${deleteFileName} has been deleted successfully.`,
        });

        setDeleteFileId(null);
        setDeleteFileName('');
      } catch (error) {
        toast({
          title: "Error deleting file",
          description: "There was an error deleting the file. Please try again.",
          variant: "destructive",
        });
      }
    };

    // Build file tree from backend files
    const fileTree = useMemo(() => buildFileTree(files), [files]);

    // Filter files based on search query
    const filteredFiles = useMemo(() => {
      if (!searchQuery.trim()) return fileTree;

      const filterNode = (node: FileNode): FileNode | null => {
        if (node.name.toLowerCase().includes(searchQuery.toLowerCase())) {
          return node;
        }
        if (node.type === 'folder' && node.children) {
          const filteredChildren = node.children
            .map(filterNode)
            .filter((n): n is FileNode => n !== null);
          if (filteredChildren.length > 0) {
            return { ...node, children: filteredChildren };
          }
        }
        return null;
      };

      return fileTree.map(filterNode).filter((n): n is FileNode => n !== null);
    }, [searchQuery, fileTree]);

    return (
      <div ref={ref} className="h-full bg-background/50 flex flex-col">
        <div className="p-3 border-b border-border/50 flex items-center justify-between">
          <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            Explorer
          </span>
          <div className="flex items-center gap-1">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant={hasUnsavedChanges ? "default" : "ghost"}
                  size="icon"
                  className="h-6 w-6"
                  onClick={onSaveFile}
                  disabled={!hasUnsavedChanges || isSaving}
                >
                  <Save className="w-3.5 h-3.5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                {hasUnsavedChanges ? 'Save file (Ctrl+S)' : 'No changes to save'}
              </TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6"
                  onClick={() => setShowCreateDialog(true)}
                >
                  <FilePlus className="w-4 h-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                Create new file
              </TooltipContent>
            </Tooltip>
          </div>
        </div>
        
        {/* Search */}
        <div className="p-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search files..."
              className="w-full bg-muted/20 border border-border/30 rounded-md pl-8 pr-3 py-1.5 
                         text-xs placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary/50"
            />
          </div>
        </div>

        {/* File Tree */}
        <div className="flex-1 overflow-y-auto py-1">
          {isLoading ? (
            <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
              Loading files...
            </div>
          ) : filteredFiles.length === 0 ? (
            <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
              No files found
            </div>
          ) : (
            filteredFiles.map((file) => (
              <FileItem
                key={file.name}
                node={file}
                depth={0}
                selectedFile={selectedFile}
                onSelect={onSelectFile}
                expandedFolders={expandedFolders}
                onToggleFolder={handleToggleFolder}
                path=""
                onDeleteFile={handleDeleteFile}
              />
            ))
          )}
        </div>

        {/* Create File Dialog */}
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New File</DialogTitle>
              <DialogDescription>
                Create a new file in your project
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="filepath">File Path</Label>
                <Input
                  id="filepath"
                  value={newFilePath}
                  onChange={(e) => setNewFilePath(e.target.value)}
                  placeholder="src/components/"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="filename">File Name</Label>
                <Input
                  id="filename"
                  value={newFileName}
                  onChange={(e) => setNewFileName(e.target.value)}
                  placeholder="NewComponent.tsx"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleCreateFile();
                    }
                  }}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateFile} disabled={createFileMutation.isPending}>
                {createFileMutation.isPending ? 'Creating...' : 'Create File'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Delete Confirmation Dialog */}
        <AlertDialog open={deleteFileId !== null} onOpenChange={() => setDeleteFileId(null)}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Are you sure?</AlertDialogTitle>
              <AlertDialogDescription>
                This will permanently delete <strong>{deleteFileName}</strong>. This action cannot be undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={confirmDeleteFile}
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              >
                {deleteFileMutation.isPending ? 'Deleting...' : 'Delete'}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    );
  }
);

FileExplorer.displayName = 'FileExplorer';
