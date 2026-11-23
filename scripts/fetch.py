#!/usr/bin/env python3
"""Pull view counts from each platform and write docs/data/views.json.

Runs hourly on GitHub Actions. Uses only the standard library.
Secrets come from environment variables (GitHub repository secrets):

  IG_USER_ID, IG_ACCESS_TOKEN                 Instagram (Graph API)
  YT_API_KEY, YT_CHANNEL_ID                    YouTube Data API v3
  TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET,
  TIKTOK_REFRESH_TOKEN                         TikTok Display API

Only posts published on or after campaign.start are counted.
Each post keeps its latest known count, so a Story whose insights
expire after 24h keeps the last number the platform reported.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "config.json")
STORE = os.path.join(ROOT, "data", "store.json")
MANUAL = os.path.join(ROOT, "data", "manual.json")
OUT = os.path.join(ROOT, "docs", "data", "views.json")


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def save(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def http(url, method="GET", data=None, headers=None):
    body = None
    if data is not None:
        body = data if isinstance(data, bytes) else json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:400]
        raise RuntimeError("HTTP %s from %s: %s" % (e.code, url.split("?")[0], detail))


def parse_time(s):
    """ISO string (with Z or +0000) -> aware datetime."""
    s = s.replace("Z", "+00:00")
    if len(s) > 5 and (s[-5] in "+-") and s[-3] != ":":
        s = s[:-2] + ":" + s[-2:]
    return datetime.fromisoformat(s)


def warn(msg):
    print("::warning::" + msg)


# ---------------------------------------------------------------- Instagram
def fetch_instagram(cfg, start):
    uid, token = os.environ.get("IG_USER_ID"), os.environ.get("IG_ACCESS_TOKEN")
    if not uid or not token:
        raise RuntimeError("IG_USER_ID / IG_ACCESS_TOKEN not set")
    base = "https://%s/%s" % (cfg.get("host", "graph.facebook.com"), cfg.get("api_version", "v23.0"))
    fields = "id,caption,media_type,media_product_type,permalink,timestamp"

    items = []
    url = "%s/%s/media?%s" % (base, uid, urllib.parse.urlencode(
        {"fields": fields, "limit": 50, "access_token": token}))
    while url:
        page = http(url)
        older = False
        for m in page.get("data", []):
            if parse_time(m["timestamp"]) < start:
                older = True
                continue
            items.append(m)
        url = None if older else page.get("paging", {}).get("next")

    if cfg.get("include_stories", True):
        url = "%s/%s/stories?%s" % (base, uid, urllib.parse.urlencode(
            {"fields": fields, "access_token": token}))
        for m in http(url).get("data", []):
            if parse_time(m["timestamp"]) >= start:
                m["media_product_type"] = "STORY"
                items.append(m)

    posts = []
    for m in items:
        try:
            ins = http("%s/%s/insights?%s" % (base, m["id"], urllib.parse.urlencode(
                {"metric": "views", "access_token": token})))
            d = ins["data"][0]
            views = d.get("total_value", {}).get("value")
            if views is None:
                views = d["values"][0]["value"]
        except Exception as e:  # one bad post must not stop the run
            warn("instagram %s: %s" % (m["id"], e))
            continue
        kind = (m.get("media_product_type") or m.get("media_type") or "").lower()
        posts.append({
            "key": "instagram:" + m["id"],
            "platform": "instagram",
            "type": {"reels": "reel", "story": "story", "feed": "post"}.get(kind, kind),
            "title": (m.get("caption") or "").strip().split("\n")[0][:90],
            "url": m.get("permalink", ""),
            "published": m["timestamp"],
            "views": int(views),
        })
    return posts


# ---------------------------------------------------------------- YouTube
def fetch_youtube(cfg, start):
    key, channel = os.environ.get("YT_API_KEY"), os.environ.get("YT_CHANNEL_ID")
    if not key or not channel:
        raise RuntimeError("YT_API_KEY / YT_CHANNEL_ID not set")
    api = "https://www.googleapis.com/youtube/v3/"
    ch = http(api + "channels?" + urllib.parse.urlencode(
        {"part": "contentDetails", "id": channel, "key": key}))
    uploads = ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    ids, token = [], None
    while True:
        q = {"part": "contentDetails", "playlistId": uploads, "maxResults": 50, "key": key}
        if token:
            q["pageToken"] = token
        page = http(api + "playlistItems?" + urllib.parse.urlencode(q))
        older = False
        for it in page.get("items", []):
            if parse_time(it["contentDetails"].get("videoPublishedAt", "1970-01-01T00:00:00Z")) < start:
                older = True
                continue
            ids.append(it["contentDetails"]["videoId"])
        token = page.get("nextPageToken")
        if older or not token:
            break

    posts = []
    for i in range(0, len(ids), 50):
        page = http(api + "videos?" + urllib.parse.urlencode(
            {"part": "snippet,statistics", "id": ",".join(ids[i:i + 50]), "key": key}))
        for v in page.get("items", []):
            posts.append({
                "key": "youtube:" + v["id"],
                "platform": "youtube",
                "type": "short",
                "title": v["snippet"]["title"][:90],
                "url": "https://www.youtube.com/shorts/" + v["id"],
                "published": v["snippet"]["publishedAt"],
                "views": int(v["statistics"].get("viewCount", 0)),
            })
    return posts


# ---------------------------------------------------------------- TikTok
def fetch_tiktok(cfg, start):
    ck, cs, rt = (os.environ.get(k) for k in
                  ("TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET", "TIKTOK_REFRESH_TOKEN"))
    if not (ck and cs and rt):
        raise RuntimeError("TIKTOK_* secrets not set")
    tok = http("https://open.tiktokapis.com/v2/oauth/token/", "POST",
               urllib.parse.urlencode({"client_key": ck, "client_secret": cs,
                                       "grant_type": "refresh_token", "refresh_token": rt}).encode(),
               {"Content-Type": "application/x-www-form-urlencoded"})
    if "access_token" not in tok:
        raise RuntimeError("TikTok token refresh failed: %s" % tok)
    if tok.get("refresh_token") and tok["refresh_token"] != rt:
        warn("TikTok issued a new refresh token: update the TIKTOK_REFRESH_TOKEN secret")

    fields = "id,title,video_description,create_time,share_url,view_count"
    url = "https://open.tiktokapis.com/v2/video/list/?fields=" + fields
    headers = {"Authorization": "Bearer " + tok["access_token"], "Content-Type": "application/json"}
    posts, cursor = [], None
    while True:
        body = {"max_count": 20}
        if cursor:
            body["cursor"] = cursor
        page = http(url, "POST", body, headers).get("data", {})
        older = False
        for v in page.get("videos", []):
            published = datetime.fromtimestamp(v["create_time"], timezone.utc)
            if published < start:
                older = True
                continue
            posts.append({
                "key": "tiktok:" + v["id"],
                "platform": "tiktok",
                "type": "video",
                "title": (v.get("title") or v.get("video_description") or "")[:90],
                "url": v.get("share_url", ""),
                "published": published.isoformat(),
                "views": int(v.get("view_count", 0)),
            })
        cursor = page.get("cursor")
        if older or not page.get("has_more"):
            break
    return posts


FETCHERS = {"instagram": fetch_instagram, "youtube": fetch_youtube, "tiktok": fetch_tiktok}


def main():
    cfg = load(CONFIG, None)
    camp = cfg["campaign"]
    tz = timezone(timedelta(hours=cfg.get("utc_offset_hours", 3)))
    start = datetime.fromisoformat(camp["start"]).replace(tzinfo=tz)
    now = datetime.now(tz)

    store = load(STORE, {"posts": {}, "history": {}, "status": {}})

    for name, pcfg in cfg["platforms"].items():
        if not pcfg.get("enabled") or name not in FETCHERS:
            continue
        try:
            fresh = FETCHERS[name](pcfg, start)
            for p in fresh:
                store["posts"][p["key"]] = p
            store["status"][name] = {"ok": True, "at": now.isoformat(), "posts": len(fresh)}
            print("%s: %d posts" % (name, len(fresh)))
        except Exception as e:
            prev = store["status"].get(name, {})
            store["status"][name] = {"ok": False, "at": now.isoformat(), "error": str(e)[:300],
                                     "last_ok": prev.get("at") if prev.get("ok") else prev.get("last_ok")}
            warn("%s failed: %s" % (name, e))

    # Manual entries (Snapchat, or any correction) are re-read every run,
    # so editing or removing a line in data/manual.json takes effect.
    store["posts"] = {k: p for k, p in store["posts"].items() if not p.get("manual")}
    for m in load(MANUAL, []):
        key = "%s:%s" % (m["platform"], m["id"])
        store["posts"][key] = {
            "key": key, "platform": m["platform"], "type": m.get("type", "story"),
            "title": m.get("title", ""), "url": m.get("url", ""),
            "published": m.get("published", camp["start"]), "views": int(m["views"]),
            "manual": True,
        }

    posts = [p for p in store["posts"].values()
             if parse_time(p["published"] if "T" in p["published"] else p["published"] + "T00:00:00+03:00") >= start]
    total = sum(p["views"] for p in posts)

    today = now.date().isoformat()
    if now >= start:
        store["history"][today] = total
    save(STORE, store)

    by_platform = {}
    for p in posts:
        by_platform[p["platform"]] = by_platform.get(p["platform"], 0) + p["views"]
    top = sorted(posts, key=lambda p: p["views"], reverse=True)[: cfg.get("top_posts", 8)]

    save(OUT, {
        "demo": False,
        "updated": now.isoformat(),
        "campaign": camp,
        "total": total,
        "platforms": by_platform,
        "status": {k: {"ok": v["ok"], "at": v["at"]} for k, v in store["status"].items()},
        "history": [{"date": d, "total": t} for d, t in sorted(store["history"].items())],
        "top": [{k: p[k] for k in ("platform", "type", "title", "url", "views")} for p in top],
    })
    print("total views: %d" % total)


if __name__ == "__main__":
    sys.exit(main())
