import { X, Code, Eye, GitBranch, Settings, Play } from 'lucide-react';

interface Tab {
  id: string;
  name: string;
  isActive: boolean;
}

interface EditorTabsProps {
  activeView: 'code' | 'preview' | 'split';
  onViewChange: (view: 'code' | 'preview' | 'split') => void;
  tabs: Tab[];
  onTabClose: (id: string) => void;
  onTabSelect: (id: string) => void;
}

export const EditorTabs = ({ 
  activeView, 
  onViewChange, 
  tabs, 
  onTabClose, 
  onTabSelect 
}: EditorTabsProps) => {
  return (
    <div className="flex items-center justify-between bg-background/80 border-b border-white/10 px-2">
      {/* File Tabs */}
      <div className="flex items-center gap-1 overflow-x-auto py-1">
        {tabs.map((tab) => (
          <div
            key={tab.id}
            onClick={() => onTabSelect(tab.id)}
            className={`group flex items-center gap-2 px-3 py-1.5 rounded-t-lg cursor-pointer 
                       text-sm transition-colors ${
              tab.isActive
                ? 'bg-[#0d1117] text-foreground border-t border-x border-white/10'
                : 'text-muted-foreground hover:text-foreground hover:bg-white/5'
            }`}
          >
            <Code className="w-3.5 h-3.5" />
            <span>{tab.name}</span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onTabClose(tab.id);
              }}
              className="opacity-0 group-hover:opacity-100 p-0.5 hover:bg-white/10 rounded transition-all"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        ))}
      </div>

      {/* View Toggle & Actions */}
      <div className="flex items-center gap-2 py-1">
        <div className="flex items-center bg-white/5 rounded-lg p-0.5">
          <button
            onClick={() => onViewChange('code')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors ${
              activeView === 'code'
                ? 'bg-primary text-white'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <Code className="w-3.5 h-3.5" />
            Code
          </button>
          <button
            onClick={() => onViewChange('split')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors ${
              activeView === 'split'
                ? 'bg-primary text-white'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            Split
          </button>
          <button
            onClick={() => onViewChange('preview')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors ${
              activeView === 'preview'
                ? 'bg-primary text-white'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <Eye className="w-3.5 h-3.5" />
            Preview
          </button>
        </div>

        <div className="w-px h-6 bg-white/10" />

        <button className="p-1.5 hover:bg-white/10 rounded transition-colors text-muted-foreground hover:text-foreground">
          <GitBranch className="w-4 h-4" />
        </button>
        <button className="flex items-center gap-1.5 px-3 py-1.5 bg-green-600 hover:bg-green-700 
                         text-white text-xs font-medium rounded-lg transition-colors">
          <Play className="w-3.5 h-3.5" />
          Run
        </button>
      </div>
    </div>
  );
};
