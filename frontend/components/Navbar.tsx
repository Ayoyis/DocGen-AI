"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Terminal, User, LogOut, Loader2 } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Navbar() {
  const [user, setUser] = useState<{ name: string; email: string } | null>(null);
  const [isLoading, setIsLoading] = useState(true); // Add loading state

  // Check auth status
  const checkAuth = () => {
    const token = localStorage.getItem("token");
    const email = localStorage.getItem("email");
    const name = localStorage.getItem("name"); // Store name too if available
    
    console.log("checkAuth:", { token: !!token, email, name });

    if (token && email) {
      setUser({ 
        name: name || email.split('@')[0], 
        email 
      });
    } else {
      setUser(null);
    }
    setIsLoading(false);
  };

  useEffect(() => {
    checkAuth();
    
    // Listen for auth changes (e.g., from OAuth callback in different tab)
    window.addEventListener('storage', checkAuth);
    
    // Custom event for same-window updates
    window.addEventListener('auth-change', checkAuth);
    
    return () => {
      window.removeEventListener('storage', checkAuth);
      window.removeEventListener('auth-change', checkAuth);
    };
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("email");
    localStorage.removeItem("name");
    setUser(null);
    window.dispatchEvent(new Event('auth-change')); // Notify other components
    window.location.href = "/login";
  };

  // Don't show buttons while checking auth (prevents flash)
  if (isLoading) {
    return (
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/5 bg-[#0a0a0f]/40 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-gradient-to-br from-indigo-600 to-violet-600">
              <Terminal className="w-4 h-4 text-white" />
            </div>
            <span className="text-base font-bold text-white">DocGen AI</span>
          </div>
          <Loader2 className="w-4 h-4 text-slate-400 animate-spin" />
        </div>
      </nav>
    );
  }

  return (
    <motion.nav
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="fixed top-0 left-0 right-0 z-50 border-b border-white/5 bg-[#0a0a0f]/40 backdrop-blur-md"
    >
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 group">
          <motion.div 
            whileHover={{ rotate: 180 }}
            transition={{ duration: 0.3 }}
            className="relative"
          >
            <div className="absolute inset-0 bg-indigo-500 blur-lg opacity-50 group-hover:opacity-75 transition-opacity" />
            <div className="relative p-1.5 rounded-lg bg-gradient-to-br from-indigo-600 to-violet-600 border border-white/20">
              <Terminal className="w-4 h-4 text-white" />
            </div>
          </motion.div>
          
          <div className="flex flex-col">
            <span className="text-base font-bold bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
              DocGen AI
            </span>
            <span className="text-[9px] text-slate-500 font-medium tracking-wider uppercase">
              Documentation
            </span>
          </div>
        </Link>

        {/* Navigation */}
        <div className="hidden md:flex items-center gap-6">
          <Link href="/" className="text-sm text-slate-400 hover:text-white transition-colors">
            Home
          </Link>
          <Link href="/generate" className="text-sm text-slate-400 hover:text-white transition-colors">
            Generate
          </Link>
          <Link href="/docs" className="text-sm text-slate-400 hover:text-white transition-colors">
            Docs
          </Link>
          <Link href="/pricing" className="text-sm text-slate-400 hover:text-white transition-colors">
            Pricing
          </Link>
        </div>

        {/* Auth Buttons - With AnimatePresence for smooth transitions */}
        <div className="flex items-center gap-3">
          <AnimatePresence mode="wait">
            {user ? (
              <motion.div
                key="user"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="flex items-center gap-3"
              >
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 backdrop-blur-sm">
                  <div className="w-6 h-6 rounded-full bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center">
                    <User className="w-3 h-3 text-white" />
                  </div>
                  <span className="text-sm text-slate-300 font-medium">{user.name}</span>
                </div>
                
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-colors border border-transparent hover:border-red-500/20"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="hidden sm:inline">Logout</span>
                </button>
              </motion.div>
            ) : (
              <motion.div
                key="auth"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="flex items-center gap-3"
              >
                <Link 
                  href="/login" 
                  className="text-sm text-slate-400 hover:text-white transition-colors px-3 py-1.5"
                >
                  Sign In
                </Link>
                <Link
                  href="/signup"
                  className="px-4 py-2 rounded-lg bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-sm font-medium transition-all shadow-lg shadow-indigo-600/20 hover:shadow-indigo-600/40 hover:scale-105 active:scale-95"
                >
                  Get Started
                </Link>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.nav>
  );
}