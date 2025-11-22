import ReactMarkdown from 'react-markdown';
import './ChatMessage.css';

const ChatMessage = ({ message, isUser }) => {
    return (
        <div className={`chat-message ${isUser ? 'user-message' : 'ai-message'} fade-in`}>
            <div className="message-avatar">
                {isUser ? (
                    <div className="avatar-user">You</div>
                ) : (
                    <div className="avatar-ai">✨</div>
                )}
            </div>
            <div className="message-content">
                {isUser ? (
                    <div className="message-text">{message}</div>
                ) : (
                    <div className="message-text markdown-content">
                        <ReactMarkdown>{message}</ReactMarkdown>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ChatMessage;
