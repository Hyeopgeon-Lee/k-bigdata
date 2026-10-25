import requests, re, json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
session=requests.Session()
posts=[('766164','해커톤 수상'),('762842','10억 개편'),('749947','학과 개편'),('786372','취업박람회'),('781895','졸업생 초청'),('781894','R 연수'),('781893','LLM 연수'),('781892','바이브코딩'),('780387','동명중'),('777791','KT')]
for seq,label in posts:
 try:
  u=f'https://www.kopo.ac.kr/kangseo/board.do?menu=1550&mode=view&post={seq}'
  r=session.post(u,data={'pageIndex':'1'},timeout=25)
  sp=BeautifulSoup(r.text,'html.parser')
  print('POST',seq,label,'STATUS',r.status_code,'LENGTH',len(r.content),'TITLE',sp.title.get_text(' ',strip=True) if sp.title else '')
  cands=[]
  for elem in sp.find_all(['div','article','table']):
   cls=' '.join(elem.get('class',[]))
   if any(x in cls for x in ('view','detail','content','editor','bbs','board')):
    count=len(elem.get_text(' ',strip=True))
    if 50<count<15000: cands.append((len(elem.find_all('img')),count,cls,elem))
  cands.sort(key=lambda x:(-x[0],-x[1]))
  for _,length,cls,elem in cands[:4]:
   print('CAND',cls,length,'TEXT',elem.get_text(' ',strip=True)[:900],'HTML',str(elem)[:1000])
  images=[{'src':tag.get('src'),'data_src':tag.get('data-src'),'alt':tag.get('alt')} for tag in sp.find_all('img') if tag.find_parent(['article']) or '/upload/' in str(tag) or 'files' in str(tag) or 'board' in str(tag)]
  print('IMAGES',json.dumps(images[-20:],ensure_ascii=False)[:5000])
  print('ATTACH', [(a.get_text(' ',strip=True),a.get('href'),a.get('onclick')) for a in sp.find_all('a') if 'download' in str(a).lower() or '첨부' in str(a)][:15])
 except Exception as e: print('ERROR',seq,str(e))
