import { useEffect, useRef } from 'react';
import ChatMessage from './ChatMessage';
import './MessageList.css';

const MessageList = ({ messages, loading, onSend }) => {
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, loading]);

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
                    message={msg}
                    onSend={onSend}
                />
            ))}

            <div ref={messagesEndRef} />
        </div>
    );
};

export default MessageList;
