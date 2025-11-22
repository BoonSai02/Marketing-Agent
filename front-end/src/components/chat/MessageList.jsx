import { useEffect, useRef } from 'react';
import ChatMessage from './ChatMessage';
import './MessageList.css';

const MessageList = ({ messages, loading }) => {
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    return (
        <div className="message-list">
            {messages.length === 0 && !loading && (
                <div className="empty-state">
                    <div className="empty-icon">💬</div>
                    <h2>Start a Conversation</h2>
                    <p>Ask me anything about your marketing strategy!</p>
                </div>
            )}

            {messages.map((msg, index) => (
                <ChatMessage
                    key={index}
                    message={msg.content}
                    isUser={msg.isUser}
                />
            ))}

            {loading && (
                <div className="chat-message ai-message fade-in">
                    <div className="message-avatar">
                        <div className="avatar-ai">✨</div>
                    </div>
                    <div className="message-content">
                        <div className="typing-indicator">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    </div>
                </div>
            )}

            <div ref={messagesEndRef} />
        </div>
    );
};

export default MessageList;
