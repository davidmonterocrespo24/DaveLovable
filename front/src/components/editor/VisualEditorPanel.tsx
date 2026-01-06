import React, { useState, useEffect } from 'react';
import { X, ChevronDown, Wand2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Separator } from '@/components/ui/separator';

interface VisualEditorPanelProps {
    onClose: () => void;
    onStyleUpdate: (property: string, value: string) => void;
    onAgentRequest: (prompt: string) => void;
    selectedElementId?: string;
    selectedElementTagName?: string;
    initialStyles?: Record<string, string>;
}

export const VisualEditorPanel: React.FC<VisualEditorPanelProps> = ({
    onClose,
    onStyleUpdate,
    onAgentRequest,
    selectedElementId,
    selectedElementTagName,
    initialStyles = {},
}) => {
    const [customPrompt, setCustomPrompt] = useState('');

    // State for properties (simplified for now, ideally strictly typed)
    // These would be populated from initialStyles

    const handleStyleChange = (property: string, value: string) => {
        onStyleUpdate(property, value);
    };

    const handleAgentSubmit = () => {
        if (!customPrompt.trim()) return;
        onAgentRequest(customPrompt);
        setCustomPrompt('');
    };

    return (
        <div className="h-full flex flex-col bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b">
                <div>
                    <h3 className="font-semibold text-sm">Visual Edits</h3>
                    {selectedElementTagName && (
                        <p className="text-xs text-muted-foreground">
                            Selected: <code className="bg-muted px-1 rounded">{selectedElementTagName.toLowerCase()}</code>
                            {selectedElementId && <span className="opacity-70">#{selectedElementId}</span>}
                        </p>
                    )}
                </div>
                <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8">
                    <X className="w-4 h-4" />
                </Button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-6">

                {/* Colors */}
                <div className="space-y-4">
                    <h3 className="font-medium text-sm text-foreground/80">Colors</h3>

                    <div className="space-y-3">
                        <div className="flex items-center justify-between">
                            <Label className="text-xs font-normal">Text color</Label>
                            <div className="flex items-center gap-2">
                                <span className="text-[10px] text-muted-foreground uppercase">Inherit</span>
                                <Switch onCheckedChange={(checked) => !checked && handleStyleChange('color', 'inherit')} />
                                {/* In a real implementation, we'd have a color picker trigger here if switch is on */}
                            </div>
                        </div>

                        <div className="flex items-center justify-between">
                            <Label className="text-xs font-normal">Background color</Label>
                            <div className="flex items-center gap-2">
                                <span className="text-[10px] text-muted-foreground uppercase">Inherit</span>
                                <Switch onCheckedChange={(checked) => !checked && handleStyleChange('backgroundColor', 'transparent')} />
                            </div>
                        </div>
                    </div>
                </div>

                <Separator />

                {/* Spacing */}
                <div className="space-y-4">
                    <h3 className="font-medium text-sm text-foreground/80">Spacing</h3>

                    <div className="space-y-3">
                        {/* Margin */}
                        <div>
                            <Label className="text-xs font-normal mb-1.5 block">Margin</Label>
                            <div className="grid grid-cols-2 gap-2">
                                <div className="relative">
                                    <Input
                                        className="h-8 text-xs pr-6"
                                        placeholder="All"
                                        onChange={(e) => handleStyleChange('margin', e.target.value)}
                                    />
                                    <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] text-muted-foreground">px</span>
                                </div>
                                {/* Simplified for demo, ordinarily would have 4 inputs or a lock toggle */}
                            </div>
                        </div>

                        {/* Padding */}
                        <div>
                            <Label className="text-xs font-normal mb-1.5 block">Padding</Label>
                            <div className="grid grid-cols-2 gap-2">
                                <div className="relative">
                                    <Input
                                        className="h-8 text-xs pr-6"
                                        placeholder="All"
                                        onChange={(e) => handleStyleChange('padding', e.target.value)}
                                    />
                                    <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] text-muted-foreground">px</span>
                                </div>
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
            </div>

            {/* Footer / Custom Agent Request */}
            <div className="p-4 border-t bg-muted/20">
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
