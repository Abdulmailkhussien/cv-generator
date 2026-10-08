# -*- coding: utf-8 -*-
"""The AI layer: three ways in, one shape out.

Voice, an existing PDF and pasted text are not three features. They are three
doors into the same room: each one ends as the dict that draw_cv_pdf() already
knows how to render, so the renderer, the form and the templates never learn
that any of this happened.

    audio  ─┐
    pdf    ─┼─→  Gemini  ─→  CV_SCHEMA dict  ─→  the form  ─→  PDF
    text   ─┘

Two decisions worth knowing before reading further.

**The PDF is handed to Gemini whole, not parsed here.** Pulling Arabic text
out of a PDF locally is a losing fight: the glyphs come back disconnected, the
word order reverses, and ligatures arrive as single unknown characters. Gemini
reads the document as a document, so the fight never starts.

**Audio goes in as audio.** Transcribing first and sending the text throws away
exactly what a CV needs most - the model hearing "اشتغلت سنتين في شركة الاتصالات"
in a Jordanian accent does better than a transcriber's guess at it, and one
less step is one less thing that breaks silently.

Everything here is urllib, like the Telegram code in app.py, so the deployment
gains no new dependency.
"""

import base64
import json
import os
import time
from datetime import datetime, timezone
import urllib.error
import urllib.request

# ============ CONFIG ============
#
# The key lives in Render → Environment and nowhere else. It is never written
# to a file: this repository is public, and anything committed once stays in
# git history after it is deleted.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# The default is an alias on purpose, not a pinned version.
#
# This deployment was first set to gemini-2.0-flash, which Google retired.
# A retired name answers HTTP 404, every door stops working at once, and
# from the outside it is indistinguishable from a broken deployment - the
# kind of outage a user reports before the owner notices.
#
# An alias cannot fail that way. The cost is that behaviour may shift a
# little as Google moves it, which for extraction and rephrasing is a far
# gentler failure than silence.
#
# To pin a version instead, set GEMINI_MODEL in Render, and put a reminder
# somewhere to revisit it. /admin/models?t=TOKEN lists what this key can
# actually reach today.
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest").strip()

# The three jobs here are not equally hard, so they need not share a model.
#
# Reading a CV out of a document, a recording or pasted text is extraction:
# the facts are already in front of the model and the work is moving them
# into fields. A stronger model does not extract better, and on audio it
# costs latency the user feels.
#
# Matching a CV to an advert is judgement - recognising that "led a team of
# six" is evidence of leadership, that "built REST endpoints in Flask" is
# evidence of API work. That is where a stronger model earns its price, and
# it is also the feature worth being known for.
#
# Unset, matching uses the same model as everything else. Set
# GEMINI_MODEL_MATCH to something stronger and compare the two on real
# adverts before deciding - the only benchmark that counts here is your own
# CVs in Arabic.
GEMINI_MODEL_MATCH = os.environ.get("GEMINI_MODEL_MATCH", "").strip() or GEMINI_MODEL

_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/%s:generateContent?key=%s"
)

# A three minute recording is roughly half a megabyte; a scanned CV can be
# several. Both caps exist to stop one upload consuming the day's quota, and
# both are checked again in the browser so the user is told before the upload
# rather than after it.
MAX_AUDIO_BYTES = 8 * 1024 * 1024
MAX_DOC_BYTES = 10 * 1024 * 1024

# Audio and a long document both take real time. Render's own gateway gives up
# well after this, so the limit that matters is the user's patience.
TIMEOUT_SECONDS = 90


# ============ A BUDGET YOU CONTROL ============
#
# Google's free allowance is a moving number, published by them and changed
# without notice, so the code cannot assume one. What it can do is count its
# own calls and stop before the day is gone.
#
# Why this matters more than the exact limit: without it, the first busy day
# spends the whole allowance by mid-morning on whoever happened to arrive
# first, and everyone after them meets a broken site. With it, you decide
# the ceiling and know when you reached it.
#
# Set AI_DAILY_BUDGET in Render once you have seen a few real days in the AI
# Studio usage page. 0 turns the cap off.
#
# The count lives in the process, which is correct here because Render runs
# one worker (WEB_CONCURRENCY=1 in the deploy log). With more workers each
# would keep its own tally and the real total would be higher.
AI_DAILY_BUDGET = int(os.environ.get("AI_DAILY_BUDGET", "300") or 0)

_calls_today = 0
_calls_date = ""


def usage():
    """(calls so far today, budget, date) - for the admin page."""
    return (_calls_today, AI_DAILY_BUDGET, _calls_date)


def _count_call():
    """Count one call, and refuse once the day's budget is spent."""
    global _calls_today, _calls_date

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if today != _calls_date:
        _calls_date = today
        _calls_today = 0

    if AI_DAILY_BUDGET and _calls_today >= AI_DAILY_BUDGET:
        print("[GEMINI] daily budget of %d reached; refusing until tomorrow"
              % AI_DAILY_BUDGET)
        raise GeminiError("budget")

    _calls_today += 1


class GeminiError(Exception):
    """Something the caller should show the user, in their language."""


# ============ THE SHAPE EVERYTHING BECOMES ============
#
# Taken from what draw_cv_pdf() reads, field for field. If a key is added here
# it must be added to the renderer too, and the other way round - this schema
# is the contract between the two.
#
# `skills` is a single comma separated string rather than a list because that
# is what the renderer splits on (app.py, "skill_list = ..."). Matching the
# renderer's habits is worth more than tidiness here.

def _obj(props, required=None):
    return {
        "type": "object",
        "properties": props,
        "required": required or list(props.keys()),
    }


_STR = {"type": "string"}

CV_SCHEMA = _obj({
    "full_name": _STR,
    "job_title": _STR,
    "email": _STR,
    "phone": _STR,
    "location": _STR,
    "linkedin": _STR,
    "summary": _STR,
    "skills": _STR,
    "experiences": {
        "type": "array",
        "items": _obj({
            "title": _STR,
            "company": _STR,
            "start_date": _STR,
            "end_date": _STR,
            "description": _STR,
        }),
    },
    "education": {
        "type": "array",
        "items": _obj({
            "degree": _STR,
            "field": _STR,
            "school": _STR,
            "year": _STR,
        }),
    },
    "certifications": {
        "type": "array",
        "items": _obj({"name": _STR, "issuer": _STR, "year": _STR}),
    },
    "languages": {
        "type": "array",
        "items": _obj({"language": _STR, "level": _STR}),
    },
    "projects": {
        "type": "array",
        "items": _obj({"name": _STR, "description": _STR, "link": _STR}),
    },
})


# ============ THE RULE THAT MATTERS MOST ============
#
# A CV carrying a date, an employer or a skill its owner never gave it is not
# a better CV. It is a trap that springs in the interview, and the person
# blames the tool that set it - correctly.
#
# So the line is drawn between *wording* and *facts*. Rewriting "كنت أرد على
# الزباين وأحل مشاكلهم" into "Handled customer enquiries and resolved
# complaints" is the job. Deciding they must have used Zendesk is not.

_NO_INVENTION = """
ABSOLUTE RULE - read this twice before answering:

You may rewrite WORDING. You may not add FACTS.

Allowed: turning casual or spoken phrasing into concise professional CV
language; starting a duty with a strong verb; tightening a rambling sentence;
fixing spelling and grammar; ordering experience newest first.

Forbidden: any employer, job title, date, duration, qualification,
certificate, tool, technology, number or achievement that the source does not
state. If the source does not mention it, the field is "" or the list is [].

Dates specifically: if someone says "I worked there two years" without saying
which years, leave start_date and end_date as "". Do NOT calculate a guess
from today's date. An empty date is honest; an invented one is a lie the
person will have to defend.

An almost-empty CV built only from what was actually said is a correct answer.
A full CV containing one invented fact is a failure.
"""


def _language_rule(language):
    if language == "ar":
        return (
            "Write every value in Modern Standard Arabic, suitable for a "
            "professional CV - never in colloquial dialect, even when the "
            "source is spoken dialect. Keep proper nouns, company names, "
            "product names and technical terms in their original form "
            "(Python stays Python, LinkedIn stays LinkedIn)."
        )

    return (
        "Write every value in professional English. Keep proper nouns and "
        "company names as given; transliterate Arabic names rather than "
        "translating them."
    )


_SHAPE_RULES = """
Field notes:

- summary: 2-3 sentences, first person implied but written without "I".
  Only what the source supports.
- skills: ONE string, items separated by commas. Not a list, not bullets.
- experiences[].description: one to three short lines separated by newline
  characters, each starting with a verb. No bullet characters - the renderer
  adds those.
- experiences: newest first.
- level (languages): one of Native / Fluent / Advanced / Intermediate /
  Beginner, or the Arabic equivalent when writing Arabic.
- Leave every field you are unsure about empty. Empty is a correct answer.
"""


# ============ TRANSPORT ============

# Google answers 503 "experiencing high demand" at random under load, and
# it means exactly what it says: try again. Handing that straight to a
# person as "the service is unavailable" makes our problem theirs, when a
# second attempt a moment later usually works.
#
# Two retries, not more. Each attempt on an audio upload costs real seconds
# and the person is watching a spinner; past a point, telling them to try
# again themselves is more honest than making them wait longer.
RETRY_STATUSES = (500, 502, 503, 504)
RETRY_ATTEMPTS = 3
RETRY_BACKOFF = (1.5, 4.0)

# A budget on the whole call, not on each attempt. An overloaded Google
# answers 503 in under a second, so retrying costs almost nothing and is
# worth doing. A request that hung for a minute is a different animal:
# retrying it twice more would leave somebody staring at a spinner for
# several minutes, which is worse than an honest "try again".
RETRY_BUDGET_SECONDS = 45


def _call(parts, schema, temperature=0.2, model=None):
    """One request to Gemini, returning the parsed JSON object."""
    if not GEMINI_API_KEY:
        raise GeminiError("missing_key")

    _count_call()

    body = json.dumps({
        "contents": [{"parts": parts}],
        "generationConfig": {
            # Low, not zero: this is extraction and rephrasing, and the
            # creative range is exactly where invention lives.
            "temperature": temperature,
            "responseMimeType": "application/json",
            "responseSchema": schema,
        },
    }).encode("utf-8")

    url = _ENDPOINT % (model or GEMINI_MODEL, GEMINI_API_KEY)

    payload = None
    last = "upstream"
    started = time.monotonic()

    for attempt in range(RETRY_ATTEMPTS):
        req = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"})

        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            break

        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:400]

            # The key must never reach a log or an error page - the URL
            # carries it as a query parameter, so the URL itself is secret.
            print("[GEMINI] HTTP %s (attempt %d/%d): %s"
                  % (exc.code, attempt + 1, RETRY_ATTEMPTS, detail))

            # These say something about the request, not the moment, so a
            # second identical attempt would fail identically.
            if exc.code in (401, 403):
                raise GeminiError("bad_key")

            if exc.code == 404:
                raise GeminiError("bad_model")

            if exc.code == 429:
                raise GeminiError("quota")

            if exc.code == 400:
                raise GeminiError("bad_request")

            last = "busy" if exc.code in RETRY_STATUSES else "upstream"

            if exc.code not in RETRY_STATUSES:
                raise GeminiError("upstream")

        except Exception as exc:
            print("[GEMINI] transport failure (attempt %d/%d): %r"
                  % (attempt + 1, RETRY_ATTEMPTS, exc))
            last = "upstream"

        if attempt >= RETRY_ATTEMPTS - 1:
            break

        if time.monotonic() - started > RETRY_BUDGET_SECONDS:
            print("[GEMINI] giving up after %.0fs rather than retrying again"
                  % (time.monotonic() - started))
            break

        time.sleep(RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)])

    if payload is None:
        raise GeminiError(last)

    try:
        candidate = payload["candidates"][0]
        text = candidate["content"]["parts"][0]["text"]

    except (KeyError, IndexError):
        # A blocked or truncated answer lands here. The reason is worth a log
        # line because "it just failed" is unfixable from a bug report.
        print("[GEMINI] unusable response: %s" % json.dumps(payload)[:400])
        raise GeminiError("empty")

    try:
        return json.loads(text)

    except ValueError:
        print("[GEMINI] response was not JSON: %s" % text[:400])
        raise GeminiError("empty")


def _inline(mime_type, raw_bytes):
    return {
        "inline_data": {
            "mime_type": mime_type,
            "data": base64.b64encode(raw_bytes).decode("ascii"),
        }
    }


def _blank_cv():
    """Every field present and empty - what the form expects on failure."""
    return {
        "full_name": "", "job_title": "", "email": "", "phone": "",
        "location": "", "linkedin": "", "summary": "", "skills": "",
        "experiences": [], "education": [], "certifications": [],
        "languages": [], "projects": [],
    }


def _normalise(data):
    """Make the answer safe to hand straight to the form.

    A missing key, a null where a string belongs, or a list of strings where
    the renderer expects a list of dicts would each surface as a stack trace
    in draw_cv_pdf() long after the cause. Fix it here instead.
    """
    out = _blank_cv()

    if not isinstance(data, dict):
        return out

    for key, blank in out.items():
        value = data.get(key, blank)

        if isinstance(blank, str):
            out[key] = value.strip() if isinstance(value, str) else ""

        else:
            out[key] = [item for item in value
                        if isinstance(item, dict)] if isinstance(value, list) else []

    return out


# ============ THE THREE DOORS ============

def extract_from_text(text, language="ar"):
    """Pasted text - a CV written elsewhere, or an answer from a chat model."""
    instruction = "\n".join([
        "Read the text below and fill the CV schema from it.",
        _NO_INVENTION,
        _language_rule(language),
        _SHAPE_RULES,
        "",
        "--- SOURCE TEXT ---",
        text[:30000],
    ])

    return _normalise(_call([{"text": instruction}], CV_SCHEMA))


def extract_from_document(raw_bytes, mime_type, language="ar"):
    """An existing CV, as PDF or Word, read by the model as a document."""
    if len(raw_bytes) > MAX_DOC_BYTES:
        raise GeminiError("too_large")

    instruction = "\n".join([
        "The attached file is an existing CV. Read it and fill the schema.",
        "Preserve the person's real history exactly; this is a conversion,",
        "not a rewrite of their career.",
        _NO_INVENTION,
        _language_rule(language),
        _SHAPE_RULES,
    ])

    return _normalise(_call(
        [_inline(mime_type, raw_bytes), {"text": instruction}], CV_SCHEMA))


def extract_from_audio(raw_bytes, mime_type, language="ar"):
    """A recording of someone describing themselves, in any dialect."""
    if len(raw_bytes) > MAX_AUDIO_BYTES:
        raise GeminiError("too_large")

    instruction = "\n".join([
        "The attached recording is a person describing their own working",
        "life, most likely in spoken Arabic dialect. Listen to all of it and",
        "fill the CV schema from what they say.",
        "",
        "Spoken speech wanders, repeats and corrects itself. Take the final",
        "version of anything they restate, and ignore filler.",
        "",
        "If a part is inaudible, leave the field empty rather than guessing",
        "at what it might have been.",
        _NO_INVENTION,
        _language_rule(language),
        _SHAPE_RULES,
    ])

    return _normalise(_call(
        [_inline(mime_type, raw_bytes), {"text": instruction}], CV_SCHEMA))


# ============ MATCHING A CV AGAINST ONE JOB AD ============
#
# This is the part people come back for. A CV builder is used once; "tell me
# why this CV will not pass for this job" is used for every advert.
#
# The design decision that makes or breaks it: the answer is split in two.
#
#   rewrites          - the person already has this, said in the wrong words.
#                       Safe to apply, and this is where the real value is.
#   genuinely_missing - the person does not have this. Reported plainly and
#                       never written into the CV.
#
# Collapsing those two into one "add these keywords" list is what the cheap
# tools do. It produces a CV that wins the filter and loses the interview,
# and modern ATS scoring penalises stuffed keywords anyway.

MATCH_SCHEMA = _obj({
    "job_title": _STR,
    "match_percent": {"type": "integer"},
    "verdict": _STR,
    "terms": {
        "type": "array",
        "items": _obj({
            "term": _STR,
            "found": {"type": "boolean"},
            "importance": {"type": "string", "enum": ["essential", "preferred"]},
            "evidence": _STR,
        }),
    },
    "rewrites": {
        "type": "array",
        # The target is structured, not prose, so the browser can apply a
        # rewrite rather than print it and leave the person to copy it by
        # hand. Advice the reader has to assemble themselves is the same
        # failure this whole project started with.
        "items": _obj({
            "where_section": {
                "type": "string",
                "enum": ["summary", "experience", "project", "skills"],
            },
            "where_index": {"type": "integer"},
            "where_field": {
                "type": "string",
                "enum": ["summary", "title", "description", "skills"],
            },
            "where_label": _STR,
            "current": _STR,
            "suggested": _STR,
            "covers": {"type": "array", "items": _STR},
        }),
    },
    "tailored_summary": _STR,
    "genuinely_missing": {
        "type": "array",
        "items": _obj({"term": _STR, "note": _STR}),
    },
})


def match_job(cv_data, job_text, language="ar"):
    """Score one CV against one advert, and say what to do about it."""
    instruction = "\n".join([
        "You are comparing a CV against one job advertisement.",
        "",
        "STEP 1 - Pull the concrete requirements out of the advert: skills,",
        "tools, qualifications, domains, responsibilities. Mark each one",
        "'essential' or 'preferred' as the advert itself frames it. Ignore",
        "boilerplate such as 'team player' or 'fast paced environment'.",
        "Aim for 10 to 20 terms; fewer if the advert is thin.",
        "",
        "STEP 2 - For each term decide whether the CV already shows it.",
        "'found' means the CV contains real evidence, even under a different",
        "name: 'led a team of 6' is evidence of leadership; 'built REST",
        "endpoints in Flask' is evidence of API development. Put the exact",
        "phrase you relied on in 'evidence'. If there is no evidence, found",
        "is false and evidence is \"\".",
        "",
        "STEP 3 - Split what is missing into two groups, and keep them apart:",
        "",
        "  rewrites - the person HAS this, but worded so the advert's own",
        "    vocabulary does not appear. Give the current text and a rewrite",
        "    that uses the advert's words for the same real work. Never add",
        "    anything the original text did not already claim.",
        "",
        "    Point at the text precisely, because the rewrite is applied",
        "    automatically rather than copied by hand:",
        "      where_section  summary | experience | project | skills",
        "      where_index    0-based position in that list; 0 for summary",
        "                     and skills",
        "      where_field    summary | title | description | skills",
        "      where_label    a short human phrase for the same place, in",
        "                     the output language",
        "      current        the existing text at that exact place, copied",
        "                     verbatim so it can be checked before replacing",
        "",
        "    'suggested' replaces that field entirely, so it must be the",
        "    complete new value for the field - not a fragment, not a note",
        "    about what to change.",
        "",
        "  genuinely_missing - the person does NOT have this. Say so plainly",
        "    in 'note' and suggest what would close the gap. It is NEVER",
        "    written into the CV. Do not place it in rewrites. Do not imply",
        "    they can claim it.",
        "",
        "STEP 4 - tailored_summary: rewrite the professional summary aimed at",
        "this advert, using only experience the CV already proves.",
        "",
        "match_percent is round(100 * found_terms / total_terms) using the",
        "terms list you produced - it must match that list, because the user",
        "is shown both and a number that disagrees with its own evidence",
        "destroys trust in everything else on the page.",
        "",
        "verdict: one short sentence, honest. If the person is far from this",
        "role, say so - a wasted application costs them more than the truth.",
        "",
        _language_rule(language),
        "",
        "--- THE CV ---",
        json.dumps(cv_data, ensure_ascii=False)[:20000],
        "",
        "--- THE ADVERT ---",
        job_text[:20000],
    ])

    result = _call([{"text": instruction}], MATCH_SCHEMA,
                   temperature=0.3, model=GEMINI_MODEL_MATCH)

    if not isinstance(result, dict):
        raise GeminiError("empty")

    # Recompute the headline number from the evidence rather than trusting
    # the model's arithmetic. The list is on screen next to the score; if the
    # two disagree the user believes neither.
    terms = [t for t in result.get("terms", []) if isinstance(t, dict)]
    found = len([t for t in terms if t.get("found")])

    result["terms"] = terms
    result["found_count"] = found
    result["total_count"] = len(terms)
    result["match_percent"] = round(100.0 * found / len(terms)) if terms else 0

    return result


def translate_cv(cv_data, target_language):
    """The same CV, written in the other language.

    This is the feature a chat model cannot finish for you. It will happily
    translate the words, and then you are left fighting a word processor to
    get an Arabic PDF that a filter can read. Here one recording produces
    both files.

    It is a translation, not a second interview: the structure, the order,
    the dates and the employers come across untouched. Only the language of
    the prose changes.
    """
    other = "Arabic" if target_language == "ar" else "English"

    instruction = "\n".join([
        "Translate the CV below into %s." % other,
        "",
        "Keep every list the same length and in the same order. A person's",
        "history does not change with the language it is written in.",
        "",
        "Do NOT translate: personal names, company names, product names,",
        "university names with an official name in the other language,",
        "technologies and certifications. 'Python' stays 'Python'.",
        "Transliterate a personal name rather than translating its meaning.",
        "",
        "Dates, numbers and links are copied exactly.",
        "",
        "Write the prose the way a CV in that language is actually written,",
        "not word for word: Arabic in Modern Standard Arabic, English in",
        "the plain professional register. The reader should not be able to",
        "tell which version came first.",
        "",
        "Add nothing. If a field is empty it stays empty.",
        "",
        "--- CV ---",
        json.dumps(cv_data, ensure_ascii=False)[:20000],
    ])

    return _normalise(_call([{"text": instruction}], CV_SCHEMA, temperature=0.2))


def list_models():
    """Model names this key can actually reach, newest API first.

    Model names are retired on Google's schedule, and a wrong one fails as
    HTTP 404 - which looks identical to a broken deployment from the
    outside. Asking the key itself turns that guess into a list.
    """
    if not GEMINI_API_KEY:
        raise GeminiError("missing_key")

    url = ("https://generativelanguage.googleapis.com/v1beta/models?key=%s"
           % GEMINI_API_KEY)

    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))

    except urllib.error.HTTPError as exc:
        print("[GEMINI] models list HTTP %s: %s"
              % (exc.code, exc.read().decode("utf-8", "replace")[:300]))
        raise GeminiError("bad_key" if exc.code in (401, 403) else "upstream")

    except Exception as exc:
        print("[GEMINI] models list failed: %r" % (exc,))
        raise GeminiError("upstream")

    out = []

    for model in payload.get("models", []):
        name = (model.get("name") or "").replace("models/", "")
        methods = model.get("supportedGenerationMethods", []) or []

        # Only the ones that can answer a generateContent call are any use
        # here; embedding models would be noise on the page.
        if name and "generateContent" in methods:
            out.append(name)

    return sorted(out)


def is_configured():
    return bool(GEMINI_API_KEY)
