"""Notify IndexNow with URLs from the deployed sitemap, never a second divergent build."""
import json
import time
import xml.etree.ElementTree as ET
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
HOST='ai.k-bigdata.kr'
KEY='3d3a35e839ee4f35b33dcc45ad0450cd'
def request(request, attempts=6):
    for attempt in range(attempts):
        try:
            with urlopen(request,timeout=25) as response:
                status=response.status;body=response.read()
                if status not in (200,202):raise ValueError(f'Unexpected HTTP {status}')
                return status,body
        except HTTPError as exc:
            if exc.code!=429 and not 500<=exc.code<=599:raise
        except (URLError,TimeoutError):pass
        if attempt+1<attempts:time.sleep(min(10*(attempt+1),40))
    raise RuntimeError('HTTP retries exhausted')
def urls_from_sitemap(body):
    urls=[x.text for x in ET.fromstring(body).findall('{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
    if not urls or len(urls)!=len(set(urls)):raise ValueError('Missing/empty/duplicate sitemap URLs')
    if any(not u.startswith(f'https://{HOST}/') for u in urls):raise ValueError('Unexpected sitemap hostname')
    return urls
def main():
    _,key=request(f'https://{HOST}/{KEY}.txt')
    if key.decode().strip()!=KEY:raise ValueError('IndexNow key verification failed')
    for attempt in range(6):
        _,body=request(f'https://{HOST}/sitemap.xml')
        urls=urls_from_sitemap(body)
        if f'https://{HOST}/admission/2027/' in urls:break
        if attempt==5:raise ValueError('Deployed admission URL missing')
        time.sleep(10)
    payload={'host':HOST,'key':KEY,'keyLocation':f'https://{HOST}/{KEY}.txt','urlList':urls}
    status,_=request(Request('https://api.indexnow.org/indexnow',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json; charset=utf-8'}))
    print(f'IndexNow accepted {len(urls)} deployed URLs with HTTP {status}')
if __name__=='__main__':main()
