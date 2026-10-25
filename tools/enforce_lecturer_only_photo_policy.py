#!/usr/bin/env python3
"""Honor the publication rule: reveal lecturer faces only in teaching/lecture photos.

For sensitive learning/career/teacher-training events, retain participant
obscuration. Only manually reviewed speaker rectangles are restored from
authentic source photos; uncertain photos remain anonymized.
Other event photos remain fully restored from their publicly sourced originals.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import re
from html import unescape

ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT/"activities"/"index.html"
OLD="/assets/activities/official-board/"
RAW="/assets/activities/official-original/"
SPEAKER="/assets/activities/speaker-original/"
DEST=ROOT/"assets"/"activities"/"speaker-original"
# Reviewed speaker face bounds (x0,y0,x1,y1) in original photo percentages.
# Never auto-classify attendee faces as lecturers.
SPEAKER_REVIEWED={
    "781895-1":(0.496,0.289,0.551,0.373), # presenter at whiteboard
    "781894-1":(0.666,0.543,0.708,0.620), # presenter by projection
    "781893-1":(0.576,0.485,0.614,0.550), # teacher at classroom front
    "781892-1":(0.798,0.438,0.858,0.523), # teacher in front of slides
    "777791-1":(0.334,0.514,0.385,0.572), # invited KT speaker
}
CARDS=re.compile(r'<article class="activity-card">.*?</article>',re.S)
PHOTO=re.compile(r'/assets/activities/(?:official-original|official-board)/([0-9]+)-([0-9]+)\.jpg')
TARGET=re.compile(r'특강|교원\s*연수|교사\s*연수|연수|진로\s*체험|진로체험|청소년.*체험|고등학생.*실습|직무\s*설명회',re.I)

def speaker_image(image_key):
    old=ROOT/"assets"/"activities"/"official-board"/(image_key+".jpg")
    original=ROOT/"assets"/"activities"/"official-original"/(image_key+".jpg")
    if not old.is_file() or not original.is_file():raise RuntimeError("Missing source for lecturer photo "+image_key)
    with Image.open(old) as im: mosaic=im.convert("RGB")
    with Image.open(original) as im:
        unblurred=im.convert("RGB").resize(mosaic.size,Image.Resampling.LANCZOS)
    w,h=mosaic.size
    x0,y0,x1,y1=SPEAKER_REVIEWED[image_key]
    rect=(int(w*x0),int(h*y0),int(w*x1),int(h*y1))
    mask=Image.new("L",mosaic.size)
    draw=ImageDraw.Draw(mask)
    draw.ellipse(rect,fill=255)
    mask=mask.filter(ImageFilter.GaussianBlur(radius=max(2,int(min(w,h)*.003))))
    out=Image.composite(unblurred,mosaic,mask)
    DEST.mkdir(parents=True,exist_ok=True)
    file=DEST/(image_key+".jpg")
    out.save(file,"JPEG",quality=89,optimize=True,progressive=True)
    return SPEAKER+image_key+".jpg"

def classify_card(html):
    title=html.split("<h3>",1)[1].split("</h3>",1)[0] if "<h3>" in html else ""
    tag=html.split('class="activity-card-meta"',1)[1].split("</span>",1)[0] if 'class="activity-card-meta"' in html else ""
    return bool(TARGET.search(unescape(re.sub(r"<[^>]*>"," ",title+" "+tag))))

def run():
    original=ARCHIVE.read_text(encoding="utf-8")
    target_map={}
    for card in CARDS.findall(original):
        route=re.search(r'href="(/activities/[^"]+/)"',card)
        if not route:raise RuntimeError("Archive card lacks detail URL")
        if not classify_card(card):continue
        slug=route.group(1).strip("/").split("/")[-1]
        target_map[slug]=True
    revised={}
    restored_speakers=set()
    for slug in target_map:
        file=ROOT/"activities"/slug/"index.html"
        if not file.exists():raise RuntimeError("Missing protected article: "+slug)
        raw=file.read_text(encoding="utf-8")
        def route_photo(m):
            seq,index=m.group(1),m.group(2)
            key=seq+"-"+index
            if key in SPEAKER_REVIEWED:
                if key not in restored_speakers:speaker_image(key)
                restored_speakers.add(key)
                return SPEAKER+key+".jpg"
            return OLD+key+".jpg"
        newer=PHOTO.sub(route_photo,raw)
        file.write_text(newer,encoding="utf-8")
        revised[slug]=True
    def fix_card(m):
        card=m.group(0)
        route=re.search(r'href="(/activities/[^"]+/)"',card)
        slug=route.group(1).strip("/").split("/")[-1] if route else None
        if slug not in revised:return card
        return PHOTO.sub(lambda n:(SPEAKER if n.group(1)+"-"+n.group(2) in restored_speakers else OLD)+n.group(1)+"-"+n.group(2)+".jpg",card)
    rebuilt=CARDS.sub(fix_card,original)
    ARCHIVE.write_text(rebuilt,encoding="utf-8")
    # Always keep the two user-uploaded 2026 photos protected until we can
    # replace them from the original files.
    assert rebuilt.count('class="activity-card"')==321
    for slug in revised:
        text=(ROOT/"activities"/slug/"index.html").read_text(encoding="utf-8")
        assert not re.search(r'/assets/activities/official-original/\d+-\d+\.jpg',text),slug
    print("PROTECTED_EVENT_POSTS",len(revised),"REVIEWED_SPEAKER_PHOTOS",len(restored_speakers),flush=True)

if __name__=="__main__":
    run()
