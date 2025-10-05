# -*- coding: utf-8 -*-
from __future__ import annotations
import re, html, time, logging, math
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import requests
import pandas as pd
from bs4 import BeautifulSoup
from dateutil import parser as dtparse
from .domains import DOMAINS, MIN_MATCHES, MIN_TOKENS

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

UA = {"User-Agent": "telotopic-poc/0.1 (+research)"}  # poli

def clean_html_to_text(html_text: str) -> str:
    soup = BeautifulSoup(html_text, "lxml")
    for tag in soup(["script","style","noscript"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    text = html.unescape(re.sub(r"\s+", " ", text)).strip()
    return text

def count_tokens(txt: str) -> int:
    # proxy simple
    return len(re.findall(r"\w+", txt))

def assign_domain(text: str) -> Optional[str]:
    text_l = text.lower()
    best = None
    best_hits = 0
    for dom, kws in DOMAINS.items():
        hits = 0
        for kw in kws:
            # phrase sensible aux limites de mot quand pertinent
            pat = r"\b" + re.escape(kw.lower()) + r"\b" if " " not in kw else re.escape(kw.lower())
            hits += len(re.findall(pat, text_l))
        if hits >= MIN_MATCHES and hits > best_hits:
            best, best_hits = dom, hits
    return best

def within_period(dt: datetime, start: datetime, end: datetime) -> bool:
    return (dt >= start) and (dt <= end)

def enforce_min_tokens(text: str) -> bool:
    return count_tokens(text) >= MIN_TOKENS

def as_iso(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")

def df_schema() -> List[str]:
    return ["actor_id","country","domain_id","period","date","url","language","text","tokens"]
