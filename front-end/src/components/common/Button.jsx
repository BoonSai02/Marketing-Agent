import './Button.css';

const Button = ({
    children,
    onClick,
    type = 'button',
    variant = 'primary',
    disabled = false,
    loading = false,
    fullWidth = false,
    className = '',
}) => {
    return (
        <button
            type={type}
            onClick={onClick}
            disabled={disabled || loading}
            className={`btn btn-${variant} ${fullWidth ? 'btn-full' : ''} ${className}`}
        >
            {loading ? (
                <span className="btn-loading">
                    <span className="spinner"></span>
                    Loading...
                </span>
            ) : (
                children
            )}
        </button>
    );
};

export default Button;
