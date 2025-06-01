import React, { useState } from 'react';
import { LoginForm } from '../components/LoginForm';
import { RegisterForm } from '../components/RegisterForm';
import { AuthDebug } from '../components/AuthDebug';
import { CsrfTest } from '../components/CsrfTest';

export const AuthPage: React.FC = () => {
  const [showLogin, setShowLogin] = useState(true);

  return (
    <div className="auth-page">
      <div className="auth-container">
        <h1>Python Chat</h1>

        {showLogin ? (
          <>
            <LoginForm />
            <div className="auth-toggle">
              <span>Don't have an account?</span>
              <button
                className="btn-ghost"
                onClick={() => setShowLogin(false)}
              >
                Create Account
              </button>
            </div>
          </>
        ) : (
          <>
            <RegisterForm onSuccess={() => setShowLogin(true)} />
            <div className="auth-toggle">
              <span>Already have an account?</span>
              <button
                className="btn-ghost"
                onClick={() => setShowLogin(true)}
              >
                Sign In
              </button>
            </div>
          </>
        )}
      </div>

      {/* Debug components - remove in production */}
      <AuthDebug />
      <CsrfTest />
    </div>
  );
};
