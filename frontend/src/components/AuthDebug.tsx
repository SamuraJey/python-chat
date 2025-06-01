import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

export const AuthDebug: React.FC = () => {
  const { isAuthenticated, user } = useAuth();
  const [pingResult, setPingResult] = useState<string | null>(null);
  const [authResult, setAuthResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const testPing = async () => {
    try {
      const response = await fetch('/api/test/ping');
      const data = await response.json();
      setPingResult(JSON.stringify(data, null, 2));
    } catch (err) {
      setPingResult('Error: ' + (err instanceof Error ? err.message : String(err)));
    }
  };

  const testAuth = async () => {
    try {
      const response = await fetch('/api/test/auth', {
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        setAuthResult(JSON.stringify(data, null, 2));
        setError(null);
      } else {
        setAuthResult(null);
        setError(`Status: ${response.status} - ${response.statusText}`);
      }
    } catch (err) {
      setAuthResult(null);
      setError('Error: ' + (err instanceof Error ? err.message : String(err)));
    }
  };

  // Test ping on component mount
  useEffect(() => {
    testPing();
  }, []);

  return (
    <div className="auth-debug" style={{ padding: '20px', border: '1px solid #ccc', borderRadius: '8px', margin: '20px' }}>
      <h3>Authentication Debug</h3>
      <div style={{ marginBottom: '10px' }}>
        <strong>isAuthenticated:</strong> {isAuthenticated ? 'Yes' : 'No'}
      </div>
      <div style={{ marginBottom: '20px' }}>
        <strong>User:</strong> {user ? user.username : 'None'}
      </div>

      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        <button onClick={testPing}>Test Ping</button>
        <button onClick={testAuth}>Test Auth Endpoint</button>
      </div>

      {pingResult && (
        <div style={{ marginBottom: '20px' }}>
          <h4>Ping Result:</h4>
          <pre style={{ background: '#f5f5f5', padding: '10px', borderRadius: '4px' }}>
            {pingResult}
          </pre>
        </div>
      )}

      {authResult && (
        <div style={{ marginBottom: '20px' }}>
          <h4>Auth Test Result:</h4>
          <pre style={{ background: '#f5f5f5', padding: '10px', borderRadius: '4px' }}>
            {authResult}
          </pre>
        </div>
      )}

      {error && (
        <div style={{ color: 'red', marginBottom: '20px' }}>
          <h4>Error:</h4>
          <pre style={{ background: '#fff0f0', padding: '10px', borderRadius: '4px' }}>
            {error}
          </pre>
        </div>
      )}
    </div>
  );
};
