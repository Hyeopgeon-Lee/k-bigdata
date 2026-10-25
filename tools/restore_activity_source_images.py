#!/usr/bin/env python3
"""Restore authentic public-source photos, never synthesize blurred faces."""
import argparse,io,json,re
from pathlib import Path
from urllib.parse import urlparse,urlunparse,urljoin
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from PIL import Image,ImageOps
import import_kopo_pages_2_5 as first
import repair_kopo_photos as repair

ROOT=Path(__file__).resolve().parents[1]
BOARD=first.BOARD
RAW=ROOT/"assets"/"activities"/"official-original"
OLD="/assets/activities/official-board/"
NEW="/assets/activities/official-original/"
SPECIAL={"766164":"sesac-hackathon-grand-prize-2025","762842":"department-funding-2025","749947":"department-reorganization-2025","781895":"alumni-ha-jae-hyeong-lecture-2026","781894":"teacher-generative-ai-r-training-2026","781893":"teacher-ai-llm-workshop-2026","781892":"public-vibe-coding-class-2026","780387":"dongmyeong-school-vibe-coding-2026","777791":"kt-researcher-career-lecture-2026"}
MID=json.loads((ROOT/"data"/"kopo_photo_audit_6_20.json").read_text())["posts"]
LATE={x["id"]:x for x in json.loads((ROOT/"data"/"kopo_photo_audit_21_32.json").read_text())["records"]}
LATE_LIST=json.loads((ROOT/"data"/"kopo_official_pages_21_32.json").read_text())
REF=re.compile(r"/assets/activities/official-board/([0-9]+)-([0-9]+)\.jpg")
FIG=re.compile(r"<figcaption[^>]*>.*?</figcaption>",re.S)
IMGTAG=re.compile(r"<img\b[^>]*>",re.S)

def request_session():
    s=requests.Session()
    s.headers.update({"User-Agent":"Mozilla/5.0 (compatible; KOPO activity archive)","Referer":BOARD})
    policy=Retry(total=3,backoff_factor=.4,status_forcelist=[429,500,502,503,504],allowed_methods=frozenset(["GET","POST"]))
    s.mount("https://",HTTPAdapter(max_retries=policy))
    s.mount("http://",HTTPAdapter(max_retries=policy))
    return s

def article(seq):
    return ROOT/"activities"/SPECIAL.get(seq,"kopo-"+seq)/"index.html"

def photos_in_gallery(html,seq):
    if '<article class="container activity-article">' not in html:
        raise RuntimeError(f"Activity article structure changed: {seq}")
    gallery=html.split('<article class="container activity-article">',1)[1].split('<div class="activity-content">',1)[0]
    ids=[]
    for x in REF.finditer(gallery):
        if x.group(1)!=seq:raise RuntimeError(f"Wrong image in {seq}")
        v=int(x.group(2))
        if v not in ids:ids.append(v)
    if ids!=list(range(1,len(ids)+1)):
        raise RuntimeError(f"Image indices changed in {seq}: {ids}")
    return ids

def live_board_images(s,seq,page,only_files=False):
    r=s.post(f"{BOARD}&mode=view&post={seq}",data={"pageIndex":str(page)},timeout=(10,45))
    r.raise_for_status()
    table=BeautifulSoup(r.text,"html.parser").select_one("table.tbl_view")
    if table is None:raise RuntimeError(f"No source article: {seq}")
    if only_files:
        urls=[]
        for img in table.select('img[src*="kopoImg.do"]'):
            u=urljoin(first.BASE,img["src"])
            if u not in urls:urls.append(u)
        return urls
    urls,ignored=repair.official_photos(table)
    return urls

def sources(s,seq,kind,page):
    if kind=="early":return live_board_images(s,seq,page,True)
    if kind=="mid":return next(x["images"] for x in MID if x["id"]==seq)
    if kind=="late":
        urls=live_board_images(s,seq,page)
        failed=set(LATE[seq]["failed"])
        urls=[u for u in urls if u not in failed]
        if len(urls)!=LATE[seq]["downloaded"]:
            raise RuntimeError(f"Late source count mismatch {seq}: {len(urls)}")
        return urls

def download_original(s,url,seq,num):
    p=urlparse(url)
    options=[url]
    if p.netloc in ("postfiles.pstatic.net","blogfiles.pstatic.net"):
        options=[urlunparse(p._replace(netloc="blogfiles.pstatic.net",query="")),
                 urlunparse(p._replace(query="type=w966")),
                 urlunparse(p._replace(query="type=w1")),url]
    errors=[]
    for candidate in dict.fromkeys(options):
        try:
            headers={"Referer":"https://blog.naver.com/"} if "pstatic.net" in candidate else {}
            r=s.get(candidate,timeout=(10,40),headers=headers)
            r.raise_for_status()
            if not 250<len(r.content)<40*1024*1024:raise RuntimeError("Invalid image size")
            with Image.open(io.BytesIO(r.content)) as src:
                photo=ImageOps.exif_transpose(src).convert("RGB")
            if min(photo.size)<90:raise RuntimeError("Tiny preview")
            photo.thumbnail((1440,1440),Image.Resampling.LANCZOS)
            return photo
        except Exception as e:errors.append(str(e)[:100])
    raise RuntimeError(f"Unable to restore source photo {seq}-{num}: {errors[:2]}")

def write_photo(s,seq,index,url):
    output=RAW/f"{seq}-{index}.jpg"
    if output.is_file():
        with Image.open(output) as previous:
            if min(previous.size)>=90:return
    im=download_original(s,url,seq,index)
    output.parent.mkdir(parents=True,exist_ok=True)
    im.save(output,"JPEG",quality=86,optimize=True,progressive=True)
    if output.stat().st_size<1000:raise RuntimeError(f"Corrupted saved file: {output}")
    print("ORIGINAL_IMAGE",seq,index,im.size,output.stat().st_size,flush=True)

def captions(s):
    def fix_fig(m):
        return '<figcaption>학과 활동 현장 사진</figcaption>' if "모자이크" in m.group(0) else m.group(0)
    s=FIG.sub(fix_fig,s)
    def fix_img(m):
        tag=m.group(0)
        if "모자이크" in tag and NEW in tag:
            tag=re.sub(r'(\balt=")[^"]*(")',r"\1학과 활동 현장 사진\2",tag)
        return tag
    return IMGTAG.sub(fix_img,s)

def update_post(seq):
    path=article(seq)
    old=path.read_text(encoding="utf-8")
    new=REF.sub(lambda m:NEW+seq+"-"+m.group(2)+".jpg" if m.group(1)==seq else m.group(0),old)
    new=captions(new)
    # No modifications to human identities or editorial content.
    if new==old or REF.search(new):raise RuntimeError(f"Failed URL switch {seq}")
    path.write_text(new,encoding="utf-8")

def update_archive(ids):
    path=ROOT/"activities"/"index.html"
    old=path.read_text(encoding="utf-8")
    def mapcard(m):
        s=m.group(0)
        for seq in ids:
            if f"/activities/{SPECIAL.get(seq,'kopo-'+seq)}/" in s:
                s=s.replace(OLD+seq+"-",NEW+seq+"-")
                s=captions(s)
                break
        return s
    new=re.sub(r'<article class="activity-card">.*?</article>',mapcard,old,flags=re.S)
    path.write_text(new,encoding="utf-8")

def early_sources(s):
    first_pages={seq:1 for seq in SPECIAL}
    r=s.get(BOARD,timeout=40);r.raise_for_status()
    frm=BeautifulSoup(r.text,"html.parser").find("form",{"name":"listfrm"})
    if not frm:raise RuntimeError("Source board form missing")
    params={i.get("name"):i.get("value","") for i in frm.select("input[name]")}
    for page in range(2,6):
        page_resp=s.post(BOARD,data={**params,"pageIndex":str(page)},timeout=40);page_resp.raise_for_status()
        soup=BeautifulSoup(page_resp.text,"html.parser")
        for row in soup.select("table.tbl_list tbody tr"):
            link=row.select_one('a[onclick*="fn_board_detail"]')
            if not link:continue
            match=re.search(r"fn_board_detail\('([^']+)'\)",link.get("onclick",""))
            if match:first_pages[match.group(1)]=page
    if len(first_pages)!=49:raise RuntimeError(f"Expected 49 early posts, got {len(first_pages)}")
    return [(seq,"early",page) for seq,page in first_pages.items()]

def batch(s,group):
    if group=="early":return early_sources(s)
    kind,dates=group.split("-",1)
    lo,hi=map(int,dates.split("_"))
    if kind=="mid":return [(x["id"],kind,x["page"]) for x in MID if lo<=x["page"]<=hi]
    if kind=="late":return [(x["id"],kind,x["page"]) for x in LATE_LIST if lo<=x["page"]<=hi]
    raise RuntimeError("Invalid source group")

def main(group):
    s=request_session()
    records=batch(s,group)
    ids=[];total=0
    for idx,(seq,kind,page) in enumerate(records,1):
        path=article(seq)
        if not path.is_file():raise RuntimeError(f"Missing original article HTML: {path}")
        html=path.read_text(encoding="utf-8")
        existing=photos_in_gallery(html,seq)
        if not existing:continue
        candidates=sources(s,seq,kind,page)
        if len(candidates)!=len(existing):
            raise RuntimeError(f"Source/photo mismatch {seq}: {len(candidates)} vs {len(existing)}")
        for n,url in enumerate(candidates,1):write_photo(s,seq,n,url)
        update_post(seq)
        ids.append(seq);total+=len(existing)
        print("RESTORED_ARTICLE",group,idx,len(records),seq,len(existing),flush=True)
    update_archive(ids)
    print("RESTORED_BATCH",group,len(ids),total,flush=True)

if __name__=="__main__":
    arg=argparse.ArgumentParser()
    arg.add_argument("--group",required=True)
    args=arg.parse_args()
    main(args.group)
