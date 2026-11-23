# عداد المشاهدات المضمونة | ليمون

صفحة عامة تعرض مشاهدات حملة ليمون مباشرة، والأرقام تنسحب آلياً من المنصات كل ساعة.

- **الصفحة:** `docs/index.html` (تُنشر على GitHub Pages)
- **الأرقام:** `docs/data/views.json` (يحدّثها GitHub Actions كل ساعة)
- **إعدادات الحملة:** `config.json`
- **أرقام سناب اليدوية:** `data/manual.json`

---

## 1) إعداد الحملة

عدّل `config.json`:

```json
"campaign": { "name": "المشاهدات المضمونة", "start": "2026-12-01", "days": 30, "target": 1000000 }
```

- `start`: تاريخ انطلاق الحملة (بتوقيت الكويت). **أي منشور قبل هذا التاريخ ما ينحسب.**
- `tiktok.enabled`: خلّه `false` إلى أن توافق تيك توك على التطبيق، وبعدها حوّله `true`.

---

## 2) رفع المشروع على GitHub

1. سوّ مستودع جديد **عام (Public)** على GitHub، مثلاً `lemon-views`. (GitHub Pages المجاني يحتاج مستودع عام. المفاتيح السرية ما تنرفع أبداً، تنحفظ في Secrets.)
2. ارفع كل محتويات هالمجلد للمستودع.
3. **Settings ← Pages**: اختار `Deploy from a branch` ← `main` ← المجلد `/docs` ← Save.
4. بعد دقيقة يصير الرابط: `https://<اسم-حسابك>.github.io/lemon-views/`
5. **Settings ← Actions ← General ← Workflow permissions**: اختار **Read and write permissions** ← Save.

---

## 3) المفاتيح السرية (Secrets)

**Settings ← Secrets and variables ← Actions ← New repository secret**، وأضف:

| الاسم | من وين |
|---|---|
| `IG_USER_ID` | رقم حساب انستغرام البزنس (انظر تحت) |
| `IG_ACCESS_TOKEN` | توكن ميتا (انظر تحت) |
| `YT_API_KEY` | مفتاح YouTube Data API v3 |
| `YT_CHANNEL_ID` | رقم قناة يوتيوب (يبدأ بـ `UC`) |
| `TIKTOK_CLIENT_KEY` | من تطبيق تيك توك |
| `TIKTOK_CLIENT_SECRET` | من تطبيق تيك توك |
| `TIKTOK_REFRESH_TOKEN` | بعد ربط حساب ليمون بالتطبيق |

### انستغرام (ميتا)

1. في [developers.facebook.com](https://developers.facebook.com) سوّ تطبيق نوعه **Business**، وأضف منتج **Instagram** (Instagram API with Facebook Login).
2. أفضل توكن: **System User Token** من Business Manager (ما ينتهي):
   **Business Settings ← Users ← System users ← Add** ← اعطه صلاحية على صفحة فيسبوك وحساب انستغرام ليمون ← **Generate token** للتطبيق، مع الصلاحيات:
   `instagram_basic`، `instagram_manage_insights`، `pages_show_list`، `pages_read_engagement`، `business_management`.
3. رقم حساب انستغرام: من **Graph API Explorer** نفّذ
   `me/accounts?fields=instagram_business_account` ← انسخ `instagram_business_account.id`.
4. بما إن الحساب حسابكم والتطبيق تطبيقكم، **ما يحتاج مراجعة من ميتا (App Review)**.

> ملاحظة: إذا استخدمت توكن مستخدم عادي بدل System User، ينتهي بعد 60 يوم ولازم تجدده.

### يوتيوب

1. [console.cloud.google.com](https://console.cloud.google.com) ← مشروع جديد ← فعّل **YouTube Data API v3**.
2. **Credentials ← Create credentials ← API key**. ويفضّل تقييده على YouTube Data API v3 فقط.
3. رقم القناة من **YouTube Studio ← Settings ← Channel ← Advanced settings**.

### تيك توك (بعد الموافقة)

1. في [developers.tiktok.com](https://developers.tiktok.com) أضف **Login Kit** و**Display API** بصلاحيات `user.info.basic` و`video.list`، وقدّم التطبيق للمراجعة.
2. بعد الموافقة، اربط حساب ليمون عبر رابط التفويض واحصل على `refresh_token` (صالح سنة).
3. أضف الأسرار الثلاثة، وغيّر `tiktok.enabled` إلى `true` في `config.json`.
4. إذا طلع تحذير في سجل Actions إن تيك توك أصدر refresh token جديد، حدّث السر `TIKTOK_REFRESH_TOKEN`.

---

## 4) سناب شات (يدوي)

مرة يومياً، افتح إحصائيات سناب وأضف أو عدّل الأرقام في `data/manual.json` (تقدر تعدّله من موقع GitHub مباشرة):

```json
[
  { "platform": "snapchat", "id": "story-2026-12-02", "type": "story", "title": "يوم في الاستوديو", "published": "2026-12-02", "views": 4200 },
  { "platform": "snapchat", "id": "spot-01", "type": "spotlight", "title": "ترند الأسبوع", "published": "2026-12-03", "views": 18500 }
]
```

- `id` لازم يكون مختلف لكل قطعة. لتحديث رقم قطعة، غيّر `views` لنفس الـ `id`.
- أي تعديل على الملف يشغّل التحديث فوراً.

---

## 5) التشغيل والتحديث

- يشتغل تلقائياً كل ساعة.
- للتحديث الفوري: **Actions ← Update views ← Run workflow**.
- إذا فشلت منصة، باقي المنصات تكمل، وتطلع رسالة تحذير في سجل التشغيل.

### قواعد الأرقام

- يُعتمد مقياس **Views** كما تعرضه كل منصة.
- **ستوري انستغرام:** ميتا تمسح أرقامها بعد 24 ساعة، فالسكربت يحفظ آخر رقم شافه (لهذا السحب كل ساعة).
- **ستوري أقل من 5 مشاهدات:** ما ترجع لها أرقام من ميتا.
- **العداد ما يتجاوز الرقم الحقيقي أبداً:** الحركة في الصفحة تركض لين آخر رقم مسحوب وتوقف.
- **تأكد في أول أسبوع** إن مشاهدات الإعلانات الممولة داخلة في رقم المنشور. قارن رقم منشور مموَّل في الصفحة مع رقمه في التطبيق، حتى ما ينحسب شي مرتين أو ينقص.

---

## 6) تعديل شكل الصفحة

الصفحة تنبني من `src/dashboard.html`. بعد أي تعديل:

```bash
python3 scripts/build_page.py
```

السكربت يدمج خط ثمانية داخل الصفحة نفسها، لأن ترخيص الخط يسمح باستخدامه على المواقع فقط إذا كان مدموجاً داخل المنتج. **لا ترفع ملفات الخط في المستودع.**

### معاينة قبل الإطلاق

```bash
python3 scripts/make_demo.py 12
python3 -m http.server 8787 --directory docs
```

`make_demo.py` يكتب أرقام تجريبية (اليوم 12 من الحملة)، وتطلع في الصفحة لافتة "بيانات تجريبية". **أول تشغيل حقيقي يمسحها.**
