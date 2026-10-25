#!/usr/bin/env python3
"""Import official KOPO department board pages 6–20, in five-page batches.

Reads each post via its POST-based detail view; downloads school-hosted photos,
mosaics detected faces, produces independent article URLs, preserves old items,
and extends the sitemap. Inventory snapshot prevents shifted page boundaries.
"""
from __future__ import annotations
import argparse, io, json, re, time
from pathlib import Path
from urllib.parse import urljoin
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from PIL import Image, ImageOps, UnidentifiedImageError
import import_kopo_pages_2_5 as site

ROOT=Path(__file__).resolve().parents[1]
BOARD=site.BOARD
BASE=site.BASE
SNAPSHOT=ROOT/"data"/"kopo_official_pages_6_20.json"
FIRST_PAGE=6
LAST_PAGE=20

def new_session():
    s=requests.Session()
    s.headers.update({"User-Agent":"Mozilla/5.0 (compatible; KOPO department archive/1.0)", "Referer":BOARD})
    retry=Retry(total=4,backoff_factor=0.5,status_forcelist=[429,500,502,503,504],allowed_methods=frozenset(["GET","POST"]))
    s.mount("https://",HTTPAdapter(max_retries=retry,pool_connections=8,pool_maxsize=8))
    return s

def listing(s):
    r=s.get(BOARD,timeout=30);r.raise_for_status()
    soup=BeautifulSoup(r.text,"html.parser")
    form=soup.find("form",{"name":"listfrm"})
    if form is None:raise RuntimeError("Official board listing form unavailable")
    base={x.get("name"):x.get("value","") for x in form.select("input[name]")}
    entries=[]
    for page in range(FIRST_PAGE,LAST_PAGE+1):
        response=s.post(BOARD,data={**base,"pageIndex":str(page)},timeout=50)
        response.raise_for_status()
        doc=BeautifulSoup(response.text,"html.parser")
        table=doc.select_one("table.tbl_list")
        if table is None:raise RuntimeError(f"Official list missing on page {page}")
        page_entries=[]
        for row in table.select("tbody tr"):
            a=row.select_one("a[onclick*=fn_board_detail]")
            if a is None:continue
            match=re.search(r"fn_board_detail\('([^']+)'\)",a.get("onclick",""))
            if match is None:continue
            seq=match.group(1)
            if not re.fullmatch(r"[0-9]+",seq):raise RuntimeError("Unexpected post identifier")
            cells=row.select("td")
            dt=cells[-1].get_text(" ",strip=True) if cells else ""
            if not re.fullmatch(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}",dt):
                raise RuntimeError(f"Bad official date: {page}/{seq}={dt}")
            page_entries.append(dict(page=page,id=seq,title=a.get_text(" ",strip=True),date=dt))
        if len(page_entries)!=10:
            raise RuntimeError(f"Page {page} has {len(page_entries)} posts rather than 10; refusing incomplete migration")
        entries+=page_entries
        print("LIST_PAGE",page,"posts",len(page_entries),"first",page_entries[0]["id"],"last",page_entries[-1]["id"],flush=True)
    if len(entries)!=150 or len({x["id"] for x in entries})!=150:
        raise RuntimeError("Unexpected duplicate/missing article IDs on pages 6–20")
    SNAPSHOT.parent.mkdir(exist_ok=True,parents=True)
    SNAPSHOT.write_text(json.dumps(entries,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("OFFICIAL_SNAPSHOT",len(entries),"items",flush=True)

def source_text(article):
    content=article.select_one("td.txt_area")
    if content is None:raise RuntimeError("Missing source body")
    for useless in content.select("script,style,noscript"):useless.decompose()
    return content.get_text(" ",strip=True)

def formatted_article(entry,body):
    title=site.normalized_title(entry["title"])
    # Distinguish recurring notices which have the same original title.
    all_entries=json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    duplicates=[e for e in all_entries if site.normalized_title(e["title"])==title]
    if len(duplicates)>1:
        dated=[e for e in duplicates if e["date"]==entry["date"]]
        title+=f" ({entry['date']} 게시)"
        if len(dated)>1:title+=f" · {entry['id']}"
    # Summarized article sections taken strictly from the official detailed text.
    clean=site.cleaned(body)
    if len(clean)<30: raise RuntimeError(f"Very short official text for {entry['id']}")
    try:a,b=site.chunks(clean)
    except ValueError:
        midpoint=max(1,len(clean)//2)
        a,b=clean[:midpoint],clean[midpoint:]
    # Extract a source-grounded lead, stripping calls to action and hashtags.
    first=re.split(r"(?<=[.!?。])\s+",clean,1)[0].strip()
    if 28<=len(first)<=190 and not first.startswith(("안녕하세요","감사")):
        lead=first
    else:
        lead=f"{title} 활동의 현장과 주요 내용을 소개합니다."
    archive_kind=("모집" in title or "수시" in title or "입시" in title or "설명회" in title)
    if archive_kind and entry["date"]<"2026-01-01":
        lead+=" 과거 학과 게시물로, 현재 입학 일정과 다를 수 있습니다."
    return dict(id=entry["id"],slug="kopo-"+entry["id"],title=title,
        tag="과거 입시 기록" if archive_kind else site.tag_for(title),
        lead=lead,date=entry["date"],sections=[("활동 내용",a[:560]),("주요 성과와 경험",b[:560])])

def attachment_urls(article):
    urls=[]
    for tag in article.select('img[src*="kopoImg.do"]'):
        src=urljoin(BASE,tag["src"])
        if src.startswith(BASE+"/cmm/fms/kopoImg.do") and src not in urls:urls.append(src)
    # Some source posts include JPEG/PNG attachments not embedded in their HTML.
    for link in article.select("td.tbl_view_file a.flie_link"):
        filename=link.get_text(" ",strip=True)
        if not re.search(r"\.(?:png|jpe?g|webp|gif)\b",filename,re.I):continue
        match=re.search(r"openAtch\('([0-9]+)'\)",link.get("onclick",""))
        if not match:continue
        key=match.group(1)
        hidden_id=article.select_one("#hhi"+key)
        hidden_sn=article.select_one("#hhs"+key)
        if not hidden_id or not hidden_sn:continue
        src=f'{BASE}/cmm/fms/kopoImg.do?atchFileId={hidden_id.get("value","")}&fileSn={hidden_sn.get("value","")}'
        if src not in urls:urls.append(src)
    return urls

def photos_for(session,table,seq,detector):
    imgs=[]
    urls=attachment_urls(table)
    for i,url in enumerate(urls):
        rsp=session.get(url,timeout=90)
        rsp.raise_for_status()
        if len(rsp.content)>22*1024*1024:
            raise RuntimeError(f"Unexpectedly large image {seq}-{i+1}")
        try:
            pic=Image.open(io.BytesIO(rsp.content))
            pic=ImageOps.exif_transpose(pic).convert("RGB")
        except (UnidentifiedImageError,OSError) as ex:
            raise RuntimeError(f"Invalid source image {seq}-{i+1}") from ex
        pic.thumbnail((1280,1280),Image.Resampling.LANCZOS)
        # Uses both OpenCV Haar and YuNet detectors, same as prior imports.
        edited,nfaces=site.enhanced_mosaic(pic,seq+"-"+str(i+1),detector)
        dest=ROOT/"assets"/"activities"/"official-board"/f"{seq}-{i+1}.jpg"
        dest.parent.mkdir(parents=True,exist_ok=True)
        edited.save(dest,"JPEG",quality=82,progressive=True,optimize=True)
        imgs.append("/"+dest.relative_to(ROOT).as_posix())
        print("PHOTO",seq,i+1,"detections",nfaces,"bytes",dest.stat().st_size,flush=True)
    return imgs

def insert_archive(imported,page_start,page_end):
    path=ROOT/"activities"/"index.html"
    html=path.read_text(encoding="utf-8")
    start=f"<!-- KOPO_PAGES_{page_start}_{page_end}_START -->"
    end=f"<!-- KOPO_PAGES_{page_start}_{page_end}_END -->"
    block=start+"\n"+"\n".join(site.card(p,images) for p,images in imported)+"\n"+end
    if start in html and end in html:
        html=re.sub(re.escape(start)+r".*?"+re.escape(end),lambda _:block,html,flags=re.S)
    else:
        # Insert at end of card grid, after previous batches (not in a nested wrapper).
        anchor='</div></div></section>\n</main>'
        if html.count(anchor)!=1:raise RuntimeError("Activity grid close marker missing or ambiguous")
        html=html.replace(anchor,block+"\n"+anchor,1)
    def rewrite_schema(m):
        schema=json.loads(m.group(1))
        if schema.get("@type")!="CollectionPage":return m.group(0)
        arr=schema["mainEntity"]["itemListElement"]
        known={x["url"] for x in arr}
        for p,_ in imported:
            url=f"{site.SITE}/activities/{p['slug']}/"
            if url not in known:
                arr.append({"@type":"ListItem","position":len(arr)+1,"name":p["title"],"url":url})
                known.add(url)
        return '<script type="application/ld+json">'+json.dumps(schema,ensure_ascii=False,separators=(",",":"))+"</script>"
    html=re.sub(r'<script type="application/ld\+json">(.*?)</script>',rewrite_schema,html,flags=re.S)
    path.write_text(html,encoding="utf-8")

def insert_sitemap(imported):
    builder=ROOT/"tools"/"build_site.py"
    old=builder.read_text(encoding="utf-8")
    marker='    ("activities/social-data-career-trends/", "activities/social-data-career-trends/index.html"),'
    if marker not in old:raise RuntimeError("SEO site-builder anchor missing")
    additions=""
    for p,_ in imported:
        slug=p["slug"]
        entry=f'    ("activities/{slug}/", "activities/{slug}/index.html"),'
        if entry not in old:additions+=entry+"\n"
    builder.write_text(old.replace(marker,additions+marker,1),encoding="utf-8")

def process(start,end):
    if not SNAPSHOT.exists():raise RuntimeError("Missing inventory; scan first")
    entries=json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    matches=[e for e in entries if start<=e["page"]<=end]
    if len(matches)!=(end-start+1)*10:raise RuntimeError("Inventory does not contain 10 entries per page")
    known=set()
    for path in (ROOT/"activities").glob("kopo-*/index.html"):
        known.add(path.parent.name)
    targets=[]
    for e in matches:
        slug="kopo-"+e["id"]
        if slug in known:print("EXISTING",e["id"],flush=True);continue
        targets.append(e)
    session=new_session()
    detector=site.get_yunet()
    imported=[]
    count=0
    for entry in targets:
        seq=entry["id"]
        resp=session.post(f"{BOARD}&mode=view&post={seq}",data={"pageIndex":str(entry["page"])},timeout=70)
        resp.raise_for_status()
        doc=BeautifulSoup(resp.text,"html.parser")
        article=doc.select_one("table.tbl_view")
        if article is None:raise RuntimeError(f"Source detail unavailable: {seq}")
        header=article.select_one(".tbl_view_tit")
        if not header or not header.get_text(" ",strip=True):raise RuntimeError(f"No official heading for {seq}")
        body=source_text(article)
        obj=formatted_article(entry,body)
        photos=photos_for(session,article,seq,detector)
        dest=ROOT/"activities"/obj["slug"]/"index.html"
        dest.parent.mkdir(parents=True,exist_ok=True)
        rendered=site.post_html(obj,photos)
        # SEO requires distinct descriptions even for same-topic historical notices.
        old_meta='<meta name="description" content="'+site.h(obj["lead"])+'">'
        new_meta='<meta name="description" content="'+site.h(obj["lead"]+" | 원문 게시번호 "+seq)+'">'
        if old_meta not in rendered:raise RuntimeError("SEO description missing for "+seq)
        rendered=rendered.replace(old_meta,new_meta,1)
        dest.write_text(rendered,encoding="utf-8")
        imported.append((obj,photos));count+=len(photos)
        print("IMPORTED",entry["page"],seq,"photos",len(photos),"chars",len(body),"title",obj["title"],flush=True)
    if imported:
        insert_archive(imported,start,end)
        insert_sitemap(imported)
    print("BATCH_COMPLETED",start,end,"new",len(imported),"photos",count,flush=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--scan",action="store_true")
    parser.add_argument("--start",type=int)
    parser.add_argument("--end",type=int)
    args=parser.parse_args()
    if args.scan:
        listing(new_session())
    else:
        if args.start not in (6,11,16) or args.end!=args.start+4:
            parser.error("Only complete fixed batches 6-10, 11-15, 16-20 are supported")
        process(args.start,args.end)
