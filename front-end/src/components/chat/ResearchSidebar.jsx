import React from 'react';
import './ResearchSidebar.css';

const ResearchSidebar = ({ isOpen, logs, onClose }) => {
    return (
        <div className={`research-sidebar ${isOpen ? 'open' : ''}`}>
            <div className="sidebar-header">
                <h3>🔍 Deep Research</h3>
                <button className="close-sidebar-btn" onClick={onClose}>&times;</button>
            </div>
            <div className="sidebar-content">
                {logs.length === 0 ? (
                    <p className="placeholder-text">Waiting for research tasks...</p>
                ) : (
                    <ul className="log-list">
                        {logs.map((log, index) => (
                            <li key={index} className="log-item fade-in">
                                <span className="log-icon">
                                    {log.includes('Searching') ? '🌐' : '✅'}
                                </span>
                                <span className="log-text">{log}</span>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
};

export default ResearchSidebar;
