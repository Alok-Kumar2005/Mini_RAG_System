"use client";

import React, { useState } from 'react';
import { api } from '@/services/api';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Lock, User } from 'lucide-react';

export default function RegisterPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setIsLoading(true);

    try {
      await api.post('/auth/register', { username, password });
      setSuccess('Registration successful! Redirecting to login...');
      setTimeout(() => {
        router.push('/login');
      }, 1500);
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="glass-panel login-panel animate-fade-in">
        <h2>Create Account</h2>
        <p className="subtitle">Join to start analyzing your documents</p>
        
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="input-group">
            <User className="input-icon" size={20} />
            <input 
              type="text" 
              className="input-field with-icon" 
              placeholder="Choose a username" 
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          
          <div className="input-group">
            <Lock className="input-icon" size={20} />
            <input 
              type="password" 
              className="input-field with-icon" 
              placeholder="Create a password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={4}
            />
          </div>

          <button type="submit" className="btn-primary w-full" disabled={isLoading || !!success}>
            {isLoading ? <div className="loader inline-loader"></div> : 'Register'}
          </button>
        </form>

        <p className="auth-link">
          Already have an account? <Link href="/login">Sign in here</Link>
        </p>
      </div>
      
      <style jsx>{`
        .login-container {
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 100vh;
          padding: 1rem;
        }
        .login-panel {
          width: 100%;
          max-width: 400px;
          padding: 2.5rem;
          text-align: center;
        }
        .subtitle {
          color: var(--text-secondary);
          margin-bottom: 2rem;
          font-size: 0.9rem;
        }
        .auth-form {
          display: flex;
          flex-direction: column;
          gap: 1rem;
          margin-bottom: 1.5rem;
        }
        .input-group {
          position: relative;
          display: flex;
          align-items: center;
        }
        .input-icon {
          position: absolute;
          left: 1rem;
          color: var(--text-secondary);
        }
        .with-icon {
          padding-left: 3rem;
        }
        .w-full {
          width: 100%;
        }
        .error-message {
          background: rgba(239, 68, 68, 0.1);
          color: var(--danger);
          padding: 0.75rem;
          border-radius: 8px;
          margin-bottom: 1rem;
          font-size: 0.875rem;
          border: 1px solid rgba(239, 68, 68, 0.2);
        }
        .success-message {
          background: rgba(16, 185, 129, 0.1);
          color: var(--success);
          padding: 0.75rem;
          border-radius: 8px;
          margin-bottom: 1rem;
          font-size: 0.875rem;
          border: 1px solid rgba(16, 185, 129, 0.2);
        }
        .auth-link {
          font-size: 0.9rem;
          color: var(--text-secondary);
        }
        .inline-loader {
          margin: 0 auto;
          width: 20px;
          height: 20px;
          border-width: 2px;
        }
      `}</style>
    </div>
  );
}
