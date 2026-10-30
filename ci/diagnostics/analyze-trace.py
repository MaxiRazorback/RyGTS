"""Offline analysis; never opens or pauses the game. Usage: analyze-trace.py CAPTURE_DIR"""
from pathlib import Path
import csv,json,sys,re,collections,statistics,struct,math
p=Path(sys.argv[1]);p=p/'native' if (p/'native').is_dir() else p
rows=list(csv.DictReader((p/'pass-profile.csv').open(newline='')))
events=(p/'events.txt').read_text(errors='replace').splitlines()
groups=collections.defaultdict(list)
for row in rows:groups[(row['kind'],row['program'],row['companion'])].append(row)
passes=[]
for key,values in groups.items():
 gpu=[float(v['gpu_span_ns'])/1e6 for v in values if v['gpu_available']=='1']
 passes.append(dict(kind=key[0],program=key[1],companion=key[2],calls=len(values),
   cpu_ms=sum(int(v['cpu_ns']) for v in values)/1e6,
   gpu_span_median_ms=statistics.median(gpu) if gpu else None,gpu_span_max_ms=max(gpu) if gpu else None,
   gpu_samples=len(gpu)))
passes.sort(key=lambda v:-v['cpu_ms'])
bindings={};writers=collections.defaultdict(set);readers=collections.defaultdict(set)
nulls=[];samplers=[];occlusion=[]
for line in events:
 if not line.startswith('scene-'):continue
 kind=line.split()[0];d=dict(re.findall(r'([\w_]+)=([^ ]+)',line))
 if kind=='scene-image' and 'actual' in d:
  (writers if d.get('storage')=='true' else readers)[d['actual']].add(d['id'])
  bindings.setdefault(d['id'],[]).append(d)
 elif kind=='scene-target':writers[d['address']].add(d['id'])
 elif kind=='scene-depth' and (d.get('write')=='true' or d.get('clear_depth')=='true'):writers[d['address']].add(d['id'])
 elif kind=='scene-null-image':nulls.append(d)
 elif kind=='scene-sampler':samplers.append(d)
 elif kind=='scene-occlusion-registers':occlusion.append(d)
manifest=list(csv.DictReader((p/'mip-manifest.csv').open(newline='')))
chains=collections.defaultdict(list)
for row in manifest:
 # These are depth-like candidates, not a claim that every R32 image is an occlusion pyramid.
 if row.get('depth_aspect')!='true' and row.get('format')!='100':continue
 if int(row['mip'])==0:continue
 path=p/row['file'];stats=None
 if row['status']=='queued' and path.exists():
  unit=int(row['unit_bytes']);count=int(row['bytes'])//unit
  fmt=row.get('format');float_depth=fmt in ('100','126','130')
  if float_depth or fmt=='124':
   # Bounded strided sampling; do not load huge raw images into RAM.
   sample_count=min(count,65536);values=[]
   with path.open('rb') as f:
    if count<=65536:raw=f.read();values=[x[0] for x in struct.iter_unpack('<f' if float_depth else '<H',raw)]
    else:
     for i in range(sample_count):f.seek((i*(count-1)//max(sample_count-1,1))*unit);values.append(struct.unpack('<f' if float_depth else '<H',f.read(unit))[0])
   if not float_depth:values=[v/65535 for v in values]
   finite=[v for v in values if math.isfinite(v)]
   stats=dict(sampled=len(values),nonfinite=len(values)-len(finite),minimum=min(finite) if finite else None,
              maximum=max(finite) if finite else None,zeros=sum(v==0 for v in finite),ones=sum(v==1 for v in finite))
  row['sample_stats']=stats
 chains[row['address']].append(row)
result=dict(capture=str(p),measurement_warning='F8 diagnostic CPU overhead and GPU spans may overlap; not normal-play or exclusive GPU timing. Worker-prepared bindings are bypassed by the existing F8 path.',
 pass_groups=passes,depth_like_mip_candidates=[dict(address=a,mips=v,writers=sorted(writers[a]),readers=sorted(readers[a])) for a,v in chains.items()],
 null_bindings=nulls,samplers=samplers,occlusion_registers=occlusion,
 mip_status_counts=dict(collections.Counter(x['status'] for x in manifest)))
(p/'scene-analysis.json').write_text(json.dumps(result,indent=2))
print(json.dumps(dict(pass_groups=len(passes),depth_like_chains=len(chains),null_bindings=len(nulls),mip_status_counts=result['mip_status_counts']),indent=2))
