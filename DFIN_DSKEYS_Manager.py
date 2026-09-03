import json
import os
import re
import shutil
import subprocess
import tempfile
import sys
import threading
import ssl
import traceback
import webbrowser
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from license_client import ensure_license
import websocket

APP_VERSION = "5.7"
APP_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / "DFIN_DSKEYS_Manager"
SETTINGS_FILE = APP_DIR / "settings.json"
def resource_path(name): return Path(getattr(sys,"_MEIPASS",Path(__file__).resolve().parent))/name

try:
    from send2trash import send2trash
except Exception:
    send2trash = None

TEXT = {
 "en": {
  "title":"DFIN DSKEYS Manager", "folder":"DSKEYS folder:", "browse":"Browse...", "scan":"Scan E-IMZO",
  "language":"Language:", "info":"Reads certificate expiry metadata from local E-IMZO. No PFX password is requested or stored.",
  "working":"Working", "soon":"Expiring within 30 days", "expired":"Expired", "duplicates":"Duplicates", "unmatched":"File not matched", "unknown":"Metadata unavailable",
  "name":"E-IMZO name", "expiry":"Expiry date", "owner":"Owner / company", "identity":"STIR / PINFL", "file":"Matched file / details",
  "move_all":"Move all expired", "move_selected":"Move selected expired", "recycle":"Recycle selected expired", "open":"Open selected location",
  "ready":"Click Scan E-IMZO. No PFX password is required.", "connecting":"Connecting to local E-IMZO and receiving certificate metadata...",
  "connect_failed":"E-IMZO connection failed", "keep_running":"Keep E-IMZO installed and running, then try again.", "eimzo_error":"E-IMZO error",
  "scan_complete":"Scan complete", "counts":"Working: {working} | Expiring soon: {soon} | Expired: {expired} | Unmatched: {unmatched} | Unknown: {unknown}",
  "no_validto":"E-IMZO metadata does not contain VALIDTO", "not_matched":"Metadata found, but physical file was not matched", "expires_soon":"Expires within 30 days",
  "nothing_move":"Nothing to move", "no_selected_move":"No matched expired files were selected.", "move_complete":"Move complete", "moved":"Moved {count} expired file(s) to:\n{folder}",
  "failures":"Failures:", "move_confirm_title":"Move all expired", "move_confirm":"Move {count} positively matched expired file(s)?\n\nWorking files will remain in DSKEYS.",
  "no_expired":"No expired files", "no_expired_text":"No matched expired files are available.", "nothing_selected":"Nothing selected", "select_expired":"Select one or more expired files first.",
  "recycle_unavailable":"Recycle Bin support unavailable", "recycle_confirm_title":"Recycle expired files", "recycle_confirm":"Send {count} expired file(s) to the Windows Recycle Bin?",
  "select_matched":"Select a matched file first.", "powered":"POWERED BY DFIN.UZ", "product":"DSKEYS Certificate Manager", "installed_note":"Python and required libraries are installed automatically by the DFIN installer.", "remove_key":"Remove key", "remove_confirm_title":"Remove key", "remove_confirm":"Send {count} selected key file(s) to the Windows Recycle Bin?", "duplicate_info":"Duplicate certificates are detected by certificate serial number.", "remove_duplicates":"Remove all duplicate copies", "remove_duplicates_confirm_title":"Remove duplicates", "remove_duplicates_confirm":"Send {count} duplicate files to Recycle Bin? One copy per group will remain.", "duplicates_removed":"Removed {count} duplicate files.", "working_stage":"Processing certificates..."
 },
 "uz": {
  "title":"DFIN DSKEYS kalitlar menejeri", "folder":"DSKEYS papkasi:", "browse":"Tanlash...", "scan":"E-IMZO ni tekshirish", "language":"Til:", "info":"Mahalliy E-IMZO orqali sertifikatlarning amal qilish muddatini o‘qiydi. PFX paroli so‘ralmaydi va saqlanmaydi.",
  "working":"Amaldagi", "soon":"30 kun ichida tugaydi", "expired":"Muddati tugagan", "duplicates":"Dublikatlar", "unmatched":"Fayl topilmadi", "unknown":"Ma’lumot mavjud emas", "name":"E-IMZO nomi", "expiry":"Amal qilish muddati", "owner":"Egasi / tashkilot", "identity":"STIR / JSHSHIR", "file":"Fayl / tafsilotlar",
  "move_all":"Barcha muddati tugaganlarni ko‘chirish", "move_selected":"Tanlanganlarni ko‘chirish", "recycle":"Tanlanganlarni Savatga o‘chirish", "open":"Fayl joylashuvini ochish", "ready":"E-IMZO ni tekshirish tugmasini bosing.", "connecting":"E-IMZO ga ulanmoqda...", "connect_failed":"E-IMZO ga ulanib bo‘lmadi", "keep_running":"E-IMZO o‘rnatilgan va ishga tushirilganini tekshiring. Ulanish 20 soniyada yakunlanmasa qayta urinib ko‘ring.", "eimzo_error":"E-IMZO xatosi", "scan_complete":"Tekshirish yakunlandi", "counts":"Amaldagi: {working} | Tez tugaydi: {soon} | Muddati tugagan: {expired} | Topilmadi: {unmatched} | Ma’lumot yo‘q: {unknown}",
  "no_validto":"VALIDTO mavjud emas", "not_matched":"Sertifikat ma’lumoti bor, fayl topilmadi", "expires_soon":"30 kun ichida tugaydi", "nothing_move":"Ko‘chirish uchun fayl yo‘q", "no_selected_move":"Fayl tanlanmagan.", "move_complete":"Amal bajarildi", "moved":"{count} ta fayl ko‘chirildi:\n{folder}", "failures":"Xatolar:", "move_confirm_title":"Fayllarni ko‘chirish", "move_confirm":"{count} ta fayl ko‘chirilsinmi?", "no_expired":"Fayl topilmadi", "no_expired_text":"Muddati tugagan fayl yo‘q.", "nothing_selected":"Hech narsa tanlanmagan", "select_expired":"Avval faylni tanlang.", "recycle_unavailable":"Windows Savati mavjud emas", "recycle_confirm_title":"Fayllarni o‘chirish", "recycle_confirm":"{count} ta fayl Savatga yuborilsinmi?", "select_matched":"Avval faylni tanlang.", "powered":"DFIN.UZ ISHLAB CHIQARGAN", "product":"DSKEYS sertifikatlar menejeri", "installed_note":"Python va kerakli kutubxonalar DFIN o‘rnatuvchisi tomonidan o‘rnatiladi.", "remove_key":"Kalitni o‘chirish", "remove_confirm_title":"Kalitni o‘chirish", "remove_confirm":"{count} ta fayl Savatga yuborilsinmi?", "duplicate_info":"Dublikatlar seriya raqami bo‘yicha aniqlanadi.", "remove_duplicates":"Barcha dublikat nusxalarni o‘chirish", "remove_duplicates_confirm_title":"Dublikatlarni o‘chirish", "remove_duplicates_confirm":"{count} ta dublikat Savatga yuborilsinmi? Har guruhdan bitta fayl qoladi.", "duplicates_removed":"{count} ta dublikat o‘chirildi.", "working_stage":"Sertifikatlar qayta ishlanmoqda..."
 },
 "ru": {
  "title":"DFIN Менеджер ключей DSKEYS", "folder":"Папка DSKEYS:", "browse":"Обзор...", "scan":"Сканировать E-IMZO",
  "language":"Язык:", "info":"Читает сроки действия сертификатов через локальный E-IMZO. Пароль PFX не запрашивается и не сохраняется.",
  "working":"Действующие", "soon":"Истекают в течение 30 дней", "expired":"Просроченные", "duplicates":"Дубликаты", "unmatched":"Файл не найден", "unknown":"Нет данных о сроке",
  "name":"Имя в E-IMZO", "expiry":"Срок действия", "owner":"Владелец / организация", "identity":"ИНН / ПИНФЛ", "file":"Файл / подробности",
  "move_all":"Переместить все просроченные", "move_selected":"Переместить выбранные", "recycle":"Удалить выбранные в Корзину", "open":"Открыть расположение файла",
  "ready":"Нажмите «Сканировать E-IMZO». Пароль PFX не требуется.", "connecting":"Подключение к локальному E-IMZO и получение данных сертификатов...",
  "connect_failed":"Не удалось подключиться к E-IMZO", "keep_running":"Убедитесь, что E-IMZO установлен и запущен, затем повторите попытку.", "eimzo_error":"Ошибка E-IMZO",
  "scan_complete":"Сканирование завершено", "counts":"Действующие: {working} | Скоро истекают: {soon} | Просроченные: {expired} | Файл не найден: {unmatched} | Нет данных: {unknown}",
  "no_validto":"В данных E-IMZO отсутствует VALIDTO", "not_matched":"Данные сертификата найдены, но физический файл не найден", "expires_soon":"Истекает в течение 30 дней",
  "nothing_move":"Нечего перемещать", "no_selected_move":"Не выбраны найденные просроченные файлы.", "move_complete":"Перемещение завершено", "moved":"Перемещено просроченных файлов: {count}\nПапка:\n{folder}",
  "failures":"Ошибки:", "move_confirm_title":"Переместить все просроченные", "move_confirm":"Переместить {count} точно найденных просроченных файлов?\n\nДействующие файлы останутся в DSKEYS.",
  "no_expired":"Просроченных файлов нет", "no_expired_text":"Нет найденных просроченных файлов.", "nothing_selected":"Ничего не выбрано", "select_expired":"Сначала выберите просроченные файлы.",
  "recycle_unavailable":"Корзина недоступна", "recycle_confirm_title":"Удалить просроченные файлы", "recycle_confirm":"Отправить {count} просроченных файлов в Корзину Windows?",
  "select_matched":"Сначала выберите найденный файл.", "powered":"РАЗРАБОТАНО DFIN.UZ", "product":"Менеджер сертификатов DSKEYS", "installed_note":"Python и необходимые библиотеки устанавливаются автоматически установщиком DFIN.", "remove_key":"Удалить ключ", "remove_confirm_title":"Удалить ключ", "remove_confirm":"Отправить {count} выбранных файлов ключей в Корзину Windows?", "duplicate_info":"Дубликаты определяются по серийному номеру сертификата.", "remove_duplicates":"Удалить все копии дубликатов", "remove_duplicates_confirm_title":"Удалить дубликаты", "remove_duplicates_confirm":"Отправить {count} дубликатов в Корзину? Одна копия останется.", "duplicates_removed":"Удалено дубликатов: {count}.", "working_stage":"Обработка сертификатов..."
 }
}

PS_SCRIPT = r'''$ErrorActionPreference = "Stop"
$token = [Threading.CancellationToken]::None
function Invoke-EImzoRequest([hashtable]$Request) {
 $socket = New-Object System.Net.WebSockets.ClientWebSocket
 $uri = [Uri]"wss://127.0.0.1:64443/service/cryptapi"
 $socket.ConnectAsync($uri, $token).GetAwaiter().GetResult()
 try {
  $json = $Request | ConvertTo-Json -Compress
  $bytes = [Text.Encoding]::UTF8.GetBytes($json)
  $segment = New-Object ArraySegment[byte] -ArgumentList (, $bytes)
  $socket.SendAsync($segment, [Net.WebSockets.WebSocketMessageType]::Text, $true, $token).GetAwaiter().GetResult()
  $stream = New-Object System.IO.MemoryStream
  try {
   do {
    $buffer = New-Object byte[] 65536
    $resultBuffer = New-Object ArraySegment[byte] -ArgumentList (, $buffer)
    $result = $socket.ReceiveAsync($resultBuffer, $token).GetAwaiter().GetResult()
    if ($result.MessageType -eq [Net.WebSockets.WebSocketMessageType]::Close) { break }
    $stream.Write($buffer, 0, $result.Count)
   } while (-not $result.EndOfMessage)
   $text = [Text.Encoding]::UTF8.GetString($stream.ToArray())
   return ($text | ConvertFrom-Json)
  } finally { $stream.Dispose() }
 } finally { $socket.Dispose() }
}
$apiKeys = @("localhost", "96D0C1491615C82B9A54D9989779DF825B690748224C2B04F500F370D51827CE2644D8D4A82C18184D73AB8530BB8ED537269603F61DB0D03D2104ABF789970B", "127.0.0.1", "A7BCFA5D490B351BE0754130DF03A068F855DB4333D43921125B9CF2670EF6A40370C646B90401955E1F7BC9CDBF59CE0B2C5467D820BE189C845D0B79CFC96F")
$apiResult = Invoke-EImzoRequest @{ name = "apikey"; arguments = $apiKeys }
if (-not $apiResult.success) { throw ("E-IMZO API key registration failed: " + $apiResult.reason) }
$data = Invoke-EImzoRequest @{ plugin = "pfx"; name = "list_all_certificates" }
$jsonOut = $data | ConvertTo-Json -Depth 20 -Compress
[IO.File]::WriteAllText($args[0], $jsonOut, (New-Object Text.UTF8Encoding($false)))
'''

@dataclass
class Record:
 name:str; path:Path|None; owner:str; tin:str; pinfl:str; serial:str
 valid_from:datetime|None; valid_to:datetime|None; status:str; details:str=""

def alias_value(alias, field):
 patterns={"TIN":[r"(?:^|,)inn=([^,]*)",r"(?:^|,)uid=([^,]*)"],"PINFL":[r"(?:^|,)1\.2\.860\.3\.16\.1\.2=([^,]*)",r"(?:^|,)pinfl=([^,]*)"]}
 for pattern in patterns.get(field,[rf"(?:^|,){re.escape(field)}=([^,]*)"]):
  match=re.search(pattern,alias,flags=re.I)
  if match:return match.group(1).strip()
 return ""

def parse_date(value):
 for fmt in ("%Y.%m.%d %H:%M:%S","%Y-%m-%d %H:%M:%S"):
  try:return datetime.strptime(value,fmt)
  except (ValueError,TypeError):pass
 return None

def load_settings():
 try:return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
 except Exception:return {}

def save_settings(data):
 try:
  APP_DIR.mkdir(parents=True,exist_ok=True); SETTINGS_FILE.write_text(json.dumps(data),encoding="utf-8")
 except Exception:pass

class App(tk.Tk):
 def __init__(self):
  super().__init__(); self.withdraw()
  if not ensure_license(self): self.destroy(); return
  settings=load_settings(); self.lang=settings.get("language","en");self.scan_running=False
  try:self.iconbitmap(default=str(resource_path("dfin_logo.ico")))
  except Exception:pass
  if self.lang not in TEXT:self.lang="en"
  self.folder_var=tk.StringVar(value=settings.get("folder",str(Path(os.environ.get("SystemDrive","C:"))/"DSKEYS")))
  self.language_var=tk.StringVar(value={"en":"English","uz":"O‘zbekcha","ru":"Русский"}.get(self.lang,"English"))
  self.status_var=tk.StringVar(); self.records=[]; self.duplicate_records=[]; self.geometry("1180x735"); self.minsize(920,580)
  self.build_ui(); self.apply_language(); self.deiconify()
 def t(self,key):return TEXT[self.lang][key]
 def build_ui(self):
  self.top=ttk.Frame(self,padding=12); self.top.pack(fill="x")
  self.header_logo=None
  try:
   raw_logo=tk.PhotoImage(file=str(resource_path("dfin_logo.png")))
   factor=max(1,raw_logo.width()//36);self.header_logo=raw_logo.subsample(factor,factor)
   ttk.Label(self.top,image=self.header_logo).grid(row=0,column=0,rowspan=2,sticky="nw",padx=(0,8))
  except Exception:pass
  self.folder_label=ttk.Label(self.top); self.folder_label.grid(row=0,column=1,sticky="w")
  ttk.Entry(self.top,textvariable=self.folder_var).grid(row=0,column=2,sticky="ew",padx=8)
  self.browse_btn=ttk.Button(self.top,command=self.browse); self.browse_btn.grid(row=0,column=3)
  self.scan_btn=ttk.Button(self.top,command=self.scan); self.scan_btn.grid(row=0,column=4,padx=(8,16))
  self.language_label=ttk.Label(self.top); self.language_label.grid(row=0,column=5,sticky="e")
  combo=ttk.Combobox(self.top,textvariable=self.language_var,values=("English","O‘zbekcha","Русский"),state="readonly",width=11)
  combo.grid(row=0,column=6,padx=(8,0)); combo.bind("<<ComboboxSelected>>",self.change_language); self.top.columnconfigure(2,weight=1)
  self.info_label=ttk.Label(self,foreground="#526070",padding=(12,0,12,10)); self.info_label.pack(fill="x")
  self.progress=ttk.Progressbar(self,mode="indeterminate")
  self.note_label=ttk.Label(self,foreground="#18794e",padding=(12,0,12,8)); self.note_label.pack(fill="x")
  self.notebook=ttk.Notebook(self); self.notebook.pack(fill="both",expand=True,padx=12); self.trees={}; self.tabs={}
  for status in ("working","soon","expired","duplicates","unmatched","unknown"):
   frame=ttk.Frame(self.notebook); self.notebook.add(frame,text=""); self.tabs[status]=frame
   tree=ttk.Treeview(frame,columns=("name","expiry","owner","id","file"),show="headings",selectmode="extended")
   widths={"name":250,"expiry":110,"owner":310,"id":150,"file":340}
   for col in widths:tree.column(col,width=widths[col],anchor="center" if col=="expiry" else "w")
   ys=ttk.Scrollbar(frame,orient="vertical",command=tree.yview); xs=ttk.Scrollbar(frame,orient="horizontal",command=tree.xview)
   tree.configure(yscrollcommand=ys.set,xscrollcommand=xs.set); tree.grid(row=0,column=0,sticky="nsew");ys.grid(row=0,column=1,sticky="ns");xs.grid(row=1,column=0,sticky="ew")
   frame.rowconfigure(0,weight=1);frame.columnconfigure(0,weight=1);self.trees[status]=tree;tree.bind("<Button-3>",lambda event,st=status:self.show_context_menu(event,st))
  actions=ttk.Frame(self,padding=12);actions.pack(fill="x")
  self.move_all_btn=ttk.Button(actions,command=self.move_all);self.move_all_btn.pack(side="left")
  self.move_selected_btn=ttk.Button(actions,command=self.move_selected);self.move_selected_btn.pack(side="left",padx=8)
  self.recycle_btn=ttk.Button(actions,command=self.recycle_selected);self.recycle_btn.pack(side="left")
  self.remove_duplicates_btn=ttk.Button(actions,command=self.remove_all_duplicate_copies);self.remove_duplicates_btn.pack(side="left",padx=8)
  self.open_btn=ttk.Button(actions,command=self.open_location);self.open_btn.pack(side="right")
  branding=tk.Frame(self,bg="#0B2F5E",height=40);branding.pack(fill="x");branding.pack_propagate(False)
  self.product_label=tk.Label(branding,bg="#0B2F5E",fg="#D8E8F5",font=("Segoe UI",9));self.product_label.pack(side="left",padx=14,pady=10)
  self.brand_label=tk.Label(branding,bg="#0B2F5E",fg="white",font=("Segoe UI",8),cursor="hand2");self.brand_label.pack(side="right",padx=14,pady=10)
  self.brand_label.bind("<Button-1>",lambda _e:webbrowser.open("https://www.dfin.uz"))
  ttk.Label(self,textvariable=self.status_var,padding=10).pack(fill="x")
 def apply_language(self):
  self.title(f"{self.t('title')} v{APP_VERSION}");self.folder_label.config(text=self.t("folder"));self.browse_btn.config(text=self.t("browse"));self.scan_btn.config(text=self.t("scan"));self.language_label.config(text=self.t("language"));self.info_label.config(text=self.t("info"));self.note_label.config(text=self.t("installed_note"))
  for status,frame in self.tabs.items():self.notebook.tab(frame,text=self.t(status))
  headings={"name":"name","expiry":"expiry","owner":"owner","id":"identity","file":"file"}
  for tree in self.trees.values():
   for col,key in headings.items():tree.heading(col,text=self.t(key))
  self.move_all_btn.config(text=self.t("move_all"));self.move_selected_btn.config(text=self.t("move_selected"));self.recycle_btn.config(text=self.t("recycle"));self.remove_duplicates_btn.config(text=self.t("remove_duplicates"));self.open_btn.config(text=self.t("open"));self.product_label.config(text=self.t("product"));self.brand_label.config(text=self.t("powered"))
  self.status_var.set(self.t("ready") if not self.records else self.count_text(self.t("scan_complete")))
 def change_language(self,_event=None):
  self.lang={"Русский":"ru","O‘zbekcha":"uz"}.get(self.language_var.get(),"en");save_settings({"language":self.lang,"folder":self.folder_var.get()});self.apply_language();self.refresh_rows()
 def browse(self):
  value=filedialog.askdirectory(initialdir=self.folder_var.get());
  if value:self.folder_var.set(value);save_settings({"language":self.lang,"folder":value})
 def _eimzo_request(self,host,origin,payload):
  ws=None
  try:
   ws=websocket.create_connection(f"wss://{host}:64443/service/cryptapi",timeout=8,origin=origin,sslopt={"cert_reqs":ssl.CERT_NONE,"check_hostname":False},suppress_origin=False)
   ws.settimeout(15);ws.send(json.dumps(payload));raw=ws.recv()
   if not raw:raise RuntimeError("E-IMZO returned an empty response")
   return json.loads(raw)
  finally:
   if ws:
    try:ws.close()
    except Exception:pass
 def fetch_eimzo(self):
  api_keys=["localhost","96D0C1491615C82B9A54D9989779DF825B690748224C2B04F500F370D51827CE2644D8D4A82C18184D73AB8530BB8ED537269603F61DB0D03D2104ABF789970B","127.0.0.1","A7BCFA5D490B351BE0754130DF03A068F855DB4333D43921125B9CF2670EF6A40370C646B90401955E1F7BC9CDBF59CE0B2C5467D820BE189C845D0B79CFC96F"]
  errors=[]
  for host in ("localhost","127.0.0.1"):
   for origin in ("https://localhost","https://127.0.0.1:64443","http://localhost"):
    try:
     registered=self._eimzo_request(host,origin,{"name":"apikey","arguments":api_keys})
     if not registered.get("success"):raise RuntimeError(registered.get("reason") or "API key registration failed")
     data=self._eimzo_request(host,origin,{"plugin":"pfx","name":"list_all_certificates"})
     return data
    except Exception as exc:errors.append(f"host={host}, origin={origin}: {type(exc).__name__}: {exc}")
  raise RuntimeError("All E-IMZO connection attempts failed:\n"+"\n".join(errors))
 def file_index(self,folder):
  result={}
  if folder.is_dir():
   for path in folder.rglob("*"):
    if path.is_file():
     for key in {path.name.casefold(),path.stem.casefold()}:result.setdefault(key,[]).append(path)
  return result
 def match_file(self,cert,index):
  name=str(cert.get("name","")).strip()
  for key in (name.casefold(),Path(name).stem.casefold(),f"{name}.pfx".casefold()):
   if index.get(key):return index[key][0]
  return None
 def scan(self):
  if self.scan_running:return
  self.scan_running=True;self.scan_btn.config(state="disabled");self.status_var.set(self.t("connecting"));self.progress.pack(fill="x",padx=12);self.progress.start(10)
  threading.Thread(target=self._scan_worker,daemon=True).start()
 def _scan_worker(self):
  try:data=self.fetch_eimzo()
  except Exception as exc:self.after(0,self._scan_failed,str(exc));return
  self.after(0,lambda:self.status_var.set(self.t("working_stage")))
  if not data.get("success"):self.after(0,self._scan_failed,str(data.get("reason") or data));return
  self.records=[];index=self.file_index(Path(self.folder_var.get().strip()));now=datetime.now()
  for cert in data.get("certificates") or []:
   alias=str(cert.get("alias") or "");valid_to=parse_date(alias_value(alias,"validto"));path=self.match_file(cert,index)
   if valid_to is None:status="unknown";details=self.t("no_validto")
   elif path is None:status="unmatched";details=self.t("not_matched")
   elif valid_to<=now:status="expired";details=self.t("expired")
   elif (valid_to-now).days<=30:status="soon";details=self.t("expires_soon")
   else:status="working";details=self.t("working")
   self.records.append(Record(str(cert.get("name") or ""),path,alias_value(alias,"cn") or alias_value(alias,"o"),alias_value(alias,"TIN"),alias_value(alias,"PINFL"),alias_value(alias,"serialnumber"),parse_date(alias_value(alias,"validfrom")),valid_to,status,details))
  groups={}
  for record in self.records:
   duplicate_key=(record.serial or record.name).strip().casefold()
   if duplicate_key:groups.setdefault(duplicate_key,[]).append(record)
  self.duplicate_records=[record for group in groups.values() if len(group)>1 for record in group]
  self.after(0,self._scan_finished)
 def _stop_progress(self):
  self.progress.stop();self.progress.pack_forget();self.scan_btn.config(state="normal");self.scan_running=False
 def _scan_failed(self,error):
  self._stop_progress();self.status_var.set(self.t("connect_failed"));messagebox.showerror(self.t("connect_failed"),f"{self.t('keep_running')}\n\n{error}")
 def _scan_finished(self):
  self._stop_progress();self.refresh_rows();self.status_var.set(self.count_text(self.t("scan_complete")));self.notebook.select(2 if any(r.status=="expired" for r in self.records) else 0)
 def refresh_rows(self):
  for tree in self.trees.values():tree.delete(*tree.get_children())
  for n,r in enumerate(self.records):self.trees[r.status].insert("","end",iid=f"{r.status}-{n}",values=(r.name,r.valid_to.strftime("%Y-%m-%d") if r.valid_to else "",r.owner,r.tin or r.pinfl,str(r.path) if r.path else r.details))
  for n,r in enumerate(self.duplicate_records):self.trees["duplicates"].insert("","end",iid=f"duplicates-{n}",values=(r.name,r.valid_to.strftime("%Y-%m-%d") if r.valid_to else "",r.owner,r.tin or r.pinfl,str(r.path) if r.path else r.details))
 def count_text(self,prefix):
  c={k:sum(r.status==k for r in self.records) for k in ("working","soon","expired","unmatched","unknown")};c["duplicates"]=len(self.duplicate_records);return f"{prefix}. "+self.t("counts").format(**c)+f" | {self.t('duplicates')}: {c['duplicates']}"
 def selected_records(self,status):
  paths={self.trees[status].item(i,"values")[4] for i in self.trees[status].selection()}
  source=self.duplicate_records if status=="duplicates" else [r for r in self.records if r.status==status]
  return [r for r in source if r.path and str(r.path) in paths]
 def show_context_menu(self,event,status):
  tree=self.trees[status];row=tree.identify_row(event.y)
  if row:
   if row not in tree.selection():tree.selection_set(row)
   menu=tk.Menu(self,tearoff=0);menu.add_command(label=self.t("remove_key"),command=lambda:self.remove_selected(status));menu.tk_popup(event.x_root,event.y_root)
 def remove_selected(self,status):
  records=self.selected_records(status)
  if not records:messagebox.showinfo(self.t("nothing_selected"),self.t("select_matched"));return
  if send2trash is None:messagebox.showerror(self.t("recycle_unavailable"),self.t("recycle_unavailable"));return
  unique=[];seen=set()
  for record in records:
   key=str(record.path).casefold()
   if key not in seen:seen.add(key);unique.append(record)
  if messagebox.askyesno(self.t("remove_confirm_title"),self.t("remove_confirm").format(count=len(unique)),icon="warning"):
   for record in unique:send2trash(str(record.path))
   self.scan()
 def remove_all_duplicate_copies(self):
  if send2trash is None:messagebox.showerror(self.t("recycle_unavailable"),self.t("recycle_unavailable"));return
  groups={}
  for r in self.records:
   k=(r.serial or r.name).strip().casefold()
   if k and r.path and r.path.exists():groups.setdefault(k,[]).append(r)
  extras=[]
  for group in groups.values():
   unique={str(r.path).casefold():r for r in group}.values();ordered=sorted(unique,key=lambda r:(r.valid_to or datetime.min,str(r.path)),reverse=True);extras.extend(ordered[1:])
  if not extras:messagebox.showinfo(self.t("nothing_move"),self.t("duplicate_info"));return
  if messagebox.askyesno(self.t("remove_duplicates_confirm_title"),self.t("remove_duplicates_confirm").format(count=len(extras)),icon="warning"):
   for r in extras:send2trash(str(r.path))
   messagebox.showinfo(self.t("move_complete"),self.t("duplicates_removed").format(count=len(extras)));self.scan()
 def target_folder(self):
  base=Path(self.folder_var.get().strip());target=base.parent/f"Expired_Keys_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}";target.mkdir(parents=True,exist_ok=False);return target
 def move_records(self,records):
  if not records:messagebox.showinfo(self.t("nothing_move"),self.t("no_selected_move"));return
  target=self.target_folder();moved=0;failed=[]
  for r in records:
   try:
    destination=target/r.path.name;counter=1
    while destination.exists():destination=target/f"{r.path.stem}_{counter}{r.path.suffix}";counter+=1
    shutil.move(str(r.path),str(destination));moved+=1
   except Exception as exc:failed.append(f"{r.name}: {exc}")
  msg=self.t("moved").format(count=moved,folder=target)
  if failed:msg+=f"\n\n{self.t('failures')}\n"+"\n".join(failed[:10])
  messagebox.showinfo(self.t("move_complete"),msg);self.scan()
 def move_all(self):
  records=[r for r in self.records if r.status=="expired" and r.path and r.path.exists()]
  if not records:messagebox.showinfo(self.t("no_expired"),self.t("no_expired_text"));return
  if messagebox.askyesno(self.t("move_confirm_title"),self.t("move_confirm").format(count=len(records))):self.move_records(records)
 def move_selected(self):self.move_records(self.selected_records("expired"))
 def recycle_selected(self):
  records=self.selected_records("expired")
  if not records:messagebox.showinfo(self.t("nothing_selected"),self.t("select_expired"));return
  if send2trash is None:messagebox.showerror(self.t("recycle_unavailable"),self.t("recycle_unavailable"));return
  if messagebox.askyesno(self.t("recycle_confirm_title"),self.t("recycle_confirm").format(count=len(records)),icon="warning"):
   for r in records:send2trash(str(r.path))
   self.scan()
 def open_location(self):
  status=list(self.trees)[self.notebook.index(self.notebook.select())];selected=self.selected_records(status)
  if not selected:messagebox.showinfo(self.t("nothing_selected"),self.t("select_matched"));return
  subprocess.Popen(["explorer","/select,",str(selected[0].path)])

if __name__=="__main__":App().mainloop()
