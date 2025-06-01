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
            <p className="auth-toggle">
              Don't have an account?{' '}
              <button onClick={() => setShowLogin(false)}>Register</button>
            </p>
          </>
        ) : (
          <>
            <RegisterForm onSuccess={() => setShowLogin(true)} />
            <p className="auth-toggle">
              Already have an account?{' '}
              <button onClick={() => setShowLogin(true)}>Login</button>
            </p>
          </>
        )}
      </div>

      {/* Debug components - remove in production */}
      <AuthDebug />
      <CsrfTest />
    </div>
  );
};
