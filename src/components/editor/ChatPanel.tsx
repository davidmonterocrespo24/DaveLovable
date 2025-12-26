import { useState, useRef, useEffect, forwardRef } from 'react';
import { Send, Sparkles, User, Bot, Paperclip, Image, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const initialMessages: Message[] = [
  {
    id: '1',
    role: 'assistant',
    content: '¡Hola! Soy tu asistente de desarrollo. Puedo ayudarte a crear y modificar tu aplicación. ¿Qué te gustaría construir hoy?',
    timestamp: new Date(),
  },
];

interface ChatPanelProps {
  onSendMessage: (message: string) => void;
}

export const ChatPanel = forwardRef<HTMLDivElement, ChatPanelProps>(
  ({ onSendMessage }, ref) => {
    const [messages, setMessages] = useState<Message[]>(initialMessages);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const scrollToBottom = () => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
      scrollToBottom();
    }, [messages]);

    // Auto-resize textarea
    useEffect(() => {
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
        textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 128)}px`;
      }
    }, [input]);

    const handleSend = () => {
      if (!input.trim() || isTyping) return;

      const userMessage: Message = {
        id: Date.now().toString(),
        role: 'user',
        content: input,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setInput('');
      onSendMessage(input);

      // Simulate AI response
      setIsTyping(true);
      setTimeout(() => {
        const aiResponse: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: getAIResponse(input),
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, aiResponse]);
        setIsTyping(false);
      }, 2000);
    };

    const getAIResponse = (userInput: string): string => {
      const input = userInput.toLowerCase();
      if (input.includes('botón') || input.includes('button')) {
        return '¡Perfecto! He añadido un nuevo componente Button con estilos modernos y variantes primary/secondary. Puedes verlo en el código y en la vista previa.';
      }
      if (input.includes('header') || input.includes('navbar')) {
        return 'He creado un Header responsive con navegación. Incluye un menú hamburguesa para móviles y links de navegación para desktop.';
      }
      if (input.includes('card') || input.includes('tarjeta')) {
        return 'He generado un componente Card con efectos hover y bordes con gradiente. Perfecto para mostrar contenido destacado.';
      }
      return 'Entendido. He actualizado el código según tu solicitud. Puedes ver los cambios en tiempo real en la vista previa a la derecha.';
    };

    const suggestions = [
      'Añade un botón con gradiente',
      'Crea un header responsive',
      'Añade animaciones hover',
    ];

    const formatTime = (date: Date) => {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    return (
      <div ref={ref} className="h-full flex flex-col bg-background/80">
        {/* Header */}
        <div className="p-4 border-b border-border/50 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center shadow-lg shadow-primary/20">
            <Sparkles className="w-5 h-5 text-primary-foreground" />
          </div>
          <div>
            <h3 className="font-semibold text-sm">Lovable AI</h3>
            <p className="text-xs text-muted-foreground">Tu asistente de desarrollo</p>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                  message.role === 'user'
                    ? 'bg-primary/20'
                    : 'bg-gradient-to-br from-primary to-purple-600'
                }`}
              >
                {message.role === 'user' ? (
                  <User className="w-4 h-4 text-primary" />
                ) : (
                  <Bot className="w-4 h-4 text-primary-foreground" />
                )}
              </div>
              <div className={`flex flex-col gap-1 ${message.role === 'user' ? 'items-end' : 'items-start'}`}>
                <div
                  className={`max-w-[85%] p-3 rounded-2xl text-sm leading-relaxed ${
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground rounded-tr-sm'
                      : 'bg-muted/30 text-foreground rounded-tl-sm border border-border/30'
                  }`}
                >
                  {message.content}
                </div>
                <span className="text-[10px] text-muted-foreground/60 px-1">
                  {formatTime(message.timestamp)}
                </span>
              </div>
            </div>
          ))}
          
          {isTyping && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center">
                <Bot className="w-4 h-4 text-primary-foreground" />
              </div>
              <div className="bg-muted/30 p-3 rounded-2xl rounded-tl-sm border border-border/30">
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-primary" />
                  <span className="text-xs text-muted-foreground">Generando código...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Suggestions */}
        {messages.length <= 2 && !isTyping && (
          <div className="px-4 pb-2 flex flex-wrap gap-2">
            {suggestions.map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => setInput(suggestion)}
                className="text-xs px-3 py-1.5 rounded-full bg-muted/20 hover:bg-muted/40 
                           text-muted-foreground hover:text-foreground transition-colors border border-border/30"
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}

        {/* Input */}
        <div className="p-4 border-t border-border/50">
          <div className="flex items-end gap-2">
            <div className="flex-1 relative">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="Describe qué quieres crear..."
                className="w-full bg-muted/20 border border-border/30 rounded-xl px-4 py-3 pr-20
                           text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary/50
                           placeholder:text-muted-foreground min-h-[48px] max-h-32 transition-all"
                rows={1}
                disabled={isTyping}
              />
              <div className="absolute right-2 bottom-2 flex items-center gap-1">
                <button 
                  className="p-1.5 text-muted-foreground hover:text-foreground transition-colors rounded hover:bg-muted/30"
                  title="Attach file"
                >
                  <Paperclip className="w-4 h-4" />
                </button>
                <button 
                  className="p-1.5 text-muted-foreground hover:text-foreground transition-colors rounded hover:bg-muted/30"
                  title="Add image"
                >
                  <Image className="w-4 h-4" />
                </button>
              </div>
            </div>
            <Button
              onClick={handleSend}
              disabled={!input.trim() || isTyping}
              className="h-12 w-12 rounded-xl bg-primary hover:bg-primary/90 p-0 shrink-0"
            >
              {isTyping ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </Button>
          </div>
        </div>
      </div>
    );
  }
);

ChatPanel.displayName = 'ChatPanel';
