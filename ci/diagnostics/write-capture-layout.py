import sys,re,struct,hashlib,json,collections
from pathlib import Path
import subprocess
root=Path(sys.argv[1]);pe=(root/'libSceVideoOut.prx').read_bytes();hdr=struct.unpack_from('<I',pe,60)[0];sections=hdr+24+struct.unpack_from('<H',pe,hdr+20)[0]
rows=[]
for i in range(struct.unpack_from('<H',pe,hdr+6)[0]):
 at=sections+i*40;size,rva,rawsize,raw=struct.unpack_from('<IIII',pe,at+8);rows.append((rva,max(size,rawsize),raw))
def offset(rva):
 for a,n,raw in rows:
  if a<=rva<a+n:return raw+rva-a
 raise ValueError('RVA not in a PE section')
symbols=subprocess.check_output([str(Path(sys.argv[3])/'llvm-pdbutil.exe'),'dump','-publics',str(root/'libSceVideoOut.pdb')],text=True)
def symbol(needle):
 matches=list(re.finditer(r'[^\n]*'+re.escape(needle)+r'[^\n]*\n[^\n]*addr = (\d+):(\d+)',symbols));assert len(matches)==1,(needle,len(matches))
 m=matches[0];return rows[int(m[1])-1][0]+int(m[2])
start=symbol('?StartFrameDumpNow@Rasterizer@Vulkan@@');flip=symbol('?FrameDumpFlip@Rasterizer@Vulkan@@');glob=symbol('?rasterizer@Impl@PageManager@VideoCore@@')
code=pe[offset(start):offset(start)+70];cmps=[(m.start(),struct.unpack('<I',m[1])[0]) for m in re.finditer(b'\x80\xb9(.{4})\x00',code,re.S)]
assert len(cmps)>=2 and cmps[0][1]+1==cmps[1][1],cmps
collect=cmps[0][1];flipcode=pe[offset(flip):offset(flip)+8192]
choices=collections.Counter(struct.unpack('<I',m[1])[0] for m in re.finditer(b'\x0f\xb6\x86(.{4})',flipcode,re.S) if collect+32<struct.unpack('<I',m[1])[0]<collect+1024)
assert len(choices)==1 and choices.most_common()[0][1]>=2,choices
request=next(iter(choices));reqpos=flipcode.index(b'\x0f\xb6\x86'+struct.pack('<I',request))
guards=[dict(rva=start+cmps[0][0],bytes=code[cmps[0][0]:cmps[0][0]+7].hex()),dict(rva=flip+reqpos,bytes=flipcode[reqpos:reqpos+7].hex())]
entry=dict(rasterizer_rva=glob,collecting_offset=collect,done_offset=collect+1,native_offset=collect-8,request_offset=request,guards=guards)
p=Path(sys.argv[2]);manifest=json.loads(p.read_text()) if p.exists() else {};sha=hashlib.sha256(pe).hexdigest().upper();manifest[sha]=entry;p.write_text(json.dumps(manifest,indent=2));print(sha,entry)
