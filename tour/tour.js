import * as T from 'https://cdn.jsdelivr.net/npm/three@0.174.0/build/three.module.js';
import {createWorld} from './world.js';

const $ = id => document.getElementById(id);
const viewport=$('viewport'), loader=$('loader');
const intro=$('intro'), map=$('map-panel'), dialog=$('detail-dialog'),help=$('help-dialog');
const toastEl=$('toast');
let renderer,camera,world,clock;
let started=false, yaw=0, pitch=0, dragging=false, pointerId=null, pointerMoved=0;
let touchLook=false, dragX=0,dragY=0, autoplay=[], waypoint=0, targetYaw=null;
const keys=new Set();
let joystick={x:0,y:0,pointer:null};
let activeRoom='elevator', nearestDoor=null, toastTimer;
const isMobile=matchMedia('(max-width:700px), (pointer:coarse)').matches;

function notify(message,time=3500){
  toastEl.textContent=message;toastEl.classList.add('active');
  clearTimeout(toastTimer);toastTimer=setTimeout(()=>toastEl.classList.remove('active'),time);
}
function fallback(error){
  console.error('3D tour failed',error);
  loader.classList.add('gone');
  const el=$('fallback');el.hidden=false;
  el.querySelector('p').textContent='3D 장면 로딩에 실패했습니다. WebGL이 지원되는 최신 브라우저에서 다시 시도해 주세요. 학과 홈페이지에서도 시설 정보를 볼 수 있습니다.';
}
function locationOf(p){
  if(p.x<-2.30 && p.z>=-8.25 && p.z<=9.3) return '8316';
  if(p.x>2.27 && p.z>=-19.5 && p.z<=-8.3) return '8317';
  if(p.z>26.15) return 'elevator';
  return 'corridor';
}
function updateLocation(){
  const location=locationOf(camera.position);
  if(location!==activeRoom){
    activeRoom=location;
    const data={
      'elevator':['본관 3층 · 엘리베이터','문이 열리면 복도를 따라 투어가 시작됩니다.'],
      'corridor':['본관 3층 · 학과 복도','8303호 교수실부터 실습실·휴게실로 이어집니다.'],
      '8316':['8316호 · 빅데이터실습실','30인 실습실 · 2인용 PC 책상 15개 · 전동 스크린'],
      '8317':['8317호 · 휴게실','곡선형 벤치 · 충전 콘센트 · 75인치 스마트 TV']
    }[location];
    $('location-name').textContent=data[0];$('location-desc').textContent=data[1];
    if(started && (location==='8316'||location==='8317'))notify(data[0]+'에 입장했습니다.',2200);
  }
  const pin=$('map-pin');
  let left=53, top=12+(26-camera.position.z)/46*77;
  if(location==='8316'){left=25;top=38+(8-camera.position.z)/17*20;}
  if(location==='8317'){left=80;top=16;}
  if(location==='elevator'){left=53;top=87;}
  pin.style.left=Math.max(8,Math.min(90,left))+'%';
  pin.style.top=Math.max(8,Math.min(92,top))+'%';
}
function clearAuto(){autoplay=[];waypoint=0;targetYaw=null;$('btn-tour').textContent='자동 투어';}
function startTour(auto=false) {
  if(!started){
    started=true;intro.classList.add('hidden');document.body.classList.add('touring');
    world.elevator();notify('엘리베이터 문이 열립니다. W·A·S·D 키 또는 모바일 조이스틱으로 이동하세요.',5400);
    setTimeout(()=>{if(started)map.classList.add('open')},1300);
  }
  if(auto) setTimeout(()=>guideTo('8316',true),1300);
}
function point(x,z){return new T.Vector3(x,1.64,z);}
function guideTo(destination,chain=false) {
  startTour();
  world.elevator();
  if(destination==='8316')world.open('lab-front');
  if(destination==='8317')world.open('lounge-main');
  const from=locationOf(camera.position);
  let exit=[];
  if(from==='8316'){
    world.open('lab-back'); exit=[point(-3.2,-2.65),point(0,-2.65)];
  }
  if(from==='8317'){
    world.open('lounge-main');exit=[point(3.1,-14),point(0,-14)];
  }
  if(from==='elevator'){
    exit=[point(0,25.6),point(0,21)];
  }
  const routes={
    lobby:[point(0,20.8),point(0,24.4)],
    '8316':[point(0,9.1),point(0,5.53),point(-2.9,5.53),point(-5.7,5.53),point(-7.43,3.1)],
    '8317':[point(0,-2.7),point(0,-13.96),point(2.95,-13.96),point(5.2,-13.96),point(8.1,-13.96)]
  };
  if(from==='8316' && destination==='8316')exit=[];
  if(from==='8317' && destination==='8317')exit=[];
  autoplay=exit.concat(routes[destination]||routes.lobby);waypoint=0;
  if(chain && destination==='8316') autoplay.push({chain:'8317'});
  $('btn-tour').textContent='투어 중단';
  map.classList.remove('open');
  notify(destination==='8316'?'8316호 빅데이터실습실로 안내합니다.':destination==='8317'?'8317호 휴게실로 안내합니다.':'엘리베이터로 안내합니다.');
}
function validPosition(x,z,prev){
  const corridor=(Math.abs(x)<1.94 && z>-20.02&&z<26.2);
  const elevator=(Math.abs(x)<1.28&&z>=26.1&&z<30.5);
  const lab=x>-12.4&&x<-2.36&&z>-7.92&&z<8.92;
  const lounge=x>2.36&&x<13.20&&z>-19.25&&z<-8.72;
  const labDoors=(Math.abs(z+2.65)<.64 && world.doors['lab-back'].open>.77) ||
    (Math.abs(z-5.52)<.65 && world.doors['lab-front'].open>.77);
  const labBridge=x<=-1.9&&x>=-2.43&&labDoors;
  const loungeBridge=x>=1.9&&x<=2.44&&Math.abs(z+14)<1.27&&world.doors['lounge-main'].open>.77;
  if(prev.z>26.19&&z<26.19&&world.doors.elevator.open<.82)return false;
  if(prev.z<26.19&&z>26.19&&world.doors.elevator.open<.82)return false;
  return corridor||elevator||lab||lounge||labBridge||loungeBridge;
}
function walk(dt){
  const forward=(keys.has('KeyW')||keys.has('ArrowUp')?1:0)-(keys.has('KeyS')||keys.has('ArrowDown')?1:0)-joystick.y;
  const sideways=(keys.has('KeyD')||keys.has('ArrowRight')?1:0)-(keys.has('KeyA')||keys.has('ArrowLeft')?1:0)+joystick.x;
  if(!forward&&!sideways)return;
  const length=Math.hypot(forward,sideways);const f=forward/Math.max(1,length),s=sideways/Math.max(1,length),speed=keys.has('ShiftLeft')?5.25:3.45;
  const dx=(-Math.sin(yaw)*f+Math.cos(yaw)*s)*speed*dt;
  const dz=(-Math.cos(yaw)*f-Math.sin(yaw)*s)*speed*dt;
  const current=camera.position.clone();
  if(validPosition(current.x+dx,current.z,current))camera.position.x+=dx;
  if(validPosition(camera.position.x,current.z+dz,current))camera.position.z+=dz;
}
function animateRoute(dt){
  if(!autoplay.length)return;
  const next=autoplay[waypoint];
  if(!next){clearAuto();return;}
  if(next.chain){const d=next.chain;clearAuto();guideTo(d);return;}
  const diff=next.clone().sub(camera.position);diff.y=0;
  const distance=diff.length();
  if(distance<.18){
    waypoint++;
    if(waypoint>=autoplay.length){
      const dest=locationOf(camera.position);
      if(dest==='8316')targetYaw=Math.PI;
      if(dest==='8317')targetYaw=-Math.PI/2;
      clearAuto();
      notify('목적지에 도착했습니다. 마우스 또는 화면 터치로 자유롭게 둘러보세요.',3700);
    }
    return;
  }
  const step=Math.min(distance,dt*6.0);diff.normalize();
  const nextPos=camera.position.clone().addScaledVector(diff,step);
  // Guided route moves through opened doors. All points remain on planned corridor/room paths.
  camera.position.x=nextPos.x; camera.position.z=nextPos.z;
  const desired=Math.atan2(-diff.x,-diff.z);
  yaw+=Math.atan2(Math.sin(desired-yaw),Math.cos(desired-yaw))*Math.min(1,dt*5);
  pitch+=(0-pitch)*Math.min(1,dt*3);
}
function findNearby(){
  nearestDoor=null;
  let best=2.25;
  for(const door of Object.values(world.doors)){
    if(door.type==='elevator'||door.target>0.5)continue;
    const dst=Math.hypot(camera.position.x-door.position[0],camera.position.z-door.position[1]);
    if(dst<best){best=dst;nearestDoor=door;}
  }
  const prompt=$('action-prompt');
  prompt.classList.toggle('visible',!!nearestDoor && started);
  if(nearestDoor)$('prompt-label').textContent=nearestDoor.name+' 열기';
  $('btn-mobile-action').style.opacity=nearestDoor?'1':'.55';
}
function performAction(){
  if(nearestDoor){world.open(nearestDoor.id);notify(nearestDoor.name+'을 열었습니다.',1700);return;}
  if(activeRoom==='8316')showDetail('8316호 · 빅데이터실습실','학생 30명이 2인용 컴퓨터 책상 15개에 앉아 데이터 수집·분석·시각화와 빅데이터 처리 기술을 실습합니다.','ROOM 8316');
  else if(activeRoom==='8317')showDetail('8317호 · 휴게실','곡선형 벽면 좌석 아래의 콘센트에서 노트북과 스마트기기를 충전할 수 있습니다. 75인치 스마트 TV, 강연대, 냉장고와 전자레인지도 마련되어 있습니다.','ROOM 8317');
}
function showDetail(title,description,tag='CAMPUS INTERACTION',kind='info',url=null){
  $('dialog-tag').textContent=tag;$('dialog-title').textContent=title;$('dialog-text').textContent=description;
  const extra=$('dialog-extra');extra.replaceChildren();
  if(kind==='video'){
    const video=document.createElement('video');
    video.setAttribute('controls','');video.setAttribute('playsinline','');
    video.setAttribute('preload','none');
    video.style.cssText='width:100%;margin-top:14px;max-height:230px;background:#071323;border-radius:8px';
    video.poster='/assets/media/department-campus-cover.webp';
    video.src='/assets/media/department-campus-a-v11.mp4';
    extra.append(video);
  }else if(url){
    const a=document.createElement('a');a.href=url;a.target='_blank';a.rel='noopener noreferrer';a.textContent='관련 콘텐츠 보기 ↗';extra.append(a);
  }
  dialog.showModal();
}
function clickHotspot(event){
  const rect=renderer.domElement.getBoundingClientRect();
  const ndc=new T.Vector2((event.clientX-rect.left)/rect.width*2-1,-(event.clientY-rect.top)/rect.height*2+1);
  const raycaster=new T.Raycaster();raycaster.setFromCamera(ndc,camera);raycaster.far=7.5;
  const hits=raycaster.intersectObjects(world.hotspots.filter(obj=>obj.visible),false);
  if(!hits.length)return;
  const data=hits[0].object.userData.interactive;
  if(!data)return;
  if(data.kind==='door'){world.open(data.doorId);notify(data.title+'을 열었습니다.');return;}
  showDetail(data.title,data.description,data.kind==='video'?'CAMPUS MEDIA':'ON-SITE EXHIBIT',data.kind,data.url);
}
function pointerDown(e){
  if(!started||dialog.open||help.open)return;
  pointerId=e.pointerId;dragX=e.clientX;dragY=e.clientY;pointerMoved=0;dragging=true;
  viewport.setPointerCapture?.(e.pointerId);
}
function pointerMove(e){
  if(!dragging||pointerId!==e.pointerId)return;
  const dx=e.clientX-dragX,dy=e.clientY-dragY;
  dragX=e.clientX;dragY=e.clientY;pointerMoved+=Math.abs(dx)+Math.abs(dy);
  if(pointerMoved>8)clearAuto();
  yaw-=dx*.0037;
  pitch=Math.max(-1.05,Math.min(1.05,pitch-dy*.0030));
}
function pointerUp(e){
  if(!dragging||pointerId!==e.pointerId)return;
  dragging=false;pointerId=null;
  if(pointerMoved<9)clickHotspot(e);
}
function setupJoystick(){
  const base=$('joy-base'),stick=$('joy-stick');
  const center=()=>{stick.style.transform='translate(0px,0px)';joystick.x=0;joystick.y=0;};
  base.addEventListener('pointerdown',e=>{e.preventDefault();e.stopPropagation();joystick.pointer=e.pointerId;base.setPointerCapture(e.pointerId);move(e)});
  base.addEventListener('pointermove',e=>{if(joystick.pointer===e.pointerId)move(e)});
  for(const name of ['pointerup','pointercancel','lostpointercapture'])base.addEventListener(name,e=>{if(joystick.pointer===e.pointerId){joystick.pointer=null;center()}});
  function move(e){
    const r=base.getBoundingClientRect(),cx=r.left+r.width/2,cy=r.top+r.height/2;
    const dx=e.clientX-cx,dy=e.clientY-cy,m=Math.max(1,Math.hypot(dx,dy)),lim=29;
    const px=dx*Math.min(lim/m,1),py=dy*Math.min(lim/m,1);
    joystick.x=px/lim;joystick.y=py/lim;
    stick.style.transform='translate('+px+'px,'+py+'px)';
    clearAuto();
  }
}
function attachEvents(){
  $('btn-start').addEventListener('click',()=>startTour());
  $('btn-guide').addEventListener('click',()=>startTour(true));
  $('btn-help').addEventListener('click',()=>help.showModal());
  $('help-close').addEventListener('click',()=>help.close());
  $('help-done').addEventListener('click',()=>help.close());
  $('dialog-close').addEventListener('click',()=>dialog.close());
  $('dialog-done').addEventListener('click',()=>dialog.close());
  $('btn-map').addEventListener('click',()=>map.classList.toggle('open'));
  $('btn-map-hide').addEventListener('click',()=>map.classList.remove('open'));
  $('btn-reset').addEventListener('click',()=>{
    clearAuto();camera.position.set(0,1.64,28.6);yaw=0;pitch=0;world.elevator();updateLocation();notify('엘리베이터 위치로 돌아왔습니다.');
  });
  $('btn-tour').addEventListener('click',()=>autoplay.length?clearAuto():guideTo('8316',true));
  document.querySelectorAll('[data-dest]').forEach(el=>el.addEventListener('click',()=>guideTo(el.dataset.dest)));
  $('btn-mobile-action').addEventListener('click',performAction);
  viewport.addEventListener('pointerdown',pointerDown);
  viewport.addEventListener('pointermove',pointerMove);
  viewport.addEventListener('pointerup',pointerUp);
  viewport.addEventListener('pointercancel',()=>{dragging=false;pointerId=null});
  window.addEventListener('keydown',e=>{
    if(e.code==='Escape'){clearAuto();return;}
    if(['KeyW','KeyA','KeyS','KeyD','ArrowUp','ArrowLeft','ArrowRight','ArrowDown','Space'].includes(e.code)&&!dialog.open&&!help.open)e.preventDefault();
    keys.add(e.code);
    if(e.code==='KeyE' && started && !dialog.open&&!help.open)performAction();
  });
  window.addEventListener('keyup',e=>keys.delete(e.code));
  window.addEventListener('blur',()=>{keys.clear();joystick.x=joystick.y=0;});
  window.addEventListener('resize',()=>{
    if(!renderer)return;
    camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();
    renderer.setSize(innerWidth,innerHeight);
  });
  setupJoystick();
}
function render(){
  const dt=Math.min(clock.getDelta(),.05);
  if(started&&!dialog.open&&!help.open){
    if(autoplay.length)animateRoute(dt); else walk(dt);
    findNearby();
    updateLocation();
  }
  camera.rotation.order='YXZ';
  camera.rotation.y=yaw;camera.rotation.x=pitch;
  world.update(dt);
  renderer.render(world.scene,camera);
  requestAnimationFrame(render);
}
function init(){
  try{
    renderer=new T.WebGLRenderer({antialias:!isMobile,alpha:false,powerPreference:'high-performance'});
    renderer.outputColorSpace=T.SRGBColorSpace;
    renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=1.37;
    renderer.setPixelRatio(Math.min(devicePixelRatio,isMobile?1.3:1.7));
    renderer.setSize(innerWidth,innerHeight);
    viewport.append(renderer.domElement);
    camera=new T.PerspectiveCamera(isMobile?77:70,innerWidth/innerHeight,.08,175);
    camera.position.set(0,1.64,28.6);
    clock=new T.Clock();
    world=createWorld(T);
    attachEvents();
    const params=new URLSearchParams(location.search);
    const room=params.get('room');
    if(room==='8316'||room==='8317'){
      setTimeout(()=>{startTour();guideTo(room)},1100);
    }
    window.tourReady=true;
    loader.classList.add('gone');
    setTimeout(()=>loader.remove(),800);
    requestAnimationFrame(render);
  }catch(error){fallback(error)}
}
init();
