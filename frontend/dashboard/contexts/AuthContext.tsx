'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

export type UserRole = 'DOCTOR' | 'NURSE';

export interface User {
  isLoggedIn: boolean;
  role: UserRole | null;
  userId: string;
  name: string;
  displayName: string;
}

interface AuthContextType {
  user: User;
  login: (userId: string, password: string) => boolean;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Hardcoded credentials with actual staff names
const CREDENTIALS = {
  'DR001': { 
    password: 'password@dr', 
    role: 'DOCTOR' as UserRole, 
    displayName: 'Dr. Rajesh Kumar',
    department: 'Neonatology',
    shift: 'Day',
    phone: '+91-9876500001'
  },
  'DR002': { 
    password: 'password@dr', 
    role: 'DOCTOR' as UserRole, 
    displayName: 'Dr. Priya Sharma',
    department: 'Pediatric Cardiology',
    shift: 'Night',
    phone: '+91-9876500002'
  },
  'NS001': { 
    password: 'password@ns', 
    role: 'NURSE' as UserRole, 
    displayName: 'Anjali Patel',
    department: 'NICU Care',
    shift: 'Day',
    phone: '+91-9876500003'
  },
  'NS002': { 
    password: 'password@ns', 
    role: 'NURSE' as UserRole, 
    displayName: 'Deepika Singh',
    department: 'Critical Care',
    shift: 'Rotating',
    phone: '+91-9876500004'
  }
};

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User>({
    isLoggedIn: false,
    role: null,
    userId: '',
    name: '',
    displayName: ''
  });

  // Restore authentication state from localStorage
  useEffect(() => {
    const savedAuth = localStorage.getItem('neovance_auth');
    if (savedAuth) {
      try {
        const authData = JSON.parse(savedAuth);
        setUser(authData);
      } catch (error) {
        console.error('Failed to restore auth state:', error);
        localStorage.removeItem('neovance_auth');
      }
    }
  }, []);

  const login = (userId: string, password: string): boolean => {
    const credentials = CREDENTIALS[userId as keyof typeof CREDENTIALS];
    
    if (credentials && credentials.password === password) {
      const newUser: User = {
        isLoggedIn: true,
        role: credentials.role,
        userId: userId,
        name: credentials.displayName,
        displayName: credentials.displayName
      };
      
      setUser(newUser);
      localStorage.setItem('neovance_auth', JSON.stringify(newUser));
      return true;
    }
    
    return false;
  };

  const logout = () => {
    const resetUser: User = {
      isLoggedIn: false,
      role: null,
      userId: '',
      name: '',
      displayName: ''
    };
    
    setUser(resetUser);
    localStorage.removeItem('neovance_auth');
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}