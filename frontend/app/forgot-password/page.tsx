"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { CheckCircle2 } from "lucide-react";
import Navbar from "@/components/Navbar";
import { Input } from "@/components/Input";

const schema = z.object({
  email: z.string().email("Invalid email address"),
});

type Form = z.infer<typeof schema>;

const API_URL = process.env.NEXT_PUBLIC_API_URL || "[localhost](http://localhost:8000)";

export default function ForgotPasswordPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState("");

  const { register, handleSubmit, formState: { errors } } = useForm<Form>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: Form) => {
    setIsLoading(true);
    setError("");

    try {
      const res = await fetch(`${API_URL}/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: data.email }),
      });

      const responseData = await res.json();

      if (!res.ok) throw new Error(responseData.detail || "Something went wrong");

      setIsSuccess(true);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  if (isSuccess) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] text-slate-200">
        <Navbar />
        <div className="relative z-10 pt-32 pb-20 px-6">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="max-w-md mx-auto text-center"
          >
            <div className="bg-slate-950/50 border border-white/10 rounded-2xl p-8 backdrop-blur-xl">
              <CheckCircle2 className="w-16 h-16 text-emerald-400 mx-auto mb-4" />
              <h1 className="text-2xl font-bold mb-2">Check your email</h1>
              <p className="text-slate-400 mb-6">
                If that email exists, we've sent a reset link. Check your inbox.
              </p>
              <Link
                href="/login"
                className="inline-block py-3 px-6 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 text-white font-semibold"
              >
                Back to Login
              </Link>
            </div>
          </motion.div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-slate-200">
      <Navbar />
      <div className="relative z-10 pt-32 pb-20 px-6">
        <div className="max-w-md mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-slate-950/50 border border-white/10 rounded-2xl p-8 backdrop-blur-xl"
          >
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold mb-2">Forgot Password</h1>
              <p className="text-slate-400">
                Enter your email and we'll send you a reset link
              </p>
            </div>

            {error && (
              <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              <Input
                label="Email"
                type="email"
                placeholder="you@example.com"
                error={errors.email?.message}
                {...register("email")}
              />

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-semibold shadow-lg shadow-indigo-600/25 transition-all disabled:opacity-50"
              >
                {isLoading ? "Sending..." : "Send Reset Link"}
              </button>
            </form>

            <p className="mt-8 text-center text-sm text-slate-400">
              Remember your password?{" "}
              <Link href="/login" className="text-indigo-400 hover:text-indigo-300 font-medium">
                Sign in
              </Link>
            </p>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
