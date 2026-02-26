"use client";

import { forwardRef } from "react";
import { AlertCircle } from "lucide-react";  // Changed from ExclamationCircleIcon

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className = "", ...props }, ref) => {
    return (
      <div className="space-y-2">
        <label className="text-sm font-medium text-slate-300">
          {label}
        </label>
        <div className="relative">
          <input
            ref={ref}
            className={`w-full px-4 py-3 rounded-xl bg-white/5 border ${
              error ? "border-red-500/50" : "border-white/10"
            } text-white placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 transition-colors ${
              className
            }`}
            {...props}
          />
          {error && (
            <AlertCircle className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-red-500" />  // Changed here too
          )}
        </div>
        {error && (
          <p className="text-sm text-red-400">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";