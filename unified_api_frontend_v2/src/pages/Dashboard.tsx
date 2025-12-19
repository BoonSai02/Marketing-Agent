import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import { useAuth } from '@/contexts/AuthContext';
import { useLocation } from 'wouter';
import { apiClient, ChatResponse } from '@/lib/api';
import { toast } from 'sonner';
import { Send, LogOut, Plus } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
}

interface ChatSession {
    id: string;
    title: string;
    messages: Message[];
    createdAt: Date;
}

export default function Dashboard() {
    const { user, logout } = useAuth();
    const [, setLocation] = useLocation();
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Load sessions on mount
    useEffect(() => {
        const loadSessions = async () => {
            try {
                const sessionList = await apiClient.getSessions();
                if (sessionList.length > 0) {
                    // Convert metadata to ChatSession (initially without messages)
                    const chatSessions: ChatSession[] = sessionList.map(s => ({
                        id: s.session_id,
                        title: s.title || 'Chat',
                        messages: [], // Will load on select
                        createdAt: new Date(s.created_at)
                    }));
                    setSessions(chatSessions);
                    // Select the most recent session
                    setCurrentSessionId(chatSessions[0].id);
                } else {
                    handleNewChat();
                }
            } catch (error) {
                console.error('Failed to load sessions:', error);
                handleNewChat();
            }
        };
        loadSessions();
    }, []);

    // Scroll to bottom when messages change
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Load history when currentSessionId changes
    useEffect(() => {
        const loadHistory = async () => {
            if (!currentSessionId) return;

            // If it's a new local session, don't fetch history
            if (currentSessionId.startsWith('session-')) {
                setMessages([]);
                return;
            }

            // Check if we already have messages for this session in state (optimization)
            // Actually, better to fetch fresh history to ensure sync
            try {
                const history = await apiClient.getHistory(currentSessionId);
                if (history.messages) {
                    const formattedMessages: Message[] = history.messages.map((msg, index) => ({
                        id: `msg-${index}-${Date.now()}`,
                        role: msg.isUser ? 'user' : 'assistant',
                        content: msg.content,
                        timestamp: new Date(), // Backend doesn't return timestamp yet
                    }));
                    setMessages(formattedMessages);

                    // Update session in list with messages
                    setSessions(prev => prev.map(s =>
                        s.id === currentSessionId ? { ...s, messages: formattedMessages } : s
                    ));
                }
            } catch (error) {
                console.error('Failed to load history for session:', currentSessionId, error);
                toast.error('Failed to load chat history');
            }
        };

        loadHistory();
    }, [currentSessionId]);

    const handleSendMessage = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!inputValue.trim() || !currentSessionId) {
            return;
        }

        const userMessage: Message = {
            id: `msg-${Date.now()}`,
            role: 'user',
            content: inputValue,
            timestamp: new Date(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setInputValue('');
        setIsLoading(true);

        try {
            // If it's a new local session (starts with 'session-'), don't send ID to backend
            // The backend will generate a proper UUID
            const isNewSession = currentSessionId?.startsWith('session-');

            const response: ChatResponse = await apiClient.chat({
                message: inputValue,
                session_id: isNewSession ? undefined : currentSessionId,
            });

            const assistantMessage: Message = {
                id: `msg-${Date.now() + 1}`,
                role: 'assistant',
                content: response.response || 'No response received',
                timestamp: new Date(),
            };

            setMessages((prev) => [...prev, assistantMessage]);

            // Update session with real UUID from backend if it was a new session
            if (isNewSession && response.session_id) {
                const newId = response.session_id;
                const newTitle = inputValue.substring(0, 30) + (inputValue.length > 30 ? '...' : '');

                // Update current ID
                setCurrentSessionId(newId);

                // Update session list
                setSessions((prev) =>
                    prev.map((session) => {
                        if (session.id === currentSessionId) {
                            return {
                                ...session,
                                id: newId,
                                title: newTitle,
                                messages: [...messages, userMessage, assistantMessage], // Use current messages + new ones
                            };
                        }
                        return session;
                    })
                );
            } else {
                // Existing session, just update messages in session list too
                setSessions((prev) =>
                    prev.map((session) => {
                        if (session.id === currentSessionId) {
                            return {
                                ...session,
                                messages: [...messages, userMessage, assistantMessage],
                            };
                        }
                        return session;
                    })
                );
            }

            if (response.is_complete) {
                toast.success('Chat session completed');
            }
        } catch (error: any) {
            const errorMessage = error.response?.data?.detail || error.message || 'Failed to send message';
            toast.error(errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

    const handleNewChat = () => {
        const newSessionId = `session-${Date.now()}`;
        const newSession: ChatSession = {
            id: newSessionId,
            title: 'New Chat',
            messages: [],
            createdAt: new Date(),
        };
        setSessions((prev) => [newSession, ...prev]);
        setCurrentSessionId(newSessionId);
    };

    const handleLogout = () => {
        logout();
        setLocation('/auth/login');
    };

    const currentSession = sessions.find((s) => s.id === currentSessionId);

    return (
        <div className="flex h-screen bg-background">
            {/* Sidebar */}
            <div className="w-64 border-r border-border bg-card flex flex-col">
                <div className="p-4 border-b border-border">
                    <Button onClick={handleNewChat} className="w-full" variant="default">
                        <Plus className="w-4 h-4 mr-2" />
                        New Chat
                    </Button>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-2">
                    {sessions.map((session) => (
                        <button
                            key={session.id}
                            onClick={() => setCurrentSessionId(session.id)}
                            className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${currentSessionId === session.id
                                ? 'bg-primary text-primary-foreground'
                                : 'hover:bg-muted text-foreground'
                                }`}
                        >
                            <div className="truncate text-sm font-medium">{session.title}</div>
                            <div className="text-xs opacity-70">
                                {session.createdAt.toLocaleDateString()}
                            </div>
                        </button>
                    ))}
                </div>

                <Separator />

                <div className="p-4 border-t border-border space-y-2">
                    <div className="text-sm">
                        <div className="font-medium text-foreground">{user?.full_name || user?.email}</div>
                        <div className="text-xs text-muted-foreground">{user?.email}</div>
                    </div>
                    <Button
                        onClick={handleLogout}
                        variant="outline"
                        className="w-full"
                        size="sm"
                    >
                        <LogOut className="w-4 h-4 mr-2" />
                        Logout
                    </Button>
                </div>
            </div>

            {/* Main Chat Area */}
            <div className="flex-1 flex flex-col">
                {/* Header */}
                <div className="border-b border-border bg-card p-4">
                    <h1 className="text-xl font-semibold text-foreground">
                        {currentSession?.title || 'Chat'}
                    </h1>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {messages.length === 0 ? (
                        <div className="h-full flex items-center justify-center">
                            <div className="text-center">
                                <div className="text-4xl mb-4">💬</div>
                                <h2 className="text-xl font-semibold text-foreground mb-2">
                                    Start a Conversation
                                </h2>
                                <p className="text-muted-foreground max-w-md">
                                    Ask me anything! I'm here to help with marketing strategies, content ideas, and more.
                                </p>
                            </div>
                        </div>
                    ) : (
                        messages.map((message) => (
                            <div
                                key={message.id}
                                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                            >
                                <div
                                    className={`max-w-2xl px-4 py-3 rounded-lg ${message.role === 'user'
                                        ? 'bg-primary text-primary-foreground'
                                        : 'bg-muted text-foreground'
                                        }`}
                                >
                                    <div className="text-sm">
                                        <ReactMarkdown
                                            components={{
                                                p: ({ children }) => <p className="mb-2">{children}</p>,
                                                strong: ({ children }) => <strong className="font-bold">{children}</strong>,
                                                em: ({ children }) => <em className="italic">{children}</em>,
                                                ul: ({ children }) => <ul className="list-disc list-inside mb-2">{children}</ul>,
                                                ol: ({ children }) => <ol className="list-decimal list-inside mb-2">{children}</ol>,
                                                li: ({ children }) => <li className="mb-1">{children}</li>,
                                                code: ({ children }) => <code className="bg-black/10 px-1 py-0.5 rounded text-xs">{children}</code>,
                                            }}
                                        >
                                            {message.content}
                                        </ReactMarkdown>
                                    </div>
                                    <div className="text-xs opacity-70 mt-2">
                                        {message.timestamp.toLocaleTimeString([], {
                                            hour: '2-digit',
                                            minute: '2-digit',
                                        })}
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                    {isLoading && (
                        <div className="flex justify-start">
                            <div className="bg-muted text-foreground px-4 py-2 rounded-lg">
                                <div className="flex space-x-2">
                                    <div className="w-2 h-2 bg-current rounded-full animate-bounce"></div>
                                    <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                                    <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input */}
                <div className="border-t border-border bg-card p-4">
                    <form onSubmit={handleSendMessage} className="flex gap-2">
                        <Input
                            type="text"
                            placeholder="Type your message..."
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            disabled={isLoading}
                            className="flex-1"
                        />
                        <Button
                            type="submit"
                            disabled={isLoading || !inputValue.trim()}
                            size="icon"
                        >
                            <Send className="w-4 h-4" />
                        </Button>
                    </form>
                </div>
            </div>
        </div>
    );
}
