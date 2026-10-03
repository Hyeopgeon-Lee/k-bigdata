"""Generate deterministic, accessible text-led OG graphics (Pillow; authoring only)."""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'data/admissions.json').read_text(encoding='utf-8'))
FONT=Path('C:/Windows/Fonts/malgunbd.ttf')
def create(name,kicker,lines,note):
    im=Image.new('RGB',(1200,630),'#041225');d=ImageDraw.Draw(im)
    for x in range(0,1200,64): d.line((x,0,x,630),fill='#0c2746')
    for y in range(0,630,64): d.line((0,y,1200,y),fill='#0c2746')
    d.rounded_rectangle((64,54,136,126),radius=16,fill='#cbff3d')
    d.text((80,69),'AI',font=ImageFont.truetype(str(FONT),32),fill='#041225')
    d.text((160,62),'한국폴리텍대학 서울강서캠퍼스',font=ImageFont.truetype(str(FONT),28),fill='#ffffff')
    d.text((160,101),'빅데이터소프트웨어공학과',font=ImageFont.truetype(str(FONT),23),fill='#9eb4cf')
    d.text((64,185),kicker,font=ImageFont.truetype(str(FONT),24),fill='#39dbff')
    for index,line in enumerate(lines):d.text((60,237+index*94),line,font=ImageFont.truetype(str(FONT),68),fill='#ffffff' if index==0 else '#cbff3d')
    d.line((64,495,1136,495),fill='#36516e',width=2)
    d.text((64,524),note,font=ImageFont.truetype(str(FONT),26),fill='#d6e3f4')
    d.text((930,570),'ai.k-bigdata.kr',font=ImageFont.truetype(str(FONT),23),fill='#39dbff')
    im.save(ROOT/'assets/promo'/name,optimize=True)
create('og-department.png','2년제 대학 학위과정 · 산업학사',['AI·데이터를 배우고,','소프트웨어로 증명하다.'],'학생 프로젝트 · 취업현황 · 교육과정 · 입학안내')
for r in DATA['rounds'][1:]:
    start=r['start'].replace('-','.');end=r['end'].replace('-','.')
    create(r['socialImage'],'2027학년도 대학입학',['만들며 배우는 대학,',r['name']+' 모집안내'],f'원서접수 {start} ~ {end} {r["deadlineTime"]} · 공식 모집요강 확인')
create('og-insights.png','AI · DATA · CLOUD · SOFTWARE',['기술의 변화를 읽고,','프로젝트의 질문을 찾다.'],'AI·IT 인사이트 · 기술 이해 · 실습 · 진로 탐색')
create('og-projects.png','STUDENT PROJECTS',['학생이 직접 만든','AI·소프트웨어 프로젝트'],'2026 작품전시회 · 역대 졸업작품 · 포트폴리오')
create('og-employment.png','ALUMNI CAREERS',['배운 기술이 이어지는','졸업생의 회사와 직무'],'공개 취업 사례 · 소프트웨어 · 데이터 · 클라우드')
