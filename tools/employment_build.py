"""Only public, allowlisted year/company/job fields may enter the SEO snapshot."""
import json
import os
import re
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
API='https://script.google.com/macros/s/AKfycbwMMOwofSybWFy3BYmPi9ol_VQsi_WFfjnEzvnrxUF4ncDZ5TQeS8tcRyOXcgCbgVU4/exec?action=careerPublic'
FIELDS={'graduation_year','company','job'}
def sanitize(rows):
    cleaned=[]; seen=set()
    year=datetime.now(timezone(timedelta(hours=9))).year
    for raw in rows:
        row={k:str(raw.get(k,'')).strip() for k in FIELDS}
        if not re.fullmatch(r'20\d{2}',row['graduation_year']) or int(row['graduation_year'])>year: continue
        if not row['company'] or not row['job']:continue
        if any(len(v)>150 or re.search(r'@|(?:\d[-\s]?){7,}',v) for v in (row['company'],row['job'])): continue
        key=tuple(row[k] for k in sorted(FIELDS))
        if key not in seen:cleaned.append(row);seen.add(key)
    return cleaned
def load_snapshot():
    cache=json.loads((ROOT/'data/employment-public.json').read_text(encoding='utf-8'))
    if os.environ.get('OFFLINE_BUILD'):return {'asOf':cache['asOf'],'rows':sanitize(cache['rows'])}
    try:
        with urlopen(Request(API,headers={'Accept':'application/json','User-Agent':'DepartmentPublicBuild/1.0'}),timeout=25) as response:
            result=json.load(response)
        if not result.get('success'):raise ValueError('Public API failure')
        rows=sanitize(result.get('data',[]))
        if not rows:raise ValueError('No usable public records')
        return {'asOf':datetime.now(timezone(timedelta(hours=9))).date().isoformat(),'rows':rows}
    except Exception as exc:
        print('Employment API unavailable; retaining reviewed public snapshot:',type(exc).__name__)
        return {'asOf':cache['asOf'],'rows':sanitize(cache['rows'])}
def cards(rows,mini=False):
    result=[]
    for r in rows:
        heading='h3' if mini else 'h2'
        result.append(f'<article class="{"employment-mini-card" if mini else "employment-card"}"><span class="employment-year">{escape(r["graduation_year"])}년 졸업</span><{heading}>{escape(r["company"])}</{heading}><p class="employment-role">{escape(r["job"])}</p></article>')
    return ''.join(result)
def inject(output,snapshot):
    rows=snapshot['rows'];page=output/'employment/index.html'
    content=page.read_text(encoding='utf-8')
    content=re.sub(r'(<div id="employment-list" class="employment-grid">).*?(</div>)',lambda m:m[1]+cards(rows)+m[2],content,flags=re.S)
    content=re.sub(r'(<p id="employment-status"[^>]*>).*?(</p>)',lambda m:m[1]+f'공개 취업 사례 {len(rows)}건 · {snapshot["asOf"]} 확인. 접속 후 최신 공개 자료로 갱신합니다.'+m[2],content,flags=re.S)
    safe=json.dumps(rows,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
    content=content.replace('</head>',f'<script id="employment-fallback" type="application/json">{safe}</script>\n</head>')
    page.write_text(content,encoding='utf-8')
    home=output/'index.html';content=home.read_text(encoding='utf-8')
    content=re.sub(r'(<div id="employment-preview-list"[^>]*>).*?(</div>)',lambda m:m[1]+cards(rows[:8],True)+m[2],content,flags=re.S)
    home.write_text(content,encoding='utf-8')
