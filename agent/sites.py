"""Static-site provisioning API for the Vps agent (prototype; bind privately)."""
import os, re, shutil
from pathlib import Path
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/sites", tags=["sites"])
ROOT = Path(os.environ.get("VPS_SITES_ROOT", "./sites")).resolve()
TOKEN = os.environ.get("VPS_AGENT_TOKEN", "")
DOMAIN = re.compile(r"^(?=.{1,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")

def auth(value):
    import hmac
    if not TOKEN or not hmac.compare_digest(value.removeprefix("Bearer "), TOKEN):
        raise HTTPException(401, "Unauthorized")

def site_path(domain):
    if not DOMAIN.fullmatch(domain.lower()):
        raise HTTPException(400, "Enter a valid domain name")
    p=(ROOT/domain.lower()).resolve()
    if p.parent != ROOT: raise HTTPException(400,"Invalid site path")
    return p

class SiteCreate(BaseModel):
    domain: str
    title: str = "Welcome"

@router.get("")
def list_sites(authorization: str=Header(default="")):
    auth(authorization); ROOT.mkdir(parents=True,exist_ok=True)
    return [{"domain":p.name,"path":str(p),"has_index":(p/"index.html").is_file()} for p in ROOT.iterdir() if p.is_dir()]

@router.post("")
def create_site(data: SiteCreate, authorization: str=Header(default="")):
    auth(authorization); p=site_path(data.domain); p.mkdir(parents=True,exist_ok=True)
    index=p/"index.html"
    if not index.exists():
        title=data.title.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")[:120]
        index.write_text(f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{title}</title><body><h1>{title}</h1><p>Deployed with Vps.</p></body></html>',encoding="utf-8")
    return {"domain":data.domain.lower(),"path":str(p),"created":True}

@router.delete("/{domain}")
def delete_site(domain: str, authorization: str=Header(default="")):
    auth(authorization); p=site_path(domain)
    if not p.exists(): raise HTTPException(404,"Site not found")
    shutil.rmtree(p); return {"deleted":domain}
