"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Sparkles, 
  Copy, 
  Check, 
  Code2, 
  FileText, 
  Zap,
  Terminal,
  ArrowRight,
  ChevronDown,
  ChevronUp,
  FunctionSquare,
  LassoIcon,
  ChevronDown as ChevronDownIcon
} from "lucide-react";
import Navbar from "@/components/Navbar";

// Language options
const languages = [
  { value: "python", label: "Python", icon: "🐍" },
  { value: "javascript", label: "JavaScript", icon: "📜" },
  { value: "typescript", label: "TypeScript", icon: "📘" },
  { value: "java", label: "Java", icon: "☕" },
  { value: "cpp", label: "C++", icon: "⚡" },
];

// Interfaces - DEFINED AT TOP LEVEL
interface CodeBlock {
  name: string;
  type: string;
  original_code: string;
  commented_code: string;
  documentation: string;
  start_line: number;
  end_line: number;
}

interface GenerateResponse {
  blocks: CodeBlock[];
  full_commented_code: string;
  language: string;
}

export default function GeneratePage() {
  const [code, setCode] = useState("");
  const [language, setLanguage] = useState("python");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<"full" | "blocks">("full");
  const [expandedBlock, setExpandedBlock] = useState<number | null>(0);
  const [showLangDropdown, setShowLangDropdown] = useState(false);

  async function generateDoc() {
    if (!code.trim()) return;
    setLoading(true);
    
    try {
      const res = await fetch("http://localhost:8000/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          code,
          language,
          top_k: 3,
        }),
      });

      if (!res.ok) throw new Error("Failed to generate");
      
      const data: GenerateResponse = await res.json();
      setResult(data);
      setExpandedBlock(0);
      
    } catch (error) {
      alert("Failed to generate documentation");
      console.error(error);
    }
    
    setLoading(false);
  }

  const handleCopy = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const lineCount = code.split("\n").length;
  const selectedLang = languages.find(l => l.value === language);

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-slate-200 selection:bg-indigo-500/30">
      {/* Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-indigo-600/20 rounded-full blur-[128px] animate-pulse" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-violet-600/10 rounded-full blur-[128px] animate-pulse delay-1000" />
      </div>

      <Navbar />

      <main className="relative z-10 pt-24 pb-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        {/* Header */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 text-center"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 mb-4 backdrop-blur-md">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            <span className="text-sm font-medium text-slate-400">AI-Powered</span>
          </div>
          
          <h1 className="text-4xl md:text-5xl font-bold mb-2 bg-gradient-to-r from-white via-indigo-200 to-indigo-400 bg-clip-text text-transparent">            
            Comment Generator            
          </h1>          

          <p className="text-slate-400 max-w-2xl mx-auto">            
            Select your language and paste your code to generate inline comments automatically            
          </p>          
        </motion.div>

        {/* Language Selector */}
        <div className="flex justify-center mb-6">
          <div className="relative">
            <button
              onClick={() => setShowLangDropdown(!showLangDropdown)}
              className="flex items-center gap-3 px-6 py-3 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
            >
              <span className="text-2xl">{selectedLang?.icon}</span>
              <span className="font-medium">{selectedLang?.label}</span>
              <ChevronDownIcon className={`w-5 h-5 transition-transform ${showLangDropdown ? 'rotate-180' : ''}`} />
            </button>
            
            <AnimatePresence>
              {showLangDropdown && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="absolute top-full left-0 right-0 mt-2 py-2 rounded-xl bg-slate-900 border border-white/10 shadow-xl z-50"
                >
                  {languages.map((lang) => (
                    <button
                      key={lang.value}
                      onClick={() => {
                        setLanguage(lang.value);
                        setShowLangDropdown(false);
                      }}
                      className={`w-full flex items-center gap-3 px-4 py-3 hover:bg-white/5 transition-colors ${
                        language === lang.value ? 'bg-white/10 text-indigo-400' : 'text-slate-300'
                      }`}
                    >
                      <span className="text-xl">{lang.icon}</span>
                      <span>{lang.label}</span>
                      {language === lang.value && <Check className="w-4 h-4 ml-auto" />}
                    </button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Main Workspace */}
        <div className="grid lg:grid-cols-2 gap-6 h-[calc(100vh-380px)] min-h-[500px]">
          {/* LEFT PANEL - Input */}
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-slate-950/50 border border-white/10 rounded-2xl overflow-hidden backdrop-blur-xl flex flex-col"
          >
            <div className="flex items-center justify-between px-5 py-4 border-b border-white/5 bg-white/[0.02]">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20">
                  <Code2 className="w-4 h-4 text-indigo-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-200">Source Code</h3>
                  <p className="text-xs text-slate-500">{lineCount} lines • {selectedLang?.label}</p>
                </div>
              </div>
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/30" />
                <div className="w-3 h-3 rounded-full bg-yellow-500/20 border border-yellow-500/30" />
                <div className="w-3 h-3 rounded-full bg-green-500/20 border border-green-500/30" />
              </div>
            </div>

            <div className="relative flex-1">
              <textarea
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder={`// Paste your ${selectedLang?.label} code here...`}
                className="w-full h-full bg-transparent p-5 pl-14 font-mono text-sm leading-relaxed resize-none focus:outline-none text-slate-300 placeholder:text-slate-600"
                spellCheck={false}
              />
              
              <div className="absolute left-0 top-0 bottom-0 w-10 bg-slate-950/30 border-r border-white/5 text-right pr-2 pt-5 text-xs text-slate-600 font-mono select-none">
                {Array.from({ length: Math.max(lineCount, 20) }, (_, i) => (
                  <div key={i}>{i + 1}</div>
                ))}
              </div>
            </div>

            <div className="p-4 border-t border-white/5 bg-white/[0.02]">
              <button
                onClick={generateDoc}
                disabled={loading || !code.trim()}
                className="group relative w-full flex items-center justify-center gap-3 py-3 px-6 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 shadow-lg shadow-indigo-600/25 overflow-hidden"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
                
                {loading ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span className="font-semibold">Analyzing {selectedLang?.label}...</span>
                  </>
                ) : (
                  <>
                    <Zap className="w-5 h-5 fill-current" />
                    <span className="font-semibold">Generate Comments</span>
                    <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </>
                )}
              </button>
            </div>
          </motion.div>

          {/* RIGHT PANEL - Output */}
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-slate-950/50 border border-white/10 rounded-2xl overflow-hidden backdrop-blur-xl flex flex-col"
          >
            {/* Tabs */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-white/5 bg-white/[0.02]">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                  <FileText className="w-4 h-4 text-emerald-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-200">Generated Output</h3>
                  {result && (
                    <p className="text-xs text-slate-500">
                      {result.blocks.length} block{result.blocks.length !== 1 ? 's' : ''} found
                    </p>
                  )}
                </div>
              </div>
              
              {result && (
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setActiveTab("full")}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                      activeTab === "full" 
                        ? "bg-white/10 text-white" 
                        : "text-slate-400 hover:text-white"
                    }`}
                  >
                    Full Code
                  </button>
                  <button
                    onClick={() => setActiveTab("blocks")}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                      activeTab === "blocks" 
                        ? "bg-white/10 text-white" 
                        : "text-slate-400 hover:text-white"
                    }`}
                  >
                    By Block
                  </button>
                </div>
              )}
            </div>

            {/* Content */}
            <div className="flex-1 overflow-auto relative">
              {!result ? (
                <div className="h-full flex flex-col items-center justify-center text-slate-600 p-8">
                  <Terminal className="w-12 h-12 mb-4 opacity-50" />
                  <p className="text-center">Your generated documentation will appear here</p>
                  <p className="text-sm mt-2 opacity-60">Paste code and click generate to start</p>
                </div>
              ) : activeTab === "full" ? (
                /* Full Code View */
                <div className="relative min-h-full">
                  <div className="sticky top-0 right-0 p-4 flex justify-end bg-gradient-to-b from-slate-950/80 to-transparent z-10">
                    <button
                      onClick={() => handleCopy(result.full_commented_code)}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 border border-white/10 text-sm font-medium transition-colors backdrop-blur-md"
                    >
                      {copied ? (
                        <>
                          <Check className="w-4 h-4 text-emerald-400" />
                          <span className="text-emerald-400">Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-4 h-4" />
                          <span>Copy All</span>
                        </>
                      )}
                    </button>
                  </div>
                  
                  <pre className="px-5 pb-5 font-mono text-sm leading-relaxed text-slate-300 whitespace-pre-wrap break-all">
                    <code>{result.full_commented_code}</code>
                  </pre>
                </div>
              ) : (
                /* Blocks View */
                <div className="p-4 space-y-3">
                  {result.blocks.map((block, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: idx * 0.1 }}
                      className="border border-white/10 rounded-xl overflow-hidden bg-white/[0.02]"
                    >
                      {/* Block Header */}
                      <button
                        onClick={() => setExpandedBlock(expandedBlock === idx ? null : idx)}
                        className="w-full flex items-center justify-between p-4 hover:bg-white/5 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          {block.type === 'class' ? (
                            <LassoIcon className="w-4 h-4 text-purple-400" />
                          ) : (
                            <FunctionSquare className="w-4 h-4 text-blue-400" />
                          )}
                          <div className="text-left">
                            <span className="font-mono font-medium text-slate-200">
                              {block.name}
                            </span>
                            <span className="ml-2 text-xs text-slate-500 capitalize">
                              {block.type}
                            </span>
                          </div>
                        </div>
                        {expandedBlock === idx ? (
                          <ChevronUp className="w-4 h-4 text-slate-400" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-slate-400" />
                        )}
                      </button>

                      {/* Block Content */}
                      <AnimatePresence>
                        {expandedBlock === idx && (
                          <motion.div
                            initial={{ height: 0 }}
                            animate={{ height: "auto" }}
                            exit={{ height: 0 }}
                            className="overflow-hidden"
                          >
                            <div className="p-4 pt-0 space-y-4">
                              {/* Documentation */}
                              {block.documentation && (
                                <div>
                                  <div className="flex items-center justify-between mb-2">
                                    <span className="text-xs font-medium text-emerald-400 uppercase tracking-wider">
                                      Function Docstring
                                    </span>
                                    <button
                                      onClick={() => handleCopy(block.documentation)}
                                      className="text-xs text-indigo-400 hover:text-indigo-300 px-2 py-1 rounded hover:bg-white/5"
                                    >
                                      Copy
                                    </button>
                                  </div>
                                  <pre className="p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/20 font-mono text-sm text-emerald-300/90 whitespace-pre-wrap">
                                    {block.documentation}
                                  </pre>
                                </div>
                              )}

                              {/* Commented Code */}
                              <div>
                                <div className="flex items-center justify-between mb-2">
                                  <span className="text-xs font-medium text-blue-400 uppercase tracking-wider">
                                    Code with Comments
                                  </span>
                                  <button
                                    onClick={() => handleCopy(block.commented_code)}
                                    className="text-xs text-indigo-400 hover:text-indigo-300 px-2 py-1 rounded hover:bg-white/5"
                                  >
                                    Copy
                                  </button>
                                </div>
                                <pre className="p-3 rounded-lg bg-black/40 border border-white/10 font-mono text-sm text-slate-300 overflow-x-auto whitespace-pre">
                                  <code>{block.commented_code}</code>
                                </pre>
                              </div>
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        </div>
      </main>
    </div>
  );
}