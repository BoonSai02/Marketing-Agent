import api from './api';

const authService = {
    /**
     * Sign up a new user
     * @param {string} email - User email
     * @param {string} password - User password
     * @param {string} fullName - User full name
     * @returns {Promise} Response with user data
     */
    async signup(email, password, fullName) {
        try {
            const response = await api.post('/api/auth/signup', {
                email,
                password,
                full_name: fullName,
            });
            return response.data;
        } catch (error) {
            throw error;
        }
    },

    /**
     * Log in a user
     * @param {string} email - User email
     * @param {string} password - User password
     * @returns {Promise} Response with token and user data
     */
    async login(email, password) {
        try {
            const response = await api.post('/api/auth/login', {
                email,
                password,
            });

            const { access_token, user } = response.data;

            // Store token and user data
            if (access_token) {
                localStorage.setItem('access_token', access_token);
            }
            if (user) {
                localStorage.setItem('user', JSON.stringify(user));
            }

            return response.data;
        } catch (error) {
            throw error;
        }
    },

    /**
     * Request password reset
     * @param {string} email - User email
     * @returns {Promise} Response message
     */
    async forgotPassword(email) {
        try {
            const response = await api.post('/api/auth/forgot-password', {
                email,
            });
            return response.data;
        } catch (error) {
            throw error;
        }
    },

    /**
     * Reset password with token
     * @param {string} token - Reset token
     * @param {string} newPassword - New password
     * @param {string} confirmPassword - Confirm password
     * @returns {Promise} Response message
     */
    async resetPassword(token, newPassword, confirmPassword) {
        try {
            const response = await api.post('/api/auth/reset-password', {
                token,
                new_password: newPassword,
                confirm_password: confirmPassword,
            });
            return response.data;
        } catch (error) {
            throw error;
        }
    },

    /**
     * Log out the current user
     */
    logout() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
    },

    /**
     * Get current user from localStorage
     * @returns {Object|null} User object or null
     */
    getCurrentUser() {
        const userStr = localStorage.getItem('user');
        if (userStr) {
            try {
                return JSON.parse(userStr);
            } catch (e) {
                return null;
            }
        }
        return null;
    },

    /**
     * Check if user is authenticated
     * @returns {boolean} True if authenticated
     */
    isAuthenticated() {
        return !!localStorage.getItem('access_token');
    },
};

export default authService;
