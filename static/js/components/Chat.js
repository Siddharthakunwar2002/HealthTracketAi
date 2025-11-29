import React, { useState, useRef, useEffect } from 'react';
import '../styles.css';

const Chat = () => {
    const [messages, setMessages] = useState([
        { 
            type: 'bot', 
            content: "Hello! 👋 I'm your AI health assistant. I can help you with:\n\n" +
                    "• General health advice\n" +
                    "• Symptom checking\n" +
                    "• Wellness tips\n" +
                    "• Exercise recommendations\n" +
                    "• Nutrition guidance\n\n" +
                    "What would you like to know about today?"
        }
    ]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [suggestions, setSuggestions] = useState([
        "What are the symptoms of common cold?",
        "How can I improve my sleep?",
        "What's a healthy diet plan?",
        "Tips for stress management"
    ]);
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const messagesEndRef = useRef(null);
    const textareaRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;

        // Add user message with animation
        const userMessage = { type: 'user', content: input };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsTyping(true);

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: input }),
            });

            const data = await response.json();
            
            if (data.status === 'success') {
                setMessages(prev => [...prev, { type: 'bot', content: data.response }]);
            } else {
                setMessages(prev => [...prev, { 
                    type: 'bot', 
                    content: "I apologize, but I'm having trouble processing your request right now. Please try again later." 
                }]);
            }
        } catch (error) {
            setMessages(prev => [...prev, { 
                type: 'bot', 
                content: "I apologize, but I'm having trouble connecting to the server. Please try again later." 
            }]);
        } finally {
            setIsTyping(false);
        }
    };

    const handleSuggestionClick = (suggestion) => {
        setInput(suggestion);
        textareaRef.current?.focus();
    };

    const formatMessage = (content) => {
        return content.split('\n').map((line, i) => (
            <React.Fragment key={i}>
                {line}
                <br />
            </React.Fragment>
        ));
    };

    return (
        <div className="chat-page">
            <div className={`chat-sidebar ${isSidebarOpen ? 'open' : 'closed'}`}>
                <button 
                    className="sidebar-toggle"
                    onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                >
                    {isSidebarOpen ? '←' : '→'}
                </button>
                <div className="sidebar-content">
                    <div className="sidebar-section">
                        <h3>Quick Tips</h3>
                        <ul>
                            <li>Be specific with your questions</li>
                            <li>Include relevant symptoms</li>
                            <li>Ask about prevention methods</li>
                            <li>Request lifestyle recommendations</li>
                        </ul>
                    </div>
                    <div className="sidebar-section">
                        <h3>Topics I Can Help With</h3>
                        <ul>
                            <li>General Health</li>
                            <li>Mental Wellness</li>
                            <li>Physical Fitness</li>
                            <li>Nutrition</li>
                            <li>Sleep Health</li>
                            <li>Stress Management</li>
                        </ul>
                    </div>
                </div>
            </div>
            <div className="chat-main">
                <div className="chat-container">
                    <div className="chat-header">
                        <div className="chat-title">
                            <h2>Health Assistant</h2>
                            <span className="status-indicator online"></span>
                        </div>
                    </div>
                    <div className="chat-messages">
                        {messages.map((message, index) => (
                            <div 
                                key={index} 
                                className={`message ${message.type}-message animate-in`}
                            >
                                {formatMessage(message.content)}
                            </div>
                        ))}
                        {isTyping && (
                            <div className="typing-indicator animate-in">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>
                    <div className="suggestions-container">
                        {suggestions.map((suggestion, index) => (
                            <button
                                key={index}
                                className="suggestion-button"
                                onClick={() => handleSuggestionClick(suggestion)}
                            >
                                {suggestion}
                            </button>
                        ))}
                    </div>
                    <form className="message-input" onSubmit={handleSubmit}>
                        <textarea
                            ref={textareaRef}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Type your health-related question here..."
                            rows="1"
                            onKeyPress={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSubmit(e);
                                }
                            }}
                        />
                        <button type="submit" disabled={!input.trim() || isTyping}>
                            Send
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default Chat; 