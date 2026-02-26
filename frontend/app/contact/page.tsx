"use client";

import { motion } from "framer-motion";
import { Mail, MessageSquare, Send, Github, Twitter, Linkedin } from "lucide-react";
import Navbar from "@/components/Navbar";
import { useState } from "react";

const contactMethods = [
  {
    icon: Mail,
    title: "Email",
    description: "Drop us a line anytime",
    value: "hello@docgen.ai",
    href: "mailto:hello@docgen.ai",
  },
  {
    icon: MessageSquare,
    title: "Live Chat",
    description: "Available 9am-6pm EST",
    value: "Start a conversation",
    href: "#",
  },
  {
    icon: Twitter,
    title: "Twitter",
    description: "Follow us for updates",
    value: "@DocGenAI",
    href: "https://twitter.com/docgenai",
  },
];

export default function ContactPage() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    subject: "",
    message: "",
  });
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Handle form submission here
    console.log("Form submitted:", formData);
    setSubmitted(true);
    setTimeout(() => setSubmitted(false), 3000);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-slate-200">
      <Navbar />

      <main className="relative z-10 pt-32 pb-20">
        {/* Hero */}
        <section className="px-6 max-w-7xl mx-auto mb-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center max-w-3xl mx-auto"
          >
            <h1 className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-white via-indigo-200 to-indigo-400 bg-clip-text text-transparent">
              Get in Touch
            </h1>
            <p className="text-xl text-slate-400">
              Have questions? We'd love to hear from you. Send us a message and we'll respond as soon as possible.
            </p>
          </motion.div>
        </section>

        {/* Contact Methods */}
        <section className="px-6 max-w-5xl mx-auto mb-16">
          <div className="grid md:grid-cols-3 gap-6">
            {contactMethods.map((method, idx) => (
              <motion.a
                key={idx}
                href={method.href}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="p-6 rounded-2xl bg-white/5 border border-white/10 hover:border-indigo-500/50 hover:bg-white/10 transition-all group"
              >
                <div className="p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20 w-fit mb-4 group-hover:bg-indigo-500/20 transition-colors">
                  <method.icon className="w-6 h-6 text-indigo-400" />
                </div>
                <h3 className="text-lg font-semibold mb-1">{method.title}</h3>
                <p className="text-sm text-slate-400 mb-3">{method.description}</p>
                <p className="text-indigo-400 font-medium">{method.value}</p>
              </motion.a>
            ))}
          </div>
        </section>

        {/* Contact Form */}
        <section className="px-6 max-w-3xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="p-8 rounded-2xl bg-slate-950/50 border border-white/10"
          >
            <h2 className="text-2xl font-bold mb-6">Send us a Message</h2>

            {submitted ? (
              <div className="p-6 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-center">
                <div className="w-12 h-12 rounded-full bg-emerald-500/20 flex items-center justify-center mx-auto mb-4">
                  <Send className="w-6 h-6 text-emerald-400" />
                </div>
                <h3 className="text-lg font-semibold text-emerald-400 mb-2">Message Sent!</h3>
                <p className="text-slate-400">We'll get back to you as soon as possible.</p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Name
                    </label>
                    <input
                      type="text"
                      name="name"
                      value={formData.name}
                      onChange={handleChange}
                      required
                      className="w-full px-4 py-3 rounded-xl bg-black/40 border border-white/10 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500/50 transition-colors"
                      placeholder="John Doe"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Email
                    </label>
                    <input
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      required
                      className="w-full px-4 py-3 rounded-xl bg-black/40 border border-white/10 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500/50 transition-colors"
                      placeholder="john@example.com"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Subject
                  </label>
                  <select
                    name="subject"
                    value={formData.subject}
                    onChange={handleChange}
                    required
                    className="w-full px-4 py-3 rounded-xl bg-black/40 border border-white/10 text-slate-200 focus:outline-none focus:border-indigo-500/50 transition-colors appearance-none cursor-pointer"
                  >
                    <option value="">Select a topic</option>
                    <option value="general">General Inquiry</option>
                    <option value="sales">Sales Question</option>
                    <option value="support">Technical Support</option>
                    <option value="enterprise">Enterprise Plan</option>
                    <option value="partnership">Partnership</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Message
                  </label>
                  <textarea
                    name="message"
                    value={formData.message}
                    onChange={handleChange}
                    required
                    rows={5}
                    className="w-full px-4 py-3 rounded-xl bg-black/40 border border-white/10 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500/50 transition-colors resize-none"
                    placeholder="How can we help you?"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full flex items-center justify-center gap-2 px-8 py-4 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-semibold shadow-lg shadow-indigo-600/25 transition-all"
                >
                  <Send className="w-5 h-5" />
                  Send Message
                </button>
              </form>
            )}
          </motion.div>
        </section>

        {/* Social Links */}
        <section className="px-6 max-w-7xl mx-auto mt-20 text-center">
          <p className="text-slate-400 mb-6">Connect with us on social media</p>
          <div className="flex justify-center gap-4">
            {[Github, Twitter, Linkedin].map((Icon, idx) => (
              <a
                key={idx}
                href="#"
                className="p-3 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-indigo-500/50 transition-all"
              >
                <Icon className="w-5 h-5 text-slate-400 hover:text-indigo-400" />
              </a>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}