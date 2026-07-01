"""
core/stat_fetcher.py
--------------------
Fetches public post statistics from TikTok, Instagram, Facebook, YouTube.

TikTok flow:
  1. tikwm.com public API  — free, no key, bypasses TikTok bot-detection
     GET https://www.tikwm.com/api/?url=<tiktok_url>
     Returns: play, digg_count, comment_count, create_time, author, cover, title
  2. TikTok /api/item/detail/ web API (fallback — sometimes blocked)
  3. Page scrape __UNIVERSAL_DATA__ (fallback)
  4. oEmbed (metadata only: author / thumbnail — always attempted)

Instagram / Facebook / YouTube:
  - Server-side stats are largely blocked by those platforms
  - oEmbed + noembed.com give author/title/thumbnail reliably
  - A clear message tells the user to enter stats manually when scraping fails

Returns a unified dict:
    {
        "views":          int or None,
        "likes":          int or None,
        "comments":       int or None,
        "date":           "YYYY-MM-DD" str or None,
        "title":          str or None,
        "author":         str or None,
        "thumbnail":      str or None,
        "engagement_text": str,
        "platform":       str,
        "error":          str or None,
    }
"""

import re
import json
import logging
from datetime import datetime
from urllib.parse import urlparse, quote

import requests

logger = logging.getLogger(__name__)

# Deployment marker — bump this string whenever stat_fetcher.py is edited.
# If you don't see this version string in the fetch-stats error/response,
# the deploy did not pick up the latest file.
STAT_FETCHER_VERSION = "v4-fixed-2026-06-30"
print(f"[stat_fetcher] loaded version: {STAT_FETCHER_VERSION}", flush=True)

TIMEOUT = 12

UA_DESKTOP = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

HEADERS_HTML = {
    "User-Agent": UA_DESKTOP,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0",
}

HEADERS_JSON = {
    "User-Agent": UA_DESKTOP,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.tiktok.com/",
}


# ── helpers ────────────────────────────────────────────────────

def _empty():
    return {
        "views": None, "likes": None, "comments": None,
        "date": None, "title": None, "author": None,
        "thumbnail": None, "error": None,
    }


def _parse_int(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return int(val)
    s = str(val).replace(",", "").replace(" ", "").strip()
    m = re.match(r"([\d.]+)\s*([KkMmBb]?)", s)
    if not m:
        return None
    num = float(m.group(1))
    mult = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}.get(m.group(2).upper(), 1)
    return int(num * mult)


def _fmt(n):
    if n is None:
        return None
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.0f}K"
    return str(n)


def _detect_platform(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "tiktok.com" in host:
        return "tiktok"
    if "instagram.com" in host:
        return "instagram"
    if "facebook.com" in host or "fb.com" in host or "fb.watch" in host:
        return "facebook"
    if "youtube.com" in host or "youtu.be" in host:
        return "youtube"
    return "unknown"


def _ts_to_date(ts) -> str:
    """Unix timestamp → YYYY-MM-DD string."""
    try:
        return datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d")
    except Exception:
        return None


def _noembed(url: str) -> dict:
    """noembed.com oEmbed proxy — gives author/title/thumbnail, no stats."""
    try:
        r = requests.get(
            f"https://noembed.com/embed?url={quote(url, safe='')}",
            headers=HEADERS_JSON, timeout=TIMEOUT,
        )
        if r.ok:
            d = r.json()
            if not d.get("error"):
                return d
    except Exception as e:
        logger.debug("noembed error %s: %s", url, e)
    return {}


# ── TikTok ─────────────────────────────────────────────────────

def _tikwm(url: str) -> dict:
    """
    tikwm.com public API — free, no key, bypasses TikTok bot detection.
    Accepts both short (vt.tiktok.com) and long URLs directly.
    Returns a parsed result dict on success, empty dict on failure.
    On failure, includes "_debug" key with the raw reason for troubleshooting.
    """
    try:
        api_url = f"https://www.tikwm.com/api/?url={quote(url, safe='')}&hd=1"
        r = requests.get(api_url, headers={"User-Agent": UA_DESKTOP}, timeout=TIMEOUT)
        if not r.ok:
            logger.warning("tikwm HTTP %s for %s — body: %s", r.status_code, url, r.text[:300])
            return {"_debug": f"tikwm HTTP {r.status_code}"}
        resp = r.json()
        if resp.get("code") != 0 or not resp.get("data"):
            logger.warning(
                "tikwm returned non-zero code for %s: code=%s msg=%s full=%s",
                url, resp.get("code"), resp.get("msg"), str(resp)[:300],
            )
            return {"_debug": f"tikwm code={resp.get('code')} msg={resp.get('msg')}"}

        d = resp["data"]
        author = d.get("author") or {}
        if isinstance(author, str):
            author = {"nickname": author}

        views_val = _parse_int(d.get("play_count"))
        if views_val is None:
            logger.warning(
                "tikwm code=0 but no play/play_count for %s — data keys: %s full=%s",
                url, list(d.keys()), str(d)[:500],
            )

        return {
            "views":    views_val,
            "likes":    _parse_int(d.get("digg_count")),
            "comments": _parse_int(d.get("comment_count")),
            "date":     _ts_to_date(d.get("create_time")),
            "title":    (d.get("title") or "")[:200] or None,
            "author":   author.get("nickname") or author.get("unique_id"),
            "thumbnail": d.get("cover") or d.get("origin_cover"),
            "_debug": None if views_val is not None else (
                f"tikwm code=0 but no play/play_count field; keys={list(d.keys())}"
            ),
        }
    except Exception as e:
        logger.warning("tikwm request exception for %s: %s", url, e)
        return {"_debug": f"tikwm exception: {e}"}


def _video_id_from_url(url: str):
    m = re.search(r"/video/(\d+)", url)
    return m.group(1) if m else None


def _video_id_from_oembed_html(html_snippet: str):
    m = re.search(r'data-video-id="(\d+)"', html_snippet)
    if m:
        return m.group(1)
    m = re.search(r'cite="https://www\.tiktok\.com/[^"]+/video/(\d+)"', html_snippet)
    return m.group(1) if m else None


def _expand_short_url(url: str) -> str:
    """Follow HTTP redirect on short URLs to get the canonical long URL."""
    host = urlparse(url).netloc.lower()
    if host in ("vt.tiktok.com", "vm.tiktok.com", "m.tiktok.com"):
        try:
            r = requests.get(url, headers=HEADERS_HTML, timeout=TIMEOUT, allow_redirects=True)
            final = r.url
            if "/video/" in final:
                return final
        except Exception as e:
            logger.debug("Short URL expand failed %s: %s", url, e)
    return url


def _tiktok_web_api(video_id: str) -> dict:
    """
    TikTok's internal web JSON API — same endpoint the browser calls.
    Works without auth in many regions; blocked on some server IPs.
    """
    try:
        ep = (
            f"https://www.tiktok.com/api/item/detail/"
            f"?itemId={video_id}&aid=1988&app_name=tiktok_web"
            f"&device_platform=web_pc&region=US"
        )
        r = requests.get(ep, headers=HEADERS_JSON, timeout=TIMEOUT)
        if not r.ok:
            return {}
        data = r.json()
        item = data.get("itemInfo", {}).get("itemStruct", {})
        if not item:
            return {}
        stats = item.get("stats", {})
        author = item.get("author", {})
        return {
            "views":    _parse_int(stats.get("playCount")),
            "likes":    _parse_int(stats.get("diggCount")),
            "comments": _parse_int(stats.get("commentCount")),
            "date":     _ts_to_date(item.get("createTime")),
            "author":   author.get("nickname") or author.get("uniqueId"),
            "title":    item.get("desc", "")[:200] or None,
            "thumbnail": None,
        }
    except Exception as e:
        logger.debug("TikTok web API error: %s", e)
        return {}


def _tiktok_page_scrape(url: str) -> dict:
    """Scrape canonical TikTok page for stats JSON blobs."""
    try:
        r = requests.get(url, headers=HEADERS_HTML, timeout=TIMEOUT)
        html = r.text

        # __UNIVERSAL_DATA_FOR_REHYDRATION__
        m = re.search(
            r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>',
            html, re.S,
        )
        if m:
            try:
                item = (
                    json.loads(m.group(1))
                    .get("__DEFAULT_SCOPE__", {})
                    .get("webapp.video-detail", {})
                    .get("itemInfo", {})
                    .get("itemStruct", {})
                )
                stats = item.get("stats", {})
                if stats.get("playCount") is not None:
                    author = item.get("author", {})
                    return {
                        "views":    _parse_int(stats["playCount"]),
                        "likes":    _parse_int(stats.get("diggCount")),
                        "comments": _parse_int(stats.get("commentCount")),
                        "date":     _ts_to_date(item.get("createTime")),
                        "author":   author.get("nickname") or author.get("uniqueId"),
                        "title":    item.get("desc", "")[:200] or None,
                        "thumbnail": None,
                    }
            except Exception as e:
                logger.debug("UNIVERSAL_DATA parse: %s", e)

        # SIGI_STATE
        m = re.search(r'<script id="SIGI_STATE"[^>]*>(.*?)</script>', html, re.S)
        if m:
            try:
                for _, item in json.loads(m.group(1)).get("ItemModule", {}).items():
                    stats = item.get("stats", {})
                    if stats.get("playCount") is not None:
                        return {
                            "views":    _parse_int(stats["playCount"]),
                            "likes":    _parse_int(stats.get("diggCount")),
                            "comments": _parse_int(stats.get("commentCount")),
                            "date":     _ts_to_date(item.get("createTime")),
                            "author":   None,
                            "title":    None,
                            "thumbnail": None,
                        }
            except Exception as e:
                logger.debug("SIGI_STATE parse: %s", e)

    except Exception as e:
        logger.debug("TikTok page scrape: %s", e)
    return {}


def _fetch_tiktok(url: str) -> dict:
    result = _empty()

    # ── Always get metadata from oEmbed first ─────────────────
    try:
        oembed_url = f"https://www.tiktok.com/oembed?url={quote(url, safe='')}"
        r = requests.get(oembed_url, headers=HEADERS_JSON, timeout=TIMEOUT)
        if r.ok:
            d = r.json()
            result["author"]    = d.get("author_name")
            result["title"]     = d.get("title")
            result["thumbnail"] = d.get("thumbnail_url")
            # Extract video_id from embed HTML if needed
            if d.get("html"):
                _vid = _video_id_from_oembed_html(d["html"])
                if _vid:
                    result["_video_id"] = _vid
    except Exception as e:
        logger.debug("TikTok oEmbed: %s", e)

    # noembed fallback for metadata
    if not result["author"]:
        ne = _noembed(url)
        result["author"]    = ne.get("author_name")
        result["title"]     = result["title"] or ne.get("title")
        result["thumbnail"] = result["thumbnail"] or ne.get("thumbnail_url")

    # ── Primary stats: tikwm.com (free proxy API) ─────────────
    tw = _tikwm(url)
    tikwm_debug = tw.pop("_debug", None)
    if tw.get("views") is not None:
        result.update({k: tw[k] for k in ("views", "likes", "comments", "date", "title")
                       if tw.get(k) is not None})
        result["author"]    = result["author"] or tw.get("author")
        result["thumbnail"] = result["thumbnail"] or tw.get("thumbnail")
        result.pop("_video_id", None)
        return result                        # ✅ best path

    # ── Fallback: expand short URL + video ID ─────────────────
    canonical = _expand_short_url(url)
    video_id  = (
        _video_id_from_url(canonical)
        or result.pop("_video_id", None)
        or _video_id_from_url(url)
    )
    result.pop("_video_id", None)

    # ── Fallback: TikTok web JSON API ─────────────────────────
    if video_id:
        wb = _tiktok_web_api(video_id)
        if wb.get("views") is not None:
            result.update({k: wb[k] for k in ("views", "likes", "comments", "date", "title")
                           if wb.get(k) is not None})
            result["author"] = result["author"] or wb.get("author")
            return result

    # ── Fallback: page scrape ─────────────────────────────────
    if canonical:
        sc = _tiktok_page_scrape(canonical)
        if sc.get("views") is not None:
            result.update({k: sc[k] for k in ("views", "likes", "comments", "date", "title")
                           if sc.get(k) is not None})
            result["author"] = result["author"] or sc.get("author")
            return result

    # ── Partial result: metadata only ─────────────────────────
    debug_suffix = f" [tikwm: {tikwm_debug}]" if tikwm_debug else ""
    if result["author"] or result["title"]:
        result["error"] = (
            "Got creator info but view/like counts are unavailable. "
            "TikTok is blocking automated access from this server. "
            "Enter stats manually." + debug_suffix
        )
    else:
        result["error"] = "Could not reach TikTok. Check the URL and try again." + debug_suffix

    return result


# ── Instagram ──────────────────────────────────────────────────

def _fetch_instagram(url: str) -> dict:
    result = _empty()

    ne = _noembed(url)
    result["author"]    = ne.get("author_name")
    result["title"]     = ne.get("title")
    result["thumbnail"] = ne.get("thumbnail_url")

    try:
        embed_url = re.sub(r"/+$", "", url) + "/embed/"
        r = requests.get(embed_url, headers=HEADERS_HTML, timeout=TIMEOUT, allow_redirects=True)
        html = r.text

        for field, pattern in [
            ("likes",    r'"likeCount"\s*:\s*(\d+)'),
            ("comments", r'"commentCount"\s*:\s*(\d+)'),
            ("views",    r'"videoViewCount"\s*:\s*(\d+)'),
            ("views",    r'"video_view_count"\s*:\s*(\d+)'),
        ]:
            if result[field] is None:
                m = re.search(pattern, html)
                if m:
                    result[field] = int(m.group(1))

        m = re.search(r'"taken_at_timestamp"\s*:\s*(\d+)', html)
        if m:
            result["date"] = _ts_to_date(m.group(1))

        if not result["date"]:
            for pat in (r'"dateCreated"\s*:\s*"([^"]+)"', r'"datePublished"\s*:\s*"([^"]+)"'):
                m = re.search(pat, html)
                if m:
                    result["date"] = m.group(1)[:10]
                    break
    except Exception as e:
        logger.debug("Instagram scrape: %s", e)

    if result["views"] is None and result["likes"] is None:
        result["error"] = (
            "Instagram stats unavailable — Instagram requires login for server access. "
            "Enter stats manually."
        )
    return result


# ── Facebook ───────────────────────────────────────────────────

def _fetch_facebook(url: str) -> dict:
    result = _empty()

    ne = _noembed(url)
    result["author"]    = ne.get("author_name")
    result["title"]     = ne.get("title")
    result["thumbnail"] = ne.get("thumbnail_url")

    try:
        r = requests.get(url, headers=HEADERS_HTML, timeout=TIMEOUT, allow_redirects=True)
        html = r.text

        if not result["title"]:
            m = re.search(r'property="og:title"\s+content="([^"]+)"', html)
            if m:
                result["title"] = m.group(1)
        if not result["thumbnail"]:
            m = re.search(r'property="og:image"\s+content="([^"]+)"', html)
            if m:
                result["thumbnail"] = m.group(1)

        for pat in (r'"videoViewCount"\s*:\s*(\d+)', r'"video_view_count"\s*:\s*(\d+)'):
            m = re.search(pat, html)
            if m:
                result["views"] = int(m.group(1))
                break

        for pat in (r'"dateCreated"\s*:\s*"([^"]+)"', r'"uploadDate"\s*:\s*"([^"]+)"'):
            m = re.search(pat, html)
            if m:
                result["date"] = m.group(1)[:10]
                break
    except Exception as e:
        logger.debug("Facebook scrape: %s", e)

    if result["views"] is None and result["likes"] is None:
        result["error"] = (
            "Facebook stats unavailable — Facebook limits server-side access. "
            "Enter stats manually."
        )
    return result


# ── YouTube ────────────────────────────────────────────────────

def _fetch_youtube(url: str) -> dict:
    result = _empty()
    try:
        oembed_url = f"https://www.youtube.com/oembed?url={quote(url, safe='')}&format=json"
        r = requests.get(oembed_url, headers=HEADERS_JSON, timeout=TIMEOUT)
        if r.ok:
            d = r.json()
            result["title"]     = d.get("title")
            result["author"]    = d.get("author_name")
            result["thumbnail"] = d.get("thumbnail_url")
    except Exception as e:
        logger.debug("YouTube oEmbed: %s", e)

    result["error"] = (
        "YouTube view counts require a YouTube Data API key. "
        "Metadata fetched — enter stats manually."
    )
    return result


# ── Public entry point ─────────────────────────────────────────

def fetch_post_stats(url: str) -> dict:
    platform = _detect_platform(url)

    dispatch = {
        "tiktok":    _fetch_tiktok,
        "instagram": _fetch_instagram,
        "facebook":  _fetch_facebook,
        "youtube":   _fetch_youtube,
    }

    if platform not in dispatch:
        return {
            **_empty(),
            "platform": "unknown",
            "engagement_text": "",
            "error": f"Unsupported platform for URL: {url}",
        }

    stats = dispatch[platform](url)
    stats["platform"] = platform

    parts = []
    if stats.get("views"):
        parts.append(f"{_fmt(stats['views'])} views")
    if stats.get("likes"):
        parts.append(f"{_fmt(stats['likes'])} likes")
    if stats.get("comments"):
        parts.append(f"{_fmt(stats['comments'])} comments")
    stats["engagement_text"] = " · ".join(parts) if parts else ""
    stats["_version"] = STAT_FETCHER_VERSION

    return stats
