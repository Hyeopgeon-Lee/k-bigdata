import * as T from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import {buildVideoWorld} from './world-v2.js';
const $=id=>document.getElementById(id);
const viewport=$('viewport'),loader=$('loader'),intro=$('intro'),map=$('map-panel');
const dialog=$('detail-dialog'),help=$('help-dialog'),toastEl=$('toast');
let renderer,camera,world,clock,started=false,yaw=0,pitch=0,dragging=false,pointerId=null,dragDistance=0;
let route=[],routeIndex=0,routeNext=null,activeRoom='elevator',nearDoor=null,toastTimer;
const held=new Set();const stick={x:0,y:0,id:null};
const coarse=matchMedia('(pointer:coarse)').matches;
const focus={elevator:[-1.80,5.4],lobby:[2.0,1.0],corridor:[10.18,21.0],'8316':[5.4,22.2],'8317':[16.8,37.8]};
function status(message,ms=3600){
 toastEl.textContent=message;toastEl.classList.add('active');clearTimeout(toastTimer);
 toastTimer=setTimeout(()=>toastEl.classList.remove('active'),ms);
}
function fail(error){
 console.error('Virtual tour loading error:',error);
 window.tourReady=false;loader.classList.add('gone');$('fallback').hidden=false;
}
function start(chain=false){
 if(!started){
   started=true;intro.classList.add('hidden');document.body.classList.add('touring');
   world.elevator();status('엘리베이터가 열립니다. 정면은 8303호 교수실, 오른쪽으로는 실습실 복도가 이어집니다.',6400);
 }
 if(chain)setTimeout(()=>guide('8316','8317'),1400);
}
function updateHUD(){
 const zone=world.region(camera.position.x,camera.position.z);
 const loc=zone==='outside'?'corridor':zone;
 if(loc!==activeRoom){
  activeRoom=loc;
  const labels={
   elevator:['본관 3층 · 엘리베이터','문이 열리면 정면의 8303호 교수실과 가로 복도가 보입니다.'],
   lobby:['본관 3층 · 학과 복도','오른쪽 복도를 따라 8320호·회의실·8317호·8316호가 이어집니다.'],
   corridor:['본관 3층 · 실습실 복도','왼쪽에는 8316호, 오른쪽에는 8320호·회의실·8317호가 있습니다.'],
   '8316':['8316호 · 빅데이터실습실','학생 PC 30대 · 3열×5줄 · 교수자 PC 전면 오른쪽'],
   '8317':['8317호 · 휴게실','곡선형 벤치·노란 의자·75인치 TV · 학생 휴식 공간'],
   '8318':['8318호 · 회의실','10명 회의 · 프로젝터·전동스크린'],
   '8319':['8319호 · 회의실','10명 회의 · 매립형 화이트보드'],
   '8320':['8320호 · 인공지능실습실','30명 수용 · AI 교육 공간']
  }[loc]||['본관 3층','학과 시설을 둘러보세요.'];
  $('location-name').textContent=labels[0];$('location-desc').textContent=labels[1];
  if(started && (loc==='8316'||loc==='8317'))status(labels[0]+'에 도착했습니다.',2200);
 }
 const pin=$('map-pin');
 const x=camera.position.x,z=camera.position.z;
 const left=Math.max(5,Math.min(91,10+(x+7)*2.95));
 const top=Math.max(5,Math.min(93,88-(z+3)*1.78));
 pin.style.left=left+'%';pin.style.top=top+'%';
}
function openDoorsFor(destination){
 world.elevator();
 if(destination==='8316'){world.open('lab-front');world.open('lab-rear');}
 if(destination==='8317')world.open('lounge');
 if(destination==='8318')world.open('room-8318');
 if(destination==='8319')world.open('room-8319');
}
function clearRoute(){route=[];routeIndex=0;routeNext=null;$('btn-tour').textContent='자동 투어';}
function waypoint(x,z){return new T.Vector3(x,1.64,z);}
function routeFromNow(destination){
 const zone=world.region(camera.position.x,camera.position.z);
 const waypoints=[];
 if(zone==='8316'){
   world.open('lab-front');
   waypoints.push(waypoint(7.56,21.35),waypoint(9.5,21.35),waypoint(10.18,21.35));
 }else if(zone==='8317'){
   world.open('lounge');
   waypoints.push(waypoint(13.1,37.8),waypoint(10.18,37.8));
 }else if(zone==='8318'){
    world.open('room-8318');
    waypoints.push(waypoint(12.8,31.25),waypoint(10.18,31.25));
  }else if(zone==='8319'){
    world.open('room-8319');
    waypoints.push(waypoint(12.8,27.25),waypoint(10.18,27.25));
  }else if(zone==='elevator'){
   waypoints.push(waypoint(-1.8,3.3),waypoint(-1.8,.65),waypoint(10.18,.65));
 }else if(zone==='lobby'){
   waypoints.push(waypoint(camera.position.x,.65),waypoint(10.18,.65));
 }else{
   waypoints.push(waypoint(10.18,camera.position.z));
 }
 const corridorZ=(zone==='8316')?21.35:(zone==='8317'?37.8:(zone==='8318'?31.25:(zone==='8319'?27.25:Math.max(.65,camera.position.z))));
 if(destination==='8316'){
   if(corridorZ!==21.35)waypoints.push(waypoint(10.18,21.35));
   waypoints.push(waypoint(9.7,21.35),waypoint(8.0,21.35),waypoint(6.35,21.35),waypoint(5.1,22.0));
 }else if(destination==='8317'){
   if(corridorZ!==37.8)waypoints.push(waypoint(10.18,37.8));
   waypoints.push(waypoint(11.1,37.8),waypoint(13.4,37.8),waypoint(16.2,37.8));
 }else if(destination==='8318'){
   if(corridorZ!==31.25)waypoints.push(waypoint(10.18,31.25));
   waypoints.push(waypoint(11.3,31.25),waypoint(12.9,31.25),waypoint(15.5,31.25));
 }else if(destination==='8319'){
   if(corridorZ!==27.25)waypoints.push(waypoint(10.18,27.25));
   waypoints.push(waypoint(11.3,27.25),waypoint(12.9,27.25),waypoint(15.5,27.25));
 }else{
   if(corridorZ!==.65)waypoints.push(waypoint(10.18,.65));
   waypoints.push(waypoint(2.6,.65),waypoint(-1.80,1.2),waypoint(-1.8,4.65));
 }
 return waypoints;
}
function guide(dest='8316',then=null) {
 start();openDoorsFor(dest);
 route=routeFromNow(dest);routeIndex=0;routeNext=then;
 map.classList.remove('open');
 $('btn-tour').textContent='자동 안내 중단';
 status(dest==='8316'?'8316호 실습실로 이동합니다.':dest==='8317'?'8317호 휴게실로 이동합니다.':dest==='8318'?'8318호 회의실로 이동합니다.':dest==='8319'?'8319호 회의실로 이동합니다.':'엘리베이터로 돌아갑니다.');
}
function updateRoute(dt){
 if(!route.length)return;
 const target=route[routeIndex];
 if(!target){const next=routeNext;clearRoute();if(next){setTimeout(()=>guide(next),1000);}else status('목적지에 도착했습니다. 자유롭게 둘러보세요.');return;}
 const dx=target.x-camera.position.x,dz=target.z-camera.position.z;
 const distance=Math.hypot(dx,dz);
 if(distance<.19){routeIndex++;return;}
 const step=Math.min(distance,dt*4.3);
 const ux=dx/distance,uz=dz/distance;
 camera.position.x+=ux*step;camera.position.z+=uz*step;
 const desired=Math.atan2(-ux,-uz);
 yaw+=Math.atan2(Math.sin(desired-yaw),Math.cos(desired-yaw))*Math.min(1,dt*5);
 pitch+=(0-pitch)*Math.min(1,dt*4);
}
function canMove(nx,nz,px,pz){
 const old=world.region(px,pz),next=world.region(nx,nz);
 if(next==='outside')return false;
 if(next===old)return true;
 // Doors gate transitions. Unentered rooms may not be crossed until their door opens.
 const pair=new Set([old,next]);
 if(pair.has('elevator')&&pair.has('lobby'))return world.doors.elevator.open>.80 && nx>-3.90&&nx<.27;
 if(pair.has('8316')&&pair.has('corridor')){
   const doorZ=Math.abs(nz-21.35)<.68?'lab-front':Math.abs(nz-34.3)<.68?'lab-rear':null;
   return doorZ && world.doors[doorZ].open>.72;
 }
 if(pair.has('8317')&&pair.has('corridor'))return world.doors.lounge.open>.72&&Math.abs(nz-37.8)<1.19;
  if(pair.has('8318')&&pair.has('corridor'))return world.doors['room-8318'].open>.72&&Math.abs(nz-31.25)<.68;
 if(pair.has('8319')&&pair.has('corridor'))return world.doors['room-8319'].open>.72&&Math.abs(nz-27.25)<.68;
 if(pair.has('lobby')&&pair.has('corridor'))return true;
 // Meeting rooms and 8320 are visible through glazing but not fully implemented in this release.
 return false;
}
function walk(dt){
 let f=(held.has('KeyW')||held.has('ArrowUp')?1:0)-(held.has('KeyS')||held.has('ArrowDown')?1:0)-stick.y;
 let r=(held.has('KeyD')||held.has('ArrowRight')?1:0)-(held.has('KeyA')||held.has('ArrowLeft')?1:0)+stick.x;
 if(!f&&!r)return;
 const norm=Math.max(1,Math.hypot(f,r));f/=norm;r/=norm;
 const speed=(held.has('ShiftLeft')?5:3.5)*Math.min(dt,.05);
 const dx=(-Math.sin(yaw)*f+Math.cos(yaw)*r)*speed;
 const dz=(-Math.cos(yaw)*f-Math.sin(yaw)*r)*speed;
 const x=camera.position.x,z=camera.position.z;
 if(canMove(x+dx,z,x,z))camera.position.x=x+dx;
 if(canMove(camera.position.x,z+dz,camera.position.x,z))camera.position.z=z+dz;
}
function nearest(){
 nearDoor=null;let distance=2.15;
 for(const d of Object.values(world.doors)){
  if(!d.position||d.target>=1)continue;
  const dst=Math.hypot(camera.position.x-d.position[0],camera.position.z-d.position[1]);
  if(dst<distance){distance=dst;nearDoor=d;}
 }
 const prompt=$('action-prompt');prompt.classList.toggle('visible',!!nearDoor&&started);
 if(nearDoor)$('prompt-label').textContent='출입문 열기';
 $('btn-mobile-action').style.opacity=nearDoor?'1':'.55';
}
function action(){
 if(nearDoor){world.open(nearDoor.id);status('출입문이 열렸습니다. 안으로 이동해 보세요.',1500);return;}
 if(activeRoom==='8316')details('8316호 빅데이터실습실','30석의 PC 실습실로, 2인용 책상 15개를 3열×5줄로 배치했습니다. 전면에는 전동 스크린과 벽면 매립형 도자기 화이트보드가 있습니다.','ROOM 8316');
 if(activeRoom==='8319')details('8319호 회의실','8318호와 같은 디자인의 10인용 타원형 원목 회의탁자·의자 10개·매립형 필기 화이트보드를 갖춘 회의실입니다. 8319호에는 빔프로젝터와 전동 스크린이 없습니다.','ROOM 8319');
  if(activeRoom==='8318')details('8318호 회의실','10인용 타원형 원목 회의탁자(4+4+1+1)와 대형 매립형 화이트보드, 천장 빔프로젝터 및 전동 스크린이 설치되는 공간입니다. 가구 배치는 계획 시안입니다.','ROOM 8318');
  if(activeRoom==='8317')details('8317호 휴게실','학생이 노트북을 사용하거나 쉬는 공간입니다. 곡선 벽면의 매립 좌석 아래 콘센트, 노란 의자, 75인치 스탠드 스마트 TV, 냉장고·전자레인지가 있습니다.','ROOM 8317');
}
function details(title,description,tag='FACILITY INFORMATION',kind='detail',url=null){
 $('dialog-tag').textContent=tag;$('dialog-title').textContent=title;$('dialog-text').textContent=description;
 const slot=$('dialog-extra');slot.replaceChildren();
 if(kind==='video'){
   const video=document.createElement('video');video.controls=true;video.playsInline=true;
   video.preload='none';video.poster='/assets/media/department-campus-cover.webp';
   video.src='/assets/media/department-campus-a-v11.mp4';
   video.style.cssText='width:100%;max-height:240px;margin-top:14px;background:#071323;border-radius:8px';
   slot.append(video);
 } else if(url){
   const link=document.createElement('a');link.href=url;link.target='_blank';link.rel='noopener noreferrer';link.textContent='자세히 보기 ↗';slot.append(link);
 }
 dialog.showModal();
}
function clickPoint(e) {
 const rect=renderer.domElement.getBoundingClientRect();
 const pointer=new T.Vector2((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);
 const rc=new T.Raycaster();rc.setFromCamera(pointer,camera);rc.far=6;
 const hits=rc.intersectObjects(world.hotspots.filter(x=>x.visible));
 if(!hits.length)return;
 const item=hits[0].object.userData.interactive;
 if(!item)return;
 if(item.kind==='door'){world.open(item.doorId);status('출입문이 열렸습니다.',1500)}
  else if(item.kind==='screen-toggle'){
    if(window.room8318ModelLoaded && typeof window.toggle8318Screen==='function'){
       window.toggle8318Screen();
       status(window.room8318ScreenDown?'8318호 전동 스크린을 내렸습니다.':'8318호 전동 스크린을 올렸습니다.',2200);
    }else status('8318호 모델이 아직 로딩 중입니다.',1600);
  }
 else details(item.title,item.description,item.kind==='video'?'CAMPUS VIDEO':'FACILITY DETAIL',item.kind,item.url);
}
function captureStart(e){
 if(!started||dialog.open||help.open)return;
 pointerId=e.pointerId;dragging=true;dragDistance=0;
 captureStart.x=e.clientX;captureStart.y=e.clientY;
 viewport.setPointerCapture?.(e.pointerId);
}
function captureMove(e){
 if(!dragging||pointerId!==e.pointerId)return;
 const dx=e.clientX-captureStart.x,dy=e.clientY-captureStart.y;
 dragDistance+=Math.abs(dx)+Math.abs(dy);
 captureStart.x=e.clientX;captureStart.y=e.clientY;
 if(dragDistance>8)clearRoute();
 yaw-=dx*.0038;pitch=Math.max(-1.07,Math.min(1.07,pitch-dy*.0030));
}
function captureEnd(e){
 if(!dragging||pointerId!==e.pointerId)return;
 dragging=false;pointerId=null;if(dragDistance<9)clickPoint(e);
}
function joystickSetup(){
 const base=$('joy-base'),knob=$('joy-stick');
 const reset=()=>{stick.x=stick.y=0;knob.style.transform='translate(0px,0px)'};
 const move=e=>{
   const rect=base.getBoundingClientRect(),cx=rect.left+rect.width/2,cy=rect.top+rect.height/2;
   const dx=e.clientX-cx,dy=e.clientY-cy;
   const scale=Math.min(1,29/Math.max(1,Math.hypot(dx,dy)));
   const px=dx*scale,py=dy*scale;
   stick.x=px/29;stick.y=py/29;
   knob.style.transform='translate('+px+'px,'+py+'px)';
 };
 base.addEventListener('pointerdown',e=>{e.preventDefault();e.stopPropagation();stick.id=e.pointerId;base.setPointerCapture(e.pointerId);clearRoute();move(e)});
 base.addEventListener('pointermove',e=>{if(stick.id===e.pointerId)move(e)});
 for(const event of ['pointerup','pointercancel','lostpointercapture'])base.addEventListener(event,e=>{
   if(stick.id===e.pointerId){stick.id=null;reset()}
 });
}
function events(){
 $('btn-start').addEventListener('click',()=>start());
 $('btn-guide').addEventListener('click',()=>start(true));
 $('btn-help').addEventListener('click',()=>help.showModal());
 $('help-close').addEventListener('click',()=>help.close());
 $('help-done').addEventListener('click',()=>help.close());
 $('dialog-close').addEventListener('click',()=>dialog.close());
 $('dialog-done').addEventListener('click',()=>dialog.close());
 $('btn-map').addEventListener('click',()=>map.classList.toggle('open'));
 $('btn-map-hide').addEventListener('click',()=>map.classList.remove('open'));
 $('btn-reset').addEventListener('click',()=>{
    clearRoute();camera.position.set(-1.8,1.64,5.43);yaw=0;pitch=0;world.elevator();updateHUD();status('엘리베이터에서 다시 시작합니다.');
 });
 $('btn-tour').addEventListener('click',()=>route.length?clearRoute():guide('8316','8317'));
 document.querySelectorAll('[data-dest]').forEach(el=>el.addEventListener('click',()=>guide(el.dataset.dest)));
 $('btn-mobile-action').addEventListener('click',action);
 viewport.addEventListener('pointerdown',captureStart);
 viewport.addEventListener('pointermove',captureMove);
 viewport.addEventListener('pointerup',captureEnd);
 viewport.addEventListener('pointercancel',()=>{dragging=false;pointerId=null});
 window.addEventListener('keydown',e=>{
   if(e.code==='Escape'){clearRoute();return;}
   if(['KeyW','KeyA','KeyS','KeyD','ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Space'].includes(e.code) && !dialog.open&&!help.open)e.preventDefault();
   held.add(e.code);
   if(e.code==='KeyE' && started&&!dialog.open&&!help.open)action();
 });
 window.addEventListener('keyup',e=>held.delete(e.code));
 window.addEventListener('blur',()=>{held.clear();stick.x=stick.y=0});
 window.addEventListener('resize',()=>{
   camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();
   renderer.setPixelRatio(Math.min(devicePixelRatio,coarse?1.3:1.65));
   renderer.setSize(innerWidth,innerHeight);
 });
 joystickSetup();
}
function render(){
 const dt=Math.min(clock.getDelta(),.05);
 if(started&&!dialog.open&&!help.open){
   if(route.length)updateRoute(dt);else walk(dt);
   nearest();updateHUD();
 }
 camera.rotation.order='YXZ';camera.rotation.y=yaw;camera.rotation.x=pitch;
 world.update(dt);renderer.render(world.scene,camera);
 requestAnimationFrame(render);
}
function init(){
 try{
   renderer=new T.WebGLRenderer({antialias:!coarse,alpha:false,powerPreference:'high-performance'});
   renderer.outputColorSpace=T.SRGBColorSpace;
   renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=1.6;
   renderer.setPixelRatio(Math.min(devicePixelRatio,coarse?1.3:1.65));
   renderer.setSize(innerWidth,innerHeight);
   viewport.appendChild(renderer.domElement);
   camera=new T.PerspectiveCamera(coarse?74:67,innerWidth/innerHeight,.075,120);
   camera.position.set(-1.8,1.64,5.43);
   yaw=0;pitch=0;clock=new T.Clock();
   world=buildVideoWorld(T);
   // Load authored independent GLB asset. Entrance at local x=-4.95 maps
   // to world x=12.03. Its exterior, furniture and lighting are in the file.
   const roomLoader=new GLTFLoader();
   roomLoader.load('/tour/models/room-8317.glb',
     (gltf)=>{
       const room=gltf.scene;
       room.name='ROOM_8317_IMPORTED_GLB';
       room.position.set(17.0,0,37.8);
       room.traverse((node)=>{
         if(node.isMesh){node.castShadow=false;node.receiveShadow=true;}
       });
       world.scene.add(room);
       window.room8317ModelLoaded=true;
       status('8317호 독립 GLB 3D 모델 로딩 완료',2600);
     },
     undefined,
     (error)=>{
       console.error('8317 GLB failed to load',error);
       window.room8317ModelLoaded=false;
       status('8317호 3D 모델을 불러올 수 없습니다. 새로고침해 주세요.',6500);
     });
   
   // Room 8318: independent GLB, 10-person conference table and motorized screen.
   roomLoader.load('/tour/models/room-8318.glb',
      (gltf)=>{
        const room=gltf.scene;
        room.name='ROOM_8318_IMPORTED_GLB';
        room.position.set(16.25,0,31.30);
        let screenDown=false;
        const screenParts=['8318_projector_screen_lowered','8318_screen_weight_bar']
          .map(name=>room.getObjectByName(name)).filter(Boolean);
        const setScreen=(down)=>{
          screenDown=down;window.room8318ScreenDown=down;
          screenParts.forEach(mesh=>{mesh.visible=down;});
        };
        window.toggle8318Screen=()=>setScreen(!screenDown);
        setScreen(false);
        room.traverse(node=>{if(node.isMesh){node.castShadow=false;node.receiveShadow=true;}});
        world.scene.add(room);
        window.room8318ModelLoaded=true;
      },
      undefined,
      (error)=>{
        console.error('8318 GLB loading failed',error);
        window.room8318ModelLoaded=false;
        status('8318호 3D 모델을 불러오지 못했습니다.',5000);
      });
    roomLoader.load('/tour/models/room-8319.glb',
      (gltf)=>{
        const room=gltf.scene;
        room.name='ROOM_8319_IMPORTED_GLB';
        room.position.set(16.25,0,27.15);
        room.traverse(node=>{if(node.isMesh){node.castShadow=false;node.receiveShadow=true;}});
        world.scene.add(room);
        window.room8319ModelLoaded=true;
      },
      undefined,
      (error)=>{
        console.error('8319 GLB loading failed',error);
        window.room8319ModelLoaded=false;
        status('8319호 3D 모델을 불러오지 못했습니다.',5000);
      });
   events();updateHUD();
   const params=new URLSearchParams(location.search);
   if(['8316','8317','8318','8319'].includes(params.get('room')))setTimeout(()=>guide(params.get('room')),1100);
   window.tourReady=true;loader.classList.add('gone');setTimeout(()=>loader.remove(),750);
   requestAnimationFrame(render);
 }catch(err){fail(err)}
}
init();