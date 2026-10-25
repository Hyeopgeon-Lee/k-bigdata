#!/usr/bin/env python3
"""Complete KOPO photo repair for pages 16–20, with Naver image fallback."""
from urllib.parse import urlparse
from io import BytesIO
import requests
from PIL import Image,ImageOps
import repair_kopo_photos as repair

original=repair.verify_photo_bytes

def with_naver_fallback(session,url,seq,index):
    try:
        return original(session,url,seq,index)
    except Exception as initial:
        if urlparse(url).netloc!="postfiles.pstatic.net":raise
        substitutions=[
            url.replace("postfiles.pstatic.net","blogfiles.pstatic.net"),
            url.split("?")[0],
            url.replace("type=w773","type=w966"),
            url.replace("type=w773","type=w1"),
            url.replace("postfiles.pstatic.net","blogfiles.pstatic.net").split("?")[0],
        ]
        attempted=set()
        for attempt in substitutions:
            if attempt in attempted:continue
            attempted.add(attempt)
            try:
                response=requests.get(attempt,headers={
                    "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    "Referer":"https://blog.naver.com/kangseokopo",
                    "Accept":"image/avif,image/webp,image/apng,image/*,*/*;q=0.8"
                },timeout=(6,12))
                response.raise_for_status()
                if len(response.content)>60*1024*1024:continue
                with Image.open(BytesIO(response.content)) as raw:
                    im=ImageOps.exif_transpose(raw).convert("RGB")
                im.thumbnail((1440,1440),Image.Resampling.LANCZOS)
                print("RECOVERED_NAVER_IMAGE",seq,index,attempt[:150],flush=True)
                return im
            except Exception as exc:
                print("NAVER_ALTERNATIVE_UNAVAILABLE",seq,index,str(exc)[:140],flush=True)
        raise initial

repair.verify_photo_bytes=with_naver_fallback
repair.repair(16,20)
