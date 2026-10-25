#!/usr/bin/env python3
"""Replace three tiny Naver thumbnails with large-res source copies."""
import io,json
from pathlib import Path
from urllib.parse import urlparse,urlunparse
import requests
from PIL import Image,ImageOps
import import_kopo_pages_2_5 as site

ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/"data/kopo_photo_audit_6_20.json").read_text(encoding="utf-8"))
items={x["id"]:x for x in data["posts"]}
s=requests.Session()
s.headers.update({"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
   "Referer":"https://blog.naver.com/kangseokopo","Accept":"image/avif,image/webp,image/*,*/*;q=0.8"})
detector=site.get_yunet()
for seq,i in [("545134",1),("545134",2),("545135",2)]:
    source=items[seq]["images"][i-1]
    parsed=urlparse(source)
    assert parsed.netloc=="postfiles.pstatic.net",source
    options=[urlunparse(parsed._replace(netloc="blogfiles.pstatic.net",query="")),
       urlunparse(parsed._replace(query="type=w966")),
       urlunparse(parsed._replace(netloc="blogfiles.pstatic.net",query="type=w1"))]
    recovered=None
    for target in options:
        try:
            r=s.get(target,timeout=(7,18));r.raise_for_status()
            if len(r.content)>18*1024*1024:raise RuntimeError("Original too large")
            im=Image.open(io.BytesIO(r.content))
            im=ImageOps.exif_transpose(im).convert("RGB")
            if im.width<640 or im.height<400:raise RuntimeError(f"Too small: {im.size}")
            recovered=im
            print("HIGH_RES_FOUND",seq,i,im.size,len(r.content),target[:90],flush=True)
            break
        except Exception as e:
            print("IMAGE_VARIANT_FAILED",seq,i,repr(e)[:140],flush=True)
    if recovered is None:raise RuntimeError(f"No usable high-resolution Naver image for {seq}/{i}")
    recovered.thumbnail((1440,1440),Image.Resampling.LANCZOS)
    edited,n=site.enhanced_mosaic(recovered,f"{seq}-{i}",detector)
    dest=ROOT/"assets"/"activities"/"official-board"/f"{seq}-{i}.jpg"
    edited.save(dest,"JPEG",quality=86,optimize=True,progressive=True)
    with Image.open(dest) as verify:
        assert verify.width>=640 and verify.height>=400,(seq,i,verify.size)
    print("HIGH_RES_REPLACED",seq,i,edited.size,"face regions",n,"bytes",dest.stat().st_size,flush=True)
print("ALL_3_HIGH_RES_REPLACED",flush=True)
