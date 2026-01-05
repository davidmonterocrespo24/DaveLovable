import { useState, useRef, useEffect, forwardRef, useImperativeHandle } from 'react';
import { Send, Sparkles, User, Bot, Paperclip, Image, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useChatSession, useChatSessions } from '@/hooks/useChat';
import { chatApi } from '@/services/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github-dark.css';
import { AgentInteraction } from './AgentInteraction';
import { ToolExecutionBlock } from './ToolExecutionBlock';
import { useToast } from '@/hooks/use-toast';
import { useQueryClient } from '@tanstack/react-query';

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
  onGitCommit?: (data: { success: boolean; error?: string; message?: string }) => void;
  onReloadPreview?: (data: { message: string }) => void;
}

export interface ChatPanelRef {
  sendMessage: (message: string) => void;
}

export const ChatPanel = forwardRef<ChatPanelRef, ChatPanelProps>(
  ({ projectId, sessionId, onCodeChange, onGitCommit, onReloadPreview }, ref) => {
    const queryClient = useQueryClient();
    const [messages, setMessages] = useState<Message[]>(initialMessages);
    const [input, setInput] = useState('');
    const [currentSessionId, setCurrentSessionId] = useState<number | undefined>(sessionId);
    const [isStreaming, setIsStreaming] = useState(false);
    const [streamInterrupted, setStreamInterrupted] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const { toast } = useToast();
    const abortControllerRef = useRef<AbortController | null>(null);
    const pendingReloadRef = useRef<{ message: string } | null>(null);

    // Get all chat sessions for this project
    const { data: sessions } = useChatSessions(projectId);

    // Load the most recent session if no sessionId is provided
    useEffect(() => {
      if (!currentSessionId && sessions && sessions.length > 0) {
        // Sort by ID to get the most recent session
        const mostRecentSession = sessions.reduce((latest, current) =>
          current.id > latest.id ? current : latest
        );
        setCurrentSessionId(mostRecentSession.id);
      }
    }, [sessions, currentSessionId]);

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

    // Check for interrupted stream on mount and attempt to reconnect
    useEffect(() => {
      const streamStateKey = `streaming_project_${projectId}`;
      const savedStreamState = sessionStorage.getItem(streamStateKey);

      if (savedStreamState) {
        const { wasStreaming, sessionId, lastMessageId } = JSON.parse(savedStreamState);
        if (wasStreaming && sessionId) {
          setStreamInterrupted(true);
          toast({
            title: "⚠️ Stream interrupted",
            description: "Checking for new messages from the AI...",
            duration: 5000,
          });

          // Attempt to reconnect and get new messages
          const attemptReconnect = async () => {
            try {
              const result = await chatApi.reconnectToSession(projectId, sessionId, lastMessageId || 0);

              if (result.has_more && result.new_messages.length > 0) {
                // We have new messages! Update the UI
                const newMessages = result.new_messages.map((msg: any) => ({
                  id: msg.id.toString(),
                  role: msg.role,
                  content: msg.content,
                  timestamp: new Date(msg.created_at),
                  agent_interactions: msg.agent_interactions || [],
                }));

                setMessages(prev => [...prev, ...newMessages]);

                toast({
                  title: "✅ Reconnected successfully",
                  description: `Received ${result.new_messages.length} new message(s) from AI`,
                  duration: 5000,
                });

                setStreamInterrupted(false);

                // Update session ID
                if (currentSessionId !== sessionId) {
                  setCurrentSessionId(sessionId);
                }

                // Notify parent of code changes
                if (onCodeChange) {
                  onCodeChange();
                }
              } else {
                // No new messages yet, backend might still be processing
                toast({
                  title: "ℹ️ No new messages yet",
                  description: "The backend may still be processing. You can send a new message or wait.",
                  duration: 6000,
                });
              }
            } catch (error) {
              console.error('[Reconnect] Failed:', error);
              toast({
                title: "⚠️ Reconnection failed",
                description: "Could not retrieve new messages. The stream was interrupted.",
                variant: "destructive",
                duration: 8000,
              });
            }
          };

          attemptReconnect();
        }
        // Clear the saved state
        sessionStorage.removeItem(streamStateKey);
      }
    }, [projectId, toast, currentSessionId, onCodeChange]);

    // Save streaming state before page unload
    useEffect(() => {
      const handleBeforeUnload = () => {
        if (isStreaming && currentSessionId) {
          const streamStateKey = `streaming_project_${projectId}`;

          // Find the last message ID
          const lastMessageId = messages.length > 0
            ? parseInt(messages[messages.length - 1].id) || 0
            : 0;

          sessionStorage.setItem(streamStateKey, JSON.stringify({
            wasStreaming: true,
            sessionId: currentSessionId,
            lastMessageId: lastMessageId,
            timestamp: new Date().toISOString()
          }));

          // Abort the fetch request if it exists
          if (abortControllerRef.current) {
            abortControllerRef.current.abort();
          }
        }
      };

      window.addEventListener('beforeunload', handleBeforeUnload);
      return () => {
        window.removeEventListener('beforeunload', handleBeforeUnload);
      };
    }, [isStreaming, messages, projectId, currentSessionId]);

    const handleSend = async () => {
      if (!input.trim() || isStreaming) return;

      const messageContent = input;
      setInput('');
      setIsStreaming(true);
      setStreamInterrupted(false); // Clear any previous interruption flag

      // Clear any pending reload from previous messages
      pendingReloadRef.current = null;

      // Create AbortController for this request
      abortControllerRef.current = new AbortController();

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

              // Refresh file explorer when write_file tool is executed
              if (interaction.message_type === 'tool_call' && interaction.tool_name === 'write_file') {
                console.log('[ChatPanel] write_file tool detected, refreshing file explorer...');
                // Use setTimeout to delay invalidation slightly to allow backend to write the file
                setTimeout(() => {
                  queryClient.invalidateQueries({ queryKey: ['project', projectId] });
                }, 500);
              }

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
            onGitCommit: (data) => {
              console.log('[ChatPanel] Git commit event:', data);
              if (data.success) {
                toast({
                  title: "✅ Changes committed",
                  description: data.message || "Your changes have been saved to Git history",
                  duration: 5000,
                });
              } else if (data.error) {
                toast({
                  title: "⚠️ Commit failed",
                  description: data.error,
                  variant: "destructive",
                  duration: 5000,
                });
              }

              // Call parent callback for screenshot capture
              if (onGitCommit) {
                onGitCommit(data);
              }
            },
            onReloadPreview: (data) => {
              console.log('[ChatPanel] Reload preview event received - storing for later:', data);

              // Store the reload request to execute AFTER complete event
              // This prevents interrupting the SSE stream before all messages are processed
              pendingReloadRef.current = data;

              toast({
                title: "🔄 Preview will reload",
                description: data.message,
                duration: 3000,
              });
            },
            onComplete: (data) => {
              console.log('[ChatPanel] Complete event - updating message content');

              // Update the streaming message with the final response
              setMessages((prev) => {
                const updated = prev.map((msg) =>
                  msg.id === streamingMessageId
                    ? {
                      ...msg,
                      content: data.message.content,
                    }
                    : msg
                );
                console.log('[ChatPanel] Messages updated with final content');
                return updated;
              });

              // Notify parent if code changes were made OR if termination signal is present
              const hasTerminationSignal = data.message.content.includes('TERMINATE') || data.message.content.includes('TASK_COMPLETED');

              if ((data.code_changes && data.code_changes.length > 0) || hasTerminationSignal) {
                if (onCodeChange) {
                  onCodeChange();
                }
              }

              setIsStreaming(false);

              // Execute pending reload AFTER stream completes
              // This ensures all messages are processed before WebContainer reloads
              if (pendingReloadRef.current && onReloadPreview) {
                console.log('[ChatPanel] Executing pending reload after stream completion');
                // Wait longer to ensure:
                // 1. React updates the DOM with the final message
                // 2. Files are fully written to the backend filesystem
                // 3. WebContainer has time to sync the files
                setTimeout(() => {
                  console.log('[ChatPanel] Now executing the reload');
                  if (onReloadPreview && pendingReloadRef.current) {
                    onReloadPreview(pendingReloadRef.current);
                    pendingReloadRef.current = null;
                  }
                }, 2000); // Increased to 2000ms (2 seconds) to give more time for file sync
              }
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

        {/* Stream Interrupted Warning Banner */}
        {streamInterrupted && (
          <div className="mx-4 mt-2 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg flex items-start gap-2">
            <div className="text-yellow-500 mt-0.5">⚠️</div>
            <div className="flex-1 text-xs">
              <p className="font-medium text-yellow-500">Connection was interrupted</p>
              <p className="text-muted-foreground mt-1">
                The AI response was interrupted when you refreshed the page. The backend may still be processing your request.
                You can continue with a new message or wait for any file changes to appear.
              </p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 px-2 text-xs"
              onClick={() => setStreamInterrupted(false)}
            >
              Dismiss
            </Button>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${message.role === 'user'
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
                  className={`max-w-[85%] p-3 rounded-2xl text-sm leading-relaxed ${message.role === 'user'
                    ? 'bg-primary text-primary-foreground rounded-tr-sm'
                    : 'bg-muted/30 text-foreground rounded-tl-sm border border-border/30'
                    }`}
                >
                  {message.role === 'assistant' ? (
                    <>
                      {/* Agent Interactions */}
                      {message.agent_interactions && message.agent_interactions.length > 0 && (() => {
                        // Process interactions: separate tool_calls and tool_responses, then match them
                        const elements: JSX.Element[] = [];

                        // First pass: collect all tool_calls and tool_responses separately
                        const toolCalls: any[] = [];
                        const toolResponses: any[] = [];
                        const thoughts: any[] = [];

                        message.agent_interactions.forEach((interaction, idx) => {
                          if (interaction.message_type === 'thought') {
                            thoughts.push({ interaction, idx });
                          } else if (interaction.message_type === 'tool_call') {
                            toolCalls.push({
                              toolName: interaction.tool_name || 'unknown',
                              agentName: interaction.agent_name,
                              arguments: interaction.tool_arguments || {},
                              response: '', // Will be filled later
                              timestamp: interaction.timestamp,
                              idx,
                            });
                          } else if (interaction.message_type === 'tool_response') {
                            toolResponses.push({
                              content: interaction.content,
                              hasError: interaction.content.toLowerCase().includes('error'),
                              idx,
                            });
                          }
                        });

                        // Second pass: match tool_calls with tool_responses in order
                        const matchedToolCalls: any[] = [];
                        for (let i = 0; i < Math.min(toolCalls.length, toolResponses.length); i++) {
                          matchedToolCalls.push({
                            ...toolCalls[i],
                            response: toolResponses[i].content,
                            hasError: toolResponses[i].hasError,
                          });
                        }

                        // Add unmatched tool calls (responses not received yet)
                        for (let i = toolResponses.length; i < toolCalls.length; i++) {
                          matchedToolCalls.push({
                            ...toolCalls[i],
                            response: '⏳ Waiting for response...',
                            hasError: false,
                          });
                        }

                        // Render thoughts first (if any)
                        thoughts.forEach(({ interaction, idx }) => {
                          elements.push(
                            <AgentInteraction
                              key={`${message.id}-thought-${idx}`}
                              agentName={interaction.agent_name}
                              messageType={interaction.message_type}
                              content={interaction.content}
                              toolName={interaction.tool_name}
                              toolArguments={interaction.tool_arguments}
                              timestamp={interaction.timestamp}
                            />
                          );
                        });

                        // Then render matched tool calls
                        if (matchedToolCalls.length > 0) {
                          elements.push(
                            <ToolExecutionBlock
                              key={`${message.id}-tools`}
                              executions={matchedToolCalls}
                            />
                          );
                        }

                        return (
                          <div className="space-y-2 mb-3">
                            <div className="text-xs font-semibold text-muted-foreground mb-2">
                              Agent Activity:
                            </div>
                            {elements}
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
                              code: ({ node, inline, className, children, ...props }: any) => {
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
                              pre: ({ children, ...props }: any) => (
                                <pre className="bg-[#0d1117] rounded-lg p-4 overflow-x-auto my-2" {...props}>
                                  {children}
                                </pre>
                              ),
                              p: ({ children, ...props }: any) => (
                                <p className="mb-2 last:mb-0" {...props}>{children}</p>
                              ),
                              ul: ({ children, ...props }: any) => (
                                <ul className="list-disc list-inside mb-2" {...props}>{children}</ul>
                              ),
                              ol: ({ children, ...props }: any) => (
                                <ol className="list-decimal list-inside mb-2" {...props}>{children}</ol>
                              ),
                              li: ({ children, ...props }: any) => (
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
