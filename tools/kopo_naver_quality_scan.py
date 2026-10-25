import requests,json,io
from urllib.parse import urlparse,urlunparse,parse_qsl,urlencode
from PIL import Image
from pathlib import Path
data=json.loads(Path('data/kopo_photo_audit_6_20.json').read_text(encoding='utf-8'))
u=next(z for z in data['posts'] if z['id']=='545134')['images'][0]
print('SOURCE',u.split('?')[0][:100])
original=urlparse(u)
types=['w1','w2','w3','w4','w580','w640','w773','w966','w1200','r1','origin','original',None]
for domain in ('postfiles.pstatic.net','blogfiles.pstatic.net'):
  for t in types:
    candidate=urlunparse(original._replace(netloc=domain,query=('type='+t if t else '')))
    try:
      response=requests.get(candidate,headers={
       'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36',
       'Referer':'https://blog.naver.com/kangseokopo',
       'Accept':'image/avif,image/webp,image/apng,image/*,*/*;q=0.8'
      },timeout=(4,8))
      if response.status_code==200:
        try:
          im=Image.open(io.BytesIO(response.content))
          print('RESULT',domain,t,'200',im.size,im.format,len(response.content),flush=True)
        except Exception:print('NONIMAGE',domain,t,len(response.content),flush=True)
      else:print('RESULT',domain,t,response.status_code,flush=True)
    except Exception as e:print('ERROR',domain,t,str(e)[:100],flush=True)
