import { forwardRef, useState, type InputHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  isPassword?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, isPassword, id, type, className = '', ...props }, ref) => {
    const [showPassword, setShowPassword] = useState(false);
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, '-');
    const inputType = isPassword ? (showPassword ? 'text' : 'password') : type;

    const input = (
      <input
        ref={ref}
        id={inputId}
        type={inputType}
        className={`form-input ${className}`}
        style={isPassword ? { paddingRight: 44 } : undefined}
        {...props}
      />
    );

    return (
      <div className="form-group">
        {label && (
          <label className="form-label" htmlFor={inputId}>
            {label}
          </label>
        )}
        {isPassword ? (
          <div className="password-wrapper">
            {input}
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowPassword((v) => !v)}
              tabIndex={-1}
            >
              {showPassword ? (
                <svg viewBox="0 0 24 24">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
                  <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
                  <line x1="1" y1="1" x2="23" y2="23" />
                </svg>
              ) : (
                <svg viewBox="0 0 24 24">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                  <circle cx="12" cy="12" r="3" />
                </svg>
              )}
            </button>
          </div>
        ) : (
          input
        )}
        {error && <div className="form-error">{error}</div>}
      </div>
    );
  },
);

Input.displayName = 'Input';
