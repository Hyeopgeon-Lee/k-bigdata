#!/usr/bin/env python3
import requests,re
from bs4 import BeautifulSoup
s=requests.Session()
s.headers['User-Agent']='Mozilla/5.0'
url='https://www.kopo.ac.kr/kangseo/board.do?menu=1550'
r=s.get(url,timeout=25);r.raise_for_status()
f=BeautifulSoup(r.text,'html.parser').find('form',{'name':'listfrm'})
assert f
fields={x.get('name'):x.get('value','') for x in f.select('input[name]')}
previous=None
for p in range(20,71):
    rr=s.post(url,data={**fields,'pageIndex':str(p)},timeout=35)
    rr.raise_for_status()
    doc=BeautifulSoup(rr.text,'html.parser')
    rows=[]
    for tr in doc.select('table.tbl_list tbody tr'):
        a=tr.select_one('a[onclick*=fn_board_detail]')
        if not a:continue
        m=re.search(r"fn_board_detail\('([^']+)'\)",a.get('onclick',''))
        if m:rows.append((m.group(1),a.get_text(' ',strip=True),tr.select('td')[-1].get_text(' ',strip=True)))
    ids=tuple(x[0] for x in rows)
    print('PAGE',p,'COUNT',len(rows),'FIRST',rows[0] if rows else None,'LAST',rows[-1] if rows else None,flush=True)
    if not rows or ids==previous or (p>20 and rows[0][2]>'2019-01-01' and p>35):
        print('STOP_PAGE',p,'DUPLICATE' if ids==previous else 'EMPTY_OR_RANGE',flush=True)
        break
    previous=ids
