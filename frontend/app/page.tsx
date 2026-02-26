"use client";

import Link from "next/link";
import { motion, useScroll, useTransform } from "framer-motion";
import { 
  ArrowRight, 
  Sparkles, 
  Code2, 
  Terminal,
  ChevronDown,
  Zap,
  Shield,
  Globe,
  Github,
  ArrowUpRight
} from "lucide-react";
import { useRef } from "react";
import Navbar from "@/components/Navbar";

const codeSnippet = `def calculate_discount(price, quantity, is_member):
    # Sum all item prices
    subtotal = sum(items)
    # Calculate tax amount
    tax = subtotal * tax_rate
    # Return final total with tax
    return subtotal + tax`;

export default function Home() {
  const containerRef = useRef(null);
  const { scrollYProgress } = useScroll({ target: containerRef });
  
  const y1 = useTransform(scrollYProgress, [0, 1], [0, -100]);
  const y2 = useTransform(scrollYProgress, [0, 1], [0, 100]);
  const opacity = useTransform(scrollYProgress, [0, 0.2], [1, 0]);

  return (
    <div ref={containerRef} className="min-h-screen bg-[#0f0f14] text-slate-300 overflow-x-hidden">
      {/* Brighter, softer background */}
      <div className="fixed inset-0 pointer-events-none">
        <motion.div 
          style={{ y: y1 }}
          className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-indigo-600/15 rounded-full blur-[100px]"
        />
        <motion.div 
          style={{ y: y2 }}
          className="absolute bottom-0 right-1/4 w-[600px] h-[600px] bg-violet-600/15 rounded-full blur-[100px]"
        />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-blue-600/10 rounded-full blur-[120px]" />
        {/* Subtle grid */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:100px_100px]" />
      </div>

      <Navbar />

      <main className="relative z-10 pt-20">
        {/* Hero Section - Added top padding to avoid navbar overlap */}
        <section className="min-h-[calc(100vh-5rem)] flex flex-col items-center justify-center px-6 relative">
          <motion.div 
            style={{ opacity }}
            className="absolute inset-0 pointer-events-none"
          >
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-500/10 rounded-full blur-[100px]" />
          </motion.div>

          <div className="max-w-6xl w-full grid lg:grid-cols-2 gap-16 items-center">
            {/* Left Content */}
            <motion.div
              initial={{ opacity: 0, x: -40 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, ease: "easeOut" }}
              className="space-y-8"
            >
              {/* Moved badge below title to avoid overlap */}
              <motion.div 
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.2 }}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/[0.05] border border-white/[0.1]"
              >
                <Sparkles className="w-4 h-4 text-indigo-400" />
                <span className="text-sm text-slate-400">Now with multi-language support</span>
                <ArrowUpRight className="w-3 h-3 text-slate-500" />
              </motion.div>

              <h1 className="text-5xl md:text-7xl font-bold leading-[1.1] tracking-tight">
                <motion.span 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                  className="block text-white"
                >
                  Generate
                </motion.span>
                <motion.span 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 }}
                  className="block bg-gradient-to-r from-indigo-300 to-violet-300 bg-clip-text text-transparent"
                >
                  Documentation
                </motion.span>
                <motion.span 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 }}
                  className="block text-slate-500"
                >
                  Automatically
                </motion.span>
              </h1>

              <motion.p 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.6 }}
                className="text-lg text-slate-400 leading-relaxed max-w-lg"
              >
                Stop writing comments manually. Our AI understands your code 
                and generates professional documentation in milliseconds.
              </motion.p>

              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.7 }}
                className="flex flex-wrap gap-4"
              >
                <Link href="/generate">
                  <motion.button 
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="group relative flex items-center gap-3 px-8 py-4 rounded-xl bg-white text-slate-950 font-semibold overflow-hidden"
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-indigo-100 to-violet-100 opacity-0 group-hover:opacity-100 transition-opacity" />
                    <Zap className="w-5 h-5 relative z-10" />
                    <span className="relative z-10">Start Generating</span>
                    <ArrowRight className="w-4 h-4 relative z-10 group-hover:translate-x-1 transition-transform" />
                  </motion.button>
                </Link>
                
                <Link href="/docs">
                  <motion.button 
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="flex items-center gap-3 px-8 py-4 rounded-xl bg-white/[0.05] border border-white/[0.1] text-white font-semibold hover:bg-white/[0.08] transition-colors"
                  >
                    <Code2 className="w-5 h-5" />
                    <span>View Examples</span>
                  </motion.button>
                </Link>
              </motion.div>

              {/* Language pills */}
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.8 }}
                className="flex flex-wrap gap-3 pt-4"
              >
                {["Python", "JavaScript", "TypeScript", "Java", "C++"].map((lang, i) => (
                  <motion.span
                    key={lang}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.9 + i * 0.1 }}
                    whileHover={{ scale: 1.05, backgroundColor: "rgba(255,255,255,0.1)" }}
                    className="px-4 py-2 rounded-full bg-white/[0.05] border border-white/[0.08] text-sm text-slate-400 cursor-default transition-colors"
                  >
                    {lang}
                  </motion.span>
                ))}
              </motion.div>
            </motion.div>

            {/* Right - Code Preview */}
            <motion.div
              initial={{ opacity: 0, x: 40 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, delay: 0.3 }}
              className="relative"
            >
              <motion.div
                animate={{ y: [0, -10, 0] }}
                transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                className="relative"
              >
                {/* Glow effect */}
                <div className="absolute -inset-4 bg-indigo-500/15 rounded-2xl blur-2xl" />
                
                <div className="relative bg-[#0f0f14] rounded-xl border border-white/[0.1] overflow-hidden shadow-2xl">
                  {/* Window header */}
                  <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.08] bg-white/[0.03]">
                    <div className="flex gap-2">
                      <div className="w-3 h-3 rounded-full bg-red-500/30 border border-red-500/40" />
                      <div className="w-3 h-3 rounded-full bg-yellow-500/30 border border-yellow-500/40" />
                      <div className="w-3 h-3 rounded-full bg-green-500/30 border border-green-500/40" />
                    </div>
                    <div className="flex items-center gap-2 px-3 py-1 rounded-md bg-white/[0.05] text-xs text-slate-500 font-mono">
                      <Terminal className="w-3 h-3" />
                      example.py
                    </div>
                    <div className="w-16" />
                  </div>

                  {/* Code */}
                  <div className="p-6 font-mono text-sm">
                    <pre className="text-slate-300 leading-relaxed">
                      <code>{codeSnippet}</code>
                    </pre>
                  </div>

                  {/* Status bar */}
                  <div className="px-4 py-2 border-t border-white/[0.08] bg-white/[0.03] flex items-center justify-between text-xs text-slate-500">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                      <span>AI Generated</span>
                    </div>
                    <span>Python 3.11</span>
                  </div>
                </div>
              </motion.div>

              {/* Floating elements */}
              <motion.div
                animate={{ y: [0, 10, 0], rotate: [0, 5, 0] }}
                transition={{ duration: 5, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
                className="absolute -top-8 -right-8 w-24 h-24 bg-violet-500/15 rounded-full blur-xl"
              />
              <motion.div
                animate={{ y: [0, -15, 0], rotate: [0, -5, 0] }}
                transition={{ duration: 6, repeat: Infinity, ease: "easeInOut", delay: 1 }}
                className="absolute -bottom-8 -left-8 w-32 h-32 bg-indigo-500/15 rounded-full blur-xl"
              />
            </motion.div>
          </div>

          {/* Scroll indicator */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.2 }}
            className="absolute bottom-10 left-1/2 -translate-x-1/2"
          >
            <motion.div
              animate={{ y: [0, 8, 0] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="flex flex-col items-center gap-2 text-slate-500"
            >
              <span className="text-xs uppercase tracking-widest">Scroll</span>
              <ChevronDown className="w-5 h-5" />
            </motion.div>
          </motion.div>
        </section>

        {/* Features Section */}
        <section className="py-32 px-6">
          <div className="max-w-6xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-center mb-16"
            >
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
                Everything you need
              </h2>
              <p className="text-slate-400">Professional documentation without the effort</p>
            </motion.div>

            <div className="grid md:grid-cols-3 gap-6">
              {[
                {
                  icon: Zap,
                  title: "Lightning Fast",
                  description: "Generate documentation in under 100ms. No waiting, no loading screens.",
                  color: "amber"
                },
                {
                  icon: Shield,
                  title: "Privacy First",
                  description: "Your code never leaves your machine. Process everything locally with our API.",
                  color: "emerald"
                },
                {
                  icon: Globe,
                  title: "Multi-Language",
                  description: "Support for Python, JavaScript, TypeScript, Java, and C++ with more coming.",
                  color: "blue"
                }
              ].map((feature, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: idx * 0.2 }}
                  whileHover={{ y: -5 }}
                  className="group p-8 rounded-2xl bg-white/[0.03] border border-white/[0.08] hover:border-white/[0.15] hover:bg-white/[0.05] transition-all cursor-pointer"
                >
                  <div className={`p-3 rounded-xl bg-${feature.color}-500/10 border border-${feature.color}-500/20 w-fit mb-6 group-hover:scale-110 transition-transform`}>
                    <feature.icon className={`w-6 h-6 text-${feature.color}-400`} />
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-3">{feature.title}</h3>
                  <p className="text-slate-400 leading-relaxed">{feature.description}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* How it works */}
        <section className="py-32 px-6 bg-white/[0.02]">
          <div className="max-w-5xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-center mb-20"
            >
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
                How it works
              </h2>
              <p className="text-slate-400">Three simple steps to better documentation</p>
            </motion.div>

            <div className="space-y-12">
              {[
                { step: "01", title: "Paste your code", desc: "Copy and paste any function or class" },
                { step: "02", title: "Select language", desc: "Choose from Python, JS, TS, Java, or C++" },
                { step: "03", title: "Get documentation", desc: "Receive comments and docstrings instantly" }
              ].map((item, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, x: idx % 2 === 0 ? -40 : 40 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: idx * 0.2 }}
                  className={`flex items-center gap-8 ${idx % 2 === 1 ? 'flex-row-reverse' : ''}`}
                >
                  <div className="flex-1">
                    <span className="text-6xl font-bold text-white/5 absolute">{item.step}</span>
                    <div className="relative">
                      <h3 className="text-2xl font-semibold text-white mb-2">{item.title}</h3>
                      <p className="text-slate-400">{item.desc}</p>
                    </div>
                  </div>
                  <div className="w-16 h-16 rounded-full bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 font-bold text-xl">
                    {item.step}
                  </div>
                  <div className="flex-1" />
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-32 px-6">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="max-w-4xl mx-auto text-center p-12 rounded-3xl bg-gradient-to-b from-white/[0.08] to-white/[0.02] border border-white/[0.1]"
          >
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Ready to get started?
            </h2>
            <p className="text-lg text-slate-400 mb-8 max-w-xl mx-auto">
              Join thousands of developers who save hours every week with automated documentation.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/generate">
                <motion.button 
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="px-8 py-4 rounded-xl bg-white text-slate-950 font-semibold hover:bg-slate-200 transition-colors"
                >
                  Try It Free
                </motion.button>
              </Link>
              <Link href="https://github.com" target="_blank">
                <motion.button 
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="px-8 py-4 rounded-xl bg-white/[0.05] border border-white/[0.1] text-white font-semibold hover:bg-white/[0.08] transition-colors flex items-center justify-center gap-2"
                >
                  <Github className="w-5 h-5" />
                  View on GitHub
                </motion.button>
              </Link>
            </div>
          </motion.div>
        </section>
      </main>
    </div>
  );
}