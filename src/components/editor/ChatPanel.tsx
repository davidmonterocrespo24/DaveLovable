import { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, User, Bot, Paperclip, Image } from 'lucide-react';
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

export const ChatPanel = ({ onSendMessage }: ChatPanelProps) => {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = () => {
    if (!input.trim()) return;

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

  return (
    <div className="h-full flex flex-col bg-background/80">
      {/* Header */}
      <div className="p-4 border-b border-white/10 flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center">
          <Sparkles className="w-4 h-4 text-white" />
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
                <Bot className="w-4 h-4 text-white" />
              )}
            </div>
            <div
              className={`max-w-[80%] p-3 rounded-2xl text-sm ${
                message.role === 'user'
                  ? 'bg-primary text-primary-foreground rounded-tr-sm'
                  : 'bg-white/5 text-foreground rounded-tl-sm'
              }`}
            >
              {message.content}
            </div>
          </div>
        ))}
        
        {isTyping && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div className="bg-white/5 p-3 rounded-2xl rounded-tl-sm">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-primary/60 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-primary/60 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-primary/60 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Suggestions */}
      {messages.length <= 2 && (
        <div className="px-4 pb-2 flex flex-wrap gap-2">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion}
              onClick={() => setInput(suggestion)}
              className="text-xs px-3 py-1.5 rounded-full bg-white/5 hover:bg-white/10 
                         text-muted-foreground hover:text-foreground transition-colors border border-white/10"
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-white/10">
        <div className="flex items-end gap-2">
          <div className="flex-1 relative">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Describe qué quieres crear..."
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 pr-20
                         text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary/50
                         placeholder:text-muted-foreground min-h-[48px] max-h-32"
              rows={1}
            />
            <div className="absolute right-2 bottom-2 flex items-center gap-1">
              <button className="p-1.5 text-muted-foreground hover:text-foreground transition-colors">
                <Paperclip className="w-4 h-4" />
              </button>
              <button className="p-1.5 text-muted-foreground hover:text-foreground transition-colors">
                <Image className="w-4 h-4" />
              </button>
            </div>
          </div>
          <Button
            onClick={handleSend}
            disabled={!input.trim()}
            className="h-12 w-12 rounded-xl bg-primary hover:bg-primary/90 p-0"
          >
            <Send className="w-5 h-5" />
          </Button>
        </div>
      </div>
    </div>
  );
};
