import React from 'react';
import ReactMarkdown from 'react-markdown';
import ProductForm from './ProductForm';
import ThinkingBlock from './ThinkingBlock';
import './ChatMessage.css';

const ChatMessage = ({ message, onSend }) => {
    const isUser = message.isUser;
    const content = message.content || '';
    const showForm = content.includes('<SHOW_PRODUCT_FORM>');
    const cleanContent = content.replace('<SHOW_PRODUCT_FORM>', '').trim();

    return (
        <div className={`message-container ${isUser ? 'user-message' : 'ai-message'}`}>
            <div className="message-bubble">
                {!isUser && Array.isArray(message.thoughts) && message.thoughts.length > 0 && (
                    <ThinkingBlock thoughts={message.thoughts} isFinished={!message.isLoading} />
                )}

                {cleanContent && (
                    <div className="markdown-content">
                        <ReactMarkdown>{cleanContent}</ReactMarkdown>
                    </div>
                )}

                {showForm && (
                    <div className="form-container">
                        <ProductForm onSubmit={(details) => onSend(details)} />
                    </div>
                )}
            </div>
        </div>
    );
};

export default ChatMessage;
