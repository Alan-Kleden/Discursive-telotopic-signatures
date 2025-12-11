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

LEGAL_PAT = re.compile(
    r"(This material may not be published|All rights reserved|Legal Statement|"
    r"Factset|Refinitiv Lipper|Subscribe|Sign in|Sign up|Skip to main content|"
    r"Back to home|Search (jobs|input)|Cookie(s)?|privacy policy)",
    re.I,
)
# blocs à supprimer par tag, rôle, ou classes/ids fréquents
KILL_TAGS = {"script","style","noscript","header","footer","nav","aside","form"}
KILL_ROLES = {"navigation","banner","search","contentinfo","complementary"}
KILL_PAT = re.compile(
    r"(cookie|consent|subscribe|paywall|meter|ad-|advert|promo|"
    r"newsletter|share|social|breadcrumb|toolbar|related|recommend|"
    r"modal|overlay|popup|banner|topbar|skip-link|site-header|site-footer|"
    r"comments|comment|byline|meta|dateline)", re.I
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

UA = {"User-Agent": "telotopic-poc/0.1 (+research)"}  # poli

def _domain_specific_decompose(soup, host: str):
    h = (host or "").lower()
    # Guardian
    if "theguardian.com" in h or "guardian.co.uk" in h:
        for sel in [
            "[data-link-name='nav2']", ".top-banner-ad-container", ".site-message",
            ".header", ".subnav", ".content__meta-container", ".ad-slot", ".consent",
            "#footer", ".sign-in", ".primary-nav", ".promo", ".newsletter",
        ]:
            for el in soup.select(sel): el.decompose()
    # Fox News
    if "foxnews.com" in h:
        for sel in [
            ".article-meta", ".trending", ".ad", ".ff-d-article-related", ".newsletter",
            ".subscription", ".social", "header", "footer", "nav",
        ]:
            for el in soup.select(sel): el.decompose()
    # FT
    if "ft.com" in h:
        for sel in [".o-ads", ".o-header", ".o-footer", ".o-share", ".o-cookie-message"]:
            for el in soup.select(sel): el.decompose()
    # UnHerd, AEI, Reason, DailySignal, Jacobin, City-Journal: traitements génériques suffisent

def clean_html_to_text(html: str, url: str = "") -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "lxml")

    # suppression générique
    for tag in list(soup.find_all(True)):
        if tag.name in KILL_TAGS:
            tag.decompose()
            continue
        if tag.has_attr("role") and str(tag["role"]).lower() in KILL_ROLES:
            tag.decompose()
            continue
        cls = " ".join(tag.get("class", []))
        iid = tag.get("id", "")
        if KILL_PAT.search(cls) or KILL_PAT.search(iid or ""):
            tag.decompose()

    # suppression spécifique au domaine
    try:
        from urllib.parse import urlparse
        host = urlparse(url).hostname or ""
    except Exception:
        host = ""
    _domain_specific_decompose(soup, host)

    # texte paragraphe par paragraphe
    parts = []
    for p in soup.find_all(["p","h2","h3","li"]):
        t = p.get_text(separator=" ", strip=True)
        if not t: 
            continue
        # filtre mentions légales et chrome résiduel
        if LEGAL_PAT.search(t):
            continue
        # lignes trop “UI”
        if len(t) < 40 and re.search(r"^(Sign in|Subscribe|Menu|Share|Search)$", t, re.I):
            continue
        parts.append(t)

    text = "\n".join(parts)

    # nettoyages finaux
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"(©\s*\d{4}\s+.*)$", "", text, flags=re.I|re.M)
    text = re.sub(r"^\s*(Skip to main content.*)$", "", text, flags=re.I|re.M)
    text = text.strip()
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
