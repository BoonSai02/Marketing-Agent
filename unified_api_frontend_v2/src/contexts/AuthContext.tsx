import React, { createContext, useContext, useState, useEffect } from 'react';
import { UserResponse, apiClient } from '@/lib/api';

interface AuthContextType {
    user: UserResponse | null;
    token: string | null;
    isLoading: boolean;
    isAuthenticated: boolean;
    login: (user: UserResponse, token: string) => void;
    logout: () => void;
    setUser: (user: UserResponse | null) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<UserResponse | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Initialize from localStorage
    useEffect(() => {
        const storedToken = localStorage.getItem('auth_token');
        const storedUser = localStorage.getItem('user');

        if (storedToken && storedUser) {
            try {
                setToken(storedToken);
                setUser(JSON.parse(storedUser));
            } catch (error) {
                console.error('Failed to parse stored user:', error);
                localStorage.removeItem('auth_token');
                localStorage.removeItem('user');
            }
        }
        setIsLoading(false);
    }, []);



    const login = (userData: UserResponse, authToken: string) => {
        setUser(userData);
        setToken(authToken);
        localStorage.setItem('auth_token', authToken);
        localStorage.setItem('user', JSON.stringify(userData));
        apiClient.setAuthToken(authToken);
    };

    const logout = () => {
        setUser(null);
        setToken(null);
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
        apiClient.clearAuth();
    };

    const value: AuthContextType = {
        user,
        token,
        isLoading,
        isAuthenticated: !!token && !!user,
        login,
        logout,
        setUser,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
