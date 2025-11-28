import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { v4 as uuidv4 } from 'uuid';

const ChatInterface = () => {
    const [messages, setMessages] = useState([
        {
            id: 'welcome',
            role: 'ai',
            content: "Hello! I'm Emily, your personal marketing strategist. I'm so excited to help you launch your product! To get started, could you tell me a little bit about what you're building?",
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
    ]);
    const [inputValue, setInputValue] = useState('');
    const [isThinking, setIsThinking] = useState(false);
    const [showProductForm, setShowProductForm] = useState(false);
    const [sessionId] = useState(() => localStorage.getItem('chat_session_id') || uuidv4());
    const messagesEndRef = useRef(null);

    useEffect(() => {
        localStorage.setItem('chat_session_id', sessionId);
    }, [sessionId]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isThinking, showProductForm]);

    // Check for form trigger in the last AI message
    useEffect(() => {
        const lastMsg = messages[messages.length - 1];
        if (lastMsg?.role === 'ai' && lastMsg.content.includes('<SHOW_PRODUCT_FORM>')) {
            setShowProductForm(true);
        }
    }, [messages]);

    const handleSendMessage = async (text) => {
        if (!text.trim()) return;

        const newUserMsg = {
            id: uuidv4(),
            role: 'user',
            content: text,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };

        setMessages(prev => [...prev, newUserMsg]);
        setInputValue('');
        setIsThinking(true);
        setShowProductForm(false); // Hide form if they type manually

        try {
            const response = await fetch('http://localhost:8003/api/agent/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text, session_id: sessionId })
            });

            if (!response.ok) throw new Error('Network response was not ok');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let aiMsgId = uuidv4();
            let aiContent = '';

            // Add placeholder AI message
            setMessages(prev => [...prev, {
                id: aiMsgId,
                role: 'ai',
                content: '',
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            }]);

            setIsThinking(false); // Stop thinking, start streaming

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.trim()) {
                        try {
                            const data = JSON.parse(line);
                            if (data.response) {
                                aiContent += data.response; // Accumulate content
                                // Update the specific AI message
                                setMessages(prev => prev.map(m =>
                                    m.id === aiMsgId ? { ...m, content: aiContent } : m
                                ));
                            }
                        } catch (e) {
                            console.error('Error parsing chunk', e);
                        }
                    }
                }
            }

        } catch (error) {
            console.error('Error:', error);
            setIsThinking(false);
            setMessages(prev => [...prev, {
                id: uuidv4(),
                role: 'ai',
                content: "I'm having trouble connecting to the server. Please try again.",
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            }]);
        }
    };

    const handleFormSubmit = (formData) => {
        // Format the data as a single text block
        const formattedResponse =
            `Product Name: ${formData.productName}\n` +
            `Product Description: ${formData.productDescription}\n` +
            `Target Audience: ${formData.targetAudience}\n` +
            `Primary Goal: ${formData.primaryGoal}\n` +
            `Budget Range: ${formData.budgetRange}\n` +
            `Timeline: ${formData.timeline}\n` +
            `Industry: ${formData.industry}\n` +
            `Unique Selling Proposition (USP): ${formData.usp}\n` +
            `Current Marketing Channels: ${formData.marketingChannels.join(', ')}\n` +
            `Geography: ${formData.geography}`;

        handleSendMessage(formattedResponse);
    };

    return (
        <div className="flex flex-col h-screen bg-gray-50 font-sans text-gray-800">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center shadow-sm z-10">
                <span className="text-2xl mr-3">🚀</span>
                <div>
                    <h1 className="text-lg font-bold text-gray-900">Emily — Your Marketing Strategist</h1>
                    <p className="text-xs text-green-600 font-medium flex items-center">
                        <span className="w-2 h-2 bg-green-500 rounded-full mr-1.5"></span>
                        Online
                    </p>
                </div>
            </header>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
                {messages.map((msg) => {
                    // Filter out tags for display
                    let displayContent = msg.content.replace('<SHOW_PRODUCT_FORM>', '').trim();

                    // Extract buttons if present
                    const buttonMatch = displayContent.match(/<BUTTONS>(.*?)<\/BUTTONS>/);
                    let buttons = [];
                    if (buttonMatch) {
                        buttons = buttonMatch[1].split(',').map(b => b.trim());
                        displayContent = displayContent.replace(buttonMatch[0], '').trim();
                    }

                    if (!displayContent && buttons.length === 0) return null;

                    const isAi = msg.role === 'ai';
                    return (
                        <div key={msg.id} className={`flex flex-col ${isAi ? 'items-end' : 'items-start'}`}>
                            <div
                                className={`max-w-[85%] sm:max-w-[75%] rounded-2xl px-5 py-3.5 shadow-sm text-[15px] leading-relaxed
                  ${isAi
                                        ? 'bg-white text-gray-800 border border-gray-100 rounded-tr-none'
                                        : 'bg-blue-600 text-white rounded-tl-none'
                                    }`}
                            >
                                <ReactMarkdown
                                    components={{
                                        a: ({ node, ...props }) => <a {...props} className="text-blue-500 hover:underline" target="_blank" rel="noopener noreferrer" />,
                                        strong: ({ node, ...props }) => <strong {...props} className="font-semibold" />,
                                        ul: ({ node, ...props }) => <ul {...props} className="list-disc pl-4 my-2 space-y-1" />,
                                        ol: ({ node, ...props }) => <ol {...props} className="list-decimal pl-4 my-2 space-y-1" />,
                                        p: ({ node, ...props }) => <p {...props} className="mb-2 last:mb-0" />
                                    }}
                                >
                                    {displayContent}
                                </ReactMarkdown>
                            </div>

                            {/* Render Buttons */}
                            {buttons.length > 0 && (
                                <div className="mt-2 flex flex-wrap gap-2 justify-end">
                                    {buttons.map((btn, idx) => (
                                        <button
                                            key={idx}
                                            onClick={() => handleSendMessage(btn)}
                                            className="bg-blue-100 hover:bg-blue-200 text-blue-700 px-4 py-2 rounded-full text-sm font-medium transition-colors"
                                        >
                                            {btn}
                                        </button>
                                    ))}
                                </div>
                            )}

                            <span className="text-[11px] text-gray-400 mt-1.5 px-1">
                                {isAi ? 'Emily' : 'You'} • {msg.timestamp}
                            </span>
                        </div>
                    );
                })}

                {isThinking && (
                    <div className="flex flex-col items-end">
                        <div className="bg-white border border-gray-100 rounded-2xl rounded-tr-none px-5 py-4 shadow-sm">
                            <div className="flex space-x-1.5">
                                <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                                <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                                <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                            </div>
                        </div>
                        <span className="text-[11px] text-gray-400 mt-1.5 px-1">Emily is thinking...</span>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="bg-white border-t border-gray-200 p-4 sm:p-6">
                {showProductForm ? (
                    <ProductForm onSubmit={handleFormSubmit} onCancel={() => setShowProductForm(false)} />
                ) : (
                    <div className="max-w-4xl mx-auto relative">
                        <input
                            type="text"
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage(inputValue)}
                            placeholder="Type your message..."
                            className="w-full bg-gray-100 text-gray-800 placeholder-gray-500 border-0 rounded-full py-3.5 pl-5 pr-12 focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all shadow-inner"
                            disabled={isThinking}
                        />
                        <button
                            onClick={() => handleSendMessage(inputValue)}
                            disabled={!inputValue.trim() || isThinking}
                            className="absolute right-2 top-1/2 -translate-y-1/2 bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
                                <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
                            </svg>
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

// --- Sub-component: Product Form ---
const ProductForm = ({ onSubmit, onCancel }) => {
    const [formData, setFormData] = useState({
        productName: '',
        productDescription: '',
        targetAudience: '',
        primaryGoal: 'Brand Awareness',
        budgetRange: 'Not sure yet',
        timeline: '',
        industry: '',
        usp: '',
        marketingChannels: [],
        geography: ''
    });

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const toggleChannel = (channel) => {
        setFormData(prev => {
            const current = prev.marketingChannels;
            return {
                ...prev,
                marketingChannels: current.includes(channel)
                    ? current.filter(c => c !== channel)
                    : [...current, channel]
            };
        });
    };

    const channels = ['Instagram', 'TikTok', 'Google Ads', 'Email', 'LinkedIn', 'YouTube', 'SEO', 'None yet'];

    return (
        <div className="bg-white rounded-xl border border-gray-200 shadow-lg p-6 max-w-3xl mx-auto animate-fade-in-up">
            <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-bold text-gray-800">Tell me about your product</h3>
                <button onClick={onCancel} className="text-sm text-gray-500 hover:text-gray-800 underline">
                    Or type freely instead
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div className="col-span-1 md:col-span-2">
                    <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">Product Name *</label>
                    <input
                        name="productName"
                        value={formData.productName}
                        onChange={handleChange}
                        className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                        placeholder="e.g. GlowTrack"
                    />
                </div>

                <div className="col-span-1 md:col-span-2">
                    <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">Description *</label>
                    <textarea
                        name="productDescription"
                        value={formData.productDescription}
                        onChange={handleChange}
                        rows={3}
                        className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all resize-none"
                        placeholder="What does it do? Who is it for?"
                    />
                </div>

                <div>
                    <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">Target Audience</label>
                    <input
                        name="targetAudience"
                        value={formData.targetAudience}
                        onChange={handleChange}
                        className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-blue-500 outline-none"
                        placeholder="e.g. 25-40yo professionals"
                    />
                </div>

                <div>
                    <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">Primary Goal</label>
                    <select
                        name="primaryGoal"
                        value={formData.primaryGoal}
                        onChange={handleChange}
                        className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-blue-500 outline-none bg-white"
                    >
                        {["Brand Awareness", "Lead Generation", "Direct Sales", "Customer Retention", "App Downloads", "Other"].map(o => (
                            <option key={o} value={o}>{o}</option>
                        ))}
                    </select>
                </div>

                <div>
                    <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">Budget Range</label>
                    <select
                        name="budgetRange"
                        value={formData.budgetRange}
                        onChange={handleChange}
                        className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-blue-500 outline-none bg-white"
                    >
                        {["Under $5k", "$5k–$20k", "$20k–$50k", "$50k–$100k", "$100k+", "Not sure yet"].map(o => (
                            <option key={o} value={o}>{o}</option>
                        ))}
                    </select>
                </div>

                <div>
                    <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">Timeline</label>
                    <input
                        name="timeline"
                        value={formData.timeline}
                        onChange={handleChange}
                        className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-blue-500 outline-none"
                        placeholder="e.g. Q1 2025"
                    />
                </div>

                <div>
                    <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">Industry</label>
                    <input
                        name="industry"
                        value={formData.industry}
                        onChange={handleChange}
                        className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-blue-500 outline-none"
                        placeholder="e.g. SaaS, Healthtech"
                    />
                </div>

                <div className="col-span-1 md:col-span-2">
                    <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">Unique Selling Proposition (USP)</label>
                    <textarea
                        name="usp"
                        value={formData.usp}
                        onChange={handleChange}
                        rows={2}
                        className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-blue-500 outline-none resize-none"
                        placeholder="What makes it different?"
                    />
                </div>

                <div className="col-span-1 md:col-span-2">
                    <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Current Marketing Channels</label>
                    <div className="flex flex-wrap gap-2">
                        {channels.map(channel => (
                            <button
                                key={channel}
                                onClick={() => toggleChannel(channel)}
                                className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors border ${formData.marketingChannels.includes(channel)
                                    ? 'bg-blue-100 text-blue-700 border-blue-200'
                                    : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100'
                                    }`}
                            >
                                {channel}
                            </button>
                        ))}
                    </div>
                </div>

                <div>
                    <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">Geography</label>
                    <input
                        name="geography"
                        value={formData.geography}
                        onChange={handleChange}
                        className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-blue-500 outline-none"
                        placeholder="e.g. USA, Global"
                    />
                </div>
            </div>

            <div className="mt-8">
                <button
                    onClick={() => onSubmit(formData)}
                    disabled={!formData.productName || !formData.productDescription}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-xl transition-all shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    Submit Details
                </button>
            </div>
        </div>
    );
};

export default ChatInterface;
