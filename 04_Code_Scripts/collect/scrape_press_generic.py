# 04_Code_Scripts/collect/scrape_press_generic.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import os, csv, re, requests
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
from bs4 import BeautifulSoup

UA = os.environ.get("SCRAPER_USER_AGENT", "TelotopicPoC/1.0")
TIMEOUT = float(os.environ.get("SCRAPER_TIMEOUT_S", "20"))
LANG_DEFAULT = "en"

def _req(url: str) -> requests.Response:
    return requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)

def _norm_ws(s: Optional[str]) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()

def _parse_date(text: str) -> Optional[str]:
    t = (text or "").strip()
    for fmt in ("%Y-%m-%d","%Y/%m/%d","%Y-%m-%dT%H:%M:%S%z","%Y-%m-%dT%H:%M:%S"):
        try: return datetime.strptime(t[:19], fmt).date().isoformat()
        except Exception: pass
    for fmt in ("%B %d, %Y","%b %d, %Y"):
        try: return datetime.strptime(t, fmt).date().isoformat()
        except Exception: pass
    m = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", t)
    if m:
        y,mn,d = m.groups()
        return f"{int(y):04d}-{int(mn):02d}-{int(d):02d}"
    return None

def _within(d: str, since: str, until: str) -> bool:
    return since <= d <= until

def _extract_text(soup: BeautifulSoup, content_sel: Optional[str]) -> str:
    node = soup.select_one(content_sel) if content_sel else soup
    if not node: node = soup
    for bad in node.select("nav,aside,footer,script,style"): bad.decompose()
    parts: List[str] = []
    for tag in node.find_all(["h1","h2","h3","p","li","blockquote"]):
        t = _norm_ws(tag.get_text(" "))
        if t: parts.append(t)
    return "\n".join(parts).strip()

def _list_items(list_soup: BeautifulSoup, list_sel: str, item_sel: Optional[str]):
    return list_soup.select(item_sel) if item_sel else list_soup.select(list_sel)

def _build_page_url(base: str, k: int) -> str:
    u = urlparse(base); q = parse_qs(u.query); q["page"] = [str(k)]
    newq = urlencode({kk:(vv[0] if isinstance(vv,list) else vv) for kk,vv in q.items()})
    return u._replace(query=newq).geturl()

def _find_next_link(soup: BeautifulSoup) -> Optional[str]:
    a = soup.select_one("a[rel='next'], .pager__item--next a, a[aria-label='Next'], a.pager-next, li.next a, a.next")
    return a.get("href") if a else None

@dataclass
class Gauges:
    pages:int=0; anchors:int=0; kept:int=0; skip_out:int=0; skip_no_date:int=0; skip_http:int=0; skip_other:int=0
    def dump(self)->str:
        return f"[pages={self.pages} anchors={self.anchors} kept={self.kept} skip(out={self.skip_out} no_date={self.skip_no_date} http={self.skip_http} other={self.skip_other})]"

def run_site(actor_id:str,country:str,domain_id:str,period:str,since:str,until:str,count:int,*,
             base_url:str,list_sel:str,link_attr:str="href",item_sel:Optional[str]=None,
             date_sel:Optional[str]=None,date_attr:Optional[str]=None,content_sel:Optional[str]=None,
             paginate_mode:str="query",max_pages:int=50,debug:bool=False,start_page:int=0) -> List[dict]:

    rows: List[dict] = []; gauges = Gauges()
    if paginate_mode=="query":
        page_index=max(0,int(start_page)); page_url=_build_page_url(base_url,page_index)
    elif paginate_mode=="next":
        page_index=0; page_url=base_url
    else:
        raise ValueError("paginate_mode must be 'query' or 'next'")

    while gauges.pages<max_pages and len(rows)<count and page_url:
        try:
            r=_req(page_url); r.raise_for_status()
        except requests.RequestException:
            gauges.skip_http+=1; 
            if debug: print(f"[http] {page_url}"); 
            break

        lsoup=BeautifulSoup(r.text,"html.parser"); gauges.pages+=1

        if debug and gauges.pages==1:
            try:
                os.makedirs("artifacts/debug",exist_ok=True)
                with open("artifacts/debug/listing_dump.html","w",encoding="utf-8") as f: f.write(r.text)
                print("[probe] wrote artifacts/debug/listing_dump.html")
            except Exception: pass
            all_as=lsoup.select("a[href]")[:200]
            print(f"[probe] page has {len(all_as)} <a> total (showing first 20):")
            for i,a in enumerate(all_as[:20],start=1):
                href=a.get("href"); txt=_norm_ws(a.get_text(" "))[:80]
                print(f"[a{str(i).zfill(2)}] {txt} :: {href}")

        items=_list_items(lsoup,list_sel,item_sel)
        anchors: List[Tuple[BeautifulSoup,str]]=[]
        for it in items:
            a = it if it.name=="a" else it.find("a")
            if not a: continue
            href=a.get(link_attr)
            if not href: continue
            anchors.append((it, urljoin(page_url, href)))

        for it,url in anchors:
            if len(rows)>=count: break
            gauges.anchors+=1
            try:
                rr=_req(url); rr.raise_for_status(); asoup=BeautifulSoup(rr.text,"html.parser")
            except requests.RequestException:
                gauges.skip_http+=1; 
                if debug: print(f"[http] {url}")
                continue

            adate=None
            if date_sel:
                dnode=asoup.select_one(date_sel) or it.select_one(date_sel)
                if dnode:
                    if date_attr: dval=dnode.get(date_attr)
                    else: dval=dnode.get("datetime") or dnode.get("content") or dnode.get_text(" ")
                    adate=_parse_date(_norm_ws(dval))
            if not adate:
                meta=asoup.select_one("time[datetime], meta[property='article:published_time'], meta[name='date'], meta[name='pubdate']")
                if meta:
                    dval=meta.get("content") or meta.get("datetime") or meta.get_text(" ")
                    adate=_parse_date(_norm_ws(dval))
            if not adate:
                gauges.skip_no_date+=1
                if debug: print(f"[no_date] {url}")
                continue
            if not _within(adate,since,until):
                gauges.skip_out+=1
                if debug: print(f"[out] {adate} {url}")
                continue

            text=_extract_text(asoup,content_sel)
            rows.append({
                "actor_id":actor_id,"country":country,"domain_id":domain_id,"period":period,
                "date":adate,"url":url,"language":LANG_DEFAULT,"text":text,"tokens":len(text.split())
            })
            gauges.kept+=1
            if debug: print(f"[keep] {adate} {url}")

        next_url=None
        if paginate_mode=="query":
            page_index+=1; next_url=_build_page_url(base_url,page_index)
        else:
            href=_find_next_link(lsoup); next_url=urljoin(page_url,href) if href else None
        page_url=next_url

    if debug: print(gauges.dump())
    return rows

def write_csv(rows: List[dict], actor_id: str, period: str, since: str, out_dir: str = "data/us_press") -> str:
    os.makedirs(out_dir, exist_ok=True)
    yyyymm = since[:7].replace("-","")
    out = os.path.join(out_dir, f"{actor_id}_{period}_{yyyymm}.csv")
    with open(out,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["actor_id","country","domain_id","period","date","url","language","text","tokens"])
        w.writeheader(); w.writerows(rows)
    return out
