import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Button, Input, Card } from '@/components';
import { Lock, Mail, User, AlertCircle, Sparkles } from 'lucide-react';

const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const { register } = useAuth();
  
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please fill in all required fields');
      return;
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters long');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      await register(email, password, fullName || undefined);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Registration failed');
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
          <h1 className="text-2xl font-bold text-dp-text tracking-tight">Create DataPilot AI Account</h1>
          <p className="text-sm text-dp-text-secondary">Start discovering, extracting and analyzing web data</p>
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
              label="Full Name (Optional)"
              type="text"
              icon={<User className="w-4 h-4" />}
              placeholder="John Doe"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />

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

            <Input
              label="Confirm Password"
              type="password"
              icon={<Lock className="w-4 h-4" />}
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />

            <Button
              type="submit"
              variant="primary"
              fullWidth
              loading={isLoading}
              className="mt-2"
            >
              Create Account
            </Button>
          </form>

          <div className="mt-6 pt-4 text-center text-xs text-dp-text-muted border-t border-dp-border">
            Already have an account?{' '}
            <Link to="/login" className="text-dp-accent font-medium hover:underline">
              Sign In
            </Link>
          </div>
        </Card>

      </div>
    </div>
  );
};

export default RegisterPage;
