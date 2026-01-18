import { useState, useRef, useEffect, forwardRef, useImperativeHandle } from 'react';
import { Send, Sparkles, User, Bot, Paperclip, Image as ImageIcon, FileText, X, Loader2, GitCommit, Undo2, Camera, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { useChatSession, useChatSessions } from '@/hooks/useChat';
import { chatApi } from '@/services/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github-dark.css';
import { AgentInteraction } from './AgentInteraction';
import { VisualEditorPanel } from './VisualEditorPanel';
import { ToolExecutionBlock } from './ToolExecutionBlock';
import { useToast } from '@/hooks/use-toast';
import { useQueryClient } from '@tanstack/react-query';
import { SelectedElementData } from './PreviewPanelWithWebContainer';
import { fileKeys } from '@/hooks/useFiles'; // Import fileKeys for correct cache invalidation

interface AgentInteractionData {
  agent_name: string;
  message_type: 'thought' | 'tool_call' | 'tool_response';
  content: string;
  tool_name?: string;
  tool_arguments?: Record<string, any>;
  timestamp: string;
}

interface FileAttachment {
  id: string;
  name: string;
  type: 'image' | 'pdf';
  mime_type: string;
  size: number;
  url?: string;  // For preview/display
  data?: string; // Base64 data for sending to backend
}

interface GitCommitData {
  success: boolean;
  message: string;
  commit_hash?: string;
  commit_count?: number;
}

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  agent_interactions?: AgentInteractionData[];
  attachments?: FileAttachment[];  // Support multimodal messages
  git_commit?: GitCommitData;  // Git commit information
}

const initialMessages: Message[] = [
  {
    id: 'welcome-message',
    role: 'assistant',
    content: 'Hello! I\'m your development assistant. I can help you create and modify your application. What would you like to build today?',
    timestamp: new Date(),
  },
];

interface ChatPanelProps {
  projectId: number;
  sessionId?: number;
  onCodeChange?: () => void;
  onGitCommit?: (data: { success: boolean; error?: string; message?: string; commit_count?: number }) => void;
  onReloadPreview?: (data: { message: string }) => void;
  // Visual Editor Props
  onVisualModeChange?: (isVisualMode: boolean) => void;
  onStyleUpdate?: (property: string, value: string) => void;

  selectedElement?: SelectedElementData;
  onFileUpdate?: (files: Array<{ path: string, content: string }>) => void;
}

export interface ChatPanelRef {
  sendMessage: (message: string, attachments?: FileAttachment[]) => void;
}

export const ChatPanel = forwardRef<ChatPanelRef, ChatPanelProps>(
  ({
    projectId,
    sessionId,
    onCodeChange,
    onGitCommit,
    onReloadPreview,
    onVisualModeChange,
    onStyleUpdate,
    selectedElement,
    onFileUpdate
  }, ref) => {
    const queryClient = useQueryClient();
    const [messages, setMessages] = useState<Message[]>(initialMessages);
    const [input, setInput] = useState('');
    const [currentSessionId, setCurrentSessionId] = useState<number | undefined>(sessionId);
    const [isStreaming, setIsStreaming] = useState(false);
    const [streamInterrupted, setStreamInterrupted] = useState(false);
    const [attachedFiles, setAttachedFiles] = useState<FileAttachment[]>([]);  // Files to send
    const [isUploadingFile, setIsUploadingFile] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const imageInputRef = useRef<HTMLInputElement>(null);
    const pdfInputRef = useRef<HTMLInputElement>(null);
    const { toast } = useToast();
    const abortControllerRef = useRef<AbortController | null>(null);
    const pendingReloadRef = useRef<{ message: string } | null>(null);
    const [shouldTriggerReload, setShouldTriggerReload] = useState(false);
    const reloadScheduledRef = useRef(false); // Prevent duplicate reload scheduling

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
      sendMessage: (message: string, attachments?: FileAttachment[]) => {
        // Pass attachments directly to handleSend (don't use setState)
        // This avoids React state timing issues where setState is async
        handleSend(message, attachments);
      },
    }));

    const scrollToBottom = () => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
      scrollToBottom();
    }, [messages]);

    // Load messages from session and git commits (only on initial load, not during streaming)
    useEffect(() => {
      const loadMessagesAndCommits = async () => {
        if (session?.messages && !isStreaming) {
          const loadedMessages: Message[] = session.messages.map((msg) => ({
            id: msg.id.toString(),
            role: msg.role,
            content: msg.content,
            timestamp: new Date(msg.created_at),
            agent_interactions: msg.agent_interactions || [],
            attachments: msg.attachments || [],
          }));

          // Load git commits and convert them to system messages
          try {
            const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/projects/${projectId}/git/history?limit=100`);
            if (response.ok) {
              const commits = await response.json();

              // Convert ALL commits to system messages (we'll show them all in chronological order)
              const commitMessages: Message[] = commits.commits.map((commit: any) => ({
                id: `commit-${commit.hash}`,
                role: 'system' as const,
                content: commit.message.split('\n')[0], // First line of commit message
                timestamp: new Date(commit.date),
                git_commit: {
                  success: true,
                  message: commit.message.split('\n')[0],
                  commit_hash: commit.hash,
                  commit_count: commits.total_commits,
                },
              }));

              // Merge messages and commits, sort by timestamp
              const allMessages = [...loadedMessages, ...commitMessages].sort(
                (a, b) => a.timestamp.getTime() - b.timestamp.getTime()
              );

              // CRITICAL: Only reload if we don't have more messages locally
              // This prevents overwriting local state with stale server data
              const serverMessageCount = allMessages.length;
              const localMessageCount = messages.length - initialMessages.length; // Exclude initial message

              if (serverMessageCount > localMessageCount) {
                console.log('[ChatPanel] Loading messages and commits from session (server has more)');
                // If we have no messages yet, show initial message, otherwise show sorted history
                if (allMessages.length === 0) {
                  setMessages(initialMessages);
                } else {
                  setMessages(allMessages);
                }
              } else {
                console.log('[ChatPanel] Skipping message reload - local state is up to date');
                console.log(`  Server: ${serverMessageCount} messages, Local: ${localMessageCount} messages`);
              }
            }
          } catch (error) {
            console.error('[ChatPanel] Failed to load git commits:', error);
            // Fallback: just load messages without commits
            const serverMessageCount = loadedMessages.length;
            const localMessageCount = messages.length - initialMessages.length;

            if (serverMessageCount > localMessageCount) {
              console.log('[ChatPanel] Loading messages from session (without commits)');
              if (loadedMessages.length === 0) {
                setMessages(initialMessages);
              } else {
                setMessages(loadedMessages);
              }
            }
          }
        }
      };

      loadMessagesAndCommits();
    }, [session, isStreaming, messages.length, projectId]);

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

    // Handle WebContainer reload AFTER streaming completes
    // Note: We don't include 'messages' in dependencies to avoid re-triggering loop
    useEffect(() => {
      // Allow reload even if scheduled (we manage that manually in the callback now)
      // Only check pendingReloadRef and isStreaming for the "fallback" behavior
      if (shouldTriggerReload && !isStreaming && pendingReloadRef.current && onReloadPreview) {
        console.log('[ChatPanel] fallback reload trigger (stream ended)');
        if (onReloadPreview && pendingReloadRef.current) {
          onReloadPreview(pendingReloadRef.current);
          pendingReloadRef.current = null;
          setShouldTriggerReload(false);
        }
      }
    }, [shouldTriggerReload, isStreaming, onReloadPreview]);

    // Handle image file selection
    const handleImageSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
      const files = event.target.files;
      if (!files || files.length === 0) return;

      setIsUploadingFile(true);

      try {
        const newAttachments: FileAttachment[] = [];

        for (const file of Array.from(files)) {
          // Validate image type
          if (!file.type.startsWith('image/')) {
            toast({
              title: "Invalid file type",
              description: `${file.name} is not an image file`,
              variant: "destructive"
            });
            continue;
          }

          // Check file size (max 10MB)
          if (file.size > 10 * 1024 * 1024) {
            toast({
              title: "File too large",
              description: `${file.name} exceeds 10MB limit`,
              variant: "destructive"
            });
            continue;
          }

          // Read file as base64
          const reader = new FileReader();
          const base64Data = await new Promise<string>((resolve, reject) => {
            reader.onload = () => {
              const result = reader.result as string;
              resolve(result.split(',')[1]); // Remove data:image/... prefix
            };
            reader.onerror = reject;
            reader.readAsDataURL(file);
          });

          // Create preview URL
          const previewUrl = URL.createObjectURL(file);

          newAttachments.push({
            id: `${Date.now()}-${file.name}`,
            name: file.name,
            type: 'image',
            mime_type: file.type,
            size: file.size,
            url: previewUrl,
            data: base64Data
          });
        }

        setAttachedFiles(prev => [...prev, ...newAttachments]);
        toast({
          title: "Images attached",
          description: `${newAttachments.length} image(s) ready to send`
        });
      } catch (error) {
        console.error('[ChatPanel] Error processing images:', error);
        toast({
          title: "Error",
          description: "Failed to process images",
          variant: "destructive"
        });
      } finally {
        setIsUploadingFile(false);
        // Reset input
        if (imageInputRef.current) {
          imageInputRef.current.value = '';
        }
      }
    };

    // Handle PDF file selection
    const handlePdfSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
      const files = event.target.files;
      if (!files || files.length === 0) return;

      setIsUploadingFile(true);

      try {
        const newAttachments: FileAttachment[] = [];

        for (const file of Array.from(files)) {
          // Validate PDF type
          if (file.type !== 'application/pdf') {
            toast({
              title: "Invalid file type",
              description: `${file.name} is not a PDF file`,
              variant: "destructive"
            });
            continue;
          }

          // Check file size (max 20MB for PDFs)
          if (file.size > 20 * 1024 * 1024) {
            toast({
              title: "File too large",
              description: `${file.name} exceeds 20MB limit`,
              variant: "destructive"
            });
            continue;
          }

          // Read file as base64
          const reader = new FileReader();
          const base64Data = await new Promise<string>((resolve, reject) => {
            reader.onload = () => {
              const result = reader.result as string;
              resolve(result.split(',')[1]); // Remove data:application/pdf;... prefix
            };
            reader.onerror = reject;
            reader.readAsDataURL(file);
          });

          newAttachments.push({
            id: `${Date.now()}-${file.name}`,
            name: file.name,
            type: 'pdf',
            mime_type: 'application/pdf',
            size: file.size,
            data: base64Data
          });
        }

        setAttachedFiles(prev => [...prev, ...newAttachments]);
        toast({
          title: "PDFs attached",
          description: `${newAttachments.length} PDF(s) ready to send`
        });
      } catch (error) {
        console.error('[ChatPanel] Error processing PDFs:', error);
        toast({
          title: "Error",
          description: "Failed to process PDFs",
          variant: "destructive"
        });
      } finally {
        setIsUploadingFile(false);
        // Reset input
        if (pdfInputRef.current) {
          pdfInputRef.current.value = '';
        }
      }
    };

    // Remove attached file
    const removeAttachment = (id: string) => {
      setAttachedFiles(prev => {
        const file = prev.find(f => f.id === id);
        // Revoke object URL to free memory
        if (file?.url) {
          URL.revokeObjectURL(file.url);
        }
        return prev.filter(f => f.id !== id);
      });
    };

    const handleSend = async (messageOverride?: string, attachmentsOverride?: FileAttachment[]) => {
      let messageContent = messageOverride || input;
      // Use provided attachments or current state
      const filesToSend = attachmentsOverride || attachedFiles;

      if (!messageContent.trim() && filesToSend.length === 0) return;
      if (isStreaming) return;

      if (!messageOverride) {
        setInput('');
      }
      setIsStreaming(true);
      setStreamInterrupted(false); // Clear any previous interruption flag

      // Clear any pending reload from previous messages
      pendingReloadRef.current = null;
      setShouldTriggerReload(false);

      // Create AbortController for this request
      abortControllerRef.current = new AbortController();

      // Auto-enhance message if images are attached
      const hasImages = filesToSend.some(f => f.type === 'image');
      if (hasImages && !messageContent.toLowerCase().includes('ui') && !messageContent.toLowerCase().includes('design')) {
        messageContent = `${messageContent}\n\n[Note: The attached image(s) show a UI/UX design that should be converted to React code with Tailwind CSS. Analyze the design, layout, colors, typography, and components shown in the image(s).]`;
      }

      // Create both messages at once to avoid race conditions
      const userMessage: Message = {
        id: Date.now().toString(),
        role: 'user',
        content: messageContent,
        timestamp: new Date(),
        attachments: filesToSend.length > 0 ? [...filesToSend] : undefined,
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
        // Log what we're sending
        console.log('[ChatPanel] Sending message with attachments:', {
          messageLength: messageContent.length,
          attachmentCount: filesToSend.length,
          attachments: filesToSend.map(f => ({
            name: f.name,
            type: f.type,
            dataLength: f.data?.length || 0
          }))
        });

        // Check total payload size (rough estimate)
        const payloadSize = JSON.stringify({
          message: messageContent,
          session_id: currentSessionId,
          attachments: filesToSend
        }).length;

        console.log('[ChatPanel] Estimated payload size:', (payloadSize / 1024 / 1024).toFixed(2), 'MB');

        if (payloadSize > 50 * 1024 * 1024) { // 50MB limit
          toast({
            title: "Request too large",
            description: "The attached files are too large. Please use smaller images.",
            variant: "destructive"
          });
          setIsStreaming(false);
          return;
        }

        await chatApi.sendMessageStream(
          projectId,
          {
            message: messageContent,
            session_id: currentSessionId,
            attachments: filesToSend.length > 0 ? filesToSend.map(file => ({
              type: file.type,
              mime_type: file.mime_type,
              data: file.data,
              name: file.name
            })) : undefined,
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

              // Note: File list refetch now happens at stream completion
              // This ensures it works regardless of which tools the agent uses

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
            onFilesReady: (data) => {
              console.log('[ChatPanel] 📁📁📁 FILES READY CALLBACK INVOKED! 📁📁📁');
              console.log('[ChatPanel] 📁 Data received:', data);
              console.log('[ChatPanel] 📁 Project ID:', projectId);

              // -------------------------------------------------------------------------
              // IMPROVED LOGIC: Trust the event! 
              // We don't wait for file count to change because EDITS don't change the count.
              // We simply force a refetch and update the UI.
              // -------------------------------------------------------------------------

              console.log('[ChatPanel] 📁 Starting refresh sequence...');

              // CHECK FOR PUSH UPDATE (Robust Fix)
              const payload = data as any;
              if (payload.files && Array.isArray(payload.files) && payload.files.length > 0) {
                console.log(`[ChatPanel] 🚀 Received ${data.files.length} pushed files. Updating WebContainer immediately.`);
                if (onFileUpdate) {
                  onFileUpdate(data.files);
                  // We continue with the standard reload sequence as a backup/consistency check
                  // This ensures that if the push update caused any transient HMR errors,
                  // they will be resolved by the full reload that follows.
                }
              }

              // Invalidate query to mark data as stale
              // FIX: Use specific fileKeys list to ensure FileExplorer updates
              queryClient.invalidateQueries({ queryKey: fileKeys.list(projectId) });
              queryClient.invalidateQueries({ queryKey: ['project', projectId] }); // Keep this for project details

              // Perform a few quick polls to ensure we catch the update (fs writes are fast but async)
              let pollAttempts = 0;
              const maxPollAttempts = 5;

              const pollInterval = setInterval(async () => {
                pollAttempts++;
                console.log(`[ChatPanel] 📁 Refresh attempt ${pollAttempts}/${maxPollAttempts}...`);

                try {
                  // Force refetch
                  await queryClient.refetchQueries({ queryKey: fileKeys.list(projectId) });

                  // We consider it a success immediately - no need to check counts
                  // The UI will react to the new data automatically via React Query

                  if (pollAttempts >= 3) {
                    clearInterval(pollInterval);
                    console.log('[ChatPanel] 📁 Refresh sequence complete');

                    // Trigger onCodeChange to notify parent (important for screenshotting, etc)
                    if (onCodeChange) {
                      onCodeChange();
                    }
                  }
                } catch (error) {
                  console.error('[ChatPanel] 📁 Error during refresh:', error);
                }
              }, 500);

              toast({
                title: "📁 Files updated",
                description: "Project files have been updated.",
                duration: 2000,
              });
            },
            onGitCommit: (data) => {
              console.log('[ChatPanel] Git commit event:', data);

              if (data.success && data.commit_hash) {
                // Add commit message to chat
                const commitMessage: Message = {
                  id: `commit-${Date.now()}`,
                  role: 'system',
                  content: data.message || 'Changes committed',
                  timestamp: new Date(),
                  git_commit: {
                    success: true,
                    message: data.message || 'Changes committed',
                    commit_hash: data.commit_hash,
                    commit_count: data.commit_count
                  }
                };

                setMessages((prev) => [...prev, commitMessage]);

                toast({
                  title: "✅ Git Commit Created",
                  description: data.message || "Changes have been committed to git.",
                  duration: 3000,
                });
              } else if (!data.success) {
                toast({
                  title: "Git Commit",
                  description: data.message || "No changes to commit",
                  duration: 2000,
                });
              }
            },
            onReloadPreview: (data) => {
              console.log('[ChatPanel] Reload preview event received:', data);
              pendingReloadRef.current = data;

              toast({
                title: "🔄 Preview will reload",
                description: data.message,
                duration: 3000,
              });

              // OPTIMIZED: Single reload after files are ready
              // We trust 'files_ready' event has already pushed file updates via applyFileUpdates
              // A single reload ensures WebContainer reflects the latest changes

              if (onReloadPreview && !reloadScheduledRef.current) {
                console.log('[ChatPanel] 🔄 Scheduling single WebContainer reload...');
                reloadScheduledRef.current = true;

                // Single reload: Wait for FS to settle (2.5s is sufficient)
                setTimeout(() => {
                  console.log('[ChatPanel] 🔄 Executing WebContainer reload...');
                  if (onReloadPreview) {
                    onReloadPreview(data);
                  }
                  reloadScheduledRef.current = false;
                }, 2500);
              }
            },
            onComplete: (data) => {
              console.log('[ChatPanel] Complete event - updating message content');
              console.log('[ChatPanel] Complete data:', data);

              // Update the streaming message with the final response
              setMessages((prev) => {
                console.log('[ChatPanel] Before complete update, messages:', prev.length);
                const streamingMsg = prev.find(m => m.id === streamingMessageId);
                console.log('[ChatPanel] Streaming message before update:', streamingMsg);
                console.log('[ChatPanel] Agent interactions count:', streamingMsg?.agent_interactions?.length || 0);

                const updated = prev.map((msg) =>
                  msg.id === streamingMessageId
                    ? {
                      ...msg, // Preserve all existing properties including agent_interactions
                      content: data.message.content,
                    }
                    : msg
                );

                const updatedStreamingMsg = updated.find(m => m.id === streamingMessageId);
                console.log('[ChatPanel] Streaming message after update:', updatedStreamingMsg);
                console.log('[ChatPanel] Agent interactions count after:', updatedStreamingMsg?.agent_interactions?.length || 0);
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

              // Clear attached files after successful send
              console.log('[ChatPanel] Clearing attached files after successful send');
              setAttachedFiles([]);

              // CRITICAL FIX: Delay setIsStreaming(false) to prevent race condition
              // The issue: onCodeChange() invalidates queries, which refetches session data
              // If we set isStreaming=false immediately, the useEffect will reload messages
              // from the OLD session data (DB hasn't been updated yet), overwriting our local state
              // Solution: Keep isStreaming=true for 3 seconds to block the useEffect from running
              console.log('[ChatPanel] Keeping isStreaming=true for 3s to prevent message reload');
              setTimeout(() => {
                console.log('[ChatPanel] Now setting isStreaming=false - safe to reload messages');
                setIsStreaming(false);
              }, 3000);

              // WebContainer reload is now handled by onFilesReady callback
              // which waits for files to actually arrive before triggering reload
              console.log('[ChatPanel] Stream complete - WebContainer reload will be triggered by onFilesReady');

              // Clear attached files after successful send
              setAttachedFiles(prev => {
                // Revoke object URLs to free memory
                prev.forEach(file => {
                  if (file.url) {
                    URL.revokeObjectURL(file.url);
                  }
                });
                return [];
              });
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

              // Clear attached files on error
              setAttachedFiles(prev => {
                prev.forEach(file => {
                  if (file.url) {
                    URL.revokeObjectURL(file.url);
                  }
                });
                return [];
              });
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

        // Clear attached files on error
        setAttachedFiles(prev => {
          prev.forEach(file => {
            if (file.url) {
              URL.revokeObjectURL(file.url);
            }
          });
          return [];
        });
      }
    };

    const suggestions = [
      'Add a button with gradient',
      'Create a responsive header',
      'Add hover animations',
    ];

    const formatTime = (date: Date) => {
      return date.toLocaleString(); // Show full date and time for debugging
    };

    const [viewMode, setViewMode] = useState<'chat' | 'visual'>('chat');

    // Toggle visual mode
    const toggleVisualMode = () => {
      const newMode = viewMode === 'chat' ? 'visual' : 'chat';
      setViewMode(newMode);
      if (onVisualModeChange) {
        onVisualModeChange(newMode === 'visual');
      }
    };

    // Handle agent request from visual editor
    const handleVisualAgentRequest = (prompt: string) => {
      // Switch back to chat
      setViewMode('chat');

      // Construct context-rich message
      let message = `[VISUAL EDIT] ${prompt}`;

      if (selectedElement) {
        message += `\n\nContext:\nTarget Element: <${selectedElement.tagName}`;
        if (selectedElement.elementId) message += ` id="${selectedElement.elementId}"`;
        if (selectedElement.className) message += ` class="${selectedElement.className}"`;
        message += `>`;

        message += `\nCSS Selector: ${selectedElement.selector}`;
        if (selectedElement.innerText) {
          message += `\nText Content: "${selectedElement.innerText}"`;
        }

        if (Object.keys(selectedElement.attributes).length > 0) {
          message += `\nAttributes: ${JSON.stringify(selectedElement.attributes)}`;
        }
      }

      // Auto-send the message
      handleSend(message);
    };

    const handleUndoCommit = async (commitHash: string) => {
      try {
        // Call backend API to revert the commit
        const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/projects/${projectId}/git/restore/${commitHash}`, {
          method: 'POST',
        });

        if (!response.ok) {
          throw new Error('Failed to revert commit');
        }

        const result = await response.json();

        // Show success message
        toast({
          title: 'Commit Reverted',
          description: `Successfully reverted commit ${commitHash.substring(0, 7)}`,
        });

        // Add the new restore commit to the chat
        if (result.commit_hash) {
          const restoreCommitMessage: Message = {
            id: `commit-${result.commit_hash}`,
            role: 'system',
            content: result.message,
            timestamp: new Date(), // Current time
            git_commit: {
              success: true,
              message: result.message,
              commit_hash: result.commit_hash,
            }
          };
          setMessages((prev) => [...prev, restoreCommitMessage]);
        }

        // Reload files to reflect the reverted changes
        queryClient.invalidateQueries({ queryKey: fileKeys.list(projectId) });

        // Trigger preview reload
        if (onReloadPreview) {
          onReloadPreview();
        }
      } catch (error) {
        console.error('Error reverting commit:', error);
        toast({
          title: 'Revert Failed',
          description: error instanceof Error ? error.message : 'Failed to revert commit',
          variant: 'destructive',
        });
      }
    };

    return (
      <div ref={containerRef} className="h-full flex flex-col bg-background/80 overflow-x-hidden">
        {/* Header */}
        <div className="p-4 border-b border-border/50 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center shadow-lg shadow-primary/20">
              <Sparkles className="w-5 h-5 text-primary-foreground" />
            </div>
            <div>
              <h3 className="font-semibold text-sm">Lovable AI</h3>
              <p className="text-xs text-muted-foreground">Your development assistant</p>
            </div>
          </div>

          <Button
            variant={viewMode === 'visual' ? 'secondary' : 'ghost'}
            size="sm"
            onClick={toggleVisualMode}
            className="text-xs gap-1.5 h-8"
          >
            <Sparkles className="w-3.5 h-3.5" />
            {viewMode === 'visual' ? 'Back to Chat' : 'Visual Edits'}
          </Button>
        </div>

        {viewMode === 'visual' ? (
          <VisualEditorPanel
            onClose={() => toggleVisualMode()}
            onStyleUpdate={(prop, val) => onStyleUpdate && onStyleUpdate(prop, val)}
            onAgentRequest={handleVisualAgentRequest}
            selectedElementId={selectedElement?.elementId}
            selectedElementTagName={selectedElement?.tagName}
            selectedElementFilepath={selectedElement?.source?.fileName}
            projectId={projectId}
            onReloadPreview={() => {
              if (onReloadPreview) {
                onReloadPreview({ message: 'Visual edits applied' });
              }
            }}
          />
        ) : (
          <>
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
            <div className="flex-1 overflow-y-auto overflow-x-hidden p-4 space-y-4">
              {messages.map((message) => {
                // Special rendering for git commit messages
                if (message.role === 'system' && message.git_commit) {
                  const commit = message.git_commit;
                  return (
                    <div
                      key={message.id}
                      className="flex gap-3 items-start"
                    >
                      <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 bg-green-500/20">
                        <GitCommit className="w-4 h-4 text-green-500" />
                      </div>
                      <div className="max-w-[70%] bg-green-500/10 border border-green-500/30 rounded-lg p-3">
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-xs font-semibold text-green-500">Git Commit</span>
                              {commit.commit_hash && (
                                <code className="text-[10px] bg-green-500/10 px-1.5 py-0.5 rounded font-mono text-green-400">
                                  {commit.commit_hash.substring(0, 7)}
                                </code>
                              )}
                              <span className="text-[10px] text-muted-foreground">
                                {message.timestamp.toLocaleString()}
                              </span>
                            </div>
                            <p className="text-sm text-foreground">{commit.message}</p>
                            {commit.commit_count !== undefined && (
                              <p className="text-xs text-muted-foreground mt-1">
                                Total commits: {commit.commit_count}
                              </p>
                            )}
                          </div>
                          {commit.commit_hash && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 text-xs text-orange-500 hover:text-orange-400 hover:bg-orange-500/10"
                              onClick={() => handleUndoCommit(commit.commit_hash!)}
                            >
                              <Undo2 className="w-3 h-3 mr-1" />
                              Undo
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                }

                // Regular user/assistant message rendering
                return (
                  <div
                    key={message.id}
                    className={`flex flex-col gap-2 ${message.role === 'user' ? 'items-end' : 'items-start'}`}
                  >
                    <div className="flex items-center gap-2">
                      <div
                        className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${message.role === 'user'
                          ? 'bg-primary/20'
                          : 'bg-gradient-to-br from-primary to-purple-600'
                          }`}
                      >
                        {message.role === 'user' ? (
                          <User className="w-3 h-3 text-primary" />
                        ) : (
                          <Bot className="w-3 h-3 text-primary-foreground" />
                        )}
                      </div>
                      <span className="text-xs font-medium text-muted-foreground">
                        {message.role === 'user' ? 'You' : 'Lovable AI'}
                      </span>
                    </div>
                    <div className={`flex flex-col gap-1 w-full`}>
                      <div
                        className={`w-full p-3 rounded-2xl text-sm leading-relaxed ${message.role === 'user'
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
                            <div className="prose prose-sm prose-invert max-w-none markdown-content overflow-hidden break-words">
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
                        <>
                          {/* User message attachments */}
                          {message.attachments && message.attachments.length > 0 && (
                            <div className="mb-2 space-y-2">
                              {message.attachments.map((file, idx) => (
                                <div key={idx} className="flex items-center gap-2">
                                  {file.type === 'image' && file.url ? (
                                    <img
                                      src={file.url}
                                      alt={file.name}
                                      className="max-w-[200px] max-h-[200px] rounded border border-primary/20"
                                    />
                                  ) : (
                                    <div className="flex items-center gap-2 bg-primary-foreground/10 px-3 py-2 rounded border border-primary/20">
                                      <FileText className="w-4 h-4" />
                                      <span className="text-xs">{file.name}</span>
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                          {message.content}
                        </>
                      )}
                    </div>
                    <span className="text-[10px] text-muted-foreground/60 px-1">
                      {formatTime(message.timestamp)}
                    </span>
                  </div>
                </div>
              );
              })}

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
              {/* File attachments preview */}
              {attachedFiles.length > 0 && (
                <div className="mb-3 flex flex-wrap gap-2">
                  {attachedFiles.map(file => (
                    <div
                      key={file.id}
                      className="relative group bg-muted/30 border border-border/50 rounded-lg p-2 flex items-center gap-2 max-w-xs"
                    >
                      {file.type === 'image' && file.url ? (
                        <img
                          src={file.url}
                          alt={file.name}
                          className="w-12 h-12 object-cover rounded"
                        />
                      ) : (
                        <div className="w-12 h-12 flex items-center justify-center bg-muted/50 rounded">
                          <FileText className="w-6 h-6 text-muted-foreground" />
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium truncate">{file.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {(file.size / 1024).toFixed(1)} KB
                        </p>
                      </div>
                      <button
                        onClick={() => removeAttachment(file.id)}
                        className="absolute -top-1 -right-1 w-5 h-5 bg-destructive text-destructive-foreground rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                        title="Remove"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

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
                    placeholder={attachedFiles.length > 0 ? "Add a message about the attached files..." : "Describe what you want to create..."}
                    className="w-full bg-muted/20 border border-border/30 rounded-xl px-4 py-3 pr-20
                               text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary/50
                               placeholder:text-muted-foreground min-h-[48px] max-h-32 transition-all"
                    rows={1}
                    disabled={isStreaming}
                  />
                  {/* Hidden file inputs */}
                  <input
                    ref={imageInputRef}
                    type="file"
                    accept="image/png,image/jpeg,image/jpg,image/webp,image/gif"
                    multiple
                    onChange={handleImageSelect}
                    className="hidden"
                  />
                  <input
                    ref={pdfInputRef}
                    type="file"
                    accept="application/pdf"
                    multiple
                    onChange={handlePdfSelect}
                    className="hidden"
                  />

                  <div className="absolute right-2 bottom-2 flex items-center gap-1">
                    <button
                      onClick={() => pdfInputRef.current?.click()}
                      disabled={isStreaming || isUploadingFile}
                      className="p-1.5 text-muted-foreground hover:text-foreground transition-colors rounded hover:bg-muted/30 disabled:opacity-50"
                      title="Attach PDF"
                    >
                      <FileText className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => imageInputRef.current?.click()}
                      disabled={isStreaming || isUploadingFile}
                      className="p-1.5 text-muted-foreground hover:text-foreground transition-colors rounded hover:bg-muted/30 disabled:opacity-50"
                      title="Add images (UI/UX designs)"
                    >
                      <ImageIcon className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <Button
                  onClick={() => handleSend()}
                  disabled={(!input.trim() && attachedFiles.length === 0) || isStreaming}
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
          </>
        )}
      </div>
    );
  }
);

ChatPanel.displayName = 'ChatPanel';
