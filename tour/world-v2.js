// Video-grounded 3F reconstruction, 2026-11-27.
// Architectural positions are approximate; the plan and two continuous walk-through videos
// determine topology. Do not treat these coordinates as surveyed measurements.
export function buildVideoWorld(T) {
 const scene = new T.Scene();
 scene.background = new T.Color('#d4dee6');
 scene.fog = new T.Fog('#d4dee6',48,95);
 const solids=[], doors={}, hotspots=[];
 const material=(c,r=.82,m=0)=>new T.MeshStandardMaterial({color:c,roughness:r,metalness:m});
 const M={
  wall:material('#f1eee8'), wallLight:material('#e5e8e8'), wood:material('#c09a72'),
  trim:material('#a07c55'), white:material('#f4f5f4'), metal:material('#8e9da5',.31,.58),
  black:material('#18222d',.34,.17), screen:material('#0a1520',.35,.04),
  desk:material('#c7a076',.68), yellow:material('#e7b93b'),
  bench:material('#767575',.97), carpet:material('#adb4b6'), navy:material('#11314b'),
  blue:material('#566979'), floor:material('#e8e8e5',.28),
  labFloor:material('#aeb4b6',.75), loungeFloor:material('#b7babc',.78),
  tile:material('#e7e5df',.44), grout:material('#d0d1ce'),
  glass:new T.MeshPhysicalMaterial({color:'#c4d9de',metalness:.07,roughness:.13,transparent:true,opacity:.28,side:T.DoubleSide,depthWrite:false}),
  glow:new T.MeshBasicMaterial({color:'#f2fbff'}),
  darkGlow:new T.MeshBasicMaterial({color:'#16435a'})
 };
 function mesh(geom,mat,x,y,z,parent=scene){
   const o=new T.Mesh(geom,mat);o.position.set(x,y,z);o.castShadow=false;o.receiveShadow=true;parent.add(o);return o;
 }
 function cube(x,y,z,w,h,d,mat,parent=scene){return mesh(new T.BoxGeometry(w,h,d),mat,x,y,z,parent);}
 function wall(x1,z1,x2,z2,height=3.45,mat=M.wall) {
   const dx=x2-x1,dz=z2-z1, len=Math.hypot(dx,dz);
   const w=cube((x1+x2)/2,height/2,(z1+z2)/2,len,height,.13,mat);
   w.rotation.y=-Math.atan2(dz,dx);return w;
 }
 function cylinder(x,y,z,r,h,mat,n=32){return mesh(new T.CylinderGeometry(r,r,h,n),mat,x,y,z);}
 function label(text, x,y,z, w=2, orientation=0, bg='#f0f4f5', color='#1f455b', font=68) {
   const c=document.createElement('canvas');c.width=1024;c.height=230;
   const ctx=c.getContext('2d');
   ctx.fillStyle=bg;ctx.fillRect(0,0,1024,230);
   ctx.fillStyle='#d6aa51';ctx.fillRect(0,0,13,230);
   ctx.fillStyle=color;ctx.textBaseline='middle';ctx.textAlign='center';
   ctx.font='700 '+font+'px "Noto Sans KR",sans-serif';ctx.fillText(text,512,117,985);
   const tx=new T.CanvasTexture(c);tx.colorSpace=T.SRGBColorSpace;
   const p=mesh(new T.PlaneGeometry(w,w*.224),new T.MeshBasicMaterial({map:tx,side:T.DoubleSide}),x,y,z);p.rotation.y=orientation;return p;
 }
 function hotspot(id,title,description,x,y,z,w,h,d,kind='detail',url=null){
   const obj=cube(x,y,z,w,h,d,new T.MeshBasicMaterial({transparent:true,opacity:0,depthWrite:false}));
   obj.visible=true;obj.userData.interactive={id,title,description,kind,url};hotspots.push(obj);return obj;
 }
 function light(x,z,power=3.0,color='#eaffff'){const a=new T.PointLight(color,power,12,2);a.position.set(x,3.15,z);scene.add(a);}
 scene.add(new T.HemisphereLight('#f3faff','#9babb9',2.0));
 const sun=new T.DirectionalLight('#fff9eb',1.5);sun.position.set(-19,25,16);scene.add(sun);
 function ceilingPanel(x,z,w=1.45,d=.42){
   cube(x,3.37,z,w,.045,d,M.glow);
   cube(x,3.40,z,w+.11,.045,d+.07,M.metal);
 }
 // Lobby runs east-west; east-wing corridor turns north. Both axes follow drawing topology.
 cube(-.1,-.08,.46,30.5,.15,4.95,M.floor);
 cube(-.1,3.49,.46,30.5,.13,4.95,M.white);
 cube(10.18,-.08,20.5,3.55,.15,37.6,M.floor);
 cube(10.18,3.49,20.5,3.55,.13,37.6,M.white);
 // Actual corridor glossy pale tile and warm wood wall skirting.
 for(let x=-15;x<15;x+=1.10)cube(x,.005,.47,.016,.007,4.8,M.grout);
 for(let z=-1.5;z<39.5;z+=1.12){
    cube(10.18,.006,z,3.35,.007,.016,M.grout);
    cube(10.18,3.41,z,1.2,.05,.42,M.glow);
    if(Math.round(z)%3===0) light(10.18,z,2.5);
 }
 for(let x=-13;x<14;x+=2.6){ceilingPanel(x,.4,1.5,.41);light(x,.4,1.6);}
 // Lobby perimeter with recess at elevator.
 wall(-15,-2.02,13.4,-2.02);
 wall(-15,2.97,-4.06,2.97);
 wall(.48,2.97,8.38,2.97);
 wall(12.03,2.97,14.8,2.97);
 wall(8.37,3.0,8.37,6.6);
 wall(12.04,3.0,12.04,8.4);
 wall(8.37,7.55,8.37,17.25);
 wall(8.37,36.72,8.37,39.35);
 wall(12.04,3.0,12.04,7.75);
 // Elevator: door opens into lobby, 8303 across south wall.
 cube(-1.81,-.06,5.43,4.35,.15,5.13,M.metal);
 cube(-1.81,3.41,5.43,4.35,.18,5.13,M.white);
 wall(-4.02,2.99,-4.02,7.96,3.4,M.metal);
 wall(.38,2.99,.38,7.96,3.4,M.metal);
 wall(-4.02,7.96,.38,7.96,3.4,M.metal);
 cube(-1.82,3.44,3.03,4.45,.22,.22,M.metal);
 const lElev=cube(-2.88,1.65,3.00,2.04,3.22,.075,M.metal);
 const rElev=cube(-.77,1.65,3.00,2.04,3.22,.075,M.metal);
 doors.elevator={id:'elevator',kind:'elevator',parts:[lElev,rElev],open:0,target:0};
 label('3F · BIGDATA SOFTWARE',-1.82,3.18,2.88,3.42,Math.PI,'#172c3b','#e5f7fb',52);
 ceilingPanel(-1.8,5.1,1.6,.73);
 // Doors of 8304, 8303, 8302, 8301 on south side, visible at first emergence.
 const faculty=[
 {id:'8304',name:'이종두 교수실',x:-6.8},
 {id:'8303',name:'김영운 교수실',x:-2.45},
 {id:'8302',name:'이협건 교수실',x:2.2},
 {id:'8301',name:'프로젝트실습실',x:6.6}
 ];
 for(const f of faculty){
    cube(f.x,1.73,-1.99,2.15,3.40,.15,M.wood);
    cube(f.x,1.65,-2.045,1.45,2.82,.05,M.glass);
    cube(f.x-.74,1.65,-2.07,.06,2.83,.12,M.metal);
    cube(f.x+.74,1.65,-2.07,.06,2.83,.12,M.metal);
    label(f.id+' '+f.name,f.x,2.99,-1.87,2.17,0,'#f5f4ee','#234459',57);
    cube(f.x+.54,1.22,-1.99,.05,.67,.10,M.metal);
 }
 // Elevator-facing wall video: wood slats, plaques, 55-inch TV, award frames.
 for(let x=-11;x<14;x+=.36){
    if(x>-4.1&&x<.6)continue;
    cube(x,1.85,-2.11,.1,3.0,.07,M.wood);
 }
 for(const f of [{x:-.1,z:-2.14},{x:11.3,z:-2.14}]){cube(f.x,1.95,f.z,1.35,.9,.14,M.black);}
 const tv=cube(-.15,2.05,-2.18,2.30,1.33,.14,M.black);
 label('빅데이터소프트웨어공학과',-.15,2.09,-2.275,2.0,0,'#0d2c4b','#e8f8ff',54);
 hotspot('tv-hall','학과 홍보영상','본관 3층 복도의 55인치 디스플레이에서 실제 학과 홍보 영상을 볼 수 있습니다.',-.15,2.04,-2.33,2.25,1.35,.27,'video');
 function plaques(x,z,axis='z'){
   for(let i=0;i<4;i++){
     const off=(i-1.5)*.88;
     const cx=axis==='z'?x:x+off,cz=axis==='z'?z+off:z;
     cube(cx,1.86,cz,axis==='z'?.12:.62,.75,axis==='z'?.61:.10,M.trim);
     cube(cx,1.85,cz,axis==='z'?.14:.53,.64,axis==='z'?.5:.13,M.white);
   }
 }
 plaques(12.09,7.8,'z');
 // Awards on wood-slatted corridor wall and actual glass / hall display panels.
 for(const z of [8.9,10.7,12.5,14.3,16.1,17.9]){
   cube(12.1,2.05,z,.10,1.15,1.35,M.wood);
   cube(12.16,2.05,z,.03,1.02,1.23,M.white);
   label(z<14?'AWARD · 수상':'MOU · 협약',12.19,2.05,z,.98,Math.PI/2,'#f5f2e8','#675329',58);
 }
 // Common wood doors and room signage / walls on east corridor.
 function openingDoor(id,name,x,z,orientation='x',width=1.28,glass=true){
   const frame = M.wood;
   if(orientation==='x') {
      cube(x,3.25,z,.19,.22,width+.26,frame);
      cube(x,1.71,z-width/2,.18,3.34,.13,frame);
      cube(x,1.71,z+width/2,.18,3.34,.13,frame);
      const pivot=new T.Group();pivot.position.set(x,0,z-width/2);scene.add(pivot);
      cube(0,1.54,width/2,.11,2.98,width-.11,glass?M.glass:M.wood,pivot);
      cube(0,1.50,width/2,.13,2.7,.04,M.metal,pivot);
      cube(0,1.45,width-.17,.15,.36,.06,M.metal,pivot);
      const hit=hotspot('door-'+id,name+' 출입문','문을 열어 실내로 들어갈 수 있습니다.',x,1.65,z,.40,2.87,width,'door');hit.userData.interactive.doorId=id;
      doors[id]={id,kind:'hinge',parts:[pivot],open:0,target:0,hit,position:[x,z]};
   }else{
      cube(x,3.25,z,width+.25,.22,.19,frame);
      cube(x-width/2,1.7,z,.13,3.34,.19,frame);
      cube(x+width/2,1.7,z,.13,3.34,.19,frame);
      const pivot=new T.Group();pivot.position.set(x-width/2,0,z);scene.add(pivot);
      cube(width/2,1.53,0,width-.12,3.0,.12,glass?M.glass:M.wood,pivot);
      const hit=hotspot('door-'+id,name+' 출입문','문을 열어 실내로 들어갈 수 있습니다.',x,1.65,z,width,2.85,.4,'door');hit.userData.interactive.doorId=id;
      doors[id]={id,kind:'hinge-z',parts:[pivot],open:0,target:0,hit,position:[x,z]};
   }
 }
 // West side: 8316, separated by two corridor-facing doors.
 const lab={x0:-1.4,x1:8.37,z0:17.35,z1:36.72};
 cube(3.45,-.08,27.0,9.75,.16,19.33,M.labFloor);
 cube(3.45,3.49,27.0,9.75,.14,19.33,M.white);
 wall(lab.x0,lab.z0,lab.x1,lab.z0);wall(lab.x0,lab.z1,lab.x1,lab.z1);
 wall(lab.x0,lab.z0,lab.x0,lab.z1);
 // Door gaps in east wall between corridor and the 8316 lab.
 wall(8.37,17.35,8.37,20.65);wall(8.37,22.05,8.37,33.6);wall(8.37,35.0,8.37,36.72);
 openingDoor('lab-front','8316호 빅데이터실습실',8.37,21.35);
 openingDoor('lab-rear','8316호 빅데이터실습실',8.37,34.3);
 label('8316 · 빅데이터실습실',8.49,2.97,24.5,2.2,-Math.PI/2,'#f0f3f4','#274969',50);
 // Outer windows (window bays with daylight).
 for(const z of [19.6,23.0,26.4,29.8,33.2]){
   cube(lab.x0+.05,2.02,z,.10,1.61,2.43,M.glass);
   cube(lab.x0+.01,1.17,z,.15,.045,2.5,M.metal);
   cube(lab.x0+.01,2.84,z,.15,.045,2.5,M.metal);
   cube(lab.x0+.02,2.0,z,.15,1.68,.035,M.metal);
 }
 // Video and photos: built-in porcelain-white recessed board, screen in front.
 cube(3.45,1.99,17.48,6.82,1.83,.07,M.white);
 cube(3.45,3.16,17.57,7.08,.14,.20,M.metal);
 cube(3.45,2.08,17.69,6.58,1.66,.028,material('#edf2f1',.33));
 // Ceiling-mounted projector between rows.
 cube(3.45,3.26,20.85,.48,.20,.62,M.black);
 cube(3.45,3.46,20.85,.04,.28,.06,M.metal);
 label('8316 · BIG DATA LAB',3.45,2.0,17.74,4.9,0,'#e9f0f0','#304e60',50);
 // 3 desks across, 5 rows, each pair with two screens, all facing front (south).
 function workstation(x,z,teacher=false){
   const w=teacher?1.75:2.30;
   cube(x,.75,z,w,.085,.78,M.desk);
   cube(x,.40,z,w-.10,.10,.63,M.trim);
   for(const offset of teacher?[0]:[-.57,.57]){
     cube(x+offset,1.13,z+.13,.79,.49,.08,M.black);
     cube(x+offset,1.13,z+.08,.69,.37,.02,material('#233744',.37));
     cube(x+offset,.91,z+.13,.07,.16,.10,M.metal);
     cube(x+offset,.79,z+.30,.47,.015,.14,M.black);
     // Chair on north side, facing the screen on south wall.
     cube(x+offset,.48,z+.64,.47,.13,.47,M.blue);
     cube(x+offset,.88,z+.88,.48,.69,.11,M.blue);
     for(const sx of [-.18,.18])cube(x+offset+sx,.23,z+.65,.05,.39,.05,M.metal);
   }
 }
 for(const z of [22.4,24.9,27.4,29.9,32.4]){
   for(const x of [0.25,3.45,6.65]) workstation(x,z);
 }
 // Teacher at front-right from facing front, near western part of front wall.
 workstation(.32,19.0,true);
 // White meeting table and textbook shelf toward rear.
 cube(2.1,.72,35.6,2.05,.08,.78,M.white);
 cube(.05,1.0,35.82,1.04,1.92,.54,M.wood);
 for(let k=0;k<8;k++)cube(-.35+k*.11,1.82,35.54,.085,.27,.15,material(k%2?'#3b648e':'#c8b37a'));
 for(let z=20.1;z<=34.5;z+=2.7){ceilingPanel(3.4,z,2.8,.52);light(3.5,z,2.8);}
 // Right side: 8320 (south), 8319 and 8318 (middle), 8317 curved lounge (north).
 const eastX0=12.03,eastX1=20.5;
 const sections=[
    {id:'8320',name:'인공지능실습실',a:7.7,b:25.1,door:15.4},
    {id:'8319',name:'회의실',a:25.1,b:29.2,door:27.25},
    {id:'8318',name:'회의실',a:29.2,b:33.4,door:31.25}
 ];
 // 8318 geometry and its planned furniture are supplied by an external GLB.
 // Avoid overlapping duplicate walls, ceiling and conference table.
 for(const s of sections){
   if(s.id==='8318'){
     openingDoor('room-'+s.id,s.id+'호 '+s.name,eastX0,s.door,'x',1.40,true);
     label(s.id+' · '+s.name,11.89,2.95,s.door+1.8,1.96,Math.PI/2,'#f2f4f4','#274969',54);
     light(16.25,31.3,3.3);
     continue;
   }
   cube(16.25,-.085,(s.a+s.b)/2,8.47,.17,s.b-s.a,M.labFloor);
   cube(16.25,3.49,(s.a+s.b)/2,8.47,.12,s.b-s.a,M.white);
   wall(eastX0,s.a,eastX1,s.a);wall(eastX0,s.b,eastX1,s.b);
   wall(eastX1,s.a,eastX1,s.b);
   wall(eastX0,s.a,eastX0,s.door-.70);
   wall(eastX0,s.door+.70,eastX0,s.b);
   openingDoor('room-'+s.id,s.id+'호 '+s.name,eastX0,s.door,'x',1.40,true);
   label(s.id+' · '+s.name,11.89,2.95,s.door+1.8,1.96,Math.PI/2,'#f2f4f4','#274969',54);
   ceilingPanel(16.4,(s.a+s.b)/2,2.3,.5);
 }
 // Meeting furniture for 8319 remains provisional; 8318 uses its own GLB.
 for(const s of sections.filter(x=>x.id==='8319')){
   const mz=(s.a+s.b)/2;
   const table=mesh(new T.CylinderGeometry(1.21,1.21,.075,48),M.desk,16.4,.82,mz);
   table.scale.set(1.85,1,.80);
   for(const side of [-1,1])for(const k of [-1.4,-.46,.46,1.4]){
     cube(16.4+k,.50,mz+side*1.18,.41,.17,.38,M.blue);
     cube(16.4+k,.87,mz+side*1.37,.42,.54,.12,M.blue);
   }
   for(const k of [-1,1]){
     cube(16.4+k*2.08,.48,mz,.4,.14,.42,M.blue);
     cube(16.4+k*2.33,.84,mz,.12,.55,.45,M.blue);
   }
   cube(16.5,2.06,s.b-.13,4.0,1.46,.06,M.white);
 }
 hotspot('8318-board','8318호 매립형 화이트보드',
  '회의실 한쪽 벽에 설치된 대형 흰색 매립형 필기용 화이트보드입니다.',
  16.25,2.05,29.36,5.0,1.45,.28,'detail');
 hotspot('8318-screen','8318호 전동 스크린',
  '8318호에만 설치되는 천장형 전동스크린과 빔프로젝터입니다. 화면을 클릭해 스크린을 올리고 내릴 수 있습니다.',
  20.09,2.23,31.3,.30,2.01,2.83,'screen-toggle');
 // 8320: visible computer screens and realistic simple workstation silhouettes.
 for(const z of [10.9,13.7,16.5,19.3,22.1])
   for(const x of [13.8,16.4,19.0]) workstation(x,z);
 // 8317 is a real external GLB scene generated by tools/build_room8317.py.
 // Keep corridor-side swinging entrance and scene hotspots here for navigation.
 // Furniture and curved architecture are no longer fabricated in this source.
 openingDoor('lounge','8317호 휴게실',12.03,37.8,'x',2.52,true);
 label('8317 · 휴게실',11.85,3.0,39.8,1.95,Math.PI/2,'#f4f2ec','#23516c',60);
 hotspot('lounge-tv','8317호 75인치 스마트 TV',
  '휴게실에 설치된 이동식 75인치 스마트 TV에서 학과 영상이 재생됩니다.',
  13.68,1.91,40.0,2.1,1.4,.30,'video');
 hotspot('bench-power','벽면 매립형 벤치 및 콘센트',
  '곡선형 벽면에 고정된 좌석 아래 콘센트가 있어 노트북 및 스마트기기를 연결할 수 있습니다.',
  21.22,.83,37.8,.7,.8,2.5,'detail');
 light(17.0,37.7,4.5,'#ffe8ce');
 // Corridor room sign band, wood trims and blue identity signage.
 for(let z=7;z<40;z+=2.25){
   if(z>=20.6 && z<=22.1)continue;
   cube(8.31,1.8,z,.08,2.9,.08,M.wood);
   cube(12.15,1.8,z,.08,2.9,.08,M.wood);
 }
 label('← 8316 BIG DATA LAB',10.1,2.68,25,2.0,0,'#123e56','#d2edfb',55);
 label('8317 LOUNGE →',10.1,2.68,36.8,2.0,0,'#123e56','#d2edfb',55);
 // Progression markers sit over actual corridor rather than fictional straight axis.
 const zones={
   elevator:{x:-1.8,z:5.4},
   lobby:{x:2.6,z:.35},
   corridor:{x:10.2,z:17},
   '8316':{x:4.2,z:24.2},
   '8317':{x:17.1,z:37.7},
   '8318':{x:16.3,z:31.4},
   '8319':{x:16.3,z:27.2},
   '8320':{x:16.3,z:16.4}
 };
 function region(x,z){
   if(x>=-4.01 && x<=.38 && z>=3.02 && z<7.99)return 'elevator';
   if(x>-1.33&&x<8.395&&z>17.35&&z<36.72)return '8316';
   if(x>12.01&&x<22.25&&z>33.4&&z<42.3)return '8317';
   if(x>12.05&&x<20.45&&z>29.2&&z<33.4)return '8318';
   if(x>12.05&&x<20.45&&z>25.1&&z<29.2)return '8319';
   if(x>12.05&&x<20.45&&z>7.7&&z<25.1)return '8320';
   if(x>8.39&&x<12.08&&z>2.95&&z<40)return 'corridor';
   if(x>-15.1&&x<15.3&&z>-1.99&&z<3.08)return 'lobby';
   return 'outside';
 }
 const routes={
   lobby:[[ -1.80,3.3],[-1.8,1.0],[3.2,.7]],
   '8316':[[ -1.8,3.3],[-1.8,.7],[10.18,.7],[10.18,21.35],[7.5,21.35],[5.4,22.2]],
   '8317':[[ -1.8,3.3],[-1.8,.7],[10.18,.7],[10.18,37.8],[12.9,37.8],[16.5,37.8]]
 };
 return {scene,doors,hotspots,zones,routes,region,
   open(id){if(doors[id])doors[id].target=1;},
   elevator(){doors.elevator.target=1;},
   update(dt){
     for(const d of Object.values(doors)){
       d.open=T.MathUtils.damp(d.open,d.target,5,dt);
       if(d.kind==='elevator'){
         d.parts[0].position.x=-2.88-d.open*2.04;
         d.parts[1].position.x=-.77+d.open*2.04;
       }else d.parts[0].rotation.y=(d.kind==='hinge-z'?-1:1)*d.open*1.48;
       if(d.hit)d.hit.visible=d.open<.65;
     }
   }
 };
}
