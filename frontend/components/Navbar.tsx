"use client";

import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";
import { 
  Menu, 
  X, 
  Sparkles, 
  Github, 
  ArrowRight,
  ChevronDown,
  Terminal
} from "lucide-react";

const navLinks = [
  { name: "Generate", href: "/generate", badge: "New" },
  { name: "Documentation", href: "/docs" },
  { name: "Pricing", href: "/pricing" },
];

export default function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [activeLink, setActiveLink] = useState("");

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <>
      <motion.nav
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        className="fixed top-0 left-0 right-0 z-50"
      >
        <div 
          className={`transition-all duration-500 ${
            isScrolled 
              ? "bg-slate-950/80 backdrop-blur-2xl border-b border-white/10 shadow-2xl shadow-black/50" 
              : "bg-transparent"
          }`}
        >
          <div className="max-w-7xl mx-auto px-6 lg:px-8">
            <div className="flex items-center justify-between h-20">
              
              {/* Logo */}
              <Link href="/" className="flex items-center gap-3 group">
                <motion.div 
                  whileHover={{ rotate: 180 }}
                  transition={{ duration: 0.3 }}
                  className="relative"
                >
                  <div className="absolute inset-0 bg-indigo-500 blur-lg opacity-50 group-hover:opacity-75 transition-opacity" />
                  <div className="relative p-2 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 border border-white/20">
                    <Terminal className="w-5 h-5 text-white" />
                  </div>
                </motion.div>
                
                <div className="flex flex-col">
                  <span className="text-lg font-bold bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent tracking-tight">
                    DocGen AI
                  </span>
                  <span className="text-[10px] text-slate-500 font-medium tracking-wider uppercase">
                    Documentation
                  </span>
                </div>
              </Link>

              {/* Desktop Navigation */}
              <div className="hidden md:flex items-center gap-1">
                {navLinks.map((link) => (
                  <Link
                    key={link.name}
                    href={link.href}
                    onMouseEnter={() => setActiveLink(link.name)}
                    onMouseLeave={() => setActiveLink("")}
                    className="relative px-4 py-2 text-sm font-medium text-slate-300 hover:text-white transition-colors group"
                  >
                    <span className="relative z-10 flex items-center gap-1.5">
                      {link.name}
                      {link.badge && (
                        <span className="px-1.5 py-0.5 text-[10px] font-bold bg-indigo-500/20 text-indigo-300 rounded-full border border-indigo-500/30">
                          {link.badge}
                        </span>
                      )}
                    </span>
                    
                    <motion.div
                      initial={false}
                      animate={{
                        opacity: activeLink === link.name ? 1 : 0,
                        scale: activeLink === link.name ? 1 : 0.95,
                      }}
                      className="absolute inset-0 rounded-lg bg-white/5 border border-white/10"
                    />
                    
                    <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-indigo-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </Link>
                ))}
              </div>

              {/* Right Side Actions */}
              <div className="hidden md:flex items-center gap-4">
                <Link 
                  href="https://github.com" 
                  target="_blank"
                  className="p-2 text-slate-400 hover:text-white transition-colors hover:bg-white/5 rounded-lg"
                >
                  <Github className="w-5 h-5" />
                </Link>

                <div className="h-6 w-px bg-white/10" />

                <Link href="/signup">                  
                  <motion.button                    
                    whileHover={{ scale: 1.02 }}                    
                    whileTap={{ scale: 0.98 }}                    
                    className="group relative flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-sm font-semibold shadow-lg shadow-indigo-600/25 overflow-hidden"                    
                  >                    
                    <Sparkles className="w-4 h-4" />                    
                    <span>Get Started</span>                    
                  </motion.button>                  
                </Link>                
              </div>

              {/* Mobile Menu Button */}
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="md:hidden p-2 text-slate-300 hover:text-white transition-colors"
              >
                {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Menu */}
        <AnimatePresence>
          {isMobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
              className="md:hidden bg-slate-950/95 backdrop-blur-2xl border-b border-white/10 overflow-hidden"
            >
              <div className="px-6 py-6 space-y-4">
                {navLinks.map((link, idx) => (
                  <motion.div
                    key={link.name}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.1 }}
                  >
                    <Link
                      href={link.href}
                      onClick={() => setIsMobileMenuOpen(false)}
                      className="flex items-center justify-between py-3 text-lg font-medium text-slate-300 hover:text-white transition-colors border-b border-white/5"
                    >
                      <span>{link.name}</span>
                      {link.badge && (
                        <span className="px-2 py-1 text-xs font-bold bg-indigo-500/20 text-indigo-300 rounded-full">
                          {link.badge}
                        </span>
                      )}
                      <ChevronDown className="w-4 h-4 rotate-[-90deg]" />
                    </Link>
                  </motion.div>
                ))}
                
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                  className="pt-4"
                >
                  <Link href="/generate" onClick={() => setIsMobileMenuOpen(false)}>
                    <button className="w-full flex items-center justify-center gap-2 py-4 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 text-white font-semibold shadow-lg shadow-indigo-600/25">
                      <Sparkles className="w-5 h-5" />
                      Get Started Free
                    </button>
                  </Link>
                </motion.div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.nav>

      {/* REMOVED: <div className="h-20" /> */}
    </>
  );
}