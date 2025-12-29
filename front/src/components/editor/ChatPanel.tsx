import { useState, useRef, useEffect, forwardRef, useImperativeHandle } from 'react';
import { Send, Sparkles, User, Bot, Paperclip, Image, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useChatSession } from '@/hooks/useChat';
import { chatApi } from '@/services/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github-dark.css';
import { AgentInteraction } from './AgentInteraction';
import { ToolExecutionBlock } from './ToolExecutionBlock';

interface AgentInteractionData {
  agent_name: string;
  message_type: 'thought' | 'tool_call' | 'tool_response';
  content: string;
  tool_name?: string;
  tool_arguments?: Record<string, any>;
  timestamp: string;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  agent_interactions?: AgentInteractionData[];
}

const initialMessages: Message[] = [
  {
    id: '1',
    role: 'assistant',
    content: 'Hello! I\'m your development assistant. I can help you create and modify your application. What would you like to build today?',
    timestamp: new Date(),
  },
];

interface ChatPanelProps {
  projectId: number;
  sessionId?: number;
  onCodeChange?: () => void;
}

export interface ChatPanelRef {
  sendMessage: (message: string) => void;
}

export const ChatPanel = forwardRef<ChatPanelRef, ChatPanelProps>(
  ({ projectId, sessionId, onCodeChange }, ref) => {
    const [messages, setMessages] = useState<Message[]>(initialMessages);
    const [input, setInput] = useState('');
    const [currentSessionId, setCurrentSessionId] = useState<number | undefined>(sessionId);
    const [isStreaming, setIsStreaming] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    // Get chat session if sessionId is provided
    const { data: session } = useChatSession(
      projectId,
      currentSessionId || 0,
      !!currentSessionId
    );

    // Expose sendMessage method to parent
    useImperativeHandle(ref, () => ({
      sendMessage: (message: string) => {
        setInput(message);
        // Trigger send automatically after a brief delay to ensure state is updated
        setTimeout(() => {
          handleSend();
        }, 100);
      },
    }));

    const scrollToBottom = () => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
      scrollToBottom();
    }, [messages]);

    // Load messages from session (only on initial load, not during streaming)
    useEffect(() => {
      if (session?.messages && !isStreaming) {
        const loadedMessages: Message[] = session.messages.map((msg) => ({
          id: msg.id.toString(),
          role: msg.role,
          content: msg.content,
          timestamp: new Date(msg.created_at),
          agent_interactions: msg.agent_interactions || [],
        }));
        setMessages([...initialMessages, ...loadedMessages]);
      }
    }, [session, isStreaming]);

    // Auto-resize textarea
    useEffect(() => {
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
        textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 128)}px`;
      }
    }, [input]);

    const handleSend = async () => {
      if (!input.trim() || isStreaming) return;

      const messageContent = input;
      setInput('');
      setIsStreaming(true);

      // Create both messages at once to avoid race conditions
      const userMessage: Message = {
        id: Date.now().toString(),
        role: 'user',
        content: messageContent,
        timestamp: new Date(),
      };

      const streamingMessageId = (Date.now() + 1).toString();
      const streamingMessage: Message = {
        id: streamingMessageId,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        agent_interactions: [],
      };

      console.log('[ChatPanel] Creating messages:', {
        userMessage,
        streamingMessage,
        streamingMessageId
      });

      // Add both messages in a single state update
      setMessages((prev) => {
        console.log('[ChatPanel] Before adding messages, count:', prev.length);
        const updated = [...prev, userMessage, streamingMessage];
        console.log('[ChatPanel] After adding messages, count:', updated.length);
        console.log('[ChatPanel] New messages:', updated);
        return updated;
      });

      try {
        await chatApi.sendMessageStream(
          projectId,
          {
            message: messageContent,
            session_id: currentSessionId,
          },
          {
            onStart: (data) => {
              // Update session ID if it's a new session
              if (data.session_id && !currentSessionId) {
                setCurrentSessionId(data.session_id);
              }
            },
            onAgentInteraction: (interaction) => {
              console.log('[ChatPanel] Received agent interaction:', interaction);
              // Add interaction to the streaming message in real-time
              setMessages((prev) => {
                console.log('[ChatPanel] Current messages:', prev.length);
                console.log('[ChatPanel] Looking for message:', streamingMessageId);
                const updated = prev.map((msg) => {
                  if (msg.id === streamingMessageId) {
                    console.log('[ChatPanel] Found streaming message, adding interaction');
                    return {
                      ...msg,
                      agent_interactions: [
                        ...(msg.agent_interactions || []),
                        interaction,
                      ],
                    };
                  }
                  return msg;
                });
                console.log('[ChatPanel] Updated messages:', updated);
                return updated;
              });
            },
            onComplete: (data) => {
              // Update the streaming message with the final response
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === streamingMessageId
                    ? {
                        ...msg,
                        content: data.message.content,
                      }
                    : msg
                )
              );

              // Notify parent if code changes were made
              if (data.code_changes && data.code_changes.length > 0 && onCodeChange) {
                onCodeChange();
              }

              setIsStreaming(false);
            },
            onError: (error) => {
              console.error('Streaming error:', error);
              // Update the streaming message with error
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === streamingMessageId
                    ? {
                        ...msg,
                        content: `Sorry, I encountered an error: ${error}. Please try again.`,
                      }
                    : msg
                )
              );
              setIsStreaming(false);
            },
          }
        );
      } catch (error) {
        console.error('Failed to send message:', error);
        // Update the streaming message with error
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === streamingMessageId
              ? {
                  ...msg,
                  content: 'Sorry, I encountered an error processing your request. Please try again.',
                }
              : msg
          )
        );
        setIsStreaming(false);
      }
    };

    const suggestions = [
      'Add a button with gradient',
      'Create a responsive header',
      'Add hover animations',
    ];

    const formatTime = (date: Date) => {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    return (
      <div ref={containerRef} className="h-full flex flex-col bg-background/80">
        {/* Header */}
        <div className="p-4 border-b border-border/50 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center shadow-lg shadow-primary/20">
            <Sparkles className="w-5 h-5 text-primary-foreground" />
          </div>
          <div>
            <h3 className="font-semibold text-sm">Lovable AI</h3>
            <p className="text-xs text-muted-foreground">Your development assistant</p>
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
                  {message.role === 'assistant' ? (
                    <>
                      {/* Agent Interactions */}
                      {message.agent_interactions && message.agent_interactions.length > 0 && (() => {
                        // Group tool calls and responses together
                        const thoughts: typeof message.agent_interactions = [];
                        const toolExecutions: Array<{
                          toolName: string;
                          agentName: string;
                          arguments: Record<string, any>;
                          response: string;
                          timestamp: string;
                          hasError?: boolean;
                        }> = [];

                        let currentToolCall: any = null;

                        message.agent_interactions.forEach((interaction) => {
                          if (interaction.message_type === 'thought') {
                            thoughts.push(interaction);
                          } else if (interaction.message_type === 'tool_call') {
                            currentToolCall = {
                              toolName: interaction.tool_name || 'unknown',
                              agentName: interaction.agent_name,
                              arguments: interaction.tool_arguments || {},
                              response: '',
                              timestamp: interaction.timestamp,
                            };
                          } else if (interaction.message_type === 'tool_response' && currentToolCall) {
                            currentToolCall.response = interaction.content;
                            currentToolCall.hasError = interaction.content.toLowerCase().includes('error');
                            toolExecutions.push(currentToolCall);
                            currentToolCall = null;
                          }
                        });

                        return (
                          <div className="space-y-2 mb-3">
                            <div className="text-xs font-semibold text-muted-foreground mb-2">
                              Agent Activity:
                            </div>

                            {/* Render thoughts */}
                            {thoughts.map((interaction, idx) => (
                              <AgentInteraction
                                key={`${message.id}-thought-${idx}`}
                                agentName={interaction.agent_name}
                                messageType={interaction.message_type}
                                content={interaction.content}
                                toolName={interaction.tool_name}
                                toolArguments={interaction.tool_arguments}
                                timestamp={interaction.timestamp}
                              />
                            ))}

                            {/* Render grouped tool executions */}
                            {toolExecutions.length > 0 && (
                              <ToolExecutionBlock executions={toolExecutions} />
                            )}
                          </div>
                        );
                      })()}

                      {/* Final Response */}
                      {message.content && (
                        <div className="prose prose-sm prose-invert max-w-none markdown-content">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            rehypePlugins={[rehypeHighlight]}
                            components={{
                              code: ({node, inline, className, children, ...props}: any) => {
                                return !inline ? (
                                  <code className={className} {...props}>
                                    {children}
                                  </code>
                                ) : (
                                  <code className="bg-muted px-1 py-0.5 rounded text-xs font-mono" {...props}>
                                    {children}
                                  </code>
                                );
                              },
                              pre: ({children, ...props}: any) => (
                                <pre className="bg-[#0d1117] rounded-lg p-4 overflow-x-auto my-2" {...props}>
                                  {children}
                                </pre>
                              ),
                              p: ({children, ...props}: any) => (
                                <p className="mb-2 last:mb-0" {...props}>{children}</p>
                              ),
                              ul: ({children, ...props}: any) => (
                                <ul className="list-disc list-inside mb-2" {...props}>{children}</ul>
                              ),
                              ol: ({children, ...props}: any) => (
                                <ol className="list-decimal list-inside mb-2" {...props}>{children}</ol>
                              ),
                              li: ({children, ...props}: any) => (
                                <li className="mb-1" {...props}>{children}</li>
                              ),
                            }}
                          >
                            {message.content}
                          </ReactMarkdown>
                        </div>
                      )}
                    </>
                  ) : (
                    message.content
                  )}
                </div>
                <span className="text-[10px] text-muted-foreground/60 px-1">
                  {formatTime(message.timestamp)}
                </span>
              </div>
            </div>
          ))}

          {isStreaming && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center">
                <Bot className="w-4 h-4 text-primary-foreground" />
              </div>
              <div className="bg-muted/30 p-3 rounded-2xl rounded-tl-sm border border-border/30">
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-primary" />
                  <span className="text-xs text-muted-foreground">AI is thinking...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggestions */}
        {messages.length <= 2 && !isStreaming && (
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
                placeholder="Describe what you want to create..."
                className="w-full bg-muted/20 border border-border/30 rounded-xl px-4 py-3 pr-20
                           text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary/50
                           placeholder:text-muted-foreground min-h-[48px] max-h-32 transition-all"
                rows={1}
                disabled={isStreaming}
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
              disabled={!input.trim() || isStreaming}
              className="h-12 w-12 rounded-xl bg-primary hover:bg-primary/90 p-0 shrink-0"
            >
              {isStreaming ? (
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
