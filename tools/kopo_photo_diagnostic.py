import json,re,requests
from bs4 import BeautifulSoup
BOARD="https://www.kopo.ac.kr/kangseo/board.do?menu=1550"
S=requests.Session()
S.headers.update({"User-Agent":"Mozilla/5.0","Referer":BOARD})
posts=["748848","745970","740753","734728","734727","727480","727467","625388","633735","602151","591392","554579","545133"]
for seq in posts:
    r=S.post(f"{BOARD}&mode=view&post={seq}",data={"pageIndex":"7"},timeout=40)
    r.raise_for_status()
    soup=BeautifulSoup(r.text,"html.parser")
    area=soup.select_one("table.tbl_view")
    if not area:print("ERROR",seq,"no article");continue
    print("\n==ARTICLE==",seq,"length",len(str(area)))
    print("IMAGE_TAGS",[(str(x)[:1000]) for x in area.find_all("img")][:18])
    print("ANCHORS",[(a.get_text(" ",strip=True)[:100],a.get("href"),a.get("onclick")) for a in area.select("a")][-24:])
    print("FILES",str(area.select_one(".tbl_view_file"))[:5000])
    body=area.select_one("td.txt_area")
    print("BODY_HTML",str(body)[:2700])
    print("GLOBAL_ATTACH_MENTIONS",[(t.get_text(" ",strip=True)[:100],t.get("href"),t.get("onclick")) for t in soup.select('a[href*="atch"],a[href*="file"],a[onclick*="down"],a[onclick*="Down"]')][-15:])
