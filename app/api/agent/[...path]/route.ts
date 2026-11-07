import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
type Context = { params: Promise<{ path: string[] }> };
const ID = /^[a-zA-Z0-9_.-]{1,128}$/;
async function forward(req: NextRequest, ctx: Context, method: "GET" | "POST" | "DELETE") {
 const base=process.env.VPS_AGENT_URL?.replace(/\/$/,""),token=process.env.VPS_AGENT_TOKEN;
 if(!base||!token)return NextResponse.json({error:"Agent is not configured."},{status:503});
 const parts=(await ctx.params).path;let endpoint="";
 if(method==="GET"&&parts.join("/")==="system")endpoint="/api/system";
 else if(method==="GET"&&parts.join("/")==="docker/status")endpoint="/api/docker/status";
 else if(method==="GET"&&parts.join("/")==="docker/containers")endpoint="/api/docker/containers";
 else if(method==="GET"&&parts.length===4&&parts[0]==="docker"&&parts[1]==="containers"&&ID.test(parts[2])&&parts[3]==="logs")endpoint=`/api/docker/containers/${encodeURIComponent(parts[2])}/logs`;
 else if(method==="POST"&&parts.length===4&&parts[0]==="docker"&&parts[1]==="containers"&&ID.test(parts[2])&&parts[3]==="action")endpoint=`/api/docker/containers/${encodeURIComponent(parts[2])}/action`;
 else if(method==="GET"&&parts.join("/")==="files")endpoint="/api/files";
 else if(method==="GET"&&parts.join("/")==="files/content")endpoint="/api/files/content";
 else if(method==="GET"&&parts.join("/")==="files/download")endpoint="/api/files/download";
 else if(method==="POST"&&parts.join("/")==="files/upload")endpoint="/api/files/upload";
 else if(method==="POST"&&parts.join("/")==="files/folder")endpoint="/api/files/folder";
 else if(method==="POST"&&parts.join("/")==="files/content")endpoint="/api/files/content";
 else if(method==="DELETE"&&parts.join("/")==="files")endpoint="/api/files";
 else if(method==="GET"&&parts.join("/")==="sites")endpoint="/api/sites";
 else if(method==="POST"&&parts.join("/")==="sites")endpoint="/api/sites";
 else if(method==="DELETE"&&parts.length===2&&parts[0]==="sites"&&/^[a-z0-9.-]{1,253}$/i.test(parts[1]))endpoint=`/api/sites/${encodeURIComponent(parts[1])}`;
 else return NextResponse.json({error:"Route not allowed."},{status:404});
 const url=new URL(base+endpoint);if(endpoint.startsWith("/api/files")){const path=req.nextUrl.searchParams.get("path");if(path)url.searchParams.set("path",path)}if(endpoint.endsWith("/logs")){const tail=req.nextUrl.searchParams.get("tail");if(tail)url.searchParams.set("tail",String(Math.max(1,Math.min(1000,Number(tail)||200))))}
 try{const response=await fetch(url,{method,headers:{Authorization:`Bearer ${token}`,...(method==="POST"?{"Content-Type":"application/json"}:{})},...(method==="POST"?{body:await req.text()}:{}),cache:"no-store",signal:AbortSignal.timeout(15000)});return new NextResponse(await response.text(),{status:response.status,headers:{"Content-Type":response.headers.get("content-type")||"application/json","Cache-Control":"no-store"}})}catch{return NextResponse.json({error:"Agent unreachable. Check private connectivity."},{status:502})}
}
export async function GET(req:NextRequest,ctx:Context){return forward(req,ctx,"GET")}
export async function POST(req:NextRequest,ctx:Context){return forward(req,ctx,"POST")}
export async function DELETE(req:NextRequest,ctx:Context){return forward(req,ctx,"DELETE")}