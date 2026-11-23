#!/usr/bin/env python3
"""Write sample data to docs/data/views.json so the page can be previewed
before launch. The file is flagged "demo": true and the page shows a
banner saying the numbers are not real. The first real run of fetch.py
overwrites it.

Usage: python3 scripts/make_demo.py [day]   (day of the campaign to simulate, default 12)
"""
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    day = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    cfg = json.load(open(os.path.join(ROOT, "config.json"), encoding="utf-8"))
    camp = dict(cfg["campaign"])
    tz = timezone(timedelta(hours=3))
    start = date.today() - timedelta(days=day - 1)      # so "today" is day N
    camp["start"] = start.isoformat()

    daily = [18000, 26000, 31000, 22000, 41000, 38000, 52000, 47000, 61000, 44000, 58000, 39000,
             66000, 51000, 72000, 48000, 69000, 75000, 57000, 81000, 64000, 78000, 70000, 88000,
             59000, 83000, 91000, 76000, 95000, 102000]
    hist, total = [], 0
    for i in range(day):
        total += daily[i % len(daily)]
        hist.append({"date": (start + timedelta(days=i)).isoformat(), "total": total})

    top = [
        ("instagram", "reel", "الفريق يشرح للمدير فكرة المشاهدات المضمونة", 142300),
        ("tiktok", "video", "سألنا أصحاب المشاريع: كم تدفع على 100 ألف مشاهدة؟", 96800),
        ("instagram", "reel", "جلسة تصوير وحدة = 4 منصات", 61250),
        ("youtube", "short", "ما وصلنا الرقم؟ نكمل مجاناً", 40120),
        ("snapchat", "story", "يوم 5 في الاستوديو", 28700),
        ("instagram", "story", "كم تتوقع سعر مليون مشاهدة؟", 22950),
        ("tiktok", "video", "ترند الأسبوع بنكهة ليمون", 19400),
        ("instagram", "carousel_album", "ليش تدفع على فيديو؟", 15880),
    ]
    out = {
        "demo": True,
        "updated": (datetime.now(tz) - timedelta(minutes=14)).isoformat(),
        "campaign": camp,
        "total": total,
        "platforms": {"instagram": int(total * .52), "tiktok": int(total * .26),
                      "youtube": int(total * .12), "snapchat": int(total * .10)},
        "status": {},
        "history": hist,
        "top": [{"platform": p, "type": t, "title": ti, "url": "", "views": v} for p, t, ti, v in top],
    }
    path = os.path.join(ROOT, "docs", "data", "views.json")
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("demo day %d, total %d -> %s" % (day, total, path))


if __name__ == "__main__":
    main()
