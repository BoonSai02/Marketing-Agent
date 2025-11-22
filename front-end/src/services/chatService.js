import api from './api';

const chatService = {
    /**
     * Send a message to the AI agent
     * @param {string} message - User message
     * @param {string|null} sessionId - Optional session ID for conversation continuity
     * @returns {Promise} Response with AI message and session info
     */
    async sendMessage(message, sessionId = null) {
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
