"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";

export default function AuthCallback() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const token = searchParams.get("token");
    const email = searchParams.get("email"); // Add this if backend sends it
    const error = searchParams.get("error");
    
    if (error) {
      console.error("Auth error:", error);
      router.push("/login?error=auth_failed");
      return;
    }
    
    if (token) {
      localStorage.setItem("token", token);
      
      // Store email if provided, otherwise use a default or fetch it
      if (email) {
        localStorage.setItem("email", email);
      } else {
        // If backend doesn't send email, you might need to fetch it
        // or set a temporary one that gets updated later
        localStorage.setItem("email", "user@example.com"); // placeholder
      }
      
      // Notify Navbar to update immediately (critical!)
      window.dispatchEvent(new Event("storage"));
      window.dispatchEvent(new Event("auth-change"));
      
      router.push("/generate");
    } else {
      router.push("/login?error=no_token");
    }
  }, [searchParams, router]);

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center text-white">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500 mx-auto mb-4"></div>
        <p>Completing sign in...</p>
      </div>
    </div>
  );
}