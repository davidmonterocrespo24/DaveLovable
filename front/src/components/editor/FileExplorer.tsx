import { forwardRef, useState, useMemo } from 'react';
import { ChevronRight, ChevronDown, File, Folder, Search, MoreHorizontal } from 'lucide-react';
import { useFiles } from '@/hooks/useFiles';
import type { ProjectFile } from '@/services/api';

interface FileNode {
  name: string;
  type: 'file' | 'folder';
  children?: FileNode[];
  fileId?: number;
  content?: string;
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
    });
  });

  return root;
}

interface FileItemProps {
  node: FileNode;
  depth: number;
  selectedFile: string;
  onSelect: (file: { name: string; id: number; content: string }) => void;
  expandedFolders: Set<string>;
  onToggleFolder: (path: string) => void;
  path: string;
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
  path 
}: FileItemProps) => {
  const currentPath = path ? `${path}/${node.name}` : node.name;
  const isOpen = expandedFolders.has(currentPath);

  const handleClick = () => {
    if (node.type === 'folder') {
      onToggleFolder(currentPath);
    } else if (node.fileId && node.content !== undefined) {
      onSelect({ name: node.name, id: node.fileId, content: node.content });
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
        <button 
          className="opacity-0 group-hover:opacity-100 p-0.5 hover:bg-muted/30 rounded transition-all"
          onClick={(e) => e.stopPropagation()}
        >
          <MoreHorizontal className="w-3.5 h-3.5" />
        </button>
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
  onSelectFile: (file: { name: string; id: number; content: string }) => void;
}

export const FileExplorer = forwardRef<HTMLDivElement, FileExplorerProps>(
  ({ projectId, selectedFile, onSelectFile }, ref) => {
    const [searchQuery, setSearchQuery] = useState('');
    const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set(['src', 'src/components']));

    // Fetch files from backend
    const { data: files = [], isLoading } = useFiles(projectId);

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
        <div className="p-3 border-b border-border/50">
          <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            Explorer
          </span>
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
              />
            ))
          )}
        </div>
      </div>
    );
  }
);

FileExplorer.displayName = 'FileExplorer';
