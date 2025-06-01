import { createContext, useContext, useState, type ReactNode, useEffect } from 'react';
import { authApi, type LoginRequest, type RegisterRequest } from '../services/api';

interface User {
  username: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginRequest) => Promise<boolean>;
  register: (userData: RegisterRequest) => Promise<boolean>;
  logout: () => Promise<boolean>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Check auth status on initial load
  useEffect(() => {
    // Use the dedicated auth status endpoint
    const checkAuthStatus = async () => {
      try {
        const response = await authApi.checkStatus();

        if (response.success && response.data?.isAuthenticated) {
          setIsAuthenticated(true);
          setUser({ username: response.data.username || 'Current User' });
        } else {
          setIsAuthenticated(false);
          setUser(null);
        }
      } catch (err) {
        setIsAuthenticated(false);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuthStatus();
  }, []);

  const login = async (credentials: LoginRequest): Promise<boolean> => {
    setError(null);
    setIsLoading(true);
    try {
      const response = await authApi.login(credentials);
      if (response.success) {
        // Use the username from the API response if available
        const username = response.data?.username || credentials.username;
        setUser({ username });
        setIsAuthenticated(true);
        return true;
      } else {
        setError(response.error || 'Login failed');
        return false;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred during login');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userData: RegisterRequest): Promise<boolean> => {
    setError(null);
    setIsLoading(true);
    try {
      const response = await authApi.register(userData);
      if (response.success) {
        // Usually, we'd navigate to login after registration
        return true;
      } else {
        setError(response.error || 'Registration failed');
        return false;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred during registration');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async (): Promise<boolean> => {
    setError(null);
    setIsLoading(true);
    try {
      const response = await authApi.logout();
      if (response.success) {
        setUser(null);
        setIsAuthenticated(false);
        return true;
      } else {
        setError(response.error || 'Logout failed');
        return false;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred during logout');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const value = {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
