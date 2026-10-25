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

jsurl='https://www.kopo.ac.kr/js/kopo/board.js?ver1.4'
j=s.get(jsurl,timeout=30)
print('JS_GET',j.status_code,len(j.content))
for phrase in ('fn_board_detail','board_detail','prdbbsSeq'):
 pos=j.text.find(phrase)
 print('JS_SNIPPET',phrase,pos,repr(j.text[max(0,pos-600):pos+1800]))
print('INLINE_FN',[(x.text[x.text.find('fn_board_detail')-300:x.text.find('fn_board_detail')+1000]) for x in sp.find_all('script') if 'fn_board_detail' in x.text][:5])
