"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Eye, EyeOff, Github, Chrome, CheckCircle2 } from "lucide-react";
import Navbar from "@/components/Navbar";
import { Input } from "@/components/Input";

const signupSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Invalid email address"),
  password: z.string()
    .min(8, "Password must be at least 8 characters")
    .regex(/[A-Z]/, "Must contain at least one uppercase letter")
    .regex(/[a-z]/, "Must contain at least one lowercase letter")
    .regex(/[0-9]/, "Must contain at least one number"),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

type SignupForm = z.infer<typeof signupSchema>;

// API URL - backend address
const API_URL = "http://localhost:8000";

export default function SignupPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState("");

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<SignupForm>({
    resolver: zodResolver(signupSchema),
  });

  const password = watch("password", "");

  const passwordRequirements = [
    { label: "At least 8 characters", met: password.length >= 8 },
    { label: "One uppercase letter", met: /[A-Z]/.test(password) },
    { label: "One lowercase letter", met: /[a-z]/.test(password) },
    { label: "One number", met: /[0-9]/.test(password) },
  ];

  // Sign up with email/password
  const onSubmit = async (data: SignupForm) => {
  setIsLoading(true);
  setError("");
  
  try {
    const res = await fetch(`${API_URL}/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: data.name,
        email: data.email,
        password: data.password,
      }),
    });
    
    if (!res.ok) {
      const err = await res.json();
  console.log("Full error:", JSON.stringify(err, null, 2)); // add this
  const detail = err.detail;
  throw new Error(
    typeof detail === "string"
      ? detail
      : Array.isArray(detail)
      ? detail.map((e: any) => e.msg).join(", ")
      : "Signup failed"
      );
    }

    const responseData = await res.json();
    console.log("Signup response:", responseData);

    localStorage.setItem("token", responseData.access_token);
    localStorage.setItem("email", data.email);
    localStorage.setItem("name", data.name);
    window.dispatchEvent(new Event("auth-change"));

    setIsSuccess(true);
  } catch (err: any) {
    setError(err.message);
  } finally {
    setIsLoading(false);
  }
};


  // Sign up with GitHub
  const handleGithubSignup = () => {
    window.location.href = `${API_URL}/auth/github`;
  };

  // Sign up with Google
  const handleGoogleSignup = () => {
    window.location.href = `${API_URL}/auth/google`;
  };

  // Show success message after signup
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
              <h1 className="text-2xl font-bold mb-2">Account Created!</h1>
              <p className="text-slate-400 mb-6">
                Your account has been created successfully.
              </p>
              <Link
                href="/login"
                className="inline-block py-3 px-6 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 text-white font-semibold"
              >
                Go to Login
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
              <h1 className="text-3xl font-bold mb-2">Create Account</h1>
              <p className="text-slate-400">
                Start generating documentation for free
              </p>
            </div>

            {/* Error message */}
            {error && (
              <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              <Input
                label="Full Name"
                placeholder="John Doe"
                error={errors.name?.message}
                {...register("name")}
              />

              <Input
                label="Email"
                type="email"
                placeholder="you@example.com"
                error={errors.email?.message}
                {...register("email")}
              />

              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-300">
                  Password
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
                    {...register("password")}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
                  >
                    {showPassword ? (
                      <EyeOff className="w-5 h-5" />
                    ) : (
                      <Eye className="w-5 h-5" />
                    )}
                  </button>
                </div>
                
                {/* Password Requirements */}
                <div className="space-y-1 mt-2">
                  {passwordRequirements.map((req, idx) => (
                    <div
                      key={idx}
                      className={`flex items-center gap-2 text-xs ${
                        req.met ? "text-emerald-400" : "text-slate-500"
                      }`}
                    >
                      <div
                        className={`w-1.5 h-1.5 rounded-full ${
                          req.met ? "bg-emerald-400" : "bg-slate-600"
                        }`}
                      />
                      {req.label}
                    </div>
                  ))}
                </div>
              </div>

              <Input
                label="Confirm Password"
                type="password"
                placeholder="••••••••"
                error={errors.confirmPassword?.message}
                {...register("confirmPassword")}
              />

              <div className="flex items-start gap-2 text-sm text-slate-400">
                <input
                  type="checkbox"
                  className="mt-1 rounded bg-white/5 border-white/10"
                />
                <span>
                  I agree to the{" "}
                  <Link href="/terms" className="text-indigo-400 hover:text-indigo-300">
                    Terms of Service
                  </Link>{" "}
                  and{" "}
                  <Link href="/privacy" className="text-indigo-400 hover:text-indigo-300">
                    Privacy Policy
                  </Link>
                </span>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-semibold shadow-lg shadow-indigo-600/25 transition-all disabled:opacity-50"
              >
                {isLoading ? "Creating account..." : "Create Account"}
              </button>
            </form>

            <div className="mt-6">
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-white/10" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-slate-950 text-slate-400">
                    Or sign up with
                  </span>
                </div>
              </div>

              <div className="mt-6 grid grid-cols-2 gap-3">
                <button 
                  onClick={handleGithubSignup}
                  className="flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
                >
                  <Github className="w-5 h-5" />
                  <span className="text-sm">GitHub</span>
                </button>
                <button 
                  onClick={handleGoogleSignup}
                  className="flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
                >
                  <Chrome className="w-5 h-5" />
                  <span className="text-sm">Google</span>
                </button>
              </div>
            </div>

            <p className="mt-8 text-center text-sm text-slate-400">
              Already have an account?{" "}
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