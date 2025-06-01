import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import type { RegisterRequest } from '../services/api';

interface RegisterFormProps {
  onSuccess?: () => void;
}

export const RegisterForm: React.FC<RegisterFormProps> = ({ onSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [password2, setPassword2] = useState('');
  const [passwordError, setPasswordError] = useState('');

  const { register, error, isLoading } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Client-side validation
    if (password !== password2) {
      setPasswordError('Passwords do not match');
      return;
    } else {
      setPasswordError('');
    }

    const userData: RegisterRequest = {
      username,
      password,
      password2,
    };

    const success = await register(userData);
    if (success && onSuccess) {
      onSuccess();
    }
  };

  return (
    <div className="auth-form">
      <h2 className="auth-title">Create Account</h2>

      {error && <div className="alert alert-error">{error}</div>}

      <form onSubmit={handleSubmit} className="auth-form-content">
        <div className="form-group">
          <label htmlFor="username" className="form-label">Username</label>
          <input
            type="text"
            id="username"
            className="input-modern"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Choose a username"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="password" className="form-label">Password</label>
          <input
            type="password"
            id="password"
            className="input-modern"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Create a password"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="password2" className="form-label">Confirm Password</label>
          <input
            type="password"
            id="password2"
            className="input-modern"
            value={password2}
            onChange={(e) => setPassword2(e.target.value)}
            placeholder="Confirm your password"
            required
          />
          {passwordError && <div className="field-error">{passwordError}</div>}
        </div>

        <button
          type="submit"
          className="btn-primary btn-large"
          disabled={isLoading}
        >
          {isLoading ? 'Creating Account...' : 'Create Account'}
        </button>
      </form>
    </div>
  );
};
