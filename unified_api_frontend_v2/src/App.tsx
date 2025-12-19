import { Route, Switch } from 'wouter';
import ErrorBoundary from './components/ErrorBoundary';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Toaster } from './components/ui/sonner';

// Pages
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import Login from './pages/auth/Login';
import Signup from './pages/auth/Signup';
import VerifyEmail from './pages/auth/VerifyEmail';
import ForgotPassword from './pages/auth/ForgotPassword';
import OAuthCallback from './pages/auth/OAuthCallback';
import NotFound from './pages/NotFound';

function Router() {
    return (
        <Switch>
            <Route path="/" component={Home} />
            <Route path="/auth/login" component={Login} />
            <Route path="/auth/signup" component={Signup} />
            <Route path="/auth/verify-email" component={VerifyEmail} />
            <Route path="/auth/forgot-password" component={ForgotPassword} />
            <Route path="/auth/callback" component={OAuthCallback} />
            <Route path="/dashboard">
                {() => (
                    <ProtectedRoute>
                        <Dashboard />
                    </ProtectedRoute>
                )}
            </Route>
            <Route path="/404" component={NotFound} />
            <Route component={NotFound} />
        </Switch>
    );
}

function App() {
    return (
        <ErrorBoundary>
            <ThemeProvider defaultTheme="light">
                <AuthProvider>
                    <Toaster />
                    <Router />
                </AuthProvider>
            </ThemeProvider>
        </ErrorBoundary>
    );
}

export default App;
