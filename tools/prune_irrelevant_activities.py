#!/usr/bin/env python3
"""Permanently remove obsolete recruitment and unrelated trend articles.

Delete indexed cards, structured data, static routes and source HTML together;
do not delete any article about an actual campus activity, class, graduate,
award, faculty publication, student project or industry collaboration.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"data"/"removed_activity_posts.json"
ARCHIVE=ROOT/"activities"/"index.html"
BUILDER=ROOT/"tools"/"build_site.py"
TEST=ROOT/"tools"/"test_site.py"
CARD=re.compile(r'<article class="activity-card">.*?</article>',re.S)
URL=re.compile(r'<h3><a href="/activities/([^/]+)/"')
SCRIPT=re.compile(r'<script type="application/ld\+json">(.*?)</script>',re.S)

def main():
    data=json.loads(MANIFEST.read_text(encoding="utf-8"))
    removed={slug for values in data["groups"].values() for slug in values}
    assert len(removed)==35 and len(data["groups"]["expired_announcements"])==26 and len(data["groups"]["unrelated_reference"])==9
    assert {"kopo-738806","kopo-707036"}<=removed
    assert all(re.fullmatch(r'kopo-\d{6}',s) for s in removed)
    source=ARCHIVE.read_text(encoding="utf-8")
    all_cards=CARD.findall(source)
    def slug(card):
        match=URL.search(card)
        if match is None:raise RuntimeError("Missing article slug in archive")
        return match.group(1)
    listing_ids=[slug(card) for card in all_cards]
    assert len(set(listing_ids))==len(listing_ids)
    if len(listing_ids)==321:
        assert removed<=set(listing_ids),f"Missing removal targets: {removed-set(listing_ids)}"
    elif len(listing_ids)==286:
        assert not (removed&set(listing_ids)),"Previously removed cards returned"
    else:raise RuntimeError(f"Unexpected number of archive posts: {len(listing_ids)}")
    source=CARD.sub(lambda m:"" if slug(m.group()) in removed else m.group(),source)
    def structure(match):
        obj=json.loads(match.group(1))
        if obj.get("@type")!="CollectionPage":return match.group(0)
        rowlist=obj.get("mainEntity",{}).get("itemListElement",[])
        kept=[x for x in rowlist if x.get("url","").split("/activities/")[-1].strip("/") not in removed]
        assert len(kept)==286,len(kept)
        for i,x in enumerate(kept,1):x["position"]=i
        obj["mainEntity"]["itemListElement"]=kept
        return '<script type="application/ld+json">'+json.dumps(obj,ensure_ascii=False,separators=(",",":")).replace("<","\\u003c")+'</script>'
    source=SCRIPT.sub(structure,source)
    assert len(CARD.findall(source))==286
    for name in removed:
        assert f"/activities/{name}/" not in source,name
    ARCHIVE.write_text(source,encoding="utf-8")

    # Remove static-site route declarations, without affecting current pages.
    builder=BUILDER.read_text(encoding="utf-8")
    for name in sorted(removed):
        row=f'    ("activities/{name}/", "activities/{name}/index.html"),\n'
        if row in builder:builder=builder.replace(row,"")
        elif f'("activities/{name}/",' in builder:raise RuntimeError("Unknown route syntax: "+name)
    BUILDER.write_text(builder,encoding="utf-8")
    for name in removed:assert f'("activities/{name}/",' not in builder

    # Remove the two old fixed archive-count test assumptions.
    tests=TEST.read_text(encoding="utf-8")
    old='self.assertGreaterEqual(count,322)'
    if old in tests:tests=tests.replace(old,'self.assertGreaterEqual(count,287)')
    old='self.assertGreaterEqual(len(cards),321)'
    if old in tests:tests=tests.replace(old,'self.assertEqual(len(cards),286)')
    TEST.write_text(tests,encoding="utf-8")

    gone=[]
    for name in sorted(removed):
        path=ROOT/"activities"/name/"index.html"
        if path.is_file():
            path.unlink()
            path.parent.rmdir()
            gone.append(name)
        elif path.parent.exists():raise RuntimeError("Unexpected extra files in removed article "+name)

    # Remove source image assets exclusively belonging to the deleted posts.
    # No removal of photos appearing in other articles.
    sourcefiles=[]
    for directory in ("official-original","official-board","speaker-original"):
        for name in removed:
            identifier=name.split("-")[1]
            folder=ROOT/"assets"/"activities"/directory
            sourcefiles.extend(folder.glob(f"{identifier}-*.jpg"))
    all_references=set()
    for htmlfile in ROOT.glob("activities/*/index.html"):
        all_references.update(re.findall(r'/assets/activities/[^"\\s]+\\.jpg',htmlfile.read_text(encoding="utf-8")))
    all_references.update(re.findall(r'/assets/activities/[^"\\s]+\\.jpg',source))
    removed_photos=0
    for photo in set(sourcefiles):
        target="/"+photo.relative_to(ROOT).as_posix()
        if target in all_references:
            continue
        photo.unlink()
        removed_photos+=1

    # Defensive route/link verification; no deleted HTML will be in _site.
    live={slug(card) for card in CARD.findall(source)}
    assert len(live)==286 and not live&removed
    manifest=data.copy()
    manifest["removed_count"]=len(removed)
    manifest["retained_count"]=len(live)
    MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("ARCHIVE_CLEANUP",len(removed),"removed",len(live),"retained",
          len(gone),"HTML deleted",removed_photos,"orphan image assets deleted",flush=True)
    for cat,ids in data["groups"].items():
        print("CATEGORY",cat,len(ids),",".join(ids),flush=True)

if __name__=="__main__":main()
