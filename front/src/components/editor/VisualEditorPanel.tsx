import React, { useState, useEffect, useRef } from 'react';
import { X, ChevronDown, Wand2, AlignLeft, AlignCenter, AlignRight, AlignJustify } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Separator } from '@/components/ui/separator';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { projectApi } from '@/services/api';
import { useToast } from '@/hooks/use-toast';

interface DragInputProps {
    value: number;
    onChange: (value: number) => void;
    label?: string;
    min?: number;
    max?: number;
    step?: number;
    unit?: string;
}

const DragInput: React.FC<DragInputProps> = ({
    value,
    onChange,
    label,
    min = 0,
    max = 999,
    step = 1,
    unit = 'px'
}) => {
    const [isDragging, setIsDragging] = useState(false);
    const [localValue, setLocalValue] = useState(value);
    const startXRef = useRef(0);
    const startValueRef = useRef(0);

    useEffect(() => {
        setLocalValue(value);
    }, [value]);

    const handleMouseDown = (e: React.MouseEvent) => {
        e.preventDefault();
        setIsDragging(true);
        startXRef.current = e.clientX;
        startValueRef.current = localValue;
        document.body.style.cursor = 'ew-resize';
        document.body.style.userSelect = 'none';
    };

    useEffect(() => {
        if (!isDragging) return;

        const handleMouseMove = (e: MouseEvent) => {
            // Calculate sensitivity based on modifier keys
            let sensitivity = 5; // Default: 5px mouse = 1 unit
            if (e.shiftKey) sensitivity = 1; // Shift: faster (1px = 1 unit)
            if (e.altKey) sensitivity = 20; // Alt: slower (20px = 1 unit)

            const delta = Math.floor((e.clientX - startXRef.current) / sensitivity) * step;
            const newValue = Math.max(min, Math.min(max, startValueRef.current + delta));
            setLocalValue(newValue);
            onChange(newValue);
        };

        const handleMouseUp = () => {
            setIsDragging(false);
            document.body.style.cursor = 'default';
            document.body.style.userSelect = 'auto';
        };

        window.addEventListener('mousemove', handleMouseMove);
        window.addEventListener('mouseup', handleMouseUp);

        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
        };
    }, [isDragging, onChange, min, max, step]);

    return (
        <div className="relative">
            {label && (
                <div className="text-[10px] text-muted-foreground uppercase text-center mb-1">
                    {label}
                </div>
            )}
            <div
                className={`
                    h-9 px-2 flex items-center justify-center
                    bg-neutral-900 border border-neutral-700 rounded-md
                    cursor-ew-resize select-none
                    hover:bg-neutral-800 transition-colors
                    ${isDragging ? 'bg-primary/20 border-primary' : ''}
                `}
                onMouseDown={handleMouseDown}
                title="Click and drag to adjust value (Shift=faster, Alt=slower)"
            >
                <span className="text-xs font-mono">
                    {localValue}{unit}
                </span>
            </div>
        </div>
    );
};

interface ColorPickerProps {
    value: string;
    onChange: (value: string) => void;
    label?: string;
}

const ColorPicker: React.FC<ColorPickerProps> = ({ value, onChange, label }) => {
    const presetColors = [
        '#000000', '#ffffff', '#ef4444', '#f97316', '#f59e0b', '#84cc16',
        '#22c55e', '#06b6d4', '#3b82f6', '#6366f1', '#a855f7', '#d946ef'
    ];

    return (
        <Popover>
            <PopoverTrigger asChild>
                <Button
                    variant="outline"
                    className="w-full justify-start text-left font-normal h-8 px-2 gap-2"
                >
                    <div
                        className="w-4 h-4 rounded-full border shadow-sm shrink-0"
                        style={{ background: value || 'transparent' }}
                    />
                    <span className="truncate text-xs text-muted-foreground flex-1">
                        {value || 'Pick a color'}
                    </span>
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-64 p-3">
                <div className="space-y-3">
                    <div className="space-y-1">
                        <Label className="text-xs">Custom Color</Label>
                        <div className="flex gap-2">
                            <Input
                                value={value}
                                onChange={(e) => onChange(e.target.value)}
                                className="h-8 text-xs"
                                placeholder="#000000"
                            />
                            <input
                                type="color"
                                value={value.startsWith('#') ? value : '#000000'}
                                onChange={(e) => onChange(e.target.value)}
                                className="h-8 w-8 p-0 border rounded cursor-pointer shrink-0 appearance-none bg-transparent"
                            />
                        </div>
                    </div>
                    <div className="space-y-1">
                        <Label className="text-xs">Presets</Label>
                        <div className="flex flex-wrap gap-1.5">
                            {presetColors.map((color) => (
                                <button
                                    key={color}
                                    className="w-6 h-6 rounded-md border shadow-sm hover:scale-105 transition-transform"
                                    style={{ background: color }}
                                    onClick={() => onChange(color)}
                                    title={color}
                                />
                            ))}
                        </div>
                    </div>
                    {value && value !== 'inherit' && value !== 'transparent' && (
                        <Button
                            variant="ghost"
                            size="sm"
                            className="w-full h-7 text-xs"
                            onClick={() => onChange('inherit')}
                        >
                            Reset to Inherit
                        </Button>
                    )}
                </div>
            </PopoverContent>
        </Popover>
    );
};

interface VisualEditorPanelProps {
    onClose: () => void;
    onStyleUpdate: (property: string, value: string) => void;
    onAgentRequest: (prompt: string) => void;
    selectedElementId?: string;
    selectedElementTagName?: string;
    selectedElementFilepath?: string;
    selectedElementClassName?: string;
    initialStyles?: Record<string, string>;
    onSave?: (styles: Record<string, string>) => void;
    projectId: number;
    onReloadPreview?: () => void;
}

export const VisualEditorPanel: React.FC<VisualEditorPanelProps> = ({
    onClose,
    onStyleUpdate,
    onAgentRequest,
    selectedElementId,
    selectedElementTagName,
    selectedElementFilepath,
    selectedElementClassName,
    initialStyles = {},
    onSave,
    projectId,
    onReloadPreview
}) => {
    const { toast } = useToast();
    const [customPrompt, setCustomPrompt] = useState('');
    const [modifiedStyles, setModifiedStyles] = useState<Record<string, string>>({});
    const [isSaving, setIsSaving] = useState(false);
    const [editedClassName, setEditedClassName] = useState(selectedElementClassName || '');

    // Spacing values
    const [marginTop, setMarginTop] = useState(0);
    const [marginRight, setMarginRight] = useState(0);
    const [marginBottom, setMarginBottom] = useState(0);
    const [marginLeft, setMarginLeft] = useState(0);
    const [paddingTop, setPaddingTop] = useState(0);
    const [paddingRight, setPaddingRight] = useState(0);
    const [paddingBottom, setPaddingBottom] = useState(0);
    const [paddingLeft, setPaddingLeft] = useState(0);

    // Reset modified styles and className when selection changes
    useEffect(() => {
        setModifiedStyles({});
        setEditedClassName(selectedElementClassName || '');
        // Reset spacing values
        setMarginTop(0);
        setMarginRight(0);
        setMarginBottom(0);
        setMarginLeft(0);
        setPaddingTop(0);
        setPaddingRight(0);
        setPaddingBottom(0);
        setPaddingLeft(0);
    }, [selectedElementId, selectedElementClassName]);

    const handleStyleChange = (property: string, value: string) => {
        setModifiedStyles(prev => ({
            ...prev,
            [property]: value
        }));
        onStyleUpdate(property, value);
    };

    const handleAgentSubmit = () => {
        if (!customPrompt.trim()) return;
        onAgentRequest(customPrompt);
        setCustomPrompt('');
    };

    const handleSave = async () => {
        if (!selectedElementTagName || !selectedElementFilepath) {
            toast({
                title: "Cannot save",
                description: "No element selected or file path not available",
                variant: "destructive",
            });
            return;
        }

        const hasStyleChanges = Object.keys(modifiedStyles).length > 0;
        const hasClassNameChanges = editedClassName !== selectedElementClassName;

        if (!hasStyleChanges && !hasClassNameChanges) {
            toast({
                title: "No changes",
                description: "No changes to save",
                variant: "destructive",
            });
            return;
        }

        setIsSaving(true);

        try {
            // Extract relative path from WebContainer absolute path
            // WebContainer paths look like: /home/1cc9j47hh9g2sacuxjymmmjo48awol-se3b/src/components/HeroSection.tsx
            // We need just: src/components/HeroSection.tsx
            let relativePath = selectedElementFilepath;

            // Remove WebContainer home directory prefix if present
            const webContainerMatch = relativePath.match(/^\/home\/[^\/]+\/(.+)$/);
            if (webContainerMatch) {
                relativePath = webContainerMatch[1];
            }

            // Also handle cases where it might just start with /
            if (relativePath.startsWith('/') && !relativePath.startsWith('/home/')) {
                relativePath = relativePath.substring(1);
            }

            console.log('[VisualEditor] Original path:', selectedElementFilepath);
            console.log('[VisualEditor] Cleaned path:', relativePath);

            // Build a more specific selector to target the exact element
            // Use className if available to create a unique selector
            let elementSelector = selectedElementTagName;
            if (selectedElementClassName && !hasClassNameChanges) {
                // Only use className as selector if we're not changing it
                // Use the first class for better specificity
                const firstClass = selectedElementClassName.split(' ')[0];
                if (firstClass) {
                    elementSelector = `${selectedElementTagName}.${firstClass}`;
                }
            } else if (selectedElementId) {
                // Use ID if available (most specific)
                elementSelector = `${selectedElementTagName}#${selectedElementId}`;
            }

            const payload: any = {
                filepath: relativePath,
                element_selector: elementSelector,
                original_class_name: selectedElementClassName, // Send original className for backend to match
            };

            if (hasStyleChanges) {
                payload.style_changes = modifiedStyles;
            }

            if (hasClassNameChanges) {
                payload.class_name = editedClassName;
            }

            const result = await projectApi.applyVisualEdit(projectId, payload);

            if (result.success) {
                toast({
                    title: "Changes applied",
                    description: `Successfully updated ${selectedElementTagName} in ${selectedElementFilepath}`,
                });

                // Reload preview to show changes
                if (onReloadPreview) {
                    onReloadPreview();
                }

                // Clear modified styles and reset className after successful save
                setModifiedStyles({});
                setEditedClassName(editedClassName); // Keep the new className as the baseline

                if (onSave) {
                    onSave(modifiedStyles);
                }
            } else {
                toast({
                    title: "Failed to apply styles",
                    description: result.message || "Could not find the element in the file",
                    variant: "destructive",
                });
            }
        } catch (error) {
            console.error('[VisualEditor] Save error:', error);
            toast({
                title: "Error saving styles",
                description: error instanceof Error ? error.message : "Failed to apply visual edits",
                variant: "destructive",
            });
        } finally {
            setIsSaving(false);
        }
    };

    const hasChanges = Object.keys(modifiedStyles).length > 0 || editedClassName !== selectedElementClassName;

    return (
        <div className="flex-1 min-h-0 flex flex-col bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            {/* Header */}
            <div className="flex-none flex items-center justify-between p-4 border-b">
                <div>
                    <h3 className="font-semibold text-sm">Visual Edits</h3>
                    {selectedElementTagName && (
                        <p className="text-xs text-muted-foreground">
                            Selected: <code className="bg-muted px-1 rounded">{selectedElementTagName.toLowerCase()}</code>
                            {selectedElementId && <span className="opacity-70">#{selectedElementId}</span>}
                        </p>
                    )}
                </div>
                <div className="flex items-center gap-2">
                    {hasChanges && (
                        <Button
                            size="sm"
                            className="h-7 text-xs bg-green-600 hover:bg-green-700 text-white"
                            onClick={handleSave}
                            disabled={isSaving}
                        >
                            {isSaving ? 'Saving...' : 'Save Changes'}
                        </Button>
                    )}
                    <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8">
                        <X className="w-4 h-4" />
                    </Button>
                </div>
            </div>

            <div className="flex-1 min-h-0 overflow-y-auto p-4 space-y-6">

                {/* Colors */}
                <div className="space-y-4">
                    <h3 className="font-medium text-sm text-foreground/80">Colors</h3>

                    <div className="space-y-3">
                        <div className="space-y-1.5">
                            <Label className="text-xs font-normal">Text color</Label>
                            <ColorPicker
                                value={initialStyles.color || ''}
                                onChange={(val) => handleStyleChange('color', val)}
                            />
                        </div>

                        <div className="space-y-1.5">
                            <Label className="text-xs font-normal">Background color</Label>
                            <ColorPicker
                                value={initialStyles.backgroundColor || ''}
                                onChange={(val) => handleStyleChange('backgroundColor', val)}
                            />
                        </div>
                    </div>
                </div>

                <Separator />

                {/* Typography - Only show for text elements */}
                {selectedElementTagName && ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'a', 'button', 'label'].includes(selectedElementTagName.toLowerCase()) && (
                    <>
                        <div className="space-y-4">
                            <h3 className="font-medium text-sm text-foreground/80">Typography</h3>

                            <div className="grid grid-cols-2 gap-4">
                                {/* Font size */}
                                <div className="space-y-1.5">
                                    <Label className="text-xs font-normal">Font size</Label>
                                    <Select onValueChange={(val) => handleStyleChange('fontSize', val)}>
                                        <SelectTrigger className="h-8 text-xs">
                                            <SelectValue placeholder="Select" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="0.75rem">Extra Small (12px)</SelectItem>
                                            <SelectItem value="0.875rem">Small (14px)</SelectItem>
                                            <SelectItem value="1rem">Body (16px)</SelectItem>
                                            <SelectItem value="1.125rem">Large (18px)</SelectItem>
                                            <SelectItem value="1.25rem">Extra Large (20px)</SelectItem>
                                            <SelectItem value="1.5rem">2XL (24px)</SelectItem>
                                            <SelectItem value="1.875rem">3XL (30px)</SelectItem>
                                            <SelectItem value="2.25rem">4XL (36px)</SelectItem>
                                            <SelectItem value="3rem">5XL (48px)</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>

                                {/* Font weight */}
                                <div className="space-y-1.5">
                                    <Label className="text-xs font-normal">Font weight</Label>
                                    <Select onValueChange={(val) => handleStyleChange('fontWeight', val)}>
                                        <SelectTrigger className="h-8 text-xs">
                                            <SelectValue placeholder="Select" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="300">Light</SelectItem>
                                            <SelectItem value="400">Normal</SelectItem>
                                            <SelectItem value="500">Medium</SelectItem>
                                            <SelectItem value="600">Semibold</SelectItem>
                                            <SelectItem value="700">Bold</SelectItem>
                                            <SelectItem value="800">Extra Bold</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>

                            {/* Text alignment */}
                            <div className="space-y-1.5">
                                <Label className="text-xs font-normal">Alignment</Label>
                                <div className="flex border border-neutral-700 rounded-md overflow-hidden">
                                    <button
                                        className="flex-1 bg-neutral-800 hover:bg-neutral-700 py-2 flex justify-center transition-colors"
                                        onClick={() => handleStyleChange('textAlign', 'left')}
                                        title="Align Left"
                                    >
                                        <AlignLeft className="w-4 h-4" />
                                    </button>
                                    <button
                                        className="flex-1 bg-neutral-800 hover:bg-neutral-700 py-2 flex justify-center transition-colors border-l border-neutral-700"
                                        onClick={() => handleStyleChange('textAlign', 'center')}
                                        title="Align Center"
                                    >
                                        <AlignCenter className="w-4 h-4" />
                                    </button>
                                    <button
                                        className="flex-1 bg-neutral-800 hover:bg-neutral-700 py-2 flex justify-center transition-colors border-l border-neutral-700"
                                        onClick={() => handleStyleChange('textAlign', 'right')}
                                        title="Align Right"
                                    >
                                        <AlignRight className="w-4 h-4" />
                                    </button>
                                    <button
                                        className="flex-1 bg-neutral-800 hover:bg-neutral-700 py-2 flex justify-center transition-colors border-l border-neutral-700"
                                        onClick={() => handleStyleChange('textAlign', 'justify')}
                                        title="Justify"
                                    >
                                        <AlignJustify className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                        </div>

                        <Separator />
                    </>
                )}

                {/* Spacing */}
                <div className="space-y-4">
                    <h3 className="font-medium text-sm text-foreground/80">Spacing</h3>

                    <div className="space-y-4">
                        {/* Margin */}
                        <div>
                            <Label className="text-xs font-normal mb-2 block">Margin</Label>
                            <div className="grid grid-cols-4 gap-2">
                                <DragInput
                                    label="T"
                                    value={marginTop}
                                    onChange={(val) => {
                                        setMarginTop(val);
                                        handleStyleChange('marginTop', `${val}px`);
                                    }}
                                />
                                <DragInput
                                    label="R"
                                    value={marginRight}
                                    onChange={(val) => {
                                        setMarginRight(val);
                                        handleStyleChange('marginRight', `${val}px`);
                                    }}
                                />
                                <DragInput
                                    label="B"
                                    value={marginBottom}
                                    onChange={(val) => {
                                        setMarginBottom(val);
                                        handleStyleChange('marginBottom', `${val}px`);
                                    }}
                                />
                                <DragInput
                                    label="L"
                                    value={marginLeft}
                                    onChange={(val) => {
                                        setMarginLeft(val);
                                        handleStyleChange('marginLeft', `${val}px`);
                                    }}
                                />
                            </div>
                        </div>

                        {/* Padding */}
                        <div>
                            <Label className="text-xs font-normal mb-2 block">Padding</Label>
                            <div className="grid grid-cols-4 gap-2">
                                <DragInput
                                    label="T"
                                    value={paddingTop}
                                    onChange={(val) => {
                                        setPaddingTop(val);
                                        handleStyleChange('paddingTop', `${val}px`);
                                    }}
                                />
                                <DragInput
                                    label="R"
                                    value={paddingRight}
                                    onChange={(val) => {
                                        setPaddingRight(val);
                                        handleStyleChange('paddingRight', `${val}px`);
                                    }}
                                />
                                <DragInput
                                    label="B"
                                    value={paddingBottom}
                                    onChange={(val) => {
                                        setPaddingBottom(val);
                                        handleStyleChange('paddingBottom', `${val}px`);
                                    }}
                                />
                                <DragInput
                                    label="L"
                                    value={paddingLeft}
                                    onChange={(val) => {
                                        setPaddingLeft(val);
                                        handleStyleChange('paddingLeft', `${val}px`);
                                    }}
                                />
                            </div>
                        </div>
                    </div>
                </div>

                <Separator />

                {/* Border */}
                <div className="space-y-4">
                    <h3 className="font-medium text-sm text-foreground/80">Border</h3>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-1.5">
                            <Label className="text-xs font-normal">Width</Label>
                            <Select onValueChange={(val) => handleStyleChange('borderWidth', val)}>
                                <SelectTrigger className="h-8 text-xs">
                                    <SelectValue placeholder="Select" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="0px">None</SelectItem>
                                    <SelectItem value="1px">1px</SelectItem>
                                    <SelectItem value="2px">2px</SelectItem>
                                    <SelectItem value="4px">4px</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="space-y-1.5">
                            <Label className="text-xs font-normal">Color</Label>
                            <div className="flex items-center gap-2 h-8">
                                <span className="text-[10px] text-muted-foreground uppercase flex-1 text-right">Inherit</span>
                                <Switch />
                            </div>
                        </div>
                    </div>

                    <div className="space-y-1.5">
                        <Label className="text-xs font-normal">Style</Label>
                        <Select onValueChange={(val) => handleStyleChange('borderStyle', val)}>
                            <SelectTrigger className="h-8 text-xs">
                                <SelectValue placeholder="Select style" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="none">None</SelectItem>
                                <SelectItem value="solid">Solid</SelectItem>
                                <SelectItem value="dashed">Dashed</SelectItem>
                                <SelectItem value="dotted">Dotted</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </div>

                <Separator />

                {/* Effects */}
                <div className="space-y-4">
                    <h3 className="font-medium text-sm text-foreground/80">Effects</h3>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-1.5">
                            <Label className="text-xs font-normal">Radius</Label>
                            <Select onValueChange={(val) => handleStyleChange('borderRadius', val)}>
                                <SelectTrigger className="h-8 text-xs">
                                    <SelectValue placeholder="Select" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="0px">None</SelectItem>
                                    <SelectItem value="4px">Small</SelectItem>
                                    <SelectItem value="8px">Medium</SelectItem>
                                    <SelectItem value="16px">Large</SelectItem>
                                    <SelectItem value="9999px">Full</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="space-y-1.5">
                            <Label className="text-xs font-normal">Shadow</Label>
                            <Select onValueChange={(val) => handleStyleChange('boxShadow', val)}>
                                <SelectTrigger className="h-8 text-xs">
                                    <SelectValue placeholder="Select" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="none">None</SelectItem>
                                    <SelectItem value="0 1px 2px 0 rgb(0 0 0 / 0.05)">Small</SelectItem>
                                    <SelectItem value="0 4px 6px -1px rgb(0 0 0 / 0.1)">Medium</SelectItem>
                                    <SelectItem value="0 10px 15px -3px rgb(0 0 0 / 0.1)">Large</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>

                    <div className="space-y-1.5">
                        <Label className="text-xs font-normal">Opacity</Label>
                        <Select onValueChange={(val) => handleStyleChange('opacity', val)}>
                            <SelectTrigger className="h-8 text-xs">
                                <SelectValue placeholder="100%" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="1">100%</SelectItem>
                                <SelectItem value="0.75">75%</SelectItem>
                                <SelectItem value="0.5">50%</SelectItem>
                                <SelectItem value="0.25">25%</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </div>

                <Separator />

                {/* Advanced - className editor */}
                <details open className="space-y-4">
                    <summary className="cursor-pointer font-medium text-sm text-foreground/80 hover:text-foreground transition-colors">
                        Advanced
                    </summary>

                    <div className="space-y-1.5 pt-2">
                        <Label className="text-xs font-normal">Classes</Label>
                        <Textarea
                            value={editedClassName}
                            onChange={(e) => setEditedClassName(e.target.value)}
                            className="min-h-[100px] text-xs font-mono bg-neutral-900/50 border-neutral-700"
                            placeholder="e.g., text-sm lg:text-base text-foreground/80 mb-6"
                        />
                        <p className="text-[10px] text-muted-foreground">
                            Edit the CSS classes directly. Changes will be applied when you save.
                        </p>
                    </div>
                </details>
            </div>

            {/* Footer / Custom Agent Request */}
            <div className="flex-none p-4 border-t bg-muted/20 mt-auto">
                <Label className="text-xs font-semibold mb-2 block flex items-center gap-1.5">
                    <Wand2 className="w-3 h-3 text-primary" />
                    Custom Style / Ask Agent
                </Label>
                <Textarea
                    value={customPrompt}
                    onChange={(e) => setCustomPrompt(e.target.value)}
                    className="min-h-[80px] text-xs mb-2 resize-none bg-background"
                    placeholder="e.g., Change this to a gradient button..."
                />
                <Button
                    className="w-full h-8 text-xs"
                    size="sm"
                    onClick={handleAgentSubmit}
                    disabled={!customPrompt.trim()}
                >
                    Apply with Agent
                </Button>
            </div>
        </div>
    );
};
