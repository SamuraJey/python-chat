// This is a utility component to test fetch requests with different CSRF handling
import React, { useEffect, useState } from 'react';

export const CsrfTest: React.FC = () => {
  const [csrfToken, setCsrfToken] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Function to get CSRF token
  const fetchCsrfToken = async () => {
    try {
      const response = await fetch('/api/test/csrf-token');

      if (!response.ok) {
        throw new Error(`Failed to fetch CSRF token: ${response.status}`);
      }

      const data = await response.json();
      setCsrfToken(data.csrf_token);
    } catch (err) {
      setError(`Error fetching CSRF token: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  // Function to test a form POST with CSRF token
  const testFormPost = async () => {
    try {
      if (!csrfToken) {
        setError('No CSRF token available');
        return;
      }

      const formData = new FormData();
      formData.append('csrf_token', csrfToken);
      formData.append('test_data', 'Hello from React!');

      const response = await fetch('/api/test/form-submit', {
        method: 'POST',
        body: formData,
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`Form submission failed: ${response.status}`);
      }

      const data = await response.json();
      setTestResult(JSON.stringify(data, null, 2));
      setError(null);
    } catch (err) {
      setError(`Form submission error: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  // Function to test a JSON POST with CSRF token
  const testJsonPost = async () => {
    try {
      if (!csrfToken) {
        setError('No CSRF token available');
        return;
      }

      const response = await fetch('/api/test/json-submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({
          csrf_token: csrfToken,
          test_data: 'Hello from React JSON!',
        }),
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`JSON submission failed: ${response.status}`);
      }

      const data = await response.json();
      setTestResult(JSON.stringify(data, null, 2));
      setError(null);
    } catch (err) {
      setError(`JSON submission error: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  return (
    <div className="csrf-test" style={{ padding: '20px', border: '1px solid #ccc', margin: '20px', borderRadius: '8px' }}>
      <h3>CSRF Test</h3>
      <div style={{ marginBottom: '20px' }}>
        <strong>CSRF Token:</strong> {csrfToken || 'None'}
      </div>

      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        <button onClick={fetchCsrfToken}>Get CSRF Token</button>
        <button onClick={testFormPost} disabled={!csrfToken}>Test Form POST</button>
        <button onClick={testJsonPost} disabled={!csrfToken}>Test JSON POST</button>
      </div>

      {testResult && (
        <div style={{ marginBottom: '20px' }}>
          <h4>Test Result:</h4>
          <pre style={{ background: '#f5f5f5', padding: '10px', borderRadius: '4px' }}>
            {testResult}
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
