"""8317 student lounge reference-based 3D glTF/GLB creator.
Coordinates metres. Local X entrance-to-arc, Z left-right. Entrance at x=-4.9.
The geometry is an authored approximation, NOT a scan or surveyed building model.
All assets generated as open procedural shapes, no photographic texture embedded.
"""
import os, json, math, base64
from pathlib import Path
import numpy as np
import trimesh
from trimesh.visual.material import PBRMaterial
from trimesh.visual.texture import TextureVisuals

ROOT=Path(__file__).resolve().parent.parent / 'tour' / 'models'
ROOT.mkdir(parents=True,exist_ok=True)
materials = {
 'paint': ('#F0EEE9',.90,.0),
 'wall': ('#ECE9E3',.89,.0),
 'wallwood': ('#C1AA8E',.79,0),
 'wood': ('#BE986D',.62,.03),
 'woodlight': ('#DDC2A0',.63,.02),
 'wooddark': ('#695544',.68,.02),
 'floor': ('#AEB4B8',.73,.01),
 'grout': ('#879397',.82,0),
 'blackmetal': ('#202C32',.33,.72),
 'steel': ('#84949C',.3,.77),
 'glass': ('#92B6C8',.13,.2),
 'bench': ('#797774',.94,0),
 'seat': ('#E6B72D',.83,0),
 'chairwood': ('#66503D',.7,0),
 'fridge': ('#858D90',.3,.65),
 'cream': ('#F8F8F5',.63,0),
 'screen': ('#162A38',.18,.05),
 'emissive': ('#FFFAE9',.43,0),
 'warm': ('#DBAE80',.76,0),
 'taupe': ('#7D6868',.87,0),
 'charcoal': ('#383B40',.91,0),
 'woodgrain': ('#AA835E',.7,0),
 'window': ('#A9C7D3',.2,.1)
}
def rgba(h,alpha=255):
 h=h.lstrip('#');return [int(h[i:i+2],16) for i in (0,2,4)]+[alpha]
scene=trimesh.Scene()
parts=[]

def add(name,mesh,mat):
 color,rough,metal=materials[mat]
 mesh.visual=TextureVisuals(material=PBRMaterial(name=mat,baseColorFactor=rgba(color),metallicFactor=metal,roughnessFactor=rough,doubleSided=True))
 mesh.metadata['room']='8317'
 parts.append((name,mesh,mat))

def cube(name,x,y,z,sx,sy,sz,mat):
 m=trimesh.creation.box(extents=(sx,sy,sz));m.apply_translation([x,y,z]);add(name,m,mat)

def cyl(name,x,y,z,r,h,mat,sections=24,axis='y'):
 m=trimesh.creation.cylinder(radius=r,height=h,sections=sections)
 if axis=='y':m.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[1,0,0]))
 elif axis=='x':m.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[0,1,0]))
 m.apply_translation([x,y,z]);add(name,m,mat)

def beam(name,a,b,r,mat,sections=12):
 a=np.array(a,dtype=float);b=np.array(b,dtype=float);v=b-a
 m=trimesh.creation.cylinder(radius=r,height=float(np.linalg.norm(v)),sections=sections)
 T=trimesh.geometry.align_vectors([0,0,1],v)
 m.apply_transform(T);m.apply_translation((a+b)/2);add(name,m,mat)

def annular(name,cx,cz,rx_outer,rz_outer,rx_inner,rz_inner,ang0,ang1,y0,y1,mat,segments=34):
 # curved annulus strip with top/bottom/side walls, no gaps, closed at ends
 vs=[]
 for j in range(segments+1):
  ang=ang0+(ang1-ang0)*j/segments
  for rx,rz in ((rx_outer,rz_outer),(rx_inner,rz_inner)):
   for y in (y0,y1):vs.append([cx+rx*math.cos(ang),y,cz+rz*math.sin(ang)])
 faces=[]
 for j in range(segments):
  p=4*j;q=4*(j+1)
  # outer, inner, top, bottom (two triangles)
  for a,b,c,d in [(p,q,q+1,p+1),(p+2,p+3,q+3,q+2),(p+1,q+1,q+3,p+3),(p,q,q+2,p+2)]:
   faces.extend([[a,b,c],[a,c,d]])
 for p in (0,4*segments):
  a,b,c,d=p,p+1,p+3,p+2
  faces.extend([[a,b,c],[a,c,d]])
 m=trimesh.Trimesh(vertices=np.array(vs),faces=np.array(faces),process=False)
 m.fix_normals();add(name,m,mat)

def oriented_box(name,x,y,z,sx,sy,sz,angle,mat):
 m=trimesh.creation.box(extents=[sx,sy,sz]);m.apply_transform(trimesh.transformations.rotation_matrix(angle,[0,1,0]));m.apply_translation([x,y,z]);add(name,m,mat)

# Floor slabs / tile seam subtle appearance
cube('8317|grey porcelain floor',0,-.085,0,10.0,.17,9.5,'floor')
for x in np.arange(-4.7,5.0,.92):cube('tile-seam-long',float(x),.002,0,.012,.004,9.2,'grout')
for z in np.arange(-4.6,4.7,.92):cube('tile-seam-cross',0,.002,float(z),9.8,.004,.012,'grout')
# White plaster ceiling, recessed warm-taupe main center panel, linear/recessed luminaries
cube('8317|ceiling',0,3.48,0,10,.15,9.5,'paint')
cube('8317|taupe ceiling inset',.05,3.34,0,7.8,.17,7.35,'taupe')
for xx in (-3.82,3.92):cube('cove warm lighting',xx,3.29,0,.055,.055,7.48,'emissive')
for zz in (-3.7,3.7):cube('cove warm lighting',0,3.29,zz,7.88,.055,.055,'emissive')
for i,zz in enumerate((-2.32,0,2.32)):
 for xx in (-2.2,.2,2.4):
  cube('ceiling narrow strip light',xx,3.22,zz,1.35,.03,.045,'emissive')
for xx,zz in [(-3.1,-3.2),(2.8,-2.6),(-2.8,2.8),(2.9,2.9),(0,0)]:
 cyl('round recessed downlight',xx,3.20,zz,.11,.035,'emissive',24)
cube('ceiling cassette AC',.75,3.17,-.58,.87,.13,.89,'cream')
for xx in np.linspace(.42,1.08,5):cube('AC grille',float(xx),3.095,-.58,.012,.011,.68,'steel')

# Bounding walls: actual curved (round) facade and pale plaster.
cube('south wall',0,1.73,-4.76,10,3.46,.14,'wall')
cube('north wall',0,1.73,4.76,10,3.46,.14,'wall')
# along corridor-facing side with opening for folding glazed entrance
cube('left wall one',-4.95,1.73,-3.73,.11,3.46,2.07,'paint')
cube('left wall two',-4.95,1.73,3.65,.11,3.46,2.25,'paint')
cube('entrance transom',-4.95,3.13,-.04,.11,.65,5.35,'paint')
# Curved wall wrapping east edge, perpendicular curved facade, +/- Z
annular('curved exterior wall',.55,0,4.5,4.75,4.33,4.58,-math.pi/2,math.pi/2,0,3.47,'wall',58)
# Beige half-height wood wall wainscoting and curved bench upholstery
annular('wall lower timber trim',.54,0,4.25,4.53,4.08,4.37,-math.pi/2,math.pi/2,0,1.06,'wallwood',58)
annular('curved fixed bench timber plinth',.34,0,4.04,4.35,3.35,3.65,-math.pi/2,math.pi/2,.08,.43,'wooddark',58)
annular('curved bench cushion seat',.34,0,4.01,4.30,3.26,3.54,-math.pi/2,math.pi/2,.42,.62,'bench',58)
annular('curved bench upright back',.34,0,4.00,4.29,3.76,4.04,-math.pi/2,math.pi/2,.63,1.25,'bench',58)
# bench cushion vertical stitch seams and access power sockets under seat
for j,ang in enumerate(np.linspace(-math.pi/2+.18,math.pi/2-.18,19)):
 x=.34+3.80*math.cos(ang);z=4.08*math.sin(ang)
 # textured vertical quilt seams
 oriented_box('bench back seam',x, .92,z,.020,.49,.025,-ang,'charcoal')
 if j%3==0:
  xx=.34+3.42*math.cos(ang); zz=3.72*math.sin(ang)
  oriented_box('USB power outlet',xx,.26,zz,.20,.11,.03,-ang,'cream')
  cyl('outlet left socket',xx-.045,.26,zz+.03,.012,.01,'blackmetal',8)
  cyl('outlet right socket',xx+.045,.26,zz+.03,.012,.01,'blackmetal',8)
# warm under bench indirect light
annular('under bench amber light',.34,0,3.85,4.17,3.83,4.15,-math.pi/2,math.pi/2,.11,.16,'warm',58)
# Warm wooden low trim on north and south walls
for zz in (-4.67,4.67):cube('wall half-height wood',0,.58,zz,9.9,1.04,.09,'wallwood')
# Left glazing: 5 black metal-framed folding glass doors toward corridor.
for zz in np.linspace(-2.25,2.20,6):
 cube('glass door mullion',-4.92,1.50,float(zz),.09,2.95,.045,'blackmetal')
for i in range(5):
 zz=-2.25+(i+.5)*.89
 cube('folding transparent door leaf',-4.94,1.5,zz,.031,2.77,.82,'glass')
 cube('folding door top rail',-4.91,2.88,zz,.09,.07,.87,'blackmetal')
 cube('folding door lower rail',-4.91,.15,zz,.09,.14,.87,'blackmetal')
 cube('vertical latch handle',-4.85,1.20,zz+.20,.07,.36,.02,'steel')
cube('glass entrance top header',-4.94,3.0,0,.12,.15,4.65,'blackmetal')
cube('glass entrance lower sill',-4.92,.05,0,.14,.10,4.65,'blackmetal')

# Windows as photo shows large daylight windows on south/south-west wall
for i,xx in enumerate((-3.1,-1.78)):
 cube('side window glass',xx,2.14,-4.65,1.05,1.35,.04,'window')
 cube('window top',xx,2.85,-4.64,1.13,.08,.12,'blackmetal')
 cube('window bottom',xx,1.45,-4.64,1.13,.08,.12,'blackmetal')
 cube('window left edge',xx-.55,2.14,-4.64,.05,1.47,.11,'blackmetal')
 cube('window right edge',xx+.55,2.14,-4.64,.05,1.47,.11,'blackmetal')
 # translucent roller blind partially covering glass
 cube('off-white roller blind',xx,2.53,-4.55,1.0,.63,.02,'cream')

# Furniture: physically-modelled wood frame yellow chairs with arms
count=0
def chair(cx,cz,angle=0):
 global count
 count+=1
 def b(name,dx,dy,dz,sx,sy,sz,mat):
  x=cx+dx*math.cos(angle)-dz*math.sin(angle)
  z=cz+dx*math.sin(angle)+dz*math.cos(angle)
  oriented_box('yellow chair %02d | '%count+name,x,dy,z,sx,sy,sz,angle,mat)
 b('seat',0,.50,0,.58,.13,.56,'seat')
 b('back upholstery',0,.89,.27,.59,.66,.13,'seat')
 for xx in (-.23,.23):
  for zz in (-.22,.22):b('wood leg',xx,.255,zz,.065,.51,.07,'chairwood')
  b('wood armrest',xx*1.27,.78,-.01,.082,.075,.54,'chairwood')
  b('wood arm post',xx*1.27,.65,-.18,.065,.33,.07,'chairwood')

def table(x,z,round=False,w=1.55,d=.79):
 if round:
  cyl('round oak tabletop',x,.78,z,.57,.068,'woodlight',48)
  cyl('round black table pedestal',x,.39,z,.056,.74,'blackmetal',16)
  cyl('round table foot disk',x,.04,z,.36,.065,'blackmetal',32)
 else:
  cube('rect oak tabletop',x,.78,z,w,.075,d,'woodlight')
  for xx in (-w/2+.07,w/2-.07):
   for zz in (-d/2+.08,d/2-.08):cube('black table legs',x+xx,.37,z+zz,.05,.73,.052,'blackmetal')
  # subtle wood grain longitudinal strips
  for off in (-.19,.13):cube('wood top thin grain',x+off,.823,z,w*.52,.003,.015,'woodgrain')

# Accessible central aisle. Groups follow the photographed room layout.
for x,z in [(-2.63,-2.68),(-2.52,1.00),(-1.55,2.80),(.50,-2.34)]: table(x,z,False,1.60,.75)
for x,z in [(-3.15,3.38),(1.85,2.56),(2.1,-2.5)]:table(x,z,True)
for x,z,a in [(-2.78,-1.83,0),(-2.1,-3.34,math.pi),(-3.55,-2.8,.25),(-3.15,.14,0),(-2.85,1.85,math.pi),(-.72,3.23,-.2),(.0,-1.45,0),(1.15,-3.35,math.pi),(-3.95,3.28,.8),(2.7,3.44,.2),(2.85,-.8,-.4),(2.67,1.2,math.pi),(-1.1,-1.3,.9),(.85,1.4,-.75),(-.2,2.0,math.pi)]:
 chair(x,z,a)

# 75 inch smart TV on mobile steel rolling stand, not wall mounted, placed towards rear-left
cube('75 inch smart TV frame',-3.32,1.92,2.23,2.03,1.20,.12,'blackmetal')
cube('75 inch dark screen',-3.32,1.92,2.15,1.90,1.06,.018,'screen')
cube('smart TV silver bezel bottom',-3.32,1.33,2.13,1.97,.025,.04,'steel')
cube('TV rear steel support',-3.32,.91,2.35,.11,.99,.10,'steel')
cube('TV foot wide base',-3.32,.21,2.35,1.52,.13,.49,'blackmetal')
for xx in (-3.93,-2.71):forz=0
for xx in (-3.93,-2.71):
 for zz in (2.16,2.53):cyl('TV stand rolling wheel',xx,.10,zz,.09,.067,'blackmetal',16,axis='x')
# Speaker and lectern (white wood platform with sloping face)
cube('lectern white body',-1.46,.72,2.73,.65,1.35,.50,'cream')
oriented_box('lectern angled wood top',-1.46,1.43,2.67,.90,.07,.58,-.08,'woodlight')
cube('lectern front emblem',-1.45,.88,2.46,.39,.19,.02,'wallwood')
# Silver refrigerator and microwave
cube('tall silver two-door refrigerator',-3.96,1.04,3.91,.79,2.09,.77,'fridge')
cube('fridge mid door divider',-3.96,1.12,3.50,.76,.026,.03,'blackmetal')
for x in (-4.24,-3.68):cube('fridge door handles',x,1.35,3.49,.025,.30,.044,'steel')
cube('microwave oak sideboard',-2.72,.42,4.14,1.10,.84,.60,'wood')
cube('microwave white body',-2.72,1.00,4.10,.65,.43,.47,'cream')
cube('microwave smoked glass',-2.79,1.03,3.85,.44,.26,.025,'screen')
cyl('microwave knob',-2.42,.98,3.84,.05,.025,'steel',16,axis='z')
# Wall sconce pairs, visible soft lighting fixtures
for xx,zz,along in [(-4.44,-3.48,'x'),(3.3,-3.8,'z'),(3.3,3.8,'z'),(-4.35,3.6,'x')]:
 if along=='z':cube('vertical wall sconce',xx,1.98,zz,.13,.72,.08,'emissive')
 else:cube('vertical wall sconce',xx,1.98,zz,.08,.72,.13,'emissive')
# glass-panel notice board near door
cube('lounge entrance notice board',-4.78,2.2,2.95,.05,.65,.53,'woodlight')

# Compress same material meshes into one GPU mesh to keep browser draw calls small.
from collections import defaultdict
buckets=defaultdict(list)
for name,m,mat in parts:
 buckets[mat].append(m)
for mat, meshes in buckets.items():
 try:merged=trimesh.util.concatenate(meshes)
 except:merged=meshes[0]
 scene.add_geometry(merged,geom_name='8317_'+mat,node_name='8317_'+mat)

# GLB is standalone model; compatible external .gltf uses one embedded binary data URL.
output=ROOT/'room-8317.glb';output.write_bytes(scene.export(file_type='glb'))
files=trimesh.exchange.gltf.export_gltf(scene,include_normals=True)
root_glb=next(k for k in files if k.endswith('.gltf'))
model=json.loads(files[root_glb])
for i,b in enumerate(model.get('buffers',[])):
 uri=b.get('uri'); payload=files.get(uri)
 if payload is None: raise RuntimeError('missing buffer '+str(uri))
 b['uri']='data:application/octet-stream;base64,'+base64.b64encode(payload).decode('ascii')
model['asset']['generator']='K-Bigdata 8317 room model / trimesh procedural modelling'
model.setdefault('extras',{})['modelInfo']={'room':'8317','verified':'photo+video references only','surveyed':False,'design':'Model exterior walls and furnishing arrangement approximate. Furniture derived from supplied photos.'}
(ROOT/'room-8317.gltf').write_text(json.dumps(model,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
report={'room':'8317','uniqueMaterials':len(buckets),'submeshParts':len(parts),'mergedMeshes':len(scene.geometry),'triangles':sum(len(m.faces) for m in scene.geometry.values()),'glb_bytes':output.stat().st_size,'gltf_bytes':(ROOT/'room-8317.gltf').stat().st_size,'note':'Not surveyed or photogrammetry reconstruction. Photo- and plan-informed editable GLB 3D model.'}
(ROOT/'quality.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))