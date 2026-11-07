"use client";
import dynamic from "next/dynamic";
const TerminalClient = dynamic(() => import("./terminal-client"), { ssr: false, loading: () => <main className="min-h-screen bg-[#080b12] p-6 text-slate-300">Loading terminal…</main> });
export default function TerminalLoader(){return <TerminalClient/>;}
