"use client";

import { motion } from "framer-motion";
import { useState } from "react";
import { 
  Book, 
  Code2, 
  Terminal, 
  Zap, 
  Shield, 
  Globe,
  ChevronRight,
  Play
} from "lucide-react";
import Navbar from "@/components/Navbar";
import Link from "next/link";

const languages = [
  { value: "python", label: "Python", icon: "🐍" },
  { value: "javascript", label: "JavaScript", icon: "📜" },
  { value: "typescript", label: "TypeScript", icon: "📘" },
  { value: "java", label: "Java", icon: "☕" },
  { value: "cpp", label: "C++", icon: "⚡" },
];

const exampleCodes: Record<string, string> = {
  python: `def calculate_total(price, quantity, is_member):
    total = price * quantity
    if is_member:
        discount = total * 0.1
        total = total - discount
    return total`,
  
  javascript: `function calculateTotal(price, quantity, isMember) {
    let total = price * quantity;
    if (isMember) {
        let discount = total * 0.1;
        total = total - discount;
    }
    return total;
}`,
  
  typescript: `function calculateTotal(price: number, quantity: number, isMember: boolean): number {
    let total = price * quantity;
    if (isMember) {
        let discount = total * 0.1;
        total = total - discount;
    }
    return total;
}`,
  
  java: `public class Calculator {
    public double calculateTotal(double price, int quantity, boolean isMember) {
        double total = price * quantity;
        if (isMember) {
            double discount = total * 0.1;
            total = total - discount;
        }
        return total;
    }
}`,
  
  cpp: `double calculateTotal(double price, int quantity, bool isMember) {
    double total = price * quantity;
    if (isMember) {
        double discount = total * 0.1;
        total = total - discount;
    }
    return total;
}`,
};

const features = [
  {
    icon: Code2,
    title: "Multi-Language Support",
    description: "Generate documentation for Python, JavaScript, TypeScript, Java, and C++.",
  },
  {
    icon: Zap,
    title: "AI-Powered",
    description: "Smart context-aware comment generation for your code.",
  },
  {
    icon: Shield,
    title: "Privacy First",
    description: "Your code is processed securely and never stored.",
  },
  {
    icon: Globe,
    title: "Multiple Formats",
    description: "Google-style, JSDoc, JavaDoc, and more.",
  },
];

export default function DocsPage() {
  const [selectedLang, setSelectedLang] = useState("python");
  const [customCode, setCustomCode] = useState(exampleCodes["python"]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [copied, setCopied] = useState(false);

  const handleLangChange = (lang: string) => {
    setSelectedLang(lang);
    setCustomCode(exampleCodes[lang]);
    setResult(null);
  };

  const generateDocs = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          code: customCode,
          language: selectedLang,
          top_k: 3,
        }),
      });
      const data = await res.json();
      setResult(data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const copyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-slate-200">
      <Navbar />
      
      <main className="relative z-10 pt-32 pb-20">
        {/* Hero Section */}
        <section className="px-6 max-w-7xl mx-auto mb-20">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center max-w-3xl mx-auto"
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 mb-6">
              <Book className="w-4 h-4 text-indigo-400" />
              <span className="text-sm font-medium text-slate-300">Documentation</span>
            </div>
            
            <h1 className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-white via-indigo-200 to-indigo-400 bg-clip-text text-transparent">
              How It Works
            </h1>
            
            <p className="text-xl text-slate-400 leading-relaxed">
              DocGen AI analyzes your code structure and generates professional 
              documentation automatically.
            </p>
          </motion.div>
        </section>

        {/* Interactive Demo */}
        <section className="px-6 max-w-6xl mx-auto mb-20">
          <div className="bg-slate-950/50 border border-white/10 rounded-2xl overflow-hidden">
            <div className="flex flex-col md:flex-row border-b border-white/10">
              {/* Language Selector */}
              <div className="flex md:flex-col border-b md:border-b-0 md:border-r border-white/10 p-4 gap-2 overflow-x-auto">
                {languages.map((lang) => (
                  <button
                    key={lang.value}
                    onClick={() => handleLangChange(lang.value)}
                    className={`flex items-center gap-2 px-4 py-3 rounded-xl text-sm font-medium transition-colors whitespace-nowrap ${
                      selectedLang === lang.value
                        ? "bg-indigo-600 text-white"
                        : "bg-white/5 text-slate-400 hover:bg-white/10 hover:text-white"
                    }`}
                  >
                    <span>{lang.icon}</span>
                    {lang.label}
                  </button>
                ))}
              </div>

              {/* Code Preview */}
              <div className="flex-1 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold">Input Your Code</h3>
                  <button
                    onClick={generateDocs}
                    disabled={loading}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-sm font-medium transition-colors"
                  >
                    {loading ? (
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                      <Play className="w-4 h-4" />
                    )}
                    {loading ? "Generating..." : "Generate Docs"}
                  </button>
                </div>

                <div className="grid md:grid-cols-2 gap-6">
                  {/* Input */}
                  <div>
                    <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Input</p>
                    <textarea
                      value={customCode}
                      onChange={(e) => setCustomCode(e.target.value)}
                      placeholder="Paste your code here..."
                      className="w-full h-64 p-4 rounded-xl bg-black/40 border border-white/10 font-mono text-sm text-slate-300 focus:outline-none focus:border-indigo-500/50 resize-none"
                      spellCheck={false}
                    />
                  </div>

                  {/* Output */}
                  <div>
                    <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">
                      Generated Documentation
                    </p>
                    {result ? (
                      <div className="space-y-3">
                        <div className="p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/20">
                          <p className="text-xs text-emerald-400 mb-2">Docstring</p>
                          <pre className="font-mono text-sm text-slate-300 whitespace-pre-wrap">
                            {result.blocks[0]?.documentation}
                          </pre>
                        </div>
                        <div className="p-4 rounded-xl bg-black/40 border border-white/10">
                          <p className="text-xs text-blue-400 mb-2">Code with Comments</p>
                          <pre className="font-mono text-sm text-slate-300 overflow-x-auto">
                            <code>{result.blocks[0]?.commented_code}</code>
                          </pre>
                        </div>
                      </div>
                    ) : (
                      <div className="h-full min-h-[16rem] flex items-center justify-center text-slate-500 border border-white/10 border-dashed rounded-xl">
                        Click "Generate Docs" to see output
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Features Grid */}
        <section className="px-6 max-w-7xl mx-auto mb-20">
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="p-6 rounded-2xl bg-white/5 border border-white/10 hover:border-white/20 transition-colors"
              >
                <div className="p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20 w-fit mb-4">
                  <feature.icon className="w-6 h-6 text-indigo-400" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-sm text-slate-400">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </section>

        {/* Supported Languages */}
        <section className="px-6 max-w-4xl mx-auto mb-20">
          <h2 className="text-3xl font-bold text-center mb-8">Supported Languages</h2>
          
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {languages.map((lang, idx) => (
              <div
                key={idx}
                className="p-4 rounded-xl bg-white/5 border border-white/10 text-center hover:bg-white/10 transition-colors"
              >
                <div className="text-4xl mb-2">{lang.icon}</div>
                <p className="font-medium">{lang.label}</p>
              </div>
            ))}
          </div>
        </section>

        {/* API Reference */}
        <section className="px-6 max-w-4xl mx-auto mb-20">
          <h2 className="text-3xl font-bold text-center mb-8">API Reference</h2>
          
          <div className="p-6 rounded-2xl bg-white/5 border border-white/10">
            <div className="flex items-center gap-3 mb-4">
              <span className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-sm font-medium">
                POST
              </span>
              <code className="text-indigo-400">/generate</code>
            </div>
            
            <p className="text-slate-400 mb-4">
              Generate documentation for the provided code.
            </p>
            
            <div className="space-y-4">
              <div>
                <p className="text-sm font-medium text-slate-300 mb-2">Request Body:</p>
                <pre className="p-4 rounded-xl bg-black/40 font-mono text-sm text-slate-400">
{`{
  "code": "string",        // Your source code
  "language": "python",    // python, javascript, typescript, java, cpp
  "top_k": 3              // Optional: number of examples
}`}
                </pre>
              </div>
              
              <div>
                <p className="text-sm font-medium text-slate-300 mb-2">Response:</p>
                <pre className="p-4 rounded-xl bg-black/40 font-mono text-sm text-slate-400">
{`{
  "blocks": [
    {
      "name": "function_name",
      "type": "function",
      "commented_code": "string",
      "documentation": "string"
    }
  ],
  "full_commented_code": "string",
  "language": "python"
}`}
                </pre>
              </div>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="px-6 max-w-4xl mx-auto text-center">
          <div className="p-12 rounded-3xl bg-gradient-to-r from-indigo-600/20 to-violet-600/20 border border-indigo-500/20">
            <h2 className="text-3xl font-bold mb-4">Ready to try it?</h2>
            <p className="text-slate-400 mb-8 max-w-xl mx-auto">
              Start generating professional documentation for your code in seconds.
            </p>
            <Link
              href="/generate"
              className="inline-flex items-center gap-2 px-8 py-4 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-semibold shadow-lg shadow-indigo-600/25 transition-all"
            >
              <Terminal className="w-5 h-5" />
              Try It Now
              <ChevronRight className="w-5 h-5" />
            </Link>
          </div>
        </section>
      </main>
    </div>
  );
}