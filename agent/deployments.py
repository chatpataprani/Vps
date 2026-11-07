"""Git-to-Docker application deployments (private agent API; admin-only)."""
import hmac, os, re, shutil, subprocess, tempfile
from pathlib import Path
from urllib.parse import urlparse
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, HttpUrl

router=APIRouter(prefix="/api/deployments",tags=["deployments"])
TOKEN=os.environ.get("VPS_AGENT_TOKEN","")
WORK=Path(os.environ.get("VPS_DEPLOY_ROOT","/var/lib/vps/deployments")).resolve()
NAME=re.compile(r"^[a-z][a-z0-9-]{1,30}$")
ALLOWED={"github.com","gitlab.com","codeberg.org"}
PORTS=range(10000,20001)

def auth(v):
 if not TOKEN or not hmac.compare_digest(v.removeprefix("Bearer ").strip(),TOKEN):raise HTTPException(401,"Unauthorized")
def docker(*args,timeout=60):
 try:return subprocess.run(["docker",*args],capture_output=True,text=True,timeout=timeout,check=True).stdout
 except subprocess.CalledProcessError as e:raise HTTPException(400,(e.stderr or e.stdout or "Docker operation failed")[-3000:])
 except subprocess.TimeoutExpired:raise HTTPException(504,"Docker operation timed out")
def safe_repo(url):
 u=urlparse(url)
 if u.scheme!="https" or u.hostname not in ALLOWED or u.username or u.password or u.query or u.fragment:raise HTTPException(400,"Use a public HTTPS Git repository on GitHub, GitLab, or Codeberg")
 return url
class Create(BaseModel):
 name:str=Field(pattern=r"^[a-z][a-z0-9-]{1,30}$")
 repository:HttpUrl
 branch:str=Field(default="main",min_length=1,max_length=128,pattern=r"^[A-Za-z0-9._/-]+$")
 port:int=Field(default=3000,ge=1,le=65535)
 environment:str=Field(default="",max_length=12000)
@router.get("")
def list_deployments(authorization:str=Header(default="")):
 auth(authorization)
 raw=docker("ps","-a","--filter","label=vps.managed=true","--format","{{.Names}}|{{.Status}}|{{.Ports}}|{{.Label \"vps.repo\"}}")
 return [{"name":line.split("|",3)[0],"status":line.split("|",3)[1],"ports":line.split("|",3)[2],"repository":line.split("|",3)[3] if "|" in line else ""} for line in raw.splitlines() if line]
@router.post("")
def create_deployment(data:Create,authorization:str=Header(default="")):
 auth(authorization);safe_repo(str(data.repository))
 name=data.name.lower();env_lines=[]
 for line in data.environment.splitlines():
  if not line.strip():continue
  key,sep,value=line.partition("=")
  if not sep or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*",key) or "\\x00" in value:raise HTTPException(400,"Environment entries must be KEY=VALUE (valid variable names)")
  env_lines.append((key,value))
 if len({k for k,v in env_lines})!=len(env_lines):raise HTTPException(400,"Duplicate environment variable")
 name=data.name.lower();WORK.mkdir(parents=True,exist_ok=True);target=WORK/name
 if target.exists():raise HTTPException(409,"Deployment name already exists")
 existing=docker("ps","-a","--filter",f"name=^{name}$","--format","{{.Names}}").splitlines()
 if existing:raise HTTPException(409,"A container with this name already exists")
 try:
  with tempfile.TemporaryDirectory(prefix="vps-build-",dir=str(WORK)) as tmp:
   subprocess.run(["git","clone","--depth","1","--branch",data.branch,"--",str(data.repository),tmp+"/src"],capture_output=True,text=True,timeout=180,check=True)
   source=Path(tmp+"/src")
   if not (source/"Dockerfile").is_file():raise HTTPException(400,"Repository must include a Dockerfile")
   docker("build","--pull","--tag",f"vps-{name}:latest","--label",f"vps.managed=true","--file",str(source/"Dockerfile"),str(source),timeout=600)
   used=set()
   for line in docker("ps","-a","--format","{{.Ports}}").splitlines():
    for m in re.findall(r"(?:0\.0\.0\.0|127\.0\.0\.1|\[::\]):(\d+)->",line):used.add(int(m))
   host=next((p for p in PORTS if p not in used),None)
   if host is None:raise HTTPException(503,"No free managed ports")
   docker("run","--detach","--name",name,"--restart","unless-stopped","--publish",f"127.0.0.1:{host}:{data.port}","--memory","512m","--cpus","1","--pids-limit","256","--label","vps.managed=true","--label",f"vps.repo={data.repository}","--label",f"vps.branch={data.branch}","--label",f"vps.host_port={host}","--label",f"vps.container_port={data.port}",*sum((["--env",f"{k}={v}"] for k,v in env_lines),[]),f"vps-{name}:latest")
   target.mkdir(exist_ok=True);(target/"deployment.json").write_text(__import__("json").dumps({"name":name,"repository":str(data.repository),"branch":data.branch,"host_port":host,"container_port":data.port}))
   return {"name":name,"repository":str(data.repository),"branch":data.branch,"host_port":host,"container_port":data.port,"url":f"http://127.0.0.1:{host}","status":"created"}
 except subprocess.TimeoutExpired:raise HTTPException(504,"Git clone/build timed out")
 except subprocess.CalledProcessError as e:raise HTTPException(400,(e.stderr or "Git clone failed")[-3000:])
@router.get("/{name}/logs")
def logs(name:str,tail:int=200,authorization:str=Header(default="")):
 auth(authorization)
 if not NAME.fullmatch(name):raise HTTPException(400,"Invalid name")
 return {"logs":docker("logs","--tail",str(max(1,min(tail,1000))),name,timeout=20)}
@router.post("/{name}/{action}")
def action(name:str,action:str,authorization:str=Header(default="")):
 auth(authorization)
 if not NAME.fullmatch(name) or action not in {"start","stop","restart"}:raise HTTPException(400,"Invalid action")
 docker(action,name);return {"name":name,"action":action,"ok":True}

@router.post("/{name}/redeploy")
def redeploy(name:str,authorization:str=Header(default="")):
 auth(authorization)
 if not NAME.fullmatch(name):raise HTTPException(400,"Invalid name")
 import json
 try:
  info=json.loads(docker("inspect",name))[0]
  labels=info.get("Config",{}).get("Labels",{})
  if labels.get("vps.managed")!="true":raise HTTPException(403,"Only Vps-managed deployments can be redeployed")
  repo=safe_repo(labels.get("vps.repo",""));branch=labels.get("vps.branch","main")
  host=int(labels["vps.host_port"]);port=int(labels["vps.container_port"])
  env=info.get("Config",{}).get("Env",[])
  if not repo:raise HTTPException(400,"Repository metadata missing; recreate deployment")
 except (KeyError,ValueError,IndexError):raise HTTPException(400,"Deployment metadata missing")
 try:
  with tempfile.TemporaryDirectory(prefix="vps-rebuild-",dir=str(WORK)) as tmp:
   subprocess.run(["git","clone","--depth","1","--branch",branch,"--",repo,tmp+"/src"],capture_output=True,text=True,timeout=180,check=True)
   source=Path(tmp+"/src")
   if not (source/"Dockerfile").is_file():raise HTTPException(400,"Repository must include a Dockerfile")
   docker("build","--pull","--tag",f"vps-{name}:latest","--label","vps.managed=true","--file",str(source/"Dockerfile"),str(source),timeout=600)
  docker("rm","--force",name)
  docker("run","--detach","--name",name,"--restart","unless-stopped","--publish",f"127.0.0.1:{host}:{port}","--memory","512m","--cpus","1","--pids-limit","256","--label","vps.managed=true","--label",f"vps.repo={repo}","--label",f"vps.branch={branch}","--label",f"vps.host_port={host}","--label",f"vps.container_port={port}",*sum((["--env",v] for v in env),[]),f"vps-{name}:latest")
  return {"name":name,"redeployed":True,"status":"recreated"}
 except subprocess.TimeoutExpired:raise HTTPException(504,"Redeploy timed out")
 except subprocess.CalledProcessError as e:raise HTTPException(400,(e.stderr or "Redeploy failed")[-3000:])

@router.delete("/{name}")
def delete(name:str,authorization:str=Header(default="")):
 auth(authorization)
 if not NAME.fullmatch(name):raise HTTPException(400,"Invalid name")
 raw=docker("inspect","--format","{{ index .Config.Labels \"vps.managed\" }}",name)
 if raw.strip()!="true":raise HTTPException(403,"Only Vps-managed deployments can be removed")
 docker("rm","--force",name);docker("image","rm",f"vps-{name}:latest")
 shutil.rmtree(WORK/name,ignore_errors=True);return {"deleted":name}
