import axios, { AxiosInstance } from 'axios';

// Get API URL from environment or use default
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface SignupRequest {
    email: string;
    password: string;
    full_name: string;
}

export interface LoginRequest {
    email: string;
    password: string;
}

export interface VerifyEmailRequest {
    email: string;
    otp: string;
}

export interface ForgotPasswordRequest {
    email: string;
}

export interface ResetPasswordRequest {
    email: string;
    otp: string;
    new_password: string;
    confirm_password: string;
}

export interface UserResponse {
    id: string;
    email: string;
    full_name?: string;
    is_active: boolean;
    created_at: string;
}

export interface SignupResponse {
    success: boolean;
    message: string;
    user?: UserResponse;
}

export interface LoginResponse {
    success: boolean;
    message: string;
    access_token?: string;
    token_type?: string;
    user?: UserResponse;
}

export interface MessageResponse {
    success: boolean;
    message: string;
}

export interface ChatRequest {
    message: string;
    session_id?: string;
}

export interface ChatResponse {
    response: string;
    session_id: string;
    is_complete: boolean;
    strategies?: string[];
}

export interface SessionMetadata {
    id: string;
    session_id: string;
    title: string;
    created_at: string;
    updated_at: string;
}

class APIClient {
    private client: AxiosInstance;
    private token: string | null = null;

    constructor() {
        this.client = axios.create({
            baseURL: API_BASE_URL,
            headers: {
                'Content-Type': 'application/json',
            },
        });

        // Load token from localStorage on initialization
        this.token = localStorage.getItem('auth_token');
        if (this.token) {
            this.setAuthToken(this.token);
        }

        // Add response interceptor for error handling
        this.client.interceptors.response.use(
            (response) => response,
            (error) => {
                if (error.response?.status === 401) {
                    // Token expired or invalid
                    this.clearAuth();
                    window.location.href = '/auth/login';
                }
                return Promise.reject(error);
            }
        );
    }

    setAuthToken(token: string) {
        this.token = token;
        this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        localStorage.setItem('auth_token', token);
    }

    clearAuth() {
        this.token = null;
        delete this.client.defaults.headers.common['Authorization'];
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
    }

    getToken(): string | null {
        return this.token;
    }

    // Auth endpoints
    async signup(data: SignupRequest): Promise<SignupResponse> {
        const response = await this.client.post<SignupResponse>('/api/auth/signup', data);
        return response.data;
    }

    async login(data: LoginRequest): Promise<LoginResponse> {
        const response = await this.client.post<LoginResponse>('/api/auth/login', data);
        if (response.data.access_token) {
            this.setAuthToken(response.data.access_token);
            if (response.data.user) {
                localStorage.setItem('user', JSON.stringify(response.data.user));
            }
        }
        return response.data;
    }

    async verifyEmail(data: VerifyEmailRequest): Promise<MessageResponse> {
        const response = await this.client.post<MessageResponse>('/api/auth/verify-email', data);
        return response.data;
    }

    async forgotPassword(data: ForgotPasswordRequest): Promise<MessageResponse> {
        const response = await this.client.post<MessageResponse>('/api/auth/forgot-password', data);
        return response.data;
    }

    async resetPassword(data: ResetPasswordRequest): Promise<MessageResponse> {
        const response = await this.client.post<MessageResponse>('/api/auth/reset-password', data);
        return response.data;
    }

    async googleLogin(): Promise<void> {
        window.location.href = `${API_BASE_URL}/api/auth/google/login`;
    }

    // Agent endpoints
    async chat(data: ChatRequest): Promise<ChatResponse> {
        const response = await this.client.post<ChatResponse>('/api/agent/chat', data);
        return response.data;
    }

    async getSessions(): Promise<SessionMetadata[]> {
        const response = await this.client.get<SessionMetadata[]>('/api/agent/sessions');
        return response.data;
    }

    async getHistory(session_id?: string): Promise<{ messages: { content: string; isUser: boolean }[]; session_id: string | null }> {
        const response = await this.client.get<{ messages: { content: string; isUser: boolean }[]; session_id: string | null }>('/api/agent/history', {
            params: { session_id }
        });
        return response.data;
    }

    async healthCheck(): Promise<{ status: string; message: string }> {
        const response = await this.client.get('/health');
        return response.data;
    }
}

export const apiClient = new APIClient();
