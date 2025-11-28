import React, { useState, useEffect } from 'react';
import './ThinkingBlock.css';

const ThinkingBlock = ({ thoughts, isFinished }) => {
    const [isOpen, setIsOpen] = useState(true);

    // Auto-collapse when finished, auto-expand when new thoughts arrive
    useEffect(() => {
        if (isFinished) {
            setIsOpen(false);
        } else {
            setIsOpen(true);
        }
    }, [isFinished]);

    if (!thoughts || thoughts.length === 0) return null;

    return (
        <div className="thinking-block">
            <div className="thinking-header" onClick={() => setIsOpen(!isOpen)}>
                <div className="thinking-title">
                    {isFinished ? (
                        <span className="thinking-icon done">✓</span>
                    ) : (
                        <span className="thinking-icon thinking-spinner">⟳</span>
                    )}
                    <span>{isFinished ? 'Research Completed' : 'Thinking...'}</span>
                </div>
                <span className={`thinking-chevron ${isOpen ? 'open' : ''}`}>▼</span>
            </div>

            {isOpen && (
                <div className="thinking-content">
                    {thoughts.map((thought, index) => (
                        <div key={index} className="thinking-step fade-in">
                            <span className="step-line">│</span>
                            <span className="step-text">{thought}</span>
                        </div>
                    ))}
                    {!isFinished && (
                        <div className="thinking-step pulse">
                            <span className="step-line">│</span>
                            <span className="step-text">...</span>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default ThinkingBlock;
