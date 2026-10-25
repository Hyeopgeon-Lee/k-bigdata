#!/usr/bin/env python3
"""Repair missed in-body /ckimage/ photos from official KOPO pages 6 through 20.

Preserves all original article prose, URLs and the 201 archive cards.
Every downloaded source photo is hosted locally and processed with OpenCV Haar + YuNet
before it appears in the public site. Images are not hotlinked from the source.
"""
from __future__ import annotations
import argparse, io, json, re, html
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from PIL import Image, ImageOps
import import_kopo_pages_2_5 as site

ROOT=Path(__file__).resolve().parents[1]
BOARD=site.BOARD
BASE=site.BASE
INVENTORY=ROOT/"data"/"kopo_official_pages_6_20.json"
AUDIT=ROOT/"data"/"kopo_photo_audit_6_20.json"
IMAGE_ROOT=ROOT/"assets"/"activities"/"official-board"

def session():
    s=requests.Session()
    s.headers.update({"User-Agent":"Mozilla/5.0 (compatible; academic department photo preservation)","Referer":BOARD})
    retry=Retry(total=4,backoff_factor=.6,status_forcelist=(429,500,502,503,504),allowed_methods=frozenset(("GET","POST")))
    s.mount("https://",HTTPAdapter(max_retries=retry,pool_connections=12,pool_maxsize=12))
    return s

def archive_entries():
    data=json.loads(INVENTORY.read_text(encoding="utf-8"))
    assert len(data)==150 and len({p["id"] for p in data})==150
    return data

def official_photos(table):
    candidates=[]
    extra=[]
    for img in table.select("img"):
        src=img.get("data-src") or img.get("src") or img.get("data-original")
        if not src:continue
        url=urljoin(BASE,src.strip())
        addr=urlparse(url)
        if addr.scheme=="https" and addr.netloc.lower() in ("www.kopo.ac.kr","kopo.ac.kr") and (
           addr.path.startswith("/ckimage/") or addr.path=="/cmm/fms/kopoImg.do" or
           addr.path.startswith("/upload/") or addr.path.startswith("/cmm/fms/")):
            if url not in candidates:candidates.append(url)
        elif url not in extra:
            extra.append(url)
    # File attachments display as kopoImg.do image elements on the official site.
    return candidates,extra

def audit_sources():
    s=session()
    arr=[]
    pages=archive_entries()
    for i,entry in enumerate(pages):
        seq=entry["id"]
        r=s.post(f"{BOARD}&mode=view&post={seq}",data={"pageIndex":str(entry["page"])},timeout=55)
        r.raise_for_status()
        doc=BeautifulSoup(r.text,"html.parser")
        article=doc.select_one("table.tbl_view")
        if article is None:raise RuntimeError(f"Missing official detail {seq}")
        images,external=official_photos(article)
        arr.append({**entry,"images":images,"unhandled":external})
        print("FOUND",entry["page"],seq,"images",len(images),"extra",len(external),flush=True)
        for u in external:print("UNHANDLED_URL",seq,u[:180],flush=True)
    counts={str(n):{"posts":len([p for p in arr if p["page"]==n]),"images":sum(len(p["images"]) for p in arr if p["page"]==n)} for n in range(6,21)}
    total=sum(len(x["images"]) for x in arr)
    unsupported=sum(len(x["unhandled"]) for x in arr)
    AUDIT.write_text(json.dumps({"posts":arr,"counts":counts,"total_images":total,"unhandled_images":unsupported},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if total<=15:raise RuntimeError("Photo audit found no missed photos; investigate source HTML")
    print("AUDIT_COMPLETE",len(arr),"articles",total,"images",unsupported,"unhandled",flush=True)
    print("PAGE_COUNTS",json.dumps(counts,ensure_ascii=False),flush=True)
    # Unhandled external images are not silently considered successfully copied.
    if unsupported:
        raise RuntimeError(f"{unsupported} images use unsupported URLs; add an explicit vetted source handling strategy")

def verify_photo_bytes(s,url,seq,i):
    r=s.get(url,timeout=70)
    r.raise_for_status()
    if len(r.content)>60*1024*1024:raise RuntimeError(f"Oversized photo {seq}-{i} >60 MiB")
    if len(r.content)<200:raise RuntimeError(f"Empty image response {seq}-{i} URL={url}")
    try:
        with Image.open(io.BytesIO(r.content)) as raw:
            pic=ImageOps.exif_transpose(raw).convert("RGB")
    except Exception as exc:
        raise RuntimeError(f"Unusable photo {seq}-{i}: {url}, {exc}") from exc
    pic.thumbnail((1440,1440),Image.Resampling.LANCZOS)
    return pic

def gallery(photo_paths,title):
    items=[]
    for i,path in enumerate(photo_paths):
        items.append('<figure class="activity-feature-image official-figure">'
          +f'<img src="{html.escape(path,quote=True)}" alt="{html.escape(title,quote=True)} 활동 사진 {i+1}" loading="lazy">'
          +f'<figcaption>학과 활동 기록 사진 {i+1} · 개인정보 보호를 위한 얼굴 감지 영역 모자이크 적용</figcaption></figure>')
    return '<div class="official-post-gallery">'+"".join(items)+'</div>' if items else ""

def refresh_article(seq,paths):
    file=ROOT/"activities"/f"kopo-{seq}"/"index.html"
    old=file.read_text(encoding="utf-8")
    match=re.search(r'<h1>(.*?)</h1>',old,re.S)
    if not match:raise RuntimeError(f"Missing article heading for {seq}")
    title=html.unescape(re.sub(r"<.*?>","",match.group(1)))
    marker=r'(<article class="container activity-article">)(?:<div class="official-post-gallery">.*?</div>)?(<div class="activity-content">)'
    new,count=re.subn(marker,lambda m:m.group(1)+gallery(paths,title)+m.group(2),old,count=1,flags=re.S)
    if count!=1:raise RuntimeError(f"Could not safely replace gallery in post {seq}")
    if paths:
        cover=site.SITE+paths[0]
        for attr in ('<meta property="og:image" content="','<meta name="twitter:image" content="'):
            pattern='('+re.escape(attr)+r')[^"]+(")'
            new,n=re.subn(pattern,lambda m:m.group(1)+cover+m.group(2),new,count=1)
            if n!=1:raise RuntimeError(f"Missing social image metadata {seq}/{attr}")
        def change_schema(m):
            obj=json.loads(m.group(1))
            if obj.get("@type")=="Article":obj["image"]=cover
            return '<script type="application/ld+json">'+json.dumps(obj,ensure_ascii=False,separators=(",",":"))+'</script>'
        new,n=re.subn(r'<script type="application/ld\+json">(.*?)</script>',change_schema,new,flags=re.S)
        if n!=1:raise RuntimeError(f"Missing article JSON-LD {seq}")
    file.write_text(new,encoding="utf-8")

def refresh_archive(cards):
    file=ROOT/"activities"/"index.html"
    old=file.read_text(encoding="utf-8")
    used=set()
    def fix(m):
        block=m.group(0)
        seqmatch=re.search(r'/activities/kopo-(\d+)/',block)
        if not seqmatch:return block
        seq=seqmatch.group(1)
        if seq not in cards:return block
        path=cards[seq]
        pattern=r'(<a class="activity-image-link"[^>]*>).*?(</a>)'
        def swap(a):
            return a.group(1)+f'<img src="{html.escape(path,quote=True)}" alt="학과 활동 사진(얼굴 감지 영역 모자이크 처리)" loading="lazy">'+a.group(2)
        block,n=re.subn(pattern,swap,block,count=1,flags=re.S)
        if n!=1:raise RuntimeError(f"Missing archive cover for {seq}")
        used.add(seq)
        return block
    new=re.sub(r'<article class="activity-card">.*?</article>',fix,old,flags=re.S)
    if used!=set(cards):raise RuntimeError(f"Archive update missing covers: {sorted(set(cards)-used)}")
    file.write_text(new,encoding="utf-8")

def repair(start,end):
    data=json.loads(AUDIT.read_text(encoding="utf-8"))
    arr=[p for p in data["posts"] if start<=p["page"]<=end]
    assert len(arr)==(end-start+1)*10
    s=session()
    detector=site.get_yunet()
    covers={}
    updated=0
    count=0
    for entry in arr:
        seq=entry["id"]
        urls=entry["images"]
        paths=[]
        for i,url in enumerate(urls,1):
            file=IMAGE_ROOT/f"{seq}-{i}.jpg"
            # Previously published attachments used the same stable path; preserve
            # their already anonymized versions rather than overwriting with originals.
            if not file.is_file():
                pic=verify_photo_bytes(s,url,seq,i)
                edited,faces=site.enhanced_mosaic(pic,f"{seq}-{i}",detector)
                IMAGE_ROOT.mkdir(parents=True,exist_ok=True)
                edited.save(file,"JPEG",quality=85,optimize=True,progressive=True)
                updated+=1
                print("DOWNLOADED",entry["page"],seq,i,"faces",faces,"bytes",file.stat().st_size,flush=True)
            else:
                print("REUSED",entry["page"],seq,i,flush=True)
            paths.append("/"+file.relative_to(ROOT).as_posix())
            count+=1
        # Replace previous incomplete gallery even for posts with 0 source photos.
        refresh_article(seq,paths)
        if paths:covers[seq]=paths[0]
        print("REPAIRED",entry["page"],seq,"images",len(paths),flush=True)
    refresh_archive(covers)
    print("BATCH_COMPLETE",start,end,"images_referenced",count,"new_photos",updated,"covers",len(covers),flush=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--audit",action="store_true")
    parser.add_argument("--start",type=int)
    parser.add_argument("--end",type=int)
    args=parser.parse_args()
    if args.audit:audit_sources()
    else:
        if args.start not in (6,11,16) or args.end!=args.start+4:parser.error("Batch must be 6–10, 11–15, or 16–20")
        repair(args.start,args.end)
