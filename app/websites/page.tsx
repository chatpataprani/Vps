"use client";

import { useMemo, useState } from "react";
import Link from "next/link";

type Site = { name:string; domain:string; kind:string; status:"Ready"|"Draft"; path:string };
const seed:Site[]=[
 {name:"Example website",domain:"example.com",kind:"Static HTML",status:"Ready",path:"sites/example.com"},
 {name:"Documentation",domain:"docs.example.com",kind:"Static HTML",status:"Draft",path:"sites/docs.example.com"},
];
export default function WebsitesPage(){
 const [sites,setSites]=useState(seed),[q,setQ]=useState(""),[modal,setModal]=useState(false),[name,setName]=useState(""),[domain,setDomain]=useState("");
 const filtered=useMemo(()=>sites.filter(s=>(s.name+s.domain+s.kind).toLowerCase().includes(q.toLowerCase())),[sites,q]);
 function create(){if(!name.trim()||!domain.trim())return;setSites(v=>[{name,domain,kind:"Static HTML",status:"Draft",path:"sites/"+domain},...v]);setName("");setDomain("");setModal(false)}
 return <main className="mx-auto max-w-6xl p-5 md:p-8 text-slate-100">
 <div className="flex flex-wrap items-center justify-between gap-4"><div><p className="text-sm text-cyan-300">HOSTING / PROJECTS</p><h1 className="text-3xl font-semibold mt-2">Websites</h1><p className="text-slate-400 mt-2">Manage static sites and prepare app deployments.</p></div><button onClick={()=>setModal(true)} className="rounded-xl bg-cyan-500 px-4 py-3 font-medium text-slate-950">＋ Create website</button></div>
 <div className="mt-7 rounded-2xl border border-slate-700 bg-slate-900/70 p-4"><input value={q} onChange={e=>setQ(e.target.value)} placeholder="Search websites…" className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-cyan-400"/>
 <div className="mt-4 grid gap-3 sm:grid-cols-2">{filtered.map(s=><article key={s.domain} className="rounded-xl border border-slate-700 bg-slate-900 p-4"><div className="flex items-start justify-between"><div><h2 className="font-semibold">{s.name}</h2><p className="mt-1 text-sm text-cyan-300">{s.domain}</p></div><span className={s.status==="Ready"?"text-emerald-300":"text-amber-300"}>{s.status}</span></div><p className="mt-4 text-sm text-slate-400">{s.kind} · {s.path}</p><div className="mt-4 flex flex-wrap gap-2"><button className="rounded-lg border border-slate-700 px-3 py-2 text-sm" onClick={()=>navigator.clipboard?.writeText(s.path)}>Copy path</button><Link href="/terminal" className="rounded-lg border border-slate-700 px-3 py-2 text-sm">Open terminal</Link></div></article>)}</div>
 {!filtered.length&&<p className="py-10 text-center text-slate-400">No websites match your search.</p>}</div>
 <div className="mt-5 rounded-xl border border-amber-900/60 bg-amber-950/20 p-4 text-sm text-amber-200">Preview mode: this page currently stores website entries in browser memory. Deploy, upload, domain, and SSL actions require the server agent and backend, which are not connected yet.</div>
 {modal&&<div className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-4"><section className="w-full max-w-md rounded-2xl border border-slate-700 bg-slate-900 p-5"><h2 className="text-xl font-semibold">Create website</h2><label className="mt-4 block text-sm text-slate-300">Website name<input value={name} onChange={e=>setName(e.target.value)} className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 p-3"/></label><label className="mt-4 block text-sm text-slate-300">Domain<input value={domain} onChange={e=>setDomain(e.target.value)} placeholder="example.com" className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 p-3"/></label><p className="mt-3 text-xs text-slate-400">Creates a local preview entry only—not a live deployment.</p><div className="mt-5 flex justify-end gap-2"><button onClick={()=>setModal(false)} className="rounded-lg px-4 py-2 text-slate-300">Cancel</button><button onClick={create} className="rounded-lg bg-cyan-500 px-4 py-2 font-medium text-slate-950">Create</button></div></section></div>}
 </main>
}