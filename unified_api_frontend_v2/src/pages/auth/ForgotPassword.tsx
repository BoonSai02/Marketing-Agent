import { useState } from 'react';
import { useLocation } from 'wouter';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { apiClient } from '@/lib/api';

export default function ForgotPassword() {
    const [, setLocation] = useLocation();
    const [step, setStep] = useState<'request' | 'reset'>('request');
    const [email, setEmail] = useState('');
    const [otp, setOtp] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleRequestReset = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);

        try {
            const response = await apiClient.forgotPassword({ email });

            if (response.success) {
                toast.success('Reset code sent to your email!');
                setStep('reset');
            } else {
                toast.error(response.message || 'Failed to send reset code');
            }
        } catch (error: any) {
            const errorMessage = error.response?.data?.detail || error.message || 'Failed to send reset code';
            toast.error(errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

    const handleResetPassword = async (e: React.FormEvent) => {
        e.preventDefault();

        if (newPassword !== confirmPassword) {
            toast.error('Passwords do not match');
            return;
        }

        if (newPassword.length < 6) {
            toast.error('Password must be at least 6 characters');
            return;
        }

        setIsLoading(true);

        try {
            const response = await apiClient.resetPassword({
                email,
                otp,
                new_password: newPassword,
                confirm_password: confirmPassword,
            });

            if (response.success) {
                toast.success('Password reset successfully!');
                setLocation('/auth/login');
            } else {
                toast.error(response.message || 'Password reset failed');
            }
        } catch (error: any) {
            const errorMessage = error.response?.data?.detail || error.message || 'Password reset failed';
            toast.error(errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-blue-50 to-white p-4">
            <Card className="w-full max-w-md">
                <CardHeader className="space-y-1">
                    <CardTitle className="text-2xl font-bold text-center">
                        {step === 'request' ? 'Forgot Password' : 'Reset Password'}
                    </CardTitle>
                    <CardDescription className="text-center">
                        {step === 'request'
                            ? 'Enter your email to receive a reset code'
                            : 'Enter the code and your new password'}
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {step === 'request' ? (
                        <form onSubmit={handleRequestReset} className="space-y-4">
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

                            <Button
                                type="submit"
                                className="w-full"
                                disabled={isLoading}
                            >
                                {isLoading ? 'Sending...' : 'Send Reset Code'}
                            </Button>
                        </form>
                    ) : (
                        <form onSubmit={handleResetPassword} className="space-y-4">
                            <div className="space-y-2">
                                <label htmlFor="otp" className="text-sm font-medium">
                                    Reset Code
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

                            <div className="space-y-2">
                                <label htmlFor="newPassword" className="text-sm font-medium">
                                    New Password
                                </label>
                                <Input
                                    id="newPassword"
                                    type="password"
                                    placeholder="At least 6 characters"
                                    value={newPassword}
                                    onChange={(e) => setNewPassword(e.target.value)}
                                    required
                                    disabled={isLoading}
                                />
                            </div>

                            <div className="space-y-2">
                                <label htmlFor="confirmPassword" className="text-sm font-medium">
                                    Confirm Password
                                </label>
                                <Input
                                    id="confirmPassword"
                                    type="password"
                                    placeholder="Confirm your password"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    required
                                    disabled={isLoading}
                                />
                            </div>

                            <Button
                                type="submit"
                                className="w-full"
                                disabled={isLoading}
                            >
                                {isLoading ? 'Resetting...' : 'Reset Password'}
                            </Button>
                        </form>
                    )}

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
