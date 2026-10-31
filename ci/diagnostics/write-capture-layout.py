import sys,re,struct,hashlib,json,collections
from pathlib import Path
import subprocess
from capture_layout import movzx_byte_loads
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
byte_loads=list(movzx_byte_loads(flipcode))
choices=collections.Counter(displacement for _,_,displacement in byte_loads if collect+32<displacement<collect+1024)
if len(choices)!=1 or choices.most_common()[0][1]<2:
 sites=[]
 for m in re.finditer(b'\x0f\xb6',flipcode):
  modrm=flipcode[m.start()+2] if m.start()+2<len(flipcode) else None
  sites.append(dict(rva=flip+m.start(),bytes=flipcode[m.start():m.start()+12].hex(),modrm=modrm,mod=None if modrm is None else modrm>>6))
 magic=struct.unpack_from('<H',pe,hdr+24)[0]
 image_base=struct.unpack_from('<Q' if magic==0x20b else '<I',pe,hdr+(24 if magic==0x20b else 28))[0]
 objdump=Path(sys.argv[3])/'llvm-objdump.exe'
 try:
  disassembly=subprocess.check_output([str(objdump),'--disassemble','--demangle','--x86-asm-syntax=intel',f'--start-address=0x{image_base+flip:x}',f'--stop-address=0x{image_base+flip+8192:x}',str(root/'libSceVideoOut.prx')],text=True,stderr=subprocess.STDOUT,timeout=30)
  disassembly=disassembly[:24000]
 except Exception as exc:
  disassembly=f'{type(exc).__name__}: {exc}'
 report=dict(schema=1,reason='capture request load was not identified uniquely',rasterizer_rva=glob,frame_dump_flip_rva=flip,collecting_offset=collect,decoded_loads=byte_loads,opcode_sites=sites[:64],frame_dump_flip_bytes=flipcode[:8192].hex(),disassembly=disassembly)
 debug_path=root/'capture-layout-debug.json'
 debug_path.write_text(json.dumps(report,indent=2))
 raise AssertionError(f'capture layout scan failed; see {debug_path.name}')
request=next(iter(choices));reqpos,reqend=next((offset,end) for offset,end,displacement in byte_loads if displacement==request)
guards=[dict(rva=start+cmps[0][0],bytes=code[cmps[0][0]:cmps[0][0]+7].hex()),dict(rva=flip+reqpos,bytes=flipcode[reqpos:reqend].hex())]
entry=dict(rasterizer_rva=glob,collecting_offset=collect,done_offset=collect+1,native_offset=collect-8,request_offset=request,guards=guards)
p=Path(sys.argv[2]);manifest=json.loads(p.read_text()) if p.exists() else {};sha=hashlib.sha256(pe).hexdigest().upper();manifest[sha]=entry;p.write_text(json.dumps(manifest,indent=2));print(sha,entry)
