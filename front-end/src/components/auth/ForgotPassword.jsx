import { useState } from 'react';
import { Link } from 'react-router-dom';
import authService from '../../services/authService';
import Input from '../common/Input';
import Button from '../common/Button';
import './Auth.css';

const ForgotPassword = () => {
    const [email, setEmail] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!email) {
            setError('Email is required');
            return;
        }

        if (!/\S+@\S+\.\S+/.test(email)) {
            setError('Email is invalid');
            return;
        }

        setLoading(true);
        setError('');

        try {
            await authService.forgotPassword(email);
            setSuccess(true);
        } catch (error) {
            setError(error.message || 'Failed to send reset email. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    if (success) {
        return (
            <div className="auth-container">
                <div className="auth-card glass fade-in">
                    <div className="auth-header">
                        <div className="success-icon">✓</div>
                        <h1 className="auth-title">Check Your Email</h1>
                        <p className="auth-subtitle">
                            If an account exists with this email, we've sent a password reset link to <strong>{email}</strong>
                        </p>
                    </div>

                    <div className="auth-footer">
                        <Link to="/login" className="auth-link-primary">
                            Back to Login
                        </Link>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="auth-container">
            <div className="auth-card glass fade-in">
                <div className="auth-header">
                    <h1 className="auth-title">Forgot Password?</h1>
                    <p className="auth-subtitle">
                        Enter your email address and we'll send you a link to reset your password
                    </p>
                </div>

                {error && (
                    <div className="alert alert-error">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="auth-form">
                    <Input
                        label="Email"
                        type="email"
                        value={email}
                        onChange={(e) => {
                            setEmail(e.target.value);
                            setError('');
                        }}
                        placeholder="you@example.com"
                        required
                    />

                    <Button type="submit" variant="primary" fullWidth loading={loading}>
                        Send Reset Link
                    </Button>
                </form>

                <div className="auth-footer">
                    <Link to="/login" className="auth-link">
                        Back to Login
                    </Link>
                </div>
            </div>
        </div>
    );
};

export default ForgotPassword;
