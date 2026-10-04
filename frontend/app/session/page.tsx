"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { refreshSession } from "@/services/api";
export default function Session() {
  const router = useRouter();
  useEffect(() => {
    refreshSession().then((ok) => router.replace(ok ? "/dashboard" : "/login"));
  }, [router]);
  return <div className="session-loading">Restoring your session…</div>;
}
