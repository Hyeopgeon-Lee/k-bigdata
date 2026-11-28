"""8319 meeting room (planned furniture, same high fidelity design as 8318) standalone GLB asset.
Reference: user's 8319/8319 door + empty-room photos, requested configuration.
Local coordinates: X = from entrance (-X) to window/rear (+X); Z = width.
Units: metres. Approximated geometry, NOT surveyed or photogrammetry.
The corridor-side door is owned by the interactive Three.js world.
"""
from __future__ import annotations
import json, math, os
from collections import defaultdict
from pathlib import Path
import numpy as np
import trimesh
from trimesh.visual.material import PBRMaterial
from trimesh.visual.texture import TextureVisuals

ROOT=Path(os.getenv('ROOM8319_OUT',Path(__file__).resolve().parent.parent/'tour'/'models'))
ROOT.mkdir(parents=True,exist_ok=True)
colors={
    'floor':('#A6ADB3',.79,0), 'tilejoint':('#89949C',.91,0),
    'plaster':('#E5E5E3',.94,0), 'wallpaint':('#EDEAE7',.91,0),
    'ceiling':('#F3F2EF',.98,0), 'acoustic':('#E7E9E8',1,0),
    'woodwall':('#BBA385',.81,0), 'woodtrim':('#9B8267',.67,0),
    'tableoak':('#C7A178',.57,0), 'tableedge':('#A98058',.63,0),
    'grain':('#B18A60',.7,0), 'underbase':('#AC805B',.72,0),
    'woodhighlight':('#E4C39C',.44,0), 'walnut':('#725138',.60,0),
    'fabricshadow':('#354955',.95,0), 'fabricstitch':('#9FB2B9',.92,0),
    'brushedbrass':('#BDA579',.34,.68), 'warmled':('#FFF0D4',.17,0),
    'chair':('#4C5D66',.91,0), 'chairback':('#52646D',.86,0),
    'chairmetal':('#566570',.35,.65), 'rubber':('#252C34',.91,0),
    'whiteboard':('#F8F9F7',.20,0),
    'silver':('#9AA9AF',.25,.70), 'darkmetal':('#26343B',.31,.65),
    'projector':('#D7DADC',.44,.15), 'lens':('#192530',.17,.10),
    'glass':('#C4DAE3',.16,.15), 'frost':('#D5E1E5',.48,.08),
    'blind':('#F1F0EB',.92,0), 'light':('#E9F9FF',.18,0),
    'black':('#1C2731',.52,.12), 'socket':('#F0F1EF',.7,0),
}
scene=trimesh.Scene()
parts=[]
def rgba(hexcolor,alpha=255):
 c=hexcolor.lstrip('#'); return [int(c[i:i+2],16) for i in (0,2,4)]+[alpha]
def add(label,mesh,material,separate=False):
 color,rough,metal=colors[material]
 kwargs=dict(name=material,baseColorFactor=rgba(color,155 if material in ('glass','frost') else 255),metallicFactor=metal,roughnessFactor=rough,doubleSided=True)
 if material in ('glass','frost'): kwargs['alphaMode']='BLEND'
 mesh.visual=TextureVisuals(material=PBRMaterial(**kwargs))
 parts.append((label,mesh,material,separate))
def box(name,x,y,z,sx,sy,sz,mat,separate=False):
 mesh=trimesh.creation.box(extents=(sx,sy,sz));mesh.apply_translation([x,y,z]);add(name,mesh,mat,separate)
def cylinder(name,x,y,z,r,h,mat,n=32,axis='y',separate=False):
 mesh=trimesh.creation.cylinder(radius=r,height=h,sections=n)
 if axis=='y':mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[1,0,0]))
 elif axis=='x':mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[0,1,0]))
 mesh.apply_translation([x,y,z]);add(name,mesh,mat,separate)
def ellipsoid(name,cx,cy,cz,rx,ry,rz,mat,sections=70):
 mesh=trimesh.creation.cylinder(radius=1.,height=2,sections=sections)
 mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[1,0,0]))
 mesh.apply_scale([rx,ry,rz]);mesh.apply_translation([cx,cy,cz]);add(name,mesh,mat)
def oriented_box(name,cx,cy,cz,sx,sy,sz,yaw,mat):
 mesh=trimesh.creation.box(extents=(sx,sy,sz))
 mesh.apply_transform(trimesh.transformations.rotation_matrix(yaw,[0,1,0]))
 mesh.apply_translation([cx,cy,cz]);add(name,mesh,mat)
def beam(name,start,end,r,mat,segments=12):
 a=np.array(start,dtype=float);b=np.array(end,dtype=float)
 mesh=trimesh.creation.cylinder(radius=r,height=float(np.linalg.norm(b-a)),sections=segments)
 mesh.apply_transform(trimesh.geometry.align_vectors([0,0,1],b-a));mesh.apply_translation((a+b)/2)
 add(name,mesh,mat)

# Dimensions are approximate. Entrance on west side (-X), with door centred.
# The real room is photographed empty; the furniture below is the requested future layout.
L=8.46;W=4.20;H=3.42
box('8319 floor slab',0,-.09,0,L,.17,W,'floor')
for x in np.arange(-4.0,4.2,.85):box('floor ceramic joint X',float(x),.002,0,.009,.003,W-.12,'tilejoint')
for z in np.arange(-2.0,2.1,.85):box('floor ceramic joint Z',0,.002,float(z),L-.14,.003,.009,'tilejoint')
# Side wall with recessed writing board: one long side, continuous plaster.
box('west writing wall',0,1.72,-2.09,L,3.44,.15,'wallpaint')
# Opposite side comprises framed frosted glass panels matching uploaded wall photo.
box('glazed wall lower kick',0,.44,2.09,L,.88,.13,'woodwall')
box('glazed wall upper header',0,3.22,2.09,L,.44,.14,'woodwall')
for i in range(5):
 x=-3.38+i*1.69
 box(f'frosted glass panel {i+1}',x,1.83,2.10,1.60,2.37,.030,'frost')
 box('glass frame vertical',x-.84,1.83,2.12,.028,2.46,.07,'woodtrim')
box('glass frame end',4.16,1.83,2.12,.028,2.46,.07,'woodtrim')
# Rear wall has actual-window-like glazing, pair of tall daylight windows.
box('rear lower wall',4.20,.43,0,.15,.86,W,'plaster')
box('rear top header',4.20,3.15,0,.15,.54,W,'plaster')
for z in (-1.05,1.05):
 box('rear glass window',4.20,1.87,z,.045,2.02,1.84,'glass')
 for zz in (z-.93,z+.93):box('rear black window stile',4.16,1.87,zz,.09,2.24,.056,'darkmetal')
 box('rear window crossbar',4.15,1.60,z,.095,.054,1.84,'darkmetal')
 box('roller blind',4.085,2.81,z,.025,.19,1.80,'blind')
 box('blind cassette',4.04,3.03,z,.09,.10,1.88,'silver')
# Entrance wall, large 1.4m clear opening between jambs, door provided by Three.js.
for z in (-1.46,1.46):box('entrance wall flank',-4.20,1.72,z,.15,3.44,1.28,'plaster')
box('entrance transom',-4.20,3.19,0,.15,.50,1.47,'plaster')
# Light wood doorway surrounds match corridor photo; no duplicate swinging leaf.
for z in (-.74,.74):box('light wood door jamb',-4.25,1.65,z,.19,3.30,.12,'woodwall')
box('light wood door top lintel',-4.25,3.31,0,.19,.19,1.62,'woodwall')
# Warm oak wainscot and natural finish on lower wall; do not obscure the writing surface.
box('west wall wood dado',0,.43,-1.97,L-.22,.82,.080,'woodwall')
box('rear wall wood dado',4.08,.43,0,.08,.82,W-.19,'woodwall')
# Large fixed recessed PORCELAIN WRITING WHITEBOARD on side wall (not a second projection screen).
# The 8319 and 8319 writing-board geometry and finish are exactly shared.
box('recessed whiteboard shadow gasket',-.18,2.06,-1.96,5.08,1.55,.015,'darkmetal')
box('recessed whiteboard glazed porcelain',-.18,2.06,-1.944,4.99,1.47,.015,'whiteboard')
# A WHITEBOARD is a fixed writing surface, NOT a second projector screen.
# Four recessed edge reveals, aluminum marker tray and two markers clarify the role.
box('writing board frame top',-.18,2.816,-1.923,5.08,.027,.044,'silver')
box('writing board frame left',-2.735,2.06,-1.923,.027,1.57,.044,'silver')
box('writing board frame right',2.375,2.06,-1.923,.027,1.57,.044,'silver')
box('whiteboard blue marker',-1.88,1.314,-1.86,.18,.023,.020,'darkmetal')
box('whiteboard eraser',-1.46,1.324,-1.85,.19,.04,.09,'chairback')
box('board bottom chalk rail',-.18,1.29,-1.92,5.12,.047,.10,'silver')
# Roof and ceiling acoustic modular tiles (cutaway visor toggled by the standalone viewer).
box('8319 ceiling panel',0,3.48,0,L,.12,W,'ceiling',separate=True)
for x in np.arange(-3.75,4.,.75):box('ceiling acoustic tile long joint',float(x),3.415,0,.008,.004,W-.05,'tilejoint')
for z in np.arange(-1.8,2.,.65):box('ceiling acoustic tile short joint',0,3.415,float(z),L-.05,.004,.008,'tilejoint')
for x in (-2.63,.08,2.68):
 box('ceiling fluorescent light frame',x,3.34,.35,1.52,.045,.48,'silver')
 box('ceiling rectangular light diffuser',x,3.307,.35,1.44,.021,.41,'light')
box('ceiling cassette AC',.92,3.24,-.79,.85,.15,.75,'projector')
for i in range(6):box('ceiling AC grille',.62+i*.115,3.15,-.79,.020,.012,.52,'silver')
# Room 8319 does not have a beam projector, projection screen, motorized housing or projected white panel.
# The only large white surface is the fixed writing whiteboard on the side wall.
# Dedicated power/control panel near door.
box('room switch panel',-4.03,1.30,-1.26,.024,.20,.16,'socket')
box('wall socket below whiteboard',-2.57,.36,-1.97,.020,.16,.20,'socket')
# Shared premium meeting design: warm honey oak, subtle bevel and cable access.
# 10-person wide oval oak conference table in wood colour matching student desks.
# 4 seats along each long side, one at each end.
# Oval solid wood tabletop: 4.25m long, 1.38m wide, bevel-like second inset edge.
ellipsoid('8319 oval table tabletop',-.04,.75,.0,2.12,.065,.73,'tableoak',sections=90)
ellipsoid('8319 oval tabletop thick wood edge',-.04,.690,.0,2.08,.034,.705,'tableedge',sections=90)
# Two central wooden support pedestals and discreet foot caps.
for x in (-1.0,.92):
 box('large oak conference pedestal',x,.39,0,.40,.69,.43,'underbase')
 box('oval table pedestal floor foot',x,.08,0,.80,.12,.58,'woodtrim')
# Subtle woodgrain decorative strokes on the tabletop face.
for i in range(16):
    z=-.52+i*.072
    radius_factor=math.sqrt(max(.03,1.0-(z/.75)**2))
    segment_length=3.84*radius_factor
    box('oak length grain',-.04,.819,z,segment_length,.002,.006,'grain')
# Small cable management central table port for laptops.
box('in-desk conference cable lid',-.02,.825,0,.48,.007,.16,'darkmetal')
box('premium meeting table chamfer highlight',-.04,.841,0,3.46,.007,.022,'woodhighlight')
box('integrated power socket accent',.035,.839,.055,.11,.007,.018,'brushedbrass')
box('flush cable access face',-.02,.829,0,.42,.006,.09,'silver')
# Chair design is conceptual; no chair photograph was provided at time of modelling.
# 10 full 3D movable office chairs around oval table, facing the centre.
chair_count=0
def chair(cx,cz,yaw):
 global chair_count
 chair_count+=1
 def oriented(label,dx,dy,dz,sx,sy,sz,material):
  x=cx+dx*math.cos(yaw)+dz*math.sin(yaw)
  z=cz-dx*math.sin(yaw)+dz*math.cos(yaw)
  oriented_box(f'8319 chair {chair_count:02d} {label}',x,dy,z,sx,sy,sz,yaw,material)
 oriented('seat cushion',0,.52,0,.52,.115,.49,'chair')
 oriented('back lumbar cushion',0,.94,.285,.50,.72,.11,'chairback')
 oriented('seat piped front edge',0,.467,-.24,.48,.014,.020,'fabricshadow')
 oriented('seat upholstery highlight',0,.585,-.06,.42,.007,.25,'chairback')
 oriented('back central vertical upholstery seam',0,.99,.349,.013,.58,.009,'fabricstitch')
 oriented('back top piping',0,1.293,.349,.43,.014,.016,'fabricshadow')
 for xx in (-.26,.26):
   oriented('arm rest',xx,.75,-.018,.053,.060,.42,'chairmetal')
   oriented('arm post',xx,.64,.07,.042,.20,.05,'chairmetal')
 oriented('swivel column',0,.29,0,.085,.40,.085,'chairmetal')
 oriented('wheel hub',0,.11,0,.17,.095,.17,'rubber')
 for a in np.linspace(0,2*math.pi,5,endpoint=False):
  x=.26*math.cos(a);z=.26*math.sin(a)
  oriented('five star base arm',x,.12,z,.09,.038,.38,'chairmetal')
  oriented('rolling wheel',x*1.4,.08,z*1.4,.095,.075,.093,'rubber')
for z,yaw in [(-1.20,math.pi),(1.20,0.0)]:
 for x in (-1.62,-.56,.51,1.58):chair(x,z,yaw)
chair(-2.83,0,-math.pi/2)
chair(2.78,0,math.pi/2)
assert chair_count==10
# Invariant: NO retractable projection screen and NO beam projector in 8319.
# A single separate built-in ceramic writing whiteboard remains.
assert len([p for p in parts if p[0]=='8319_projector_screen_lowered'])==0
assert len([p for p in parts if p[0]=='overhead beam projector'])==0
assert len([p for p in parts if p[0]=='recessed whiteboard glazed porcelain'])==1

# Matching recessed perimeter coves: warm indirect strips beneath the ceiling.
for side in (-1.93,1.93):
 box('8319 perimeter cove diffuser',0,3.29,side,7.65,.012,.031,'warmled')
 box('8319 perimeter cove timber trim',0,3.31,side,7.65,.025,.034,'woodhighlight')
# Decorative oak baseboards and slim corner shadow reveals.
for side in (-1.985,1.985):
 box('8319 lower timber skirting',0,.105,side,8.12,.15,.026,'woodtrim')
for x in (-4.03,4.03):
 box('8319 door-corridor wall skirting',x,.095,0,.027,.13,3.76,'woodtrim')
# Gentle pinstripe accents on the long oak oval table underside.
for x in (-1.5,-.95,-.45,.10,.64,1.19,1.72):
 z_extent=.68*math.sqrt(max(.05,1.0-((x+.04)/2.13)**2))
 box('8319 oak tabletop lateral fine grain',x,.822,0,.012,.002,2*z_extent,'woodhighlight')
# Two slender whiteboard pen rests integrated with the bottom marker rail.
for x in (-1.82,-1.30):
 box('8319 pen rest',x,1.322,-1.866,.23,.018,.027,'brushedbrass')

# Natural wood and brushed metal PBR materials for coordinated professional meeting spaces.
# Both 8319 and 8319 share identical construction, measurements and furniture style.
# Preserve screen as a standalone mesh for toggling; other meshes merge by material.
by_mat=defaultdict(list)
for label,geom,mat,separate in parts:
 if separate:
  key={'8319 ceiling panel':'8319_ceiling','8319_projector_screen_lowered':'8319_projector_screen_lowered','8319_screen_weight_bar':'8319_screen_weight_bar'}[label]
  scene.add_geometry(geom,geom_name=key,node_name=key)
 else:by_mat[mat].append(geom)
for mat,items in by_mat.items():
 scene.add_geometry(trimesh.util.concatenate(items),geom_name='8319_'+mat,node_name='8319_'+mat)
output=ROOT/'room-8319.glb';output.write_bytes(scene.export(file_type='glb'))
# Sanity-check mesh, resolution, room geometry and future furniture data.
loaded=trimesh.load(output,force='scene')
triangles=sum(len(m.faces) for m in loaded.geometry.values())
assert len(loaded.geometry)>=15,(len(loaded.geometry),list(loaded.geometry))
assert triangles>3500,triangles
assert output.stat().st_size>10000,output.stat().st_size
report={
 'room':'8319','geometryMeshes':len(loaded.geometry),
 'sourceParts':len(parts),'triangles':triangles,'glb_bytes':output.stat().st_size,
 'chairs':chair_count,'tableSeats':'4 + 4 + 1 + 1',
 'projectionScreenCount':0,'projectorCount':0,'writingWhiteboardCount':1,
 'projectionScreenDefault':'not-installed',
 'designEdition':'unified-meeting-premium-v2','sharedGeometryWith':'8318',
 'features':['large oval oak 10-seater meeting table','two rows of 4 chairs plus end chairs','built-in ceramic whiteboard','frosted partition','window and roller blinds'],
 'dataProvenance':'user-supplied empty-room photos and room instructions; approximate dimensions; conceptual future furniture',
 'surveyed':False,'source':'manual reconstructed 3D mesh, not a scanned model'
}
(ROOT/'room-8319-quality.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))