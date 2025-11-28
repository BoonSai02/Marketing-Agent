import api from './api';

const API_URL = 'http://localhost:8002';

const chatService = {
    /**
     * Send a message to the AI agent
     * @param {string} message - User message
     * @param {string|null} sessionId - Optional session ID for conversation continuity
     * @returns {Promise} Response with AI message and session info
     */
    async sendMessage(message, sessionId = null) {
        // Legacy method kept for compatibility if needed, but UI should use stream
        try {
            const response = await api.post('/api/agent/chat', {
                message,
                session_id: sessionId,
            });
            return response.data;
        } catch (error) {
            throw error;
        }
    },

    async *sendMessageStream(message, sessionId = null) {
        const response = await fetch(`${API_URL}/api/agent/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message,
                session_id: sessionId,
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');

            // Process all complete lines
            buffer = lines.pop() || ''; // Keep the last incomplete line in buffer

            for (const line of lines) {
                if (line.trim()) {
                    try {
                        yield JSON.parse(line);
                    } catch (e) {
                        console.error('Error parsing JSON chunk:', e);
                    }
                }
            }
        }
    },

    /**
     * Get session ID from localStorage
     * @returns {string|null} Session ID or null
     */
    getSessionId() {
        return localStorage.getItem('chat_session_id');
    },

    /**
     * Save session ID to localStorage
     * @param {string} sessionId - Session ID to save
     */
    saveSessionId(sessionId) {
        localStorage.setItem('chat_session_id', sessionId);
    },

    /**
     * Clear current session
     */
    clearSession() {
        localStorage.removeItem('chat_session_id');
    },
};

export default chatService;
