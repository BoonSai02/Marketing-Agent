import { useState } from 'react';
import { useLocation } from 'wouter';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { apiClient } from '@/lib/api';

export default function VerifyEmail() {
    const [, setLocation] = useLocation();
    const [email, setEmail] = useState('');
    const [otp, setOtp] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);

        try {
            const response = await apiClient.verifyEmail({ email, otp });

            if (response.success) {
                toast.success('Email verified successfully!');
                setLocation('/auth/login');
            } else {
                toast.error(response.message || 'Verification failed');
            }
        } catch (error: any) {
            const errorMessage = error.response?.data?.detail || error.message || 'Verification failed';
            toast.error(errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-blue-50 to-white p-4">
            <Card className="w-full max-w-md">
                <CardHeader className="space-y-1">
                    <CardTitle className="text-2xl font-bold text-center">Verify Email</CardTitle>
                    <CardDescription className="text-center">
                        Enter the verification code sent to your email
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="space-y-2">
                            <label htmlFor="email" className="text-sm font-medium">
                                Email
                            </label>
                            <Input
                                id="email"
                                type="email"
                                placeholder="name@example.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                disabled={isLoading}
                            />
                        </div>

                        <div className="space-y-2">
                            <label htmlFor="otp" className="text-sm font-medium">
                                Verification Code
                            </label>
                            <Input
                                id="otp"
                                type="text"
                                placeholder="Enter 6-digit code"
                                value={otp}
                                onChange={(e) => setOtp(e.target.value)}
                                required
                                disabled={isLoading}
                                maxLength={6}
                            />
                        </div>

                        <Button
                            type="submit"
                            className="w-full"
                            disabled={isLoading}
                        >
                            {isLoading ? 'Verifying...' : 'Verify Email'}
                        </Button>
                    </form>

                    <div className="mt-4 text-center text-sm">
                        <button
                            onClick={() => setLocation('/auth/login')}
                            className="text-primary hover:underline font-medium"
                        >
                            Back to Login
                        </button>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
