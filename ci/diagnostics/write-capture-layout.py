import sys,re,struct,hashlib,json,collections
from pathlib import Path
import subprocess
from capture_layout import movzx_byte_loads,pdb_procedure,pdb_procedure_ref,pe_image_base
root=Path(sys.argv[1]);pe=(root/'libSceVideoOut.prx').read_bytes();hdr=struct.unpack_from('<I',pe,60)[0];sections=hdr+24+struct.unpack_from('<H',pe,hdr+20)[0]
rows=[]
for i in range(struct.unpack_from('<H',pe,hdr+6)[0]):
 at=sections+i*40;size,rva,rawsize,raw=struct.unpack_from('<IIII',pe,at+8);rows.append((rva,max(size,rawsize),raw))
def offset(rva):
 for a,n,raw in rows:
  if a<=rva<a+n:return raw+rva-a
 raise ValueError('RVA not in a PE section')
symbols=subprocess.check_output([str(Path(sys.argv[3])/'llvm-pdbutil.exe'),'dump','-publics',str(root/'libSceVideoOut.pdb')],text=True)
pdbutil=str(Path(sys.argv[3])/'llvm-pdbutil.exe')
def symbol(needle):
 matches=list(re.finditer(r'[^\n]*'+re.escape(needle)+r'[^\n]*\n[^\n]*addr = (\d+):(\d+)',symbols));assert len(matches)==1,(needle,len(matches))
 m=matches[0];return rows[int(m[1])-1][0]+int(m[2])
start=symbol('?StartFrameDumpNow@Rasterizer@Vulkan@@');flip=symbol('?FrameDumpFlip@Rasterizer@Vulkan@@');glob=symbol('?rasterizer@Impl@PageManager@VideoCore@@')
proc_ref=subprocess.Popen([pdbutil,'dump','--globals',str(root/'libSceVideoOut.pdb')],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
module_index,proc_record_offset=pdb_procedure_ref(proc_ref.stdout,'Vulkan::Rasterizer::FrameDumpFlip')
proc_ref_status=proc_ref.wait(timeout=60)
if proc_ref_status:raise RuntimeError(f'llvm-pdbutil dump --globals failed with exit code {proc_ref_status}')
proc_dump=subprocess.check_output([pdbutil,'dump','--symbols',f'--modi={module_index}',str(root/'libSceVideoOut.pdb')],text=True,stderr=subprocess.STDOUT,timeout=60)
proc_lines=proc_dump.splitlines();proc_context=[]
for i,line in enumerate(proc_lines):
 if 'Vulkan::Rasterizer::FrameDumpFlip' in line:proc_context.extend(proc_lines[max(0,i-2):i+5])
proc_context=list(dict.fromkeys(proc_context))
flip_segment,flip_offset,flip_size=pdb_procedure(proc_dump,'Vulkan::Rasterizer::FrameDumpFlip',proc_record_offset)
assert rows[flip_segment-1][0]+flip_offset==flip,('FrameDumpFlip PDB address mismatch',flip_segment,flip_offset,flip)
print(f'FrameDumpFlip function size: {flip_size} bytes')
code=pe[offset(start):offset(start)+70];cmps=[(m.start(),struct.unpack('<I',m[1])[0]) for m in re.finditer(b'\x80\xb9(.{4})\x00',code,re.S)]
assert len(cmps)>=2 and cmps[0][1]+1==cmps[1][1],cmps
collect=cmps[0][1];flipcode=pe[offset(flip):offset(flip)+flip_size] if 0<flip_size<=1048576 else b''
byte_loads=list(movzx_byte_loads(flipcode))
choices=collections.Counter(displacement for _,_,displacement in byte_loads if collect+32<displacement<collect+1024)
if len(choices)!=1 or choices.most_common()[0][1]<2:
 sites=[]
 for m in re.finditer(b'\x0f\xb6',flipcode):
  modrm=flipcode[m.start()+2] if m.start()+2<len(flipcode) else None
  sites.append(dict(rva=flip+m.start(),bytes=flipcode[m.start():m.start()+12].hex(),modrm=modrm,mod=None if modrm is None else modrm>>6))
 image_base=pe_image_base(pe,hdr)
 objdump=Path(sys.argv[3])/'llvm-objdump.exe'
 try:
  stop=flip+flip_size if 0<flip_size<=1048576 else flip+8192
  disassembly=subprocess.check_output([str(objdump),'--disassemble','--demangle','--x86-asm-syntax=intel',f'--start-address=0x{image_base+flip:x}',f'--stop-address=0x{image_base+stop:x}',str(root/'libSceVideoOut.prx')],text=True,stderr=subprocess.STDOUT,timeout=30)
  disassembly_truncated=len(disassembly)>160000
  disassembly=disassembly[:160000]
 except Exception as exc:
  disassembly=f'{type(exc).__name__}: {exc}'
  disassembly_truncated=False
 report=dict(schema=1,reason='capture request load was not identified uniquely',rasterizer_rva=glob,frame_dump_flip_rva=flip,frame_dump_flip_size=flip_size,frame_dump_flip_module_index=module_index,frame_dump_flip_record_offset=proc_record_offset,frame_dump_flip_pdb_records=proc_context,collecting_offset=collect,decoded_loads=byte_loads,opcode_sites=sites[:64],frame_dump_flip_bytes=flipcode[:16384].hex(),frame_dump_flip_bytes_truncated=len(flipcode)>16384,disassembly=disassembly,disassembly_truncated=disassembly_truncated)
 debug_path=Path(sys.argv[2]).with_name('capture-layout-debug.json')
 debug_path.write_text(json.dumps(report,indent=2))
 raise AssertionError(f'capture layout scan failed; see {debug_path.name}')
request=next(iter(choices));reqpos,reqend=next((offset,end) for offset,end,displacement in byte_loads if displacement==request)
guards=[dict(rva=start+cmps[0][0],bytes=code[cmps[0][0]:cmps[0][0]+7].hex()),dict(rva=flip+reqpos,bytes=flipcode[reqpos:reqend].hex())]
entry=dict(rasterizer_rva=glob,collecting_offset=collect,done_offset=collect+1,native_offset=collect-8,request_offset=request,guards=guards)
p=Path(sys.argv[2]);manifest=json.loads(p.read_text()) if p.exists() else {};sha=hashlib.sha256(pe).hexdigest().upper();manifest[sha]=entry;p.write_text(json.dumps(manifest,indent=2));print(sha,entry)
