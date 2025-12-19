import { useAuth } from '@/contexts/AuthContext';
import { useLocation } from 'wouter';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { MessageCircle, Zap, Shield, BarChart3 } from 'lucide-react';
import { useEffect } from 'react';

export default function Home() {
    const { isAuthenticated } = useAuth();
    const [, setLocation] = useLocation();

    useEffect(() => {
        if (isAuthenticated) {
            setLocation('/dashboard');
        }
    }, [isAuthenticated, setLocation]);

    if (isAuthenticated) {
        return null;
    }

    return (
        <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
            {/* Header */}
            <header className="border-b border-border bg-white/80 backdrop-blur-sm sticky top-0 z-50">
                <div className="container max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
                    <div className="text-2xl font-bold text-primary">Unified API</div>
                    <div className="flex gap-4">
                        <Button
                            variant="outline"
                            onClick={() => setLocation('/auth/login')}
                        >
                            Login
                        </Button>
                        <Button onClick={() => setLocation('/auth/signup')}>
                            Sign Up
                        </Button>
                    </div>
                </div>
            </header>

            {/* Hero Section */}
            <section className="container max-w-6xl mx-auto px-4 py-20 text-center">
                <h1 className="text-5xl font-bold text-foreground mb-6">
                    AI-Powered Marketing Assistant
                </h1>
                <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
                    Unlock the power of intelligent marketing strategies with our advanced AI agent.
                    Get personalized recommendations and insights tailored to your business needs.
                </p>
                <div className="flex gap-4 justify-center">
                    <Button size="lg" onClick={() => setLocation('/auth/signup')}>
                        Get Started
                    </Button>
                    <Button size="lg" variant="outline">
                        Learn More
                    </Button>
                </div>
            </section>

            {/* Features Section */}
            <section className="py-20 bg-white">
                <div className="container max-w-6xl mx-auto px-4">
                    <h2 className="text-3xl font-bold text-center text-foreground mb-12">
                        Why Choose Us?
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        <Card>
                            <CardHeader>
                                <MessageCircle className="w-8 h-8 text-primary mb-2" />
                                <CardTitle>Smart Chat</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <CardDescription>
                                    Engage with our intelligent AI assistant for real-time marketing insights
                                </CardDescription>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardHeader>
                                <Zap className="w-8 h-8 text-primary mb-2" />
                                <CardTitle>Fast & Reliable</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <CardDescription>
                                    Get instant responses powered by cutting-edge AI technology
                                </CardDescription>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardHeader>
                                <Shield className="w-8 h-8 text-primary mb-2" />
                                <CardTitle>Secure</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <CardDescription>
                                    Your data is protected with enterprise-grade security measures
                                </CardDescription>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardHeader>
                                <BarChart3 className="w-8 h-8 text-primary mb-2" />
                                <CardTitle>Analytics</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <CardDescription>
                                    Track your marketing performance with detailed analytics
                                </CardDescription>
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="py-20 bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
                <div className="container max-w-6xl mx-auto px-4 text-center">
                    <h2 className="text-4xl font-bold mb-6">Ready to Transform Your Marketing?</h2>
                    <p className="text-xl mb-8 opacity-90">
                        Join thousands of businesses using AI to drive growth
                    </p>
                    <Button
                        size="lg"
                        variant="secondary"
                        onClick={() => setLocation('/auth/signup')}
                    >
                        Start Free Trial
                    </Button>
                </div>
            </section>

            {/* Footer */}
            <footer className="border-t border-border bg-white py-8">
                <div className="container max-w-6xl mx-auto px-4 text-center text-muted-foreground">
                    <p>&copy; 2024 Unified API. All rights reserved.</p>
                </div>
            </footer>
        </div>
    );
}
