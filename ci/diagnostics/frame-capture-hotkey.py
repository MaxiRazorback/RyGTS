import ctypes,hashlib,sys,struct,subprocess,re
from pathlib import Path
if len(sys.argv)!=2:raise SystemExit('Usage: frame-capture-hotkey.py PID')
pid=int(sys.argv[1]);module_path=Path('libs/libSceVideoOut.prx').resolve()
expected=hashlib.sha256(module_path.read_bytes()).hexdigest().upper()
k=ctypes.WinDLL('kernel32',use_last_error=True);p=ctypes.WinDLL('psapi',use_last_error=True)
k.OpenProcess.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32];k.OpenProcess.restype=ctypes.c_void_p
k.CloseHandle.argtypes=[ctypes.c_void_p]
k.ReadProcessMemory.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.ReadProcessMemory.restype=ctypes.c_int
k.WriteProcessMemory.argtypes=k.ReadProcessMemory.argtypes;k.WriteProcessMemory.restype=ctypes.c_int
p.EnumProcessModulesEx.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_uint32,ctypes.POINTER(ctypes.c_uint32),ctypes.c_uint32];p.EnumProcessModulesEx.restype=ctypes.c_int
p.GetModuleFileNameExW.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_wchar_p,ctypes.c_uint32];p.GetModuleFileNameExW.restype=ctypes.c_uint32
h=k.OpenProcess(0x100438,False,pid)
if not h:raise ctypes.WinError(ctypes.get_last_error())
try:
 modules=(ctypes.c_void_p*2048)();needed=ctypes.c_uint32()
 if not p.EnumProcessModulesEx(h,modules,ctypes.sizeof(modules),ctypes.byref(needed),3):raise ctypes.WinError(ctypes.get_last_error())
 base=None
 for handle in modules[:needed.value//ctypes.sizeof(ctypes.c_void_p)]:
  path=ctypes.create_unicode_buffer(32768)
  if p.GetModuleFileNameExW(h,handle,path,len(path)) and path.value.casefold()==str(module_path).casefold():base=handle;break
 if not base:raise SystemExit('Expected renderer not loaded')

 import time,zlib
 u=ctypes.WinDLL('user32',use_last_error=True);g=ctypes.WinDLL('gdi32',use_last_error=True)
 try:u.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
 except AttributeError:pass
 HWND=ctypes.c_void_p;DC=ctypes.c_void_p
 class Rect(ctypes.Structure):_fields_=[('l',ctypes.c_long),('t',ctypes.c_long),('r',ctypes.c_long),('b',ctypes.c_long)]
 class Point(ctypes.Structure):_fields_=[('x',ctypes.c_long),('y',ctypes.c_long)]
 class BI(ctypes.Structure):_fields_=[('size',ctypes.c_uint32),('w',ctypes.c_long),('h',ctypes.c_long),('planes',ctypes.c_uint16),('bits',ctypes.c_uint16),('compression',ctypes.c_uint32),('bytes',ctypes.c_uint32),('x',ctypes.c_long),('y',ctypes.c_long),('colors',ctypes.c_uint32),('important',ctypes.c_uint32)]
 u.GetWindowThreadProcessId.argtypes=[HWND,ctypes.POINTER(ctypes.c_uint32)]
 u.GetWindowTextW.argtypes=[HWND,ctypes.c_wchar_p,ctypes.c_int]
 u.GetForegroundWindow.restype=HWND
 u.GetAncestor.argtypes=[HWND,ctypes.c_uint];u.GetAncestor.restype=HWND
 u.IsWindowVisible.argtypes=[HWND];u.GetClientRect.argtypes=[HWND,ctypes.POINTER(Rect)];u.ClientToScreen.argtypes=[HWND,ctypes.POINTER(Point)]
 u.GetDC.argtypes=[HWND];u.GetDC.restype=DC;u.ReleaseDC.argtypes=[HWND,DC]
 cb=ctypes.WINFUNCTYPE(ctypes.c_int,HWND,ctypes.c_void_p)
 g.CreateCompatibleDC.argtypes=[DC];g.CreateCompatibleDC.restype=DC;g.DeleteDC.argtypes=[DC]
 g.CreateDIBSection.argtypes=[DC,ctypes.POINTER(BI),ctypes.c_uint,ctypes.POINTER(ctypes.c_void_p),ctypes.c_void_p,ctypes.c_uint];g.CreateDIBSection.restype=ctypes.c_void_p
 g.SelectObject.argtypes=[DC,ctypes.c_void_p];g.SelectObject.restype=ctypes.c_void_p;g.DeleteObject.argtypes=[ctypes.c_void_p]
 g.StretchBlt.argtypes=[DC,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,DC,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_uint]
 g.SetStretchBltMode.argtypes=[DC,ctypes.c_int]
 windows=[]
 @cb
 def each(hwnd,l):
  owner=ctypes.c_uint32();u.GetWindowThreadProcessId(hwnd,ctypes.byref(owner));title=ctypes.create_unicode_buffer(512);u.GetWindowTextW(hwnd,title,512)
  if owner.value==pid and u.IsWindowVisible(hwnd) and 'Gran Turismo' in title.value:windows.append(hwnd)
  return 1
 u.EnumWindows(each,0)
 if not windows:raise SystemExit('Visible game window missing')
 hwnd=windows[0];screen=u.GetDC(None);dc=g.CreateCompatibleDC(screen);rect=Rect();u.GetClientRect(hwnd,ctypes.byref(rect));w,hgt=rect.r,rect.b
 info=BI();info.size=ctypes.sizeof(info);info.w=w;info.h=-hgt;info.planes=1;info.bits=32;bits=ctypes.c_void_p()
 bitmap=g.CreateDIBSection(screen,ctypes.byref(info),0,ctypes.byref(bits),None,0)
 if not bitmap:raise ctypes.WinError(ctypes.get_last_error())
 old=g.SelectObject(dc,bitmap);g.SetStretchBltMode(dc,3)
 def shot():
  rect=Rect();origin=Point();u.GetClientRect(hwnd,ctypes.byref(rect));u.ClientToScreen(hwnd,ctypes.byref(origin))
  if rect.r<640 or rect.b<360:raise RuntimeError('Game window minimized or too small')
  if not g.StretchBlt(dc,0,0,w,hgt,screen,origin.x,origin.y,rect.r,rect.b,0x00CC0020):raise ctypes.WinError(ctypes.get_last_error())
  return ctypes.string_at(bits,w*hgt*4)
 def save(data,name):
  rows=[]
  for y in range(hgt):
   row=data[y*w*4:(y+1)*w*4];rgb=bytearray(w*3)
   rgb[0::3]=row[2::4];rgb[1::3]=row[1::4];rgb[2::3]=row[0::4]
   rows.append(b'\0'+rgb)
  def chunk(t,b):return struct.pack('>I',len(b))+t+b+struct.pack('>I',zlib.crc32(t+b))
  Path(name).write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,hgt,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(rows),1))+chunk(b'IEND',b''))
 def get(a,n=1):
  b=ctypes.create_string_buffer(n);count=ctypes.c_size_t()
  if not k.ReadProcessMemory(h,a,b,n,ctypes.byref(count)) or count.value!=n:raise ctypes.WinError(ctypes.get_last_error())
  return b.raw
 def put(a,v):
  b=ctypes.c_ubyte(v);count=ctypes.c_size_t()
  if not k.WriteProcessMemory(h,a,ctypes.byref(b),1,ctypes.byref(count)) or count.value!=1:raise ctypes.WinError(ctypes.get_last_error())
 import json,threading,shutil,datetime,traceback,os
 layout_file=Path('investigation-build/frame-capture-layouts.json')
 layout=json.loads(layout_file.read_text()).get(expected) if layout_file.exists() else None
 status_lock=threading.Lock()
 root=Path('investigation-build/frame-captures');root.mkdir(exist_ok=True)
 state=root/'hotkey-status.json'
 busy=threading.Event();closing=threading.Event();native_count=0
 performance_session=None
 main_thread_id=k.GetCurrentThreadId()
 k.GetCurrentProcess.restype=ctypes.c_void_p
 k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
 k.SetPriorityClass(k.GetCurrentProcess(),0x4000) # Below normal: keep the observer behind game work.
 def status(message,**extra):
  with status_lock:state.write_text(json.dumps(dict(time=datetime.datetime.now().isoformat(),pid=pid,helper_pid=os.getpid(),main_thread_id=main_thread_id,message=message,**extra),indent=2))
  try:print(message,flush=True)
  except OSError:pass # Hidden helpers may have an invalid inherited console handle.
 def tail(path,destination):
  try:
   with Path(path).open('rb') as f:
    f.seek(0,2);total=f.tell();f.seek(max(0,total-512*1024));data=f.read()
   destination.write_bytes(data)
   return total
  except OSError as e:return str(e)
 class PM(ctypes.Structure):
  _fields_=[('cb',ctypes.c_uint32),('faults',ctypes.c_uint32)]+[(x,ctypes.c_size_t) for x in ('peak_working','working','peak_paged','paged','peak_nonpaged','nonpaged','commit','peak_commit','private')]
 p.GetProcessMemoryInfo.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_uint32]
 k.GetProcessTimes.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p]
 k.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_uint32];k.WaitForSingleObject.restype=ctypes.c_uint32
 class PhysicalMemory(ctypes.Structure):
  _fields_=[('length',ctypes.c_uint32),('load',ctypes.c_uint32)]+[(x,ctypes.c_uint64) for x in ('total_physical','available_physical','commit_limit','available_commit','total_virtual','available_virtual','extended_virtual')]
 k.GlobalMemoryStatusEx.argtypes=[ctypes.POINTER(PhysicalMemory)];k.GlobalMemoryStatusEx.restype=ctypes.c_int
 def sample():
  vals=[ctypes.c_uint64() for _ in range(4)];memory=PM();memory.cb=ctypes.sizeof(memory)
  k.GetProcessTimes(h,*[ctypes.byref(v) for v in vals]);p.GetProcessMemoryInfo(h,ctypes.byref(memory),memory.cb)
  result=dict(time=datetime.datetime.now().isoformat(),process_cpu_seconds=(vals[2].value+vals[3].value)/1e7,private_bytes=memory.private,working_set_bytes=memory.working,page_fault_count=memory.faults)
  physical=PhysicalMemory();physical.length=ctypes.sizeof(physical)
  if k.GlobalMemoryStatusEx(ctypes.byref(physical)):
   result.update(system_total_physical_bytes=physical.total_physical,system_available_physical_bytes=physical.available_physical,system_commit_limit_bytes=physical.commit_limit,system_available_commit_bytes=physical.available_commit)
  return result
 def performance_worker(session):
  folder=session['folder'];stop=session['stop'];started=session['monotonic']
  records=[];gpu_process=None;gpu_file=None;streams={};reason='hotkey'
  try:
   for name in ('stdout.log','stderr.log'):
    tail('logs/'+name,folder/('start-'+name))
    try:
     stream=Path('logs/'+name).open('rb');stream.seek(0,2)
     streams[name]=[stream,(folder/('live-'+name)).open('wb'),0]
    except OSError:pass
   gpu=shutil.which('nvidia-smi')
   if gpu:
    gpu_file=(folder/'gpu.csv').open('wb')
    try:
     gpu_process=subprocess.Popen([gpu,'--query-gpu=timestamp,utilization.gpu,utilization.memory,memory.used,clocks.current.graphics,power.draw,temperature.gpu','--format=csv','-lms','1000'],stdout=gpu_file,stderr=subprocess.STDOUT,creationflags=0x08000000)
    except OSError:(folder/'gpu-error.txt').write_text(traceback.format_exc())
   with (folder/'performance.jsonl').open('w',buffering=1) as output:
    previous=None
    while not closing.is_set() and k.WaitForSingleObject(h,0)!=0:
     row=sample();row['elapsed_seconds']=time.monotonic()-started
     row['foreground']=u.GetAncestor(u.GetForegroundWindow(),2)==hwnd
     if previous:
      elapsed=row['elapsed_seconds']-previous['elapsed_seconds']
      row['cpu_threads_used']=(row['process_cpu_seconds']-previous['process_cpu_seconds'])/elapsed if elapsed>0 else 0
     output.write(json.dumps(row)+'\n');records.append(row);previous=row
     for stream,destination,written in streams.values():
      if written>=64*1024*1024:continue
      data=stream.read(min(1024*1024,64*1024*1024-written))
      destination.write(data)
     for entry in streams.values():entry[2]=entry[1].tell()
     if stop.is_set():break
     if row['elapsed_seconds']>=1800:reason='30-minute limit';break
     if len(records)%20==0:
      if shutil.disk_usage(folder).free<1024**3:reason='low disk space';break
      status('Performance recording active: '+str(folder),performance_recording=True,performance_folder=str(folder))
     stop.wait(.25)
    else:reason='game/helper exited'
  except Exception:
   reason='capture error';(folder/'performance-error.txt').write_text(traceback.format_exc())
  finally:
   for stream,destination,_ in streams.values():
    stream.close();destination.close()
   if gpu_process:
    try:
     gpu_process.terminate();gpu_process.wait(timeout=3)
    except (OSError,subprocess.TimeoutExpired):
     try:gpu_process.kill();gpu_process.wait(timeout=1)
     except (OSError,subprocess.TimeoutExpired):pass
   if gpu_file:gpu_file.close()
   for name in ('stdout.log','stderr.log'):tail('logs/'+name,folder/('end-'+name))
   summary=dict(continuous=True,samples=len(records),stop_reason=reason,
     duration_seconds=records[-1]['elapsed_seconds'] if records else 0,
     before=records[0] if records else None,after=records[-1] if records else None,
     note='250ms process samples; 1s GPU samples when available. Frame statistics are in engine logs. No repeated GPU dumps or thread suspension.')
   if len(records)>1:
    duration=records[-1]['elapsed_seconds']-records[0]['elapsed_seconds']
    cpu=records[-1]['process_cpu_seconds']-records[0]['process_cpu_seconds']
    summary.update(cpu_seconds=cpu,average_cpu_threads=cpu/duration if duration else 0,
      peak_sampled_private_bytes=max(r['private_bytes'] for r in records),
      peak_sampled_working_set_bytes=max(r['working_set_bytes'] for r in records))
   (folder/'performance.json').write_text(json.dumps(summary,indent=2))
   status('Performance recording saved: '+str(folder),performance_recording=False,performance_folder=str(folder),last_capture=str(folder))
   if not closing.is_set():k.Beep(800,100)
 def toggle_performance():
  global performance_session
  if performance_session and performance_session['thread'].is_alive():
   if performance_session['stop'].is_set():return
   status('Stopping performance recording...',performance_recording=False,performance_folder=str(performance_session['folder']))
   performance_session['stop'].set()
   if u.GetAncestor(u.GetForegroundWindow(),2)==hwnd:
    try:save(shot(),performance_session['folder']/'visible-stop.png')
    except Exception:pass
   return
  if u.GetAncestor(u.GetForegroundWindow(),2)!=hwnd:
   status('Ignored performance start: game is not in front');return
  pressed=datetime.datetime.now();folder=root/(pressed.strftime('%Y%m%d-%H%M%S-%f')+'-performance');folder.mkdir()
  save(shot(),folder/'visible.png')
  (folder/'capture.json').write_text(json.dumps(dict(pressed=pressed.isoformat(),pid=pid,
    renderer_sha256=expected,renderer_path=str(module_path),native_requested=False,
    continuous_performance=True,runtime=json.loads(Path('investigation-build/current-native-test.json').read_text()) if Path('investigation-build/current-native-test.json').exists() else {}),indent=2))
  session=dict(folder=folder,stop=threading.Event(),monotonic=time.monotonic())
  session['thread']=threading.Thread(target=performance_worker,args=(session,),daemon=True)
  performance_session=session
  status('Performance recording started: '+str(folder),performance_recording=True,performance_folder=str(folder))
  session['thread'].start();k.Beep(1300,60)
 def stack_sample(folder):
  tool=Path('tools/stackdump.exe').resolve()
  if not tool.is_file():return
  try:
   started=datetime.datetime.now().isoformat()
   result=subprocess.run([str(tool),str(pid),'96'],capture_output=True,timeout=6,creationflags=0x08000000)
   (folder/'thread-stacks.txt').write_bytes(result.stdout+result.stderr)
   (folder/'thread-stacks.json').write_text(json.dumps(dict(started=started,finished=datetime.datetime.now().isoformat(),returncode=result.returncode,note='Read-only thread sample; threads may briefly pause during context capture'),indent=2))
  except Exception:(folder/'thread-stacks-error.txt').write_text(traceback.format_exc())
 def archive(folder,native):
  try:
   sizes={n:tail('logs/'+n,folder/n) for n in ('stdout.log','stderr.log')}
   first=sample()
   gpu=shutil.which('nvidia-smi')
   if gpu:
    try:
     result=subprocess.run([gpu,'--query-gpu=timestamp,utilization.gpu,utilization.memory,memory.used,clocks.current.graphics,power.draw,temperature.gpu','--format=csv'],capture_output=True,timeout=5)
     (folder/'gpu.csv').write_bytes(result.stdout+result.stderr)
    except (OSError,subprocess.TimeoutExpired):pass
   closing.wait(2);second=sample()
   if gpu:
    try:
     result=subprocess.run([gpu,'--query-gpu=timestamp,utilization.gpu,utilization.memory,memory.used,clocks.current.graphics,power.draw,temperature.gpu','--format=csv,noheader'],capture_output=True,timeout=5)
     with (folder/'gpu.csv').open('ab') as f:f.write(result.stdout+result.stderr)
    except (OSError,subprocess.TimeoutExpired):pass
   (folder/'performance.json').write_text(json.dumps(dict(before=first,after=second,log_file_sizes=sizes),indent=2))
   if native:
    source=Path('user/log/dump-native-exp');start=time.monotonic();previous=None;stable_since=start
    request_ns=int(datetime.datetime.fromisoformat(json.loads((folder/'capture.json').read_text())['pressed']).timestamp()*1e9)
    rasterizer=struct.unpack('<Q',get(base+layout['rasterizer_rva'],8))[0]
    # The existing atomic request starts at a flip, so the dump contains a whole following frame.
    put(rasterizer+layout['request_offset'],0) if get(rasterizer+layout['collecting_offset'])[0] or get(rasterizer+layout['done_offset'])[0] else None
    while time.monotonic()-start<90 and not closing.is_set():
     if get(rasterizer+layout['collecting_offset'])[0] or get(rasterizer+layout['done_offset'])[0]:put(rasterizer+layout['request_offset'],0)
     files=list(source.glob('*'))
     signature=tuple(sorted((f.name,f.stat().st_size,f.stat().st_mtime_ns) for f in files if f.is_file()))
     if signature!=previous:previous=signature;stable_since=time.monotonic()
     fresh_events=(source/'events.txt').exists() and (source/'events.txt').stat().st_mtime_ns>=request_ns
     fresh_memory=not (source/'mem.txt').exists() or (source/'mem.txt').stat().st_mtime_ns>=request_ns
     if get(rasterizer+layout['done_offset'])[0] and fresh_events and fresh_memory and time.monotonic()-stable_since>2:
      shutil.copytree(source,folder/'native',dirs_exist_ok=True,
       ignore=lambda directory,names:[name for name in names if Path(directory,name).is_file() and Path(directory,name).stat().st_mtime_ns<request_ns])
      (folder/'native-status.txt').write_text('Native resources saved after the hotkey request. They may be later than visible.png.\n')
      status('Native frame saved: '+str(folder));break
     if k.WaitForSingleObject(h,0)==0:break
     closing.wait(.25)
    else:(folder/'native-status.txt').write_text('No completed GPU dump within 90 seconds. Screenshot and logs remain available.\n')
   tail('logs/stdout.log',folder/'stdout-after.log')
  except Exception:
   (folder/'capture-error.txt').write_text(traceback.format_exc());status('Capture error; screenshot retained: '+str(folder))
  finally:
   if native:busy.clear()
 def save_burst(folder,frames):
  try:
   burst=folder/'visible-burst';burst.mkdir()
   metrics=[]
   for i,(elapsed,pixels) in enumerate(frames):
    save(pixels,burst/f'{i:03}.png')
    # Exclude the overlay and menus at the left when measuring a blank 3D scene.
    sampled=[pixels[(y*w+x)*4:(y*w+x)*4+3] for y in range(hgt//5,4*hgt//5,12) for x in range(2*w//5,9*w//10,12)]
    metrics.append(dict(frame=i,elapsed_seconds=elapsed,mean_rgb=sum(sum(v) for v in sampled)/(3*len(sampled)),black_fraction=sum(max(v)<8 for v in sampled)/len(sampled)))
   (burst/'frames.json').write_text(json.dumps(metrics,indent=2))
   status('Visible flicker burst saved: '+str(folder))
  except Exception:(folder/'burst-error.txt').write_text(traceback.format_exc())
 def capture(want_native,want_burst=False):
  global native_count
  if u.GetAncestor(u.GetForegroundWindow(),2)!=hwnd:
   status('Ignored hotkey: game is not in front');return
  pressed=datetime.datetime.now();data=shot() # Copy the visible image before any GPU request or file compression.
  folder=root/pressed.strftime('%Y%m%d-%H%M%S-%f');folder.mkdir()
  if not want_native and not want_burst:
   threading.Thread(target=stack_sample,args=(folder,),daemon=True).start()
  native=False;reason='Screenshot and performance only'
  try:
   if want_native:
    if busy.is_set():reason='GPU capture already pending; screenshot saved'
    elif not layout or any(get(base+guard['rva'],len(bytes.fromhex(guard['bytes'])))!=bytes.fromhex(guard['bytes']) for guard in layout['guards']):reason='Unrecognized renderer layout; screenshot only'
    elif native_count>=12 or shutil.disk_usage(root).free<2*1024**3:reason='GPU capture storage limit reached; screenshot only'
    else:
     rasterizer=struct.unpack('<Q',get(base+layout['rasterizer_rva'],8))[0]
     if not struct.unpack('<Q',get(rasterizer+layout['native_offset'],8))[0]:reason='Native renderer is off; screenshot only'
     elif get(rasterizer+layout['collecting_offset'])[0]:reason='Renderer is already collecting; screenshot only'
     else:
      source=Path('user/log/dump-native-exp')
      if source.exists():
       resolved=source.resolve();workspace=Path.cwd().resolve()
       if not resolved.is_relative_to(workspace):raise RuntimeError('Dump path is outside this workspace')
       source.rename(folder/'previous-raw') # Preserve previous evidence, never delete it.
      put(rasterizer+layout['done_offset'],0);put(rasterizer+layout['request_offset'],1)
      busy.set();native=True;native_count+=1;reason='Native frame requested'
   runtime={}
   settings=Path('investigation-build/current-native-test.json')
   if settings.exists():
    candidate=json.loads(settings.read_text(encoding="utf-8-sig"))
    if candidate.get('pid')==pid:runtime=candidate
   (folder/'capture.json').write_text(json.dumps(dict(pressed=pressed.isoformat(),pid=pid,renderer_sha256=expected,renderer_path=str(module_path),native_requested=native,visible_burst=want_burst,runtime=runtime,note=reason),indent=2))
  except Exception:reason='GPU request failed; screenshot retained';(folder/'request-error.txt').write_text(traceback.format_exc())
  threading.Thread(target=archive,args=(folder,native),daemon=True).start()
  if want_burst:
   frames=[(0.0,data)];start=time.monotonic()
   # Hold at most 64 MiB of pixels; compress only after the sampling ends.
   count=min(24,max(2,64*1024*1024//(w*hgt*4)))
   for i in range(1,count):
    closing.wait(max(0,start+i*.037-time.monotonic()))
    if closing.is_set() or u.GetAncestor(u.GetForegroundWindow(),2)!=hwnd:break
    frames.append((time.monotonic()-start,shot()))
   threading.Thread(target=save_burst,args=(folder,frames),daemon=True).start()
   reason='Visible flicker burst requested; no GPU dump'
  save(data,folder/'visible.png')
  status(reason+': '+str(folder),last_capture=str(folder))
  threading.Thread(target=lambda:k.Beep(1100,60),daemon=True).start()
 class Msg(ctypes.Structure):
  _fields_=[('hwnd',HWND),('message',ctypes.c_uint32),('wparam',ctypes.c_size_t),('lparam',ctypes.c_ssize_t),('time',ctypes.c_uint32),('point',Point),('private',ctypes.c_uint32)]
 u.RegisterHotKey.argtypes=[HWND,ctypes.c_int,ctypes.c_uint,ctypes.c_uint]
 u.UnregisterHotKey.argtypes=[HWND,ctypes.c_int]
 u.PeekMessageW.argtypes=[ctypes.POINTER(Msg),HWND,ctypes.c_uint,ctypes.c_uint,ctypes.c_uint]
 registered=[]
 try:
  for hotkey,mods in ((1,0x4000),(2,0x4002),(3,0x4004)):
   if not u.RegisterHotKey(None,hotkey,mods,0x77):raise ctypes.WinError(ctypes.get_last_error())
   registered.append(hotkey)
  status('Ready: F8 = visible frame + native dump; Ctrl+F8 = start/stop continuous performance; Shift+F8 = visible flicker burst')
  message=Msg()
  while k.WaitForSingleObject(h,0)!=0:
   # A controller can request the same bounded capture without keyboard input.
   # Wait for foreground focus rather than consuming a request behind another window.
   request_file=root/'capture-request.json'
   if request_file.exists() and not busy.is_set() and u.GetAncestor(u.GetForegroundWindow(),2)==hwnd:
    try:
     request=json.loads(request_file.read_text(encoding='utf-8-sig'))
     if request.get('pid')==pid:
      mode=request.get('mode','native')
      if mode not in ('native','visible','burst'):raise ValueError('Unknown capture mode')
      request_file.unlink()
      capture(mode=='native',mode=='burst')
    except Exception:status('Capture request failed: '+traceback.format_exc())
   while u.PeekMessageW(ctypes.byref(message),None,0,0,1):
    if message.message==0x312:
     try:
      if message.wparam==2:toggle_performance()
      else:capture(message.wparam==1,message.wparam==3)
     except Exception:status('Hotkey capture failed: '+traceback.format_exc())
   time.sleep(.005)
 finally:
  closing.set()
  if performance_session:
   performance_session['stop'].set()
   performance_session['thread'].join(timeout=8)
  for hotkey in registered:u.UnregisterHotKey(None,hotkey)
  status('Stopped: game exited or capture helper closed')
  g.SelectObject(dc,old);g.DeleteObject(bitmap);g.DeleteDC(dc);u.ReleaseDC(None,screen)
finally:k.CloseHandle(h)
