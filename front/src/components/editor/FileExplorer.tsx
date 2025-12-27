import { forwardRef, useState, useMemo } from 'react';
import { ChevronRight, ChevronDown, File, Folder, Search, MoreHorizontal } from 'lucide-react';

interface FileNode {
  name: string;
  type: 'file' | 'folder';
  children?: FileNode[];
}

const mockFiles: FileNode[] = [
  {
    name: 'src',
    type: 'folder',
    children: [
      {
        name: 'components',
        type: 'folder',
        children: [
          { name: 'Button.tsx', type: 'file' },
          { name: 'Card.tsx', type: 'file' },
          { name: 'Header.tsx', type: 'file' },
        ],
      },
      { name: 'App.tsx', type: 'file' },
      { name: 'index.css', type: 'file' },
      { name: 'main.tsx', type: 'file' },
    ],
  },
  { name: 'package.json', type: 'file' },
  { name: 'vite.config.ts', type: 'file' },
  { name: 'tailwind.config.ts', type: 'file' },
];

interface FileItemProps {
  node: FileNode;
  depth: number;
  selectedFile: string;
  onSelect: (name: string) => void;
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
    } else {
      onSelect(node.name);
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
  selectedFile: string;
  onSelectFile: (name: string) => void;
}

export const FileExplorer = forwardRef<HTMLDivElement, FileExplorerProps>(
  ({ selectedFile, onSelectFile }, ref) => {
    const [searchQuery, setSearchQuery] = useState('');
    const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set(['src', 'src/components']));

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

    // Filter files based on search query
    const filteredFiles = useMemo(() => {
      if (!searchQuery.trim()) return mockFiles;
      
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

      return mockFiles.map(filterNode).filter((n): n is FileNode => n !== null);
    }, [searchQuery]);

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
          {filteredFiles.map((file) => (
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
          ))}
        </div>
      </div>
    );
  }
);

FileExplorer.displayName = 'FileExplorer';
