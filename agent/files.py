"""Confined file manager API. All operations stay inside VPS_FILES_ROOT."""
import os, hmac
from pathlib import Path
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

router=APIRouter(prefix="/api/files",tags=["files"])
ROOT=Path(os.environ.get("VPS_FILES_ROOT","./sites")).resolve()
TOKEN=os.environ.get("VPS_AGENT_TOKEN","")
MAX_TEXT=1024*1024

def auth(v):
    if not TOKEN or not hmac.compare_digest(v.removeprefix("Bearer ").strip(),TOKEN):
        raise HTTPException(401,"Unauthorized")

def safe(path:str)->Path:
    if not path or path.startswith("/") or "\\" in path or any(x in (".","..") for x in path.split("/")):
        raise HTTPException(400,"Invalid relative path")
    target=(ROOT/path).resolve()
    if target!=ROOT and ROOT not in target.parents: raise HTTPException(400,"Path outside file root")
    cur=ROOT
    for part in path.split("/"):
        cur=cur/part
        if cur.is_symlink(): raise HTTPException(400,"Symlinks are not allowed")
    return target

class FileWrite(BaseModel):
    path:str=Field(min_length=1,max_length=512)
    content:str=Field(max_length=MAX_TEXT)
class FolderCreate(BaseModel):
    path:str=Field(min_length=1,max_length=512)

@router.get("")
def list_files(path:str="",authorization:str=Header(default="")):
    auth(authorization); ROOT.mkdir(parents=True,exist_ok=True)
    p=ROOT if not path else safe(path)
    if not p.exists(): raise HTTPException(404,"Path not found")
    if not p.is_dir(): raise HTTPException(400,"Not a directory")
    rows=[]
    for x in sorted(p.iterdir(),key=lambda z:(not z.is_dir(),z.name.lower())):
        if x.is_symlink(): continue
        st=x.stat()
        rows.append({"name":x.name,"path":str(x.relative_to(ROOT)),"type":"directory" if x.is_dir() else "file","size":st.st_size,"modified":st.st_mtime})
    return {"root":str(ROOT),"path":path,"items":rows}

@router.get("/content")
def read_file(path:str,authorization:str=Header(default="")):
    auth(authorization); p=safe(path)
    if not p.is_file(): raise HTTPException(404,"File not found")
    if p.stat().st_size>MAX_TEXT: raise HTTPException(413,"File exceeds 1 MiB text editor limit")
    try: return {"path":path,"content":p.read_text(encoding="utf-8")}
    except UnicodeDecodeError: raise HTTPException(415,"File is not UTF-8 text")

@router.post("/folder")
def create_folder(data:FolderCreate,authorization:str=Header(default="")):
    auth(authorization); p=safe(data.path); p.mkdir(parents=True,exist_ok=False); return {"created":data.path}

@router.post("/content")
def write_file(data:FileWrite,authorization:str=Header(default="")):
    auth(authorization); p=safe(data.path); p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists() and not p.is_file(): raise HTTPException(400,"Target is not a file")
    tmp=p.with_name(p.name+".vps-tmp")
    tmp.write_text(data.content,encoding="utf-8"); os.replace(tmp,p)
    return {"saved":data.path,"bytes":len(data.content.encode())}

@router.delete("")
def delete_file(path:str,authorization:str=Header(default="")):
    auth(authorization); p=safe(path)
    if not p.exists(): raise HTTPException(404,"Path not found")
    if p.is_dir(): raise HTTPException(400,"Directory deletion is disabled; delete files individually")
    p.unlink(); return {"deleted":path}
