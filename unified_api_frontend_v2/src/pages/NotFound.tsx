import { useLocation } from 'wouter';
import { Button } from '@/components/ui/button';

export default function NotFound() {
    const [, setLocation] = useLocation();

    return (
        <div className="min-h-screen flex items-center justify-center bg-background">
            <div className="text-center">
                <h1 className="text-9xl font-bold text-primary">404</h1>
                <h2 className="text-3xl font-semibold text-foreground mt-4 mb-2">
                    Page Not Found
                </h2>
                <p className="text-muted-foreground mb-8">
                    The page you're looking for doesn't exist or has been moved.
                </p>
                <Button onClick={() => setLocation('/')}>
                    Go Home
                </Button>
            </div>
        </div>
    );
}
