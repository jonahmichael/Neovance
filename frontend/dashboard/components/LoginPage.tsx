'use client';

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Activity, AlertCircle } from 'lucide-react';

export default function LoginPage() {
  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    // Simple delay to simulate authentication
    await new Promise(resolve => setTimeout(resolve, 500));

    const success = login(userId, password);
    
    if (!success) {
      setError('Invalid credentials. Please try again.');
    }
    
    setIsLoading(false);
  };

  const isFormValid = userId.trim() !== '' && password.trim() !== '';

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4 font-sans">
      <div className="w-full max-w-md">
        {/* Branding Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Activity className="h-12 w-12 text-blue-600 mr-3" />
            <h1 className="text-3xl font-bold text-gray-800 font-sans">Neovance-AI</h1>
          </div>
          <p className="text-gray-600 text-lg font-sans">Clinical Dashboard Login</p>
          <p className="text-gray-500 text-sm mt-2 font-sans">NICU Monitoring & EOS Risk Assessment</p>
        </div>

        {/* Login Card */}
        <Card className="bg-white border-gray-200 shadow-lg">
          <CardHeader className="text-center pb-2">
            <CardTitle className="text-gray-800 text-xl font-sans">Access Dashboard</CardTitle>
            <p className="text-gray-600 text-sm font-sans">Enter your credentials to continue</p>
          </CardHeader>
          
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Error Message */}
              {error && (
                <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <AlertCircle className="h-5 w-5 text-red-600" />
                  <span className="text-red-700 text-sm font-sans">{error}</span>
                </div>
              )}

              {/* User ID Field */}
              <div className="space-y-2">
                <label htmlFor="userId" className="text-sm font-medium text-gray-700 font-sans">
                  User ID
                </label>
                <Input
                  id="userId"
                  type="text"
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  placeholder="Enter your User ID"
                  className="bg-white border-gray-300 text-gray-900 placeholder:text-gray-500 focus:border-blue-500 font-sans"
                  disabled={isLoading}
                />
              </div>

              {/* Password Field */}
              <div className="space-y-2">
                <label htmlFor="password" className="text-sm font-medium text-gray-700 font-sans">
                  Password
                </label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="bg-white border-gray-300 text-gray-900 placeholder:text-gray-500 focus:border-blue-500 font-sans"
                  disabled={isLoading}
                />
              </div>

              {/* Login Button */}
              <Button
                type="submit"
                disabled={!isFormValid || isLoading}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-medium py-3 font-sans"
              >
                {isLoading ? (
                  <div className="flex items-center justify-center gap-2">
                    <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                    <span className="font-sans">Authenticating...</span>
                  </div>
                ) : (
                  <span className="font-sans">Login to Dashboard</span>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center mt-6">
          <p className="text-sm font-sans" style={{color: '#8C7C69'}}>
            Powered by Puopolo/Kaiser EOS Risk Calculator
          </p>
        </div>
      </div>
    </div>
  );
}