import { useEffect, useState } from 'react';
import { useLocation } from 'wouter';
import { toast } from 'sonner';
import { useAuth } from '@/contexts/AuthContext';

export default function OAuthCallback() {
    const [, setLocation] = useLocation();
    const { login, isAuthenticated } = useAuth();
    const [debugInfo, setDebugInfo] = useState<string>('Initializing...');
    const [errorState, setErrorState] = useState<string | null>(null);

    useEffect(() => {
        if (isAuthenticated) {
            setDebugInfo('Authenticated! Redirecting to dashboard...');
            setTimeout(() => setLocation('/dashboard'), 1000); // Small delay to see the success message
        }
    }, [isAuthenticated, setLocation]);

    useEffect(() => {
        const handleOAuthCallback = () => {
            const params = new URLSearchParams(window.location.search);
            const token = params.get('token');
            const userStr = params.get('user');
            const error = params.get('error');

            setDebugInfo(`Params received - Token: ${!!token}, User: ${!!userStr}, Error: ${error}`);

            if (error) {
                const errorMsg = error || 'OAuth authentication failed';
                setErrorState(errorMsg);
                toast.error(errorMsg);
                return;
            }

            if (token && userStr) {
                try {
                    const user = JSON.parse(decodeURIComponent(userStr));
                    setDebugInfo(`User parsed successfully: ${user.email}`);
                    // Update auth context and storage
                    login(user, token);
                    toast.success('Login successful!');
                    // Redirect handled by useEffect above
                } catch (e: any) {
                    console.error('Failed to parse user data', e);
                    const errorMsg = `Failed to parse user data: ${e.message}`;
                    setErrorState(errorMsg);
                    toast.error(errorMsg);
                }
            } else {
                if (!isAuthenticated) {
                    const msg = 'Missing token or user data in URL';
                    setDebugInfo(msg);
                    setErrorState(msg);
                }
            }
        };

        if (!isAuthenticated) {
            handleOAuthCallback();
        }
    }, [setLocation, login, isAuthenticated]);

    return (
        <div className="min-h-screen flex flex-col items-center justify-center p-4">
            <div className="text-center max-w-lg w-full">
                {errorState ? (
                    <div className="bg-destructive/10 text-destructive p-4 rounded-md mb-4">
                        <h3 className="font-bold text-lg mb-2">Authentication Failed</h3>
                        <p>{errorState}</p>
                        <p className="text-xs mt-2 text-muted-foreground font-mono">{debugInfo}</p>
                        <button
                            onClick={() => setLocation('/auth/login')}
                            className="mt-4 bg-primary text-primary-foreground px-4 py-2 rounded hover:bg-primary/90"
                        >
                            Back to Login
                        </button>
                    </div>
                ) : (
                    <>
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
                        <p className="text-muted-foreground mb-2">Completing authentication...</p>
                        <p className="text-xs text-muted-foreground font-mono bg-muted p-2 rounded break-all">
                            {debugInfo}
                        </p>
                    </>
                )}
            </div>
        </div>
    );
}
