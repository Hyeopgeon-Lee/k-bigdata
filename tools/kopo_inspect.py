import requests
from bs4 import BeautifulSoup
import json
url='https://www.kopo.ac.kr/kangseo/board.do?menu=1550'
s=requests.Session()
r=s.get(url,timeout=30)
print('GET',r.status_code,'len',len(r.content),'final',r.url)
print('TITLE',BeautifulSoup(r.text,'html.parser').title)
sp=BeautifulSoup(r.text,'html.parser')
for a in sp.find_all('a'):
 t=a.get_text(' ',strip=True)
 if any(q in t for q in ['새싹 해커톤','학과 개편','강서구 취업박람회','부산대학교 대학원','빅데이터 분석과 R 활용','인공지능·LLM','바이브코딩','동명중학교','KT 현직자']):
  print('POST_ANCHOR',json.dumps({'title':t,'href':a.get('href'),'onclick':a.get('onclick'),'parent':str(a.parent)[:1000]},ensure_ascii=False))
for x in sp.find_all('form'):
 if any(key in str(x) for key in ('board','bbs','list')):
  print('FORM',str(x)[:2000])
print('SCRIPTS',[(x.get('src'),x.text[:800] if x.text and ('fn_view' in x.text or 'goView' in x.text) else '') for x in sp.find_all('script')][-18:])
