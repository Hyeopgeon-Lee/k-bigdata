// 3D prototype: building-scale coordinates in metres. Architectural positions are provisional.
export function createWorld(T) {
  const scene = new T.Scene();
  scene.background = new T.Color(0x122235);
  scene.fog = new T.FogExp2(0x172d43, 0.009);
  const hotspots = [];
  const doors = {};
  const solid = (color, roughness=0.8, metalness=0) => new T.MeshStandardMaterial({color,roughness,metalness});
  const mat = {
    floor:solid(0xd5dce1,0.88), corridor:solid(0xe6e8eb,.72), grout:solid(0xaebbc5),
    plaster:solid(0xf0ede7), timber:solid(0xc69a68), trim:solid(0x9d7951),
    glass:new T.MeshPhysicalMaterial({color:0xc3e2ee,transparent:true,opacity:.25,metalness:.08,roughness:.12,depthWrite:false,side:T.DoubleSide}),
    metal:solid(0x6f8190,.36,.58), black:solid(0x182533,.38,.32),
    screen:new T.MeshBasicMaterial({color:0x131f2c}), blue:solid(0x31617c,.8),
    yellow:solid(0xe2b12e,.8), couch:solid(0x707475,1), white:solid(0xf8faf9),
    board:solid(0xe5eaeb,.3), navy:solid(0x071b2e), line:solid(0x9aadb5)
  };
  function box(x,y,z,w,h,d,m,parent=scene) {
    const mesh = new T.Mesh(new T.BoxGeometry(w,h,d),m);
    mesh.position.set(x,y,z); mesh.castShadow=h>.12; mesh.receiveShadow=true; parent.add(mesh); return mesh;
  }
  function plane(x,y,z,w,h,m,rotY=0,parent=scene) {
    const mesh=new T.Mesh(new T.PlaneGeometry(w,h),m);
    mesh.position.set(x,y,z);mesh.rotation.y=rotY;parent.add(mesh);return mesh;
  }
  function textTexture(label,opts={}) {
    const c=document.createElement('canvas');c.width=1024;c.height=256;
    const ctx=c.getContext('2d');ctx.clearRect(0,0,c.width,c.height);
    ctx.fillStyle=opts.background||'#092941';ctx.fillRect(0,0,1024,256);
    ctx.fillStyle=opts.highlight||'#b9e6f2';ctx.fillRect(0,0,13,256);
    ctx.fillStyle=opts.color||'#ffffff';ctx.textAlign='center';ctx.textBaseline='middle';
    const size=opts.size||68;ctx.font='800 '+size+'px "Pretendard", "Noto Sans KR", sans-serif';
    ctx.fillText(label,512,128,980);
    const texture=new T.CanvasTexture(c); texture.colorSpace=T.SRGBColorSpace;
    texture.anisotropy=4;return texture;
  }
  function sign(label,x,y,z,w=2.2,rotation=0,bg='#092941') {
    return plane(x,y,z,w,w*.25,new T.MeshBasicMaterial({map:textTexture(label,{background:bg}),side:T.DoubleSide}),rotation);
  }
  function interactiveBox(x,y,z,w,h,d,title,description,kind='info',url=null,color=0x70efff) {
    const hit=box(x,y,z,w,h,d,new T.MeshBasicMaterial({color,transparent:true,opacity:0,depthWrite:false}));
    hit.castShadow=false;hit.userData.interactive={kind,title,description,url};
    hotspots.push(hit);return hit;
  }
  function light(x,y,z,color=0xffffff,power=16,distance=11){
    const l=new T.PointLight(color,power,distance,2);l.position.set(x,y,z);scene.add(l);return l;
  }
  scene.add(new T.HemisphereLight(0xf4faff,0x6c8295,2.2));
  const sun=new T.DirectionalLight(0xffe6c5,2.1);sun.position.set(-15,18,-28);sun.castShadow=false;scene.add(sun);

  // Corridor and elevator lobby. +z = elevator / professor-room end.
  box(0,-.10,4,4.6,.20,48,mat.corridor);
  box(0,3.56,4,4.6,.12,48,solid(0xe1e5e6));
  for(let z=-19;z<27;z+=1.75) {
    box(0,.011,z,4.38,.007,.015,mat.grout);
    if(z>-18 && z<26){
      box(-.72,3.49,z,.95,.04,.22,new T.MeshBasicMaterial({color:0xd7fbff}));
      box(.92,3.49,z,.95,.04,.22,new T.MeshBasicMaterial({color:0xd7fbff}));
      if(Math.round(z)%3===0)light(0,3.12,z,0xe1f7ff,3.8,7);
    }
  }
  for(let x=-2.2;x<=2.2;x+=1.1) box(x,.012,4,.012,.006,47.6,mat.grout);
  box(0,1.73,-20.3,4.6,3.47,.15,mat.plaster);
  box(-2.26,1.73,16.8,.12,3.46,19.9,mat.plaster);
  box(2.26,1.73,9.5,.12,3.46,34,mat.plaster);
  for(let z=10;z<26;z+=1.16){
    box(2.30,1.82,z,.045,2.92,.07,mat.trim);
    box(-2.30,1.82,z,.045,2.92,.07,mat.trim);
  }
  for(let z=-19;z<=27;z+=4.6){
    box(-2.28,.30,z,.10,.6,4.2,mat.trim);
    box(2.28,.30,z,.10,.6,4.2,mat.trim);
  }
  // Elevator cabin and two powered sliding leaves.
  box(0,-.04,28.4,2.85,.10,4.55,mat.floor);
  box(0,3.26,28.4,2.85,.14,4.55,mat.metal);
  box(-1.43,1.64,28.4,.10,3.3,4.56,mat.metal);
  box(1.43,1.64,28.4,.10,3.3,4.56,mat.metal);
  box(0,1.64,30.75,2.85,3.3,.10,mat.metal);
  box(0,3.36,26.13,3.1,.20,.24,mat.metal);
  const elevL=box(-.69,1.63,26.18,1.36,3.22,.12,mat.metal);
  const elevR=box(.69,1.63,26.18,1.36,3.22,.12,mat.metal);
  box(0,3.19,28.4,1.1,.05,1.36,new T.MeshBasicMaterial({color:0xe5fcff}));
  sign('3F · BIG DATA SOFTWARE',0,2.93,25.9,2.56,0,'#16384a');
  doors.elevator={id:'elevator',open:0,target:0,type:'elevator',parts:[elevL,elevR]};

  // Faculty corridor: visible when stepping out of elevator.
  const faculty=[
    {id:'8303',name:'김영운 교수실',z:23.0},
    {id:'8302',name:'이협건 교수실',z:19.5},
    {id:'8301',name:'프로젝트실습실',z:15.9}
  ];
  for(const a of faculty){
    box(2.31,1.62,a.z, .065,2.58,1.68,mat.timber);
    box(2.28,1.69,a.z,.075,2.24,1.15,mat.glass);
    sign(a.id+' '+a.name,2.19,2.97,a.z,1.8,-Math.PI/2,'#124264');
  }
  // Academic awards and project posters along the corridor.
  for(let i=0;i<6;i++){
    const z=22.4-i*1.34;
    box(-2.33,1.95,z,.085,1.14,.95,mat.trim);
    box(-2.38,1.95,z,.028,1.0,.82,mat.white);
    sign(i<3?'AWARDS · 수상성과':'PROJECT · 산학협력',-2.42,1.94,z,.74,Math.PI/2,i<3?'#71501a':'#16415a');
    interactiveBox(-2.45,1.95,z,.28,1.2,1.01,i<3?'학과 수상 전시':'산학협력 업무협약',
      i<3?'대상·장관상 등 학생들의 수상 실적을 전시하는 복도입니다. 실제 수상 액자와 상세 자료는 다음 제작 단계에서 연결합니다.':'우리 학과의 기업 업무협약이 전시되는 구역입니다. 기업별 실제 협약 문서의 공개 가능 여부를 확인한 후 콘텐츠를 연결합니다.');
  }
  // Wall mounted 55 inch display between faculty offices.
  box(2.34,2.15,21.15,.16,1.07,1.94,mat.black);
  sign('BIGDATA SOFTWARE',2.22,2.14,21.15,1.6,-Math.PI/2,'#061b40');
  interactiveBox(2.24,2.18,21.15,.26,1.2,2.0,'학과 소개 영상','교수실 사이 55인치 벽걸이 TV에서 학과 소개 영상을 확인할 수 있습니다.','video');
  light(.4,3.15,21,0xc6eafa,4.0,8);

  // 8316 computer laboratory. Front face at +z, teacher station front-right facing the screen.
  const left=-12.8,right=-2.2,back=-8.25,front=9.3;
  box((left+right)/2,-.10,(front+back)/2,right-left,.20,front-back,mat.floor);
  box((left+right)/2,3.50,(front+back)/2,right-left,.12,front-back,solid(0xe8ecec));
  box(left,1.72,(back+front)/2,.16,3.46,front-back,mat.plaster);
  box((left+right)/2,1.72,back,right-left,3.46,.18,mat.plaster);
  box((left+right)/2,1.72,front,right-left,3.46,.18,mat.plaster);
  function segmentedWall(x,zMin,zMax,holes,material) {
    const sorted=holes.slice().sort((a,b)=>a[0]-b[0]);let cur=zMin;
    for(const [a,b] of sorted){
      if(a>cur)box(x,1.74,(cur+a)/2,.16,3.48,a-cur,material);
      cur=Math.max(cur,b);
    }
    if(zMax>cur)box(x,1.74,(cur+zMax)/2,.16,3.48,zMax-cur,material);
  }
  segmentedWall(right,back,front,[[-3.37,-1.93],[4.8,6.24]],mat.plaster);
  // Aluminum framed lab windows along the outer wall.
  for(const z of [-5.8,-2.8,.2,3.2]){
    box(left+.12,2.05,z,.06,1.58,2.36,mat.glass);
    box(left+.06,2.05,z,.09,1.6,.045,mat.metal);
    box(left+.06,1.28,z,.09,.06,2.36,mat.metal);
    box(left+.06,2.82,z,.09,.06,2.36,mat.metal);
  }
  // White ceramic board recessed behind electric projection screen.
  box(-7.5,1.97,front-.12,6.3,1.77,.06,mat.board);
  box(-7.5,3.11,front-.25,6.58,.12,.18,mat.metal);
  box(-7.5,2.08,front-.27,6.1,1.65,.035,solid(0xe7f0f3,.28));
  box(-7.5,3.35,5.7,.25,.23,.4,mat.black);
  box(-7.5,3.50,5.7,1.0,.08,.28,mat.metal);
  // Screen label and teaching equipment.
  sign('BIG DATA LAB · 8316',-7.5,2.03,front-.305,4.1,Math.PI,'#e9eff2');
  function computer(x,z,look=1,student=true){
    const width=student?2.33:1.65;
    box(x,.73,z,width,.085,.78,mat.timber);
    box(x,.42,z,width-.14,.12,.65,mat.trim);
    for(const d of student?[-.52,.52]:[0]){
      box(x+d,1.17,z+.09,.75,.53,.075,mat.black);
      box(x+d,1.15,z+.04,.68,.43,.015,new T.MeshBasicMaterial({color:0x132e42}));
      box(x+d,.90,z+.10,.08,.12,.08,mat.metal);
      box(x+d,.78,z+.22,.52,.018,.15,mat.black);
      box(x+d,.58,z-.56,.45,.50,.35,mat.blue);
      box(x+d,.91,z-.79,.46,.70,.10,mat.blue);
      box(x+d,.35,z-.59,.08,.5,.08,mat.metal);
    }
    return {x,z,width};
  }
  const desks=[];
  for(const z of [-5.75,-3.22,-.69,1.84,4.37]){
    for(const x of [-10.77,-7.48,-4.19]) desks.push(computer(x,z));
  }
  computer(-11.08,7.45,1,false);
  // End-of-room small meeting and textbook storage, kept out of walking area.
  box(-11.73,.9,-7.50,1.55,1.80,.49,solid(0xc2a684));
  box(-10.44,1.09,-7.45,1.18,.08,.52,mat.white);
  for(let i=0;i<8;i++)box(-11.95+i*.21,1.22,-7.13,.12,.26,.18,solid(i%2?0x385b88:0xb9ab7b));
  for(let z=back+.7;z<front-1;z+=2.5){
    box(-7.5,3.43,z,2.2,.036,.64,new T.MeshBasicMaterial({color:0xe2f9ff}));
    light(-7.5,3.18,z,0xe9f5ff,3.0,7);
  }
  sign('8316 · 빅데이터실습실',-2.08,2.96,.85,2.4,Math.PI/2);
  // Two corridor-facing doors as in the supplied floorplan.
  function door(id,x,z,name,isGlass=false,width=1.42) {
    box(x,3.25,z,.19,.22,width+.28,mat.timber);
    for(const dz of [-width/2,width/2])box(x,1.73,z+dz,.2,3.45,.13,mat.timber);
    const pivotA=new T.Group(),pivotB=new T.Group();
    pivotA.position.set(x,0,z-width/2);
    pivotB.position.set(x,0,z+width/2);
    const dmat=isGlass?mat.glass:solid(0xb9d5d9,.42,.12);
    box(0,1.55,width/4,.08,3.03,width/2-.08,dmat,pivotA);
    box(0,1.55,-width/4,.08,3.03,width/2-.08,dmat,pivotB);
    if(isGlass){
      box(0,1.55,width/4,.08,.045,width/2-.05,mat.metal,pivotA);
      box(0,1.55,-width/4,.08,.045,width/2-.05,mat.metal,pivotB);
    }
    scene.add(pivotA,pivotB);
    const hit=interactiveBox(x,1.65,z,.35,2.9,width,name,'출입문을 열고 안으로 이동할 수 있습니다.','door');
    hit.userData.interactive.doorId=id;
    doors[id]={id,open:0,target:0,type:'hinged',parts:[pivotA,pivotB],hit,name,position:[x,z]};
  }
  door('lab-back',right,-2.65,'8316호 뒤쪽 출입문');
  door('lab-front',right,5.52,'8316호 앞쪽 출입문');

  // 8317 lounge at the curved end of the east wing, actual furniture/colors reflected.
  const loungeZ=-14.00, loungeX=9.0;
  box(7.73,-.11,-14,11.50,.21,11.1,solid(0xb9bfc1,.94));
  box(7.73,3.53,-14,11.50,.12,11.1,solid(0x806f70));
  box(5.83,1.76,-19.48,7.5,3.50,.17,mat.plaster);
  box(5.83,1.76,-8.55,7.5,3.50,.17,mat.plaster);
  segmentedWall(2.2,-19.48,-8.55,[[-15.43,-12.62]],mat.plaster);
  // Approximate rounded facade and fixed curved wall seats.
  function curvedStrip(cx,cz,rx,rz,start,end,count,y,h,depth,material){
    for(let i=0;i<count;i++){
      const a=start+(end-start)*i/count,b=start+(end-start)*(i+1)/count;
      const x1=cx+rx*Math.cos(a),z1=cz+rz*Math.sin(a);
      const x2=cx+rx*Math.cos(b),z2=cz+rz*Math.sin(b);
      const dx=x2-x1,dz=z2-z1,len=Math.hypot(dx,dz);
      const m=box((x1+x2)/2,y,(z1+z2)/2,len,h,depth,material);
      m.rotation.y=-Math.atan2(dz,dx);
    }
  }
  curvedStrip(loungeX,loungeZ,4.5,5.46,-Math.PI/2,Math.PI/2,20,1.72,3.46,.18,mat.plaster);
  curvedStrip(loungeX-.15,loungeZ,3.9,4.94,-Math.PI/2,Math.PI/2,18,.43,.46,.83,mat.couch);
  curvedStrip(loungeX-.10,loungeZ,4.0,4.97,-Math.PI/2,Math.PI/2,18,.88,.64,.24,mat.couch);
  // Warm wall sconces on the curve and cove lighting above.
  curvedStrip(loungeX,loungeZ,4.25,5.13,-Math.PI/2,Math.PI/2,20,3.31,.07,.14,new T.MeshBasicMaterial({color:0xffe4bd}));
  for(const a of [-.95,-.25,.55]){const x=loungeX+3.53*Math.cos(a),z=loungeZ+4.4*Math.sin(a);light(x,2.88,z,0xffd5a9,3,6)}
  function loungeChair(x,z,rotation=0){
    const group=new T.Group();group.position.set(x,0,z);group.rotation.y=rotation;scene.add(group);
    box(0,.47,0,.66,.18,.62,mat.yellow,group);
    box(0,.82,-.28,.64,.72,.13,mat.yellow,group);
    for(const sx of [-.24,.24])for(const sz of [-.22,.22])box(sx,.24,sz,.075,.48,.07,mat.trim,group);
    return group;
  }
  function smallTable(x,z,round=false){
    box(x,.66,z,.12,.8,.12,mat.metal);
    if(round){const top=new T.Mesh(new T.CylinderGeometry(.66,.66,.075,40),mat.timber);top.position.set(x,1.04,z);top.castShadow=true;scene.add(top);}
    else box(x,1.02,z,1.94,.09,.86,mat.timber);
  }
  smallTable(6.2,-17.1,false);smallTable(6.4,-10.8,false);smallTable(10.8,-14.7,true);
  for(const [x,z,r] of [[5.4,-17.85,0],[6.55,-17.8,0],[7.4,-16.8,Math.PI],[5.5,-11.55,0],[7.4,-11.5,0],[9.7,-13.8,.7],[11.6,-14.9,-.6]])loungeChair(x,z,r);
  // 75-inch smart TV on mobile stand, with a movable lectern beside it.
  box(4.62,1.65,-10.4,2.4,1.35,.12,mat.black);
  plane(4.62,1.65,-10.47,2.24,1.2,new T.MeshBasicMaterial({map:textTexture('BIGDATA SOFTWARE',{background:'#112946',size:66})}),Math.PI);
  box(4.62,.77,-10.43,.10,1.16,.12,mat.metal);
  box(4.62,.18,-10.43,1.55,.13,.50,mat.black);
  box(6.72,.95,-10.20,.77,.12,.58,mat.timber);box(6.72,.46,-10.2,.22,.96,.32,mat.metal);
  interactiveBox(4.62,1.65,-10.5,2.53,1.44,.35,'75인치 스마트 TV','휴게실의 이동식 스마트 TV로 학생 활동과 학과 소개 영상을 볼 수 있습니다.','video');
  // Refrigerator and microwave.
  box(3.03,1.07,-18.42,.86,2.12,.84,solid(0x89979c,.36,.53));
  box(3.03,1.73,-17.97,.8,.02,.02,mat.metal);
  box(4.04,1.10,-18.44,.74,.54,.59,mat.white);
  box(4.04,1.14,-18.12,.55,.32,.015,mat.black);
  light(6.3,3.15,-13,0xffefd9,8,11);
  sign('8317 · 휴게실',2.07,2.93,-14,2.15,-Math.PI/2);
  door('lounge-main',2.2,-14,'8317호 유리 접이식 출입문',true,2.81);
  interactiveBox(10.8,1.05,-14.5,1.9,.9,2.1,'학생 휴식·학습 공간','둥근 외벽에 고정된 벤치형 좌석 하부에 콘센트가 설치되어 있어 노트북과 스마트기기를 사용할 수 있습니다.');

  // Corridor wayfinding and floor marker.
  sign('→ 8317 LOUNGE',0,2.62,-8.25,2.55,0,'#12394c');
  sign('← 8316 BIG DATA',0,2.62,7.22,2.55,0,'#12394c');
  return {
    scene,doors,hotspots,
    open(id){ if(doors[id])doors[id].target=1; },
    elevator(){doors.elevator.target=1;},
    update(dt){
      for(const door of Object.values(doors)){
        door.open=T.MathUtils.damp(door.open,door.target,3.8,dt);
        if(door.type==='elevator'){
          door.parts[0].position.x=-.69-door.open*.81;
          door.parts[1].position.x=.69+door.open*.81;
        }else{
          door.parts[0].rotation.y=door.open*1.35;
          door.parts[1].rotation.y=-door.open*1.35;
          door.hit.visible=door.open<.8;
        }
      }
    }
  };
}
