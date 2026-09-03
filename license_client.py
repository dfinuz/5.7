import hashlib,json,os,socket,urllib.request,urllib.error,winreg
from pathlib import Path
from tkinter import messagebox,simpledialog
URL="https://vadmdnxwrkjpfppsfwkj.supabase.co/functions/v1/activate-dskeys-license"
F=Path(os.environ.get("APPDATA",str(Path.home())))/"DFIN_DSKEYS_Manager"/"license.json"
def did():
 v=[socket.gethostname()]
 try:
  with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r"SOFTWARE\Microsoft\Cryptography") as k:v.append(str(winreg.QueryValueEx(k,"MachineGuid")[0]))
 except OSError:pass
 return hashlib.sha256("|".join(v).encode()).hexdigest()
def ensure_license(parent):
 try:key=json.loads(F.read_text()).get("license_key","")
 except:key=""
 while True:
  if not key:
   key=simpledialog.askstring("DFIN licence","Enter your DFIN licence key:",parent=parent)
   if key is None:return False
  try:
   d=json.dumps({"license_key":key.strip().upper(),"device_id":did(),"app_version":"5.7"}).encode();q=urllib.request.Request(URL,data=d,headers={"Content-Type":"application/json"},method="POST")
   with urllib.request.urlopen(q,timeout=20) as r:res=json.loads(r.read())
  except urllib.error.HTTPError as e:
   try:res=json.loads(e.read())
   except:res={"ok":False,"message":"Licence rejected"}
  except Exception as e:messagebox.showerror("Licence connection failed",str(e),parent=parent);return False
  if res.get("ok"):
   F.parent.mkdir(parents=True,exist_ok=True);F.write_text(json.dumps({"license_key":key.strip().upper()}));return True
  messagebox.showerror("Licence rejected",res.get("message","Invalid licence"),parent=parent);key=""
