"""
AI-powered group message handler.
Avval regex bilan parse qiladi; AI faqat regex yetishmasa chaqiriladi.
"""
import json
import logging
import re
import asyncio
import time
from aiogram import Router, F
from aiogram.types import Message

from config import Config
from utils.db import add_ad, get_monitored_group_ids

logger = logging.getLogger(__name__)
router = Router()

_group_cache: set[int] = set()
_cache_ts: float = 0.0
_CACHE_TTL = 60.0


async def _get_groups() -> set[int]:
    global _group_cache, _cache_ts
    if time.time() - _cache_ts > _CACHE_TTL:
        _group_cache = await get_monitored_group_ids()
        _cache_ts = time.time()
    return _group_cache


def _normalize_chat_id(chat_id: int) -> int:
    s = str(abs(chat_id))
    if s.startswith("100") and len(s) > 10:
        return int(s[3:])
    return abs(chat_id)


def _make_link(chat_id: int, msg_id: int, username: str = "") -> str:
    if username:
        return f"https://t.me/{username}/{msg_id}"
    bare = _normalize_chat_id(chat_id)
    return f"https://t.me/c/{bare}/{msg_id}"


# ── Regex-based parser ────────────────────────────────────────────────────────

# Shahar/mamlakat synonyms (lowercase)
_LOCATIONS = {
    "toshkent": ["toshkent", "tashkent", "ташкент", "toshkend"],
    "samarqand": ["samarqand", "samarkand", "самарканд"],
    "buxoro": ["buxoro", "buxara", "bukhara", "бухара"],
    "namangan": ["namangan", "наманган"],
    "andijon": ["andijon", "andijan", "андижан", "anjion"],
    "farg'ona": ["farg'ona", "fargona", "fergana", "фергана"],
    "nukus": ["nukus", "нукус"],
    "urganch": ["urganch", "urgench", "ургенч"],
    "termiz": ["termiz", "termez", "термез"],
    "qarshi": ["qarshi", "karshi", "карши"],
    "navoiy": ["navoiy", "navoi", "навои"],
    "jizzax": ["jizzax", "jizak", "джизак"],
    "shahrisabz": ["shahrisabz", "шахрисабз"],
    "guliston": ["guliston", "гулистан"],
    "chirchiq": ["chirchiq", "чирчик"],
    "moskva": ["москва", "moskva", "moscow", "moska", "мск"],
    "rossiya": ["россия", "russia", "rusiya", "рф"],
    "turkiya": ["turkiya", "турция", "turkey", "türkiye", "stambul", "istanbul", "стамбул", "анкара"],
    "germaniya": ["germaniya", "германия", "germany", "berlin", "берлин"],
    "xitoy": ["xitoy", "китай", "china", "pekin", "пекин"],
    "gruziya": ["gruziya", "грузия", "georgia", "tbilisi", "тбилиси"],
    "ozarbayjon": ["ozarbayjon", "азербайджан", "azerbaijan", "baku", "баку"],
    "tojikiston": ["tojikiston", "таджикистан", "tajikistan", "dushanbe", "душанбе"],
    "qirg'iziston": ["qirg'iziston", "кыргызстан", "kyrgyzstan", "bishkek", "бишкек"],
    "turkmaniston": ["turkmaniston", "туркменистан", "turkmenistan", "ashgabat"],
    "qozog'iston": ["qozog'iston", "qozoqiston", "казахстан", "kazakhstan"],
    "dubay": ["dubay", "dubai", "дубай", "оаэ", "uae"],
    "polsha": ["polsha", "польша", "poland", "warsaw"],
    "novosibirsk": ["novosibirsk", "новосибирск", "нск"],
    "yekaterinburg": ["yekaterinburg", "екатеринбург", "екб"],
    "sankt-peterburg": ["петербург", "питер", "piter", "spb", "спб", "санкт-петербург"],
    "almata": ["алматы", "алмата", "almata", "alma-ata"],
    "astana": ["астана", "нур-султан", "astana"],
    "krasnodar": ["краснодар", "krasnodar"],
    "kazan": ["казань", "kazan"],
    "rostov": ["ростов", "rostov"],
    "omsk": ["омск", "omsk"],
    "tyumen": ["тюмень", "tyumen"],
    "ufa": ["уфа", "ufa"],
    "samara": ["самара", "samara"],
    "chelyabinsk": ["челябинск"],
    "shimkent": ["шымкент", "shymkent"],
    "qashqadaryo": ["қашқадарё", "кашкадарья", "qashqadaryo", "kashkadarya"],
    "xorazm": ["хорезм", "khorezm", "xorazm"],
    "surxondaryo": ["сурхандарья", "surxondaryo"],
    "sirdaryo": ["сырдарья", "sirdaryo"],
    "baliqchi": ["baliqchi", "баликчи"],
    "belarusiya": ["беларусь", "belarus", "minsk", "минск"],
    "latviya": ["латвия", "latvia", "riga", "рига"],
    "ukraina": ["украина", "ukraine", "kiev", "киев"],
}

_LOC_RE: dict[str, re.Pattern] = {}
for _canonical, _variants in _LOCATIONS.items():
    _pat = "|".join(re.escape(v) for v in sorted(_variants, key=len, reverse=True))
    _LOC_RE[_canonical] = re.compile(rf'\b({_pat})\b', re.IGNORECASE)


_UZ_SUFFIX_RE = re.compile(
    r'(ga|dan|ning|da|ni|gа|dаn|dа|ni|ga|dagi|gacha)\b',
    re.IGNORECASE
)


def _strip_suffixes(text: str) -> str:
    return _UZ_SUFFIX_RE.sub(' ', text)


def _find_locations(text: str) -> list[str]:
    # Check both original and suffix-stripped text
    combined = text + " " + _strip_suffixes(text)
    found = []
    seen = set()
    for canonical, pat in _LOC_RE.items():
        if canonical not in seen and pat.search(combined):
            found.append(canonical)
            seen.add(canonical)
    return found


_ARROW_RE = re.compile(
    r'([^\n\r→\-]{2,40}?)\s*(?:→|->|–>|—>)\s*([^\n\r→\-]{2,40})',
    re.IGNORECASE
)
_WEIGHT_RE = re.compile(
    r'(\d[\d.,]*)\s*(?:тонн|тон\b|ton[na]*\b|т\b|tn\b|kg\b|кг\b)',
    re.IGNORECASE
)
_PRICE_RE = re.compile(
    r'(\d[\d\s]*(?:\.\d+)?)\s*(\$|usd|сум|so\'m|so`m|€|eur)',
    re.IGNORECASE
)
_PHONE_RE = re.compile(
    r'(?:\+998|998)?[-\s]?([39][0-9])[-\s]?(\d{3})[-\s]?(\d{2})[-\s]?(\d{2})'
)

_TRUCK_KEYWORDS = {
    "Tent":        ["tent", "тент"],
    "Ref":         [r"\bref\b", "рефр", "реф"],
    "Ref rejimsiz":["ref rejimsiz", "рефрижератор"],
    "Izoterma":    ["izotherma", "izoterma", "изотерм"],
    "Kichkina Isuzu": ["kichkina isuzu", "кичкина исузу", r"\bisuzu\b"],
    "Katta Isuzu": ["katta isuzu", "катта исузу"],
    "Bortovoy":    ["bortovoy", "борт", "бортовой"],
    "Konteyner":   ["konteyner", "контейн"],
    "Kamaz":       ["kamaz", "камаз"],
    "Mega":        [r"\bmega\b", "мега"],
    "Ploshadka":   ["ploshadka", "площадка"],
    "Tral":        [r"\btral\b", "трал"],
    "Sprinter":    ["sprinter", "спринтер"],
    "Dagruz":      ["dagruz", "dogr"],
}

_TRUCK_RE: dict[str, re.Pattern] = {
    name: re.compile("|".join(pats), re.IGNORECASE)
    for name, pats in _TRUCK_KEYWORDS.items()
}


def _extract_phone(text: str) -> str:
    m = _PHONE_RE.search(text)
    if m:
        return f"+998{m.group(1)}{m.group(2)}{m.group(3)}{m.group(4)}"
    return ""


def _extract_weight(text: str) -> str:
    m = _WEIGHT_RE.search(text)
    return f"{m.group(1)}t" if m else ""


def _extract_price(text: str) -> str:
    m = _PRICE_RE.search(text)
    return f"{m.group(1).strip()}{m.group(2)}" if m else ""


def _extract_truck(text: str) -> str:
    for name, pat in _TRUCK_RE.items():
        if pat.search(text):
            return name
    return ""


def _title(loc: str) -> str:
    return loc.replace("'", "'").title()


def _parse_regex(text: str) -> list[dict]:
    """Try to extract logistics ad from text using regex only. Returns [] if not confident."""
    from_loc = to_loc = ""

    # Try arrow pattern first
    m = _ARROW_RE.search(text)
    if m:
        raw_from = m.group(1).strip()[:40]
        raw_to   = m.group(2).strip()[:40]
        # Remove emoji chars
        raw_from = re.sub(r'[^\w\sЀ-ӿ\'-]', '', raw_from).strip()
        raw_to   = re.sub(r'[^\w\sЀ-ӿ\'-]', '', raw_to).strip()
        if len(raw_from) >= 3 and len(raw_to) >= 3:
            from_loc = raw_from
            to_loc   = raw_to

    # If no arrow, try detecting two known locations in order
    if not from_loc or not to_loc:
        locs = _find_locations(text)
        if len(locs) >= 2:
            from_loc = _title(locs[0])
            to_loc   = _title(locs[1])

    if not from_loc or not to_loc:
        return []

    return [{
        "from_loc": from_loc,
        "to_loc":   to_loc,
        "weight":   _extract_weight(text),
        "truck":    _extract_truck(text),
        "cargo":    "",
        "price":    _extract_price(text),
        "phone":    _extract_phone(text),
    }]


# ── AI prompt & helpers ───────────────────────────────────────────────────────

SYSTEM_PROMPT = """Sen logistika zayafkalarini ajratuvchi AI yordamchisisan.
Foydalanuvchi Telegram guruh xabarini beradi. Barcha logistika zayafkalarini JSON massiv sifatida qaytarasan.

Qoidalar:
1. Imlo xatolarini tuzat: "teshent"→"Toshkent", "maskvaga"→"Moskva"
2. Bitta xabarda bir nechta zayafka bo'lsa — BARCHASINI ajrat
3. Logistika emas deb hisoblasang — [] qaytar
4. FAQAT JSON massiv qaytar

Maydonlar: from_loc, to_loc, weight, truck (Tent/Ref/Izoterma/Kamaz/...), cargo, price, phone (+998...)
Misol: [{"from_loc":"Toshkent","to_loc":"Moskva","weight":"20t","truck":"Tent","cargo":"","price":"800$","phone":"+998901234567"}]"""


def _parse_json(raw: str) -> list:
    m = re.search(r'\[.*\]', raw, re.DOTALL)
    if not m:
        return []
    try:
        data = json.loads(m.group(0))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _fix_phones(ads: list) -> list:
    for ad in ads:
        p = re.sub(r'[\s\-\(\)]', '', ad.get("phone") or "")
        if not p:
            continue
        if p.startswith("+998") and len(p) == 13:
            continue
        digits = re.sub(r'^\+?\d{1,3}', '', p) if p.startswith('+') else p
        m = re.search(r'(9[0-9]{8})', digits)
        if m:
            ad["phone"] = f"+998{m.group(1)}"
        elif re.match(r'^998[0-9]{9}$', p):
            ad["phone"] = f"+{p}"
    return ads


# ── Rate limiter ──────────────────────────────────────────────────────────────

_ai_lock = asyncio.Semaphore(1)
_last_ai_call: float = 0.0
_groq_retry_until: float = 0.0   # epoch seconds — don't call Groq until this time
_MIN_INTERVAL = 3.0               # seconds between AI calls


async def _call_groq(text: str) -> list[dict] | None:
    global _groq_retry_until
    if not Config.GROQ_API_KEY:
        return []
    now = time.time()
    if now < _groq_retry_until:
        wait_sec = int(_groq_retry_until - now)
        logger.debug(f"Groq cooldown {wait_sec}s qoldi, skip")
        return None  # signal: use fallback

    try:
        from groq import Groq
        client = Groq(api_key=Config.GROQ_API_KEY)

        def _call():
            return client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": text[:2500]},
                ],
                max_tokens=800,
                temperature=0.1,
            )

        resp = await asyncio.to_thread(_call)
        _groq_retry_until = 0.0
        return _parse_json(resp.choices[0].message.content.strip())

    except Exception as e:
        err = str(e)
        if "429" in err or "rate_limit" in err:
            # Parse retry-after if available
            m = re.search(r'Please try again in ([\d.]+)s', err)
            wait = float(m.group(1)) if m else 60.0
            _groq_retry_until = time.time() + wait + 2
            logger.warning(f"Groq 429 — {wait:.0f}s kutamiz")
        else:
            logger.warning(f"Groq xato: {e}")
        return None  # signal: use fallback


async def _call_gemini(text: str) -> list[dict]:
    if not Config.GOOGLE_API_KEY:
        return []
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=Config.GOOGLE_API_KEY)
        prompt = f"{SYSTEM_PROMPT}\n\nXabar:\n{text[:2500]}"

        def _call():
            return client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.1, max_output_tokens=800),
            )

        resp = await asyncio.to_thread(_call)
        return _parse_json(resp.text)
    except Exception as e:
        err = str(e)
        if "429" in err or "RESOURCE_EXHAUSTED" in err:
            m = re.search(r'retry in ([\d.]+)s', err)
            wait = float(m.group(1)) if m else 30.0
            logger.warning(f"Gemini 429 — {wait:.0f}s keyin qayta urinish kerak (skip)")
        else:
            logger.warning(f"Gemini xato: {e}")
        return []


async def parse_with_ai(text: str) -> list[dict]:
    """1) Regex; 2) Groq; 3) Gemini — cascade."""
    global _last_ai_call

    # Step 1: Regex
    result = _parse_regex(text)
    if result:
        logger.debug(f"Regex parse OK: {result[0].get('from_loc')} → {result[0].get('to_loc')}")
        return _fix_phones(result)

    # Step 2 & 3: AI (throttled)
    async with _ai_lock:
        wait = _MIN_INTERVAL - (time.time() - _last_ai_call)
        if wait > 0:
            await asyncio.sleep(wait)

        result = await _call_groq(text)
        _last_ai_call = time.time()

        if result is None:
            # Groq rate-limited — try Gemini
            result = await _call_gemini(text)
            _last_ai_call = time.time()

        if result:
            return _fix_phones(result)

    return []


# ── Aiogram router ────────────────────────────────────────────────────────────

@router.message(F.chat.type.in_({"group", "supergroup"}))
async def on_group_message(msg: Message):
    try:
        groups = await _get_groups()
        if not groups:
            return

        chat_id = msg.chat.id
        bare_id = _normalize_chat_id(chat_id)
        if chat_id not in groups and bare_id not in groups:
            return

        text = msg.text or msg.caption
        if not text or len(text.strip()) < 15:
            return

        logger.info(f"📨 Guruh {bare_id} msg#{msg.message_id}: {text[:60]}...")

        ads = await parse_with_ai(text)
        if not ads:
            return

        username = msg.chat.username or ""
        link     = _make_link(chat_id, msg.message_id, username)
        source   = msg.chat.title or f"Guruh {bare_id}"

        saved = 0
        for ad in ads:
            from_loc = (ad.get("from_loc") or "").strip()
            to_loc   = (ad.get("to_loc") or "").strip()
            if not from_loc or not to_loc:
                continue

            ad_data = {
                "from_loc":   from_loc,
                "to_loc":     to_loc,
                "weight":     (ad.get("weight") or "").strip(),
                "truck":      (ad.get("truck") or "").strip(),
                "cargo":      (ad.get("cargo") or "").strip(),
                "price":      (ad.get("price") or "").strip(),
                "km":         0,
                "hours":      0,
                "phone":      (ad.get("phone") or "").strip(),
                "link":       link,
                "customs":    "",
                "source":     source,
                "group_id":   bare_id,
                "message_id": msg.message_id,
                "raw_text":   text,
            }
            new_id = await add_ad(ad_data)
            if new_id is None:
                continue
            ad_data["id"] = new_id
            saved += 1
            logger.info(f"  ✅ {from_loc}→{to_loc} | {ad.get('truck','')} | {ad.get('phone','—')}")
            from utils.notify import notify_subscribers
            asyncio.create_task(notify_subscribers(ad_data))

        if saved:
            logger.info(f"  💾 {saved} ta zayafka saqlandi (guruh {bare_id})")

    except Exception as e:
        logger.error(f"Group handler error: {e}")
