import { useState, useEffect } from 'react';
import chatService from '../../services/chatService';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import './ChatInterface.css';

const ChatInterface = () => {
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [sessionId, setSessionId] = useState(null);

    useEffect(() => {
        // Load session ID if exists
        const existingSession = chatService.getSessionId();
        if (existingSession) {
            setSessionId(existingSession);
        }
    }, []);

    const handleSendMessage = async (messageText) => {
        // Add user message to chat
        const userMessage = {
            content: messageText,
            isUser: true,
        };
        setMessages((prev) => [...prev, userMessage]);

        setLoading(true);

        try {
            const response = await chatService.sendMessage(messageText, sessionId);

            // Save session ID if new
            if (response.session_id && !sessionId) {
                setSessionId(response.session_id);
                chatService.saveSessionId(response.session_id);
            }

            // Add AI response to chat
            const aiMessage = {
                content: response.response,
                isUser: false,
            };
            setMessages((prev) => [...prev, aiMessage]);
        } catch (error) {
            // Add error message
            const errorMessage = {
                content: `Error: ${error.message || 'Failed to get response. Please try again.'}`,
                isUser: false,
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setLoading(false);
        }
    };

    const handleNewChat = () => {
        setMessages([]);
        setSessionId(null);
        chatService.clearSession();
    };

    return (
        <div className="chat-interface">
            <div className="chat-header">
                <div className="chat-header-content">
                    <h1 className="chat-title">
                        <span className="chat-icon">✨</span>
                        Marketing Agent
                    </h1>
                    <p className="chat-subtitle">Your AI-powered marketing assistant</p>
                </div>
                {messages.length > 0 && (
                    <button onClick={handleNewChat} className="new-chat-button">
                        + New Chat
                    </button>
                )}
            </div>

            <MessageList messages={messages} loading={loading} />
            <MessageInput onSend={handleSendMessage} disabled={loading} />
        </div>
    );
};

export default ChatInterface;
