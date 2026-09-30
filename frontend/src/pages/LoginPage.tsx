import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Button, Input, Card } from '@/components';
import { Lock, Mail, AlertCircle, Sparkles } from 'lucide-react';

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please fill in all fields');
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Invalid email or password');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-dp-bg-base flex flex-col justify-center items-center p-4">
      <div className="w-full max-w-md space-y-6">
        
        {/* Brand Logo & Title */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-dp-accent/10 border border-dp-accent/20 mb-2">
            <Sparkles className="w-6 h-6 text-dp-accent" />
          </div>
          <h1 className="text-2xl font-bold text-dp-text tracking-tight">DataPilot AI</h1>
          <p className="text-sm text-dp-text-secondary">Sign in to your intelligent data workspace</p>
        </div>

        {/* Card Form */}
        <Card variant="bordered" padding="lg" className="shadow-xl bg-dp-bg-raised">
          <form onSubmit={handleSubmit} className="space-y-4">
            
            {error && (
              <div className="p-3 rounded-lg bg-dp-error/10 border border-dp-error/20 text-dp-error text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <Input
              label="Email Address"
              type="email"
              icon={<Mail className="w-4 h-4" />}
              placeholder="you@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />

            <Input
              label="Password"
              type="password"
              icon={<Lock className="w-4 h-4" />}
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            <Button
              type="submit"
              variant="primary"
              fullWidth
              loading={isLoading}
              className="mt-2"
            >
              Sign In
            </Button>
          </form>

          <div className="mt-6 pt-4 text-center text-xs text-dp-text-muted border-t border-dp-border">
            Don't have an account?{' '}
            <Link to="/register" className="text-dp-accent font-medium hover:underline">
              Create Account
            </Link>
          </div>
        </Card>

      </div>
    </div>
  );
};

export default LoginPage;
