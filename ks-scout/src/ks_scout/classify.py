from __future__ import annotations
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from groq import Groq, RateLimitError
from openai import OpenAI

from .cache import Cache
from .config import Config

_SYSTEM_PROMPT = """\
You evaluate Kickstarter hardware projects as leads for an EE consultancy that helps teams \
graduate from prototype to production: custom PCB design, BOM optimisation, EMC compliance, \
DFM (design for manufacturing), and firmware hardening.

The IDEAL lead is a team that built a WORKING PROTOTYPE with off-the-shelf modules (Arduino, \
Raspberry Pi, ESP32 dev boards, sensor breakout boards, motor drivers, Bluetooth/WiFi modules \
wired together) and genuinely believes the product is ready — but has NO plan or a naive plan \
("find a manufacturer", "I'll deal with it later") for the jump to a production PCB.

You will be shown the project title, category, blurb, creator bio, story excerpt, and risks \
section. Output strict JSON only — no prose, no markdown fences.

━━ STEP 1 — Does the product contain electronics? ━━
Look for: circuit boards, microcontrollers, sensors, wireless radios, batteries, motors, \
displays, firmware, power regulation, or any embedded system.
If the product is PURELY mechanical, textile, structural, or consumable (no electronic \
components at all) → return LOW immediately. These are not leads.
Examples of non-electronics: hydration packs, gym equipment, furniture, clothing, \
food products, mechanical tools, structural accessories.

━━ STEP 2 — What level of electronics is this? ━━
Classify the team's electronics maturity. The consultancy's sweet spot is teams at the \
"devkit prototype" stage who need to professionalise — not raw beginners, not pros.

HIGH — devkit prototype, no professional EE (★ BEST LEAD ★):
  Product clearly has electronics AND the team signals they are hobbyist/prototype-level:
  • Explicit mention of Arduino, Raspberry Pi, ESP32 dev board, Teensy, Adafruit, SparkFun,
    Seeed Grove, breakout boards, breadboard, jumper wires, off-the-shelf modules
  • "We prototyped with...", "using an Arduino to control...", "powered by Raspberry Pi"
  • Describes connecting pre-made modules together rather than designing a custom board
  • No mention of custom PCB, schematic capture, PCB layout, EMC, CE/FCC certification
  • Scaling plan is vague or absent: "we'll work with a manufacturer", "mass production TBD",
    "we'll figure out manufacturing after the campaign"
  • Team bio: industrial design, software/marketing/business, mechanical, "maker"/hobbyist —
    NOT electrical/electronics/embedded engineering
  • Risks section hand-waves electronics production risks
  • BONUS SIGNAL: product photos show dev boards, jumper wires, breadboards, 3D-printed
    enclosures with visible off-the-shelf modules
  → These teams HAVE a product that works. They just don't know what they don't know about
    turning it into something manufacturable. THIS IS THE BEST LEAD.

MED — professional-grade electronics, EE capability ambiguous:
  • Mentions "PCB" but no details on who designed it or at what revision
  • Mentions a specific MCU/sensor part number BUT in a way that sounds professional
    (datasheet-level detail, not "I used an Arduino")
  • Team has "engineers" but discipline is unclear (mechanical? software? EE?)
  • Product appears too complex for pure hobbyist work but no EE explicitly named
  • Mentions "firmware" in a professional context (OTA updates, bootloader, RTOS)
  • Prior similar product shipped, but technical ownership is murky
  • Company with existing products but unclear if they have in-house EE or outsourced it

LOW — professional EE clearly present (not a lead):
  • Custom PCB explicitly mentioned with revision history ("rev 3", "4-layer board", "we
    spun several prototypes", "our PCB design")
  • Named professional EE roles: "our electrical engineer", "embedded systems engineer",
    "hardware engineer", "EE lead", "electronics design team"
  • Production-ready language: "schematic", "layout", "gerber files", "EMC testing",
    "CE marking", "FCC certification", "DFM review", "pick-and-place", "assembly house"
  • Team already working with a contract manufacturer (CM) at the PCB level
  • Multiple complex electronics products previously shipped with documented EE depth
  • Very complex system (drone with custom flight controller, robotic arm with custom
    motor drivers, medical device with certified electronics) — these almost certainly
    have EE talent even if not named explicitly

━━ EDGE CASES ━━
• "Raspberry Pi" as the FINAL product brain (not just prototype) → MED or LOW depending
  on team. Using a Pi Compute Module on a custom carrier board → likely MED/LOW (has EE).
  Using a Pi 4 plugged into stuff → likely HIGH.
• Software-heavy team building a hardware gadget: "we're app developers who built this
  smart lock" with no EE partner mentioned → HIGH.
• Team mentions hiring an EE freelancer or looking for one → MED (they know they need
  help, still a lead but more aware).
• Pure accessories (phone cases, stands, cables) even if "designed" → check for actual
  electronics. Passive accessories with no electronics → LOW.

━━ BIAS ━━
When in doubt between HIGH and MED, choose HIGH. False positives are cheap.
Only choose LOW when professional EE capability is explicit and unambiguous.

Output schema (JSON only, no markdown):
{"ee_gap": "HIGH"|"MED"|"LOW", "confidence": <float 0.0-1.0>, "evidence": "<1-2 sentences citing specific phrases from the inputs that prove the devkit/prototype stage or professional EE level>", "team": ["<full name and role if available, e.g. 'John Smith — Industrial Designer'>", "..."]}

The "team" field: list every person you can identify from the creator bio, story, or description. Include their role/title if mentioned. If no clear names or team info is found, use an empty array []. Include the creator and any co-founders or key team members named in the text.\
"""

# Provider → base_url
_PROVIDER_CONFIG: dict[str, dict] = {
    "groq":     {"base_url": None},
    "deepseek": {"base_url": "https://api.deepseek.com"},
}

# HTTP status codes that mean credit/auth exhausted — stop the whole batch
_FATAL_STATUS_CODES = {401, 402}

# Retry tracking across runs
_RETRY_FILE = Path("output/.ks-scout-retry.json")
_MAX_RETRIES = 3


class CreditExhaustedError(Exception):
    """Raised when the LLM provider returns 401 or 402 — not transient, stop retrying."""


def _load_retry_state() -> dict:
    """Return {failures: int, last_error: str, last_run: str} or empty dict."""
    try:
        return json.loads(_RETRY_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_retry_state(failures: int, error: str) -> None:
    _RETRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    _RETRY_FILE.write_text(json.dumps({
        "failures": failures,
        "last_error": error,
        "last_run": datetime.now(timezone.utc).isoformat(),
    }, indent=2), encoding="utf-8")


def _clear_retry_state() -> None:
    try:
        _RETRY_FILE.unlink(missing_ok=True)
    except OSError:
        pass


def handle_fatal_error(exc: Exception, output_dir: str = "output") -> str:
    """Record a fatal error, increment retry counter, and return a status message.

    On the 3rd failure writes *output/WARNING_CREDIT.txt*.
    Call this from the CLI when classification stops due to CreditExhaustedError.
    """
    state = _load_retry_state()
    failures = state.get("failures", 0) + 1
    msg = str(exc)[:500]

    if failures >= _MAX_RETRIES:
        warning_path = Path(output_dir) / "WARNING_CREDIT.txt"
        warning_path.parent.mkdir(parents=True, exist_ok=True)
        warning_path.write_text(
            f"LLM CREDIT EXHAUSTED — {failures} consecutive failed runs\n"
            f"Last error: {msg}\n"
            f"Last attempt: {datetime.now(timezone.utc).isoformat()}\n"
            f"\n"
            f"Top up your DeepSeek balance at https://platform.deepseek.com\n"
            f"Then delete this file and run ks-scout again.\n",
            encoding="utf-8",
        )
        # Reset the retry counter so we don't keep writing the warning every run
        _clear_retry_state()
        return (
            f"Credit exhausted after {failures} consecutive failed runs. "
            f"Warning written to {warning_path}"
        )

    _save_retry_state(failures, msg)
    remaining = _MAX_RETRIES - failures
    return (
        f"LLM credit/auth error (attempt {failures}/{_MAX_RETRIES}). "
        f"{remaining} retries remaining across future runs. "
        f"State saved to {_RETRY_FILE}"
    )


def check_retry_state() -> str | None:
    """Return a warning string if there are pending retries from a previous run, or None."""
    state = _load_retry_state()
    if not state:
        return None
    failures = state.get("failures", 0)
    last_err = state.get("last_error", "unknown")
    last_run = state.get("last_run", "?")
    return (
        f"⚠  Retry state: {failures}/{_MAX_RETRIES} failed runs. "
        f"Last error ({last_run[:10]}): {last_err[:120]}"
    )


def _build_payload(detail: dict) -> str:
    cat = detail.get("category_name", "")
    parent = detail.get("parent_category", "")
    cat_str = f"{parent} > {cat}" if parent else cat

    bio = (detail.get("creator_bio") or "").strip()
    risks = (detail.get("risks_text") or "").strip()
    story = (detail.get("story_text") or "")[:3000].strip()
    blurb = (detail.get("description") or "")[:500]

    return (
        f"Title: {detail.get('name', '')}\n"
        f"Category: {cat_str}\n"
        f"Blurb: {blurb}\n"
        f"Creator bio: {bio or '(not provided)'}\n"
        f"Story excerpt: {story or '(not provided)'}\n"
        f"Risks and challenges: {risks or '(not provided)'}"
    )


def _llm_call(payload: str, config: Config, api_key: str) -> str:
    """Route the LLM call to the configured provider and return the raw response text.

    Raises CreditExhaustedError for 401/402 so the caller can stop the whole batch.
    """
    provider = config.llm_provider.lower()
    provider_cfg = _PROVIDER_CONFIG.get(provider)
    if provider_cfg is None:
        raise ValueError(
            f"Unknown LLM provider {provider!r}. Valid options: {', '.join(_PROVIDER_CONFIG)}"
        )

    delays = [1, 4, 16]

    if provider == "groq":
        client = Groq(api_key=api_key)
        last_err: Exception | None = None
        for attempt, pre_sleep in enumerate([0] + delays):
            if pre_sleep:
                time.sleep(pre_sleep)
            try:
                resp = client.chat.completions.create(
                    model=config.llm_model,
                    messages=[
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": payload},
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=300,
                    temperature=0.1,
                )
                return resp.choices[0].message.content  # type: ignore[union-attr,return-value]
            except RateLimitError as exc:
                last_err = exc
                if attempt < len(delays):
                    continue
            except Exception as exc:
                error_str = str(exc).lower()
                if any(str(code) in error_str for code in _FATAL_STATUS_CODES):
                    raise CreditExhaustedError(str(exc)) from exc
                last_err = exc
                break
        raise last_err  # type: ignore[misc]

    else:
        # OpenAI-compatible (DeepSeek, and any future provider)
        client = OpenAI(api_key=api_key, base_url=provider_cfg["base_url"])
        last_err: Exception | None = None
        for attempt, pre_sleep in enumerate([0] + delays):
            if pre_sleep:
                time.sleep(pre_sleep)
            try:
                resp = client.chat.completions.create(
                    model=config.llm_model,
                    messages=[
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": payload},
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=300,
                    temperature=0.1,
                )
                return resp.choices[0].message.content  # type: ignore[union-attr,return-value]
            except Exception as exc:
                error_str = str(exc).lower()
                if any(str(code) in error_str for code in _FATAL_STATUS_CODES):
                    raise CreditExhaustedError(str(exc)) from exc
                last_err = exc
                if attempt < len(delays):
                    continue
                break
        raise last_err  # type: ignore[misc]


def classify_project(
    detail: dict,
    config: Config,
    cache: Cache,
    api_key: str,
    verbose: bool = False,
) -> dict:
    """Classify one project.  Returns a dict with ee_gap, confidence, evidence.

    If the provider returns 401/402 the dict will include ``_fatal: True`` so
    the caller can stop the entire batch.
    """
    payload = _build_payload(detail)
    input_hash = hashlib.sha256(payload.encode()).hexdigest()

    cached = cache.get_classification(input_hash)
    if cached is not None:
        if verbose:
            print(f"  [cache] classify '{detail.get('name', detail.get('pid'))}'")
        return cached

    if verbose:
        print(f"  [llm]   classify '{detail.get('name', detail.get('pid'))}'...")

    try:
        raw = _llm_call(payload, config, api_key)
        result = json.loads(raw)
        result["ee_gap"] = str(result.get("ee_gap", "MED")).upper()
        if result["ee_gap"] not in ("HIGH", "MED", "LOW"):
            result["ee_gap"] = "MED"
        result["confidence"] = float(result.get("confidence", 0.5))
        result["evidence"] = result.get("evidence", "")
        result["team"] = result.get("team", [])
        if not isinstance(result["team"], list):
            result["team"] = [str(result["team"])]
        cache.set_classification(input_hash, result)
        return result

    except CreditExhaustedError as exc:
        name = detail.get("name", str(detail.get("pid", "?")))
        print(f"  Fatal: credit/auth exhausted for '{name}': {exc}")
        return {"ee_gap": "ERR", "confidence": 0.0, "evidence": str(exc), "team": [], "_fatal": True}

    except Exception as exc:
        name = detail.get("name", str(detail.get("pid", "?")))
        print(f"  Warning: LLM failed for '{name}': {exc}")
        return {"ee_gap": "ERR", "confidence": 0.0, "evidence": str(exc), "team": []}
