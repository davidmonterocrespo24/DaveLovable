import { forwardRef, useRef, useEffect } from 'react';
import Editor, { OnMount } from '@monaco-editor/react';
import type * as Monaco from 'monaco-editor';

interface CodeEditorProps {
  selectedFile: {
    name: string;
    id: number;
    content: string;
  } | null;
  isTyping: boolean;
  onContentChange?: (content: string) => void;
}

// Get language from file extension
const getLanguage = (filename: string): string => {
  const ext = filename.split('.').pop()?.toLowerCase();
  switch (ext) {
    case 'ts':
    case 'tsx':
      return 'typescript';
    case 'js':
    case 'jsx':
      return 'javascript';
    case 'css':
      return 'css';
    case 'json':
      return 'json';
    case 'html':
      return 'html';
    case 'md':
      return 'markdown';
    default:
      return 'plaintext';
  }
};

export const CodeEditor = forwardRef<HTMLDivElement, CodeEditorProps>(
  ({ selectedFile, isTyping, onContentChange }, ref) => {
    const editorRef = useRef<Monaco.editor.IStandaloneCodeEditor | null>(null);
    const monacoRef = useRef<typeof Monaco | null>(null);

    const handleEditorDidMount: OnMount = (editor, monaco) => {
      editorRef.current = editor;
      monacoRef.current = monaco;

      // Configure TypeScript compiler options
      monaco.languages.typescript.typescriptDefaults.setCompilerOptions({
        target: monaco.languages.typescript.ScriptTarget.Latest,
        allowNonTsExtensions: true,
        moduleResolution: monaco.languages.typescript.ModuleResolutionKind.NodeJs,
        module: monaco.languages.typescript.ModuleKind.ESNext,
        noEmit: true,
        esModuleInterop: true,
        jsx: monaco.languages.typescript.JsxEmit.React,
        reactNamespace: 'React',
        allowJs: true,
        typeRoots: ['node_modules/@types'],
        skipLibCheck: true,
        paths: {
          '@/*': ['./src/*']
        }
      });

      monaco.languages.typescript.javascriptDefaults.setCompilerOptions({
        target: monaco.languages.typescript.ScriptTarget.Latest,
        allowNonTsExtensions: true,
        moduleResolution: monaco.languages.typescript.ModuleResolutionKind.NodeJs,
        module: monaco.languages.typescript.ModuleKind.ESNext,
        noEmit: true,
        esModuleInterop: true,
        jsx: monaco.languages.typescript.JsxEmit.React,
        allowJs: true
      });

      // Add common library type definitions
      const reactTypes = `
        declare module 'react' {
          export function useState<T>(initialState: T | (() => T)): [T, (value: T) => void];
          export function useEffect(effect: () => void | (() => void), deps?: any[]): void;
          export function useRef<T>(initialValue: T): { current: T };
          export const Fragment: any;
          export default any;
        }
      `;

      const lucideReactTypes = `
        declare module 'lucide-react' {
          import { FC, SVGProps } from 'react';
          export type LucideIcon = FC<SVGProps<SVGSVGElement>>;
          export const Menu: LucideIcon;
          export const X: LucideIcon;
          export const Search: LucideIcon;
          export const User: LucideIcon;
          export const ShoppingBag: LucideIcon;
          export const ChevronRight: LucideIcon;
          export const ChevronDown: LucideIcon;
          export const File: LucideIcon;
          export const Folder: LucideIcon;
          export const MoreHorizontal: LucideIcon;
          export const Plus: LucideIcon;
          export const Trash2: LucideIcon;
          export const FilePlus: LucideIcon;
          export const Sparkles: LucideIcon;
          export const Settings: LucideIcon;
          export const Share2: LucideIcon;
          export const ChevronLeft: LucideIcon;
          export const PanelLeftClose: LucideIcon;
          export const PanelLeft: LucideIcon;
          export const Cloud: LucideIcon;
          export const Zap: LucideIcon;
          export const History: LucideIcon;
          export const Save: LucideIcon;
          export const FileText: LucideIcon;
        }
      `;

      monaco.languages.typescript.typescriptDefaults.addExtraLib(reactTypes, 'file:///node_modules/@types/react/index.d.ts');
      monaco.languages.typescript.typescriptDefaults.addExtraLib(lucideReactTypes, 'file:///node_modules/@types/lucide-react/index.d.ts');

      // Configure diagnostics to ignore certain warnings
      monaco.languages.typescript.typescriptDefaults.setDiagnosticsOptions({
        noSemanticValidation: false,
        noSyntaxValidation: false,
        diagnosticCodesToIgnore: [7027, 6133, 6192, 80001] // Ignore: unreachable code, unused vars, implicit any
      });

      monaco.languages.typescript.javascriptDefaults.setDiagnosticsOptions({
        noSemanticValidation: false,
        noSyntaxValidation: false,
        diagnosticCodesToIgnore: [7027, 6133, 6192, 80001]
      });
    };

    const handleEditorChange = (value: string | undefined) => {
      if (value !== undefined && !isTyping) {
        onContentChange?.(value);
      }
    };

    // Update editor content when file changes
    useEffect(() => {
      if (editorRef.current && selectedFile) {
        const currentValue = editorRef.current.getValue();
        if (currentValue !== selectedFile.content) {
          editorRef.current.setValue(selectedFile.content);
        }
      }
    }, [selectedFile?.id]);

    const language = selectedFile ? getLanguage(selectedFile.name) : 'plaintext';
    const value = selectedFile?.content || '// Select a file to view its contents';

    return (
      <div ref={ref} className="h-full bg-[#0d1117]">
        <Editor
          height="100%"
          language={language}
          value={value}
          onChange={handleEditorChange}
          onMount={handleEditorDidMount}
          theme="vs-dark"
          options={{
            readOnly: !selectedFile || isTyping,
            minimap: { enabled: false },
            fontSize: 14,
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 2,
            wordWrap: 'off',
            padding: { top: 16, bottom: 16 },
            fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
            cursorBlinking: 'smooth',
            smoothScrolling: true,
          }}
        />
      </div>
    );
  }
);

CodeEditor.displayName = 'CodeEditor';
