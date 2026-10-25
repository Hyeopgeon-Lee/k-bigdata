import requests,re,json
from bs4 import BeautifulSoup
url="https://www.kopo.ac.kr/kangseo/board.do?menu=1550"
s=requests.Session()
r=s.get(url,timeout=30);r.raise_for_status()
soup=BeautifulSoup(r.text,"html.parser")
f=soup.find("form",{"name":"listfrm"})
print("FORM",f.get("action"),[(i.get("name"),i.get("value")) for i in f.select("input")])
fields={i.get("name"):i.get("value","") for i in f.select("input") if i.get("name")}
for page in range(2,6):
 values={**fields,"pageIndex":str(page)}
 rr=s.post(url,data=values,timeout=35);rr.raise_for_status()
 sp=BeautifulSoup(rr.text,"html.parser")
 table=sp.select_one("table.tbl_list")
 print("PAGE",page,"len",len(rr.content),"title",sp.title.get_text(" ",strip=True),"rows",len(table.select("tbody tr")) if table else None)
 for tr in (table.select("tbody tr") if table else []):
  a=tr.select_one("a[onclick*=fn_board_detail]")
  if not a:continue
  seq=re.search(r"fn_board_detail\('([^']+)'\)",a.get("onclick",""))
  print("ITEM",page,seq.group(1) if seq else None,a.get_text(" ",strip=True),[x.get_text(" ",strip=True) for x in tr.find_all("td")][-1])

print("==DETAIL SCAN==",flush=True)
items=[]
for page in range(2,6):
 rr=s.post(url,data={**fields,"pageIndex":str(page)},timeout=45);sp=BeautifulSoup(rr.text,"html.parser")
 for tr in sp.select("table.tbl_list tbody tr"):
  a=tr.select_one("a[onclick*=fn_board_detail]")
  if not a:continue
  m=re.search(r"fn_board_detail\('([^']+)'\)",a.get("onclick",""))
  if m:items.append((page,m.group(1),a.get_text(" ",strip=True)))
for page,seq,title in items:
 rr=s.post(url+"&mode=view&post="+seq,data={"pageIndex":str(page)},timeout=45)
 sp=BeautifulSoup(rr.text,"html.parser")
 body=sp.select_one("td.txt_area")
 imgs=sp.select('table.tbl_view img[src*="kopoImg.do"]')
 bodytxt=body.get_text(" ",strip=True) if body else ""
 print("DETAIL",page,seq,"IMAGES",len(imgs),"CHARS",len(bodytxt),"TITLE",title,"BODY",bodytxt[:1250],flush=True)
