import { ChevronRight, ChevronDown, File, Folder } from 'lucide-react';
import { useState } from 'react';

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
}

const FileItem = ({ node, depth, selectedFile, onSelect }: FileItemProps) => {
  const [isOpen, setIsOpen] = useState(depth === 0);

  const handleClick = () => {
    if (node.type === 'folder') {
      setIsOpen(!isOpen);
    } else {
      onSelect(node.name);
    }
  };

  return (
    <div>
      <div
        className={`flex items-center gap-1 py-1 px-2 cursor-pointer hover:bg-white/5 rounded transition-colors ${
          selectedFile === node.name ? 'bg-primary/20 text-primary' : 'text-muted-foreground'
        }`}
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
        onClick={handleClick}
      >
        {node.type === 'folder' ? (
          <>
            {isOpen ? (
              <ChevronDown className="w-3 h-3" />
            ) : (
              <ChevronRight className="w-3 h-3" />
            )}
            <Folder className="w-4 h-4 text-primary/70" />
          </>
        ) : (
          <>
            <span className="w-3" />
            <File className="w-4 h-4 text-muted-foreground" />
          </>
        )}
        <span className="text-sm truncate">{node.name}</span>
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

export const FileExplorer = ({ selectedFile, onSelectFile }: FileExplorerProps) => {
  return (
    <div className="h-full bg-background/50 border-r border-white/10">
      <div className="p-3 border-b border-white/10">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          Explorer
        </span>
      </div>
      <div className="py-2">
        {mockFiles.map((file) => (
          <FileItem
            key={file.name}
            node={file}
            depth={0}
            selectedFile={selectedFile}
            onSelect={onSelectFile}
          />
        ))}
      </div>
    </div>
  );
};
