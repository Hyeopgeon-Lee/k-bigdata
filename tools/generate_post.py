#!/usr/bin/env python3
"""Publish a researched insight with --input draft.json; --check only validates.
Never fabricate prose from headline keywords. See tools/INSIGHT_EDITORIAL.md.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
import json
import os
from pathlib import Path
import re
from urllib.parse import urlparse
ROOT = Path(__file__).resolve().parents[1]
POSTS_FILE = ROOT / 'data/posts.json'
KST = timezone(timedelta(hours=9))
BANNED = ('자동 발행 안내', '학과 홍보용', '기사에 없는 내용을 추측하지 않고', '제목으로 확인되는 기술 흐름', '공개된 기사 제목과 출처를 바탕으로 자동 구성')
def body_text(post):
    pieces = list(post.get('body', []))
    for s in post.get('sections', []):
        pieces += s.get('paragraphs', []) + s.get('bullets', [])
        pieces += [' '.join(row) for row in s.get('table', {}).get('rows', [])]
    return '\n'.join(pieces)
def validate(post, strict=True):
    for key in ('slug','date','title','excerpt','source','sourceUrl','connection','sections'):
        if not post.get(key): raise ValueError(f'Missing {key}')
    if not re.fullmatch(r'[a-z0-9-]+', post['slug']): raise ValueError('Invalid slug')
    datetime.strptime(post['date'], '%Y-%m-%d')
    raw = json.dumps(post, ensure_ascii=False)
    if any(x in raw for x in BANNED): raise ValueError('Disallowed boilerplate in article')
    if not strict: return
    if post.get('editorialVersion') != 2: raise ValueError('Research format version 2 required')
    if len(body_text(post)) < 3000: raise ValueError('Insight needs at least 3,000 characters of substantive content')
    if len(post['sections']) < 6: raise ValueError('At least six explanatory sections required')
    for section in post['sections']:
        if not section.get('heading') or not section.get('paragraphs'): raise ValueError('Empty section')
    refs = post.get('references', [])
    if len({r['url'] for r in refs}) < 2: raise ValueError('At least two distinct source documents required')
    for ref in refs:
        u = urlparse(ref['url'])
        if u.scheme != 'https' or not u.netloc or not ref.get('title'): raise ValueError('Invalid source')
        if u.netloc == 'news.google.com': raise ValueError('Use original sources, not headline aggregators')
    if len(post.get('learningPoints', [])) < 3 or not post.get('projectPrompt'): raise ValueError('Learning checkpoints and concrete exercise required')
    if not any(s.get('table') or s.get('code') for s in post['sections']): raise ValueError('A useful comparison or worked example is required')
def publish(post, posts, today=None):
    validate(post)
    today = today or datetime.now(KST).date().isoformat()
    if post['date'] != today: raise ValueError('New post date must be today in Korea')
    if any(p['slug'] == post['slug'] or p['date'] == today for p in posts): raise ValueError('Already published this slug or a post for today')
    for old in posts:
        if post['title'] == old['title'] or SequenceMatcher(None,body_text(post),body_text(old),autojunk=False).ratio() > .72:
            raise ValueError('Duplicate title or substantially repeated content')
    return [post, *posts]
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path)
    parser.add_argument('--check', action='store_true')
    args=parser.parse_args()
    posts=json.loads(POSTS_FILE.read_text(encoding='utf-8'))
    seen=set()
    for post in posts:
        validate(post, strict=post.get('editorialVersion') == 2)
        if post['slug'] in seen: raise ValueError('Duplicate slug')
        seen.add(post['slug'])
    if args.input:
        updated=publish(json.loads(args.input.read_text(encoding='utf-8')),posts)
        temp=POSTS_FILE.with_suffix('.json.tmp')
        temp.write_text(json.dumps(updated,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        os.replace(temp,POSTS_FILE)
        print('Published researched insight:',updated[0]['title'])
    else:
        print(f'Validated {len(posts)} articles. New publication requires a researched --input draft.')
if __name__=='__main__':main()
