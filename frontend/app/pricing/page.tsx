"use client";

import { motion } from "framer-motion";
import { Check, Zap, Building2, Users } from "lucide-react";
import Navbar from "@/components/Navbar";
import Link from "next/link";

const plans = [
  {
    name: "Free",
    description: "Perfect for trying out DocGen AI",
    price: "$0",
    period: "forever",
    icon: Zap,
    features: [
      "50 generations per month",
      "Python & JavaScript support",
      "Basic documentation",
      "Community support",
    ],
    cta: "Get Started",
    href: "/signup",
    popular: false,
  },
  {
    name: "Pro",
    description: "For professional developers",
    price: "$19",
    period: "/month",
    icon: Users,
    features: [
      "Unlimited generations",
      "All programming languages",
      "Advanced AI models",
      "Priority support",
      "API access",
      "Custom templates",
    ],
    cta: "Start Free Trial",
    href: "/signup",
    popular: true,
  },
  {
    name: "Enterprise",
    description: "For teams and organizations",
    price: "Custom",
    period: "",
    icon: Building2,
    features: [
      "Everything in Pro",
      "Self-hosted option",
      "SSO & SAML",
      "Dedicated support",
      "Custom AI training",
      "SLA guarantee",
      "Audit logs",
    ],
    cta: "Contact Sales",
    href: "/contact",
    popular: false,
  },
];

const faqs = [
  {
    q: "Can I upgrade or downgrade my plan?",
    a: "Yes, you can change your plan at any time. Upgrades take effect immediately, and downgrades at the end of your billing cycle.",
  },
  {
    q: "Is there a free trial for Pro?",
    a: "Yes, Pro plans come with a 14-day free trial. No credit card required.",
  },
  {
    q: "What happens if I exceed my generation limit?",
    a: "Free users can upgrade to Pro for unlimited generations. Pro users have fair-use limits that reset monthly.",
  },
  {
    q: "Do you offer refunds?",
    a: "Yes, we offer a 30-day money-back guarantee if you're not satisfied with our service.",
  },
];

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-slate-200">
      <Navbar />
      
      <main className="relative z-10 pt-32 pb-20">
        {/* Hero */}
        <section className="px-6 max-w-7xl mx-auto mb-20">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center max-w-3xl mx-auto"
          >
            <h1 className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-white via-indigo-200 to-indigo-400 bg-clip-text text-transparent">
              Simple, Transparent Pricing
            </h1>
            <p className="text-xl text-slate-400">
              Choose the plan that fits your needs. Start free, upgrade when you're ready.
            </p>
          </motion.div>
        </section>

        {/* Pricing Cards */}
        <section className="px-6 max-w-7xl mx-auto mb-20">
          <div className="grid md:grid-cols-3 gap-8">
            {plans.map((plan, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                className={`relative p-8 rounded-2xl border ${
                  plan.popular
                    ? "bg-gradient-to-b from-indigo-600/20 to-slate-950/50 border-indigo-500/50"
                    : "bg-slate-950/50 border-white/10"
                } backdrop-blur-xl`}
              >
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                    <span className="px-4 py-1 rounded-full bg-gradient-to-r from-indigo-600 to-violet-600 text-sm font-medium">
                      Most Popular
                    </span>
                  </div>
                )}
                
                <div className="p-3 rounded-xl bg-white/5 w-fit mb-6">
                  <plan.icon className="w-6 h-6 text-indigo-400" />
                </div>
                
                <h3 className="text-2xl font-bold mb-2">{plan.name}</h3>
                <p className="text-slate-400 mb-6">{plan.description}</p>
                
                <div className="mb-6">
                  <span className="text-4xl font-bold">{plan.price}</span>
                  <span className="text-slate-400">{plan.period}</span>
                </div>
                
                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature, fidx) => (
                    <li key={fidx} className="flex items-center gap-3 text-sm">
                      <Check className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                      <span className="text-slate-300">{feature}</span>
                    </li>
                  ))}
                </ul>
                
                <Link
                  href={plan.href}
                  className={`block w-full py-3 px-4 rounded-xl text-center font-semibold transition-all ${
                    plan.popular
                      ? "bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white shadow-lg shadow-indigo-600/25"
                      : "bg-white/5 hover:bg-white/10 border border-white/10 text-white"
                  }`}
                >
                  {plan.cta}
                </Link>
              </motion.div>
            ))}
          </div>
        </section>

        {/* Feature Comparison */}
        <section className="px-6 max-w-4xl mx-auto mb-20">
          <h2 className="text-3xl font-bold text-center mb-12">Compare Plans</h2>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="text-left py-4 px-4 font-medium text-slate-400">Feature</th>
                  <th className="text-center py-4 px-4 font-medium text-slate-400">Free</th>
                  <th className="text-center py-4 px-4 font-medium text-indigo-400">Pro</th>
                  <th className="text-center py-4 px-4 font-medium text-slate-400">Enterprise</th>
                </tr>
              </thead>
              <tbody className="text-sm">
                {[
                  ["Monthly Generations", "50", "Unlimited", "Unlimited"],
                  ["Languages", "2", "15+", "15+"],
                  ["API Access", "—", "✓", "✓"],
                  ["Custom Templates", "—", "✓", "✓"],
                  ["Priority Support", "—", "✓", "✓"],
                  ["SSO/SAML", "—", "—", "✓"],
                  ["Self-hosted", "—", "—", "✓"],
                ].map((row, idx) => (
                  <tr key={idx} className="border-b border-white/5">
                    <td className="py-4 px-4 text-slate-300">{row[0]}</td>
                    <td className="py-4 px-4 text-center text-slate-400">{row[1]}</td>
                    <td className="py-4 px-4 text-center text-indigo-400">{row[2]}</td>
                    <td className="py-4 px-4 text-center text-slate-400">{row[3]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* FAQ */}
        <section className="px-6 max-w-3xl mx-auto mb-20">
          <h2 className="text-3xl font-bold text-center mb-12">Frequently Asked Questions</h2>
          
          <div className="space-y-4">
            {faqs.map((faq, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="p-6 rounded-xl bg-white/5 border border-white/10"
              >
                <h3 className="font-semibold mb-2 text-white">{faq.q}</h3>
                <p className="text-slate-400 text-sm">{faq.a}</p>
              </motion.div>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="px-6 max-w-4xl mx-auto text-center">
          <div className="p-12 rounded-3xl bg-gradient-to-r from-indigo-600/20 to-violet-600/20 border border-indigo-500/20">
            <h2 className="text-3xl font-bold mb-4">Still have questions?</h2>
            <p className="text-slate-400 mb-8">
              Our team is here to help you choose the right plan.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/contact"
                className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-xl bg-white/10 hover:bg-white/20 border border-white/10 text-white font-semibold transition-all"
              >
                Contact Sales
              </Link>
              <Link
                href="/generate"
                className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-semibold shadow-lg shadow-indigo-600/25 transition-all"
              >
                Try for Free
              </Link>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}