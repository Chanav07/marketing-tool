"""LLM-backed competitor discovery.

Provider-isolated: this module is the only place that talks to an LLM, so
swapping OpenAI for another provider is a one-file change. Feeds the brand's
stage 1-2 context (vision/goal/moat + personas) and operating regions to the
model and returns a list of suggested competitors.
"""
import json

from openai import AsyncOpenAI

from app.core.config import get_settings


class LLMNotConfigured(RuntimeError):
    """Raised when no LLM API key is configured."""


_COMPETITOR_SCHEMA = {
    "type": "object",
    "properties": {
        "competitors": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "website": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["name", "website", "description"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["competitors"],
    "additionalProperties": False,
}

_SYSTEM_TAILORED = (
    "You are a market-research analyst. Given a brand's strategy, target personas, "
    "and the regions it wants to operate in, identify real, currently-operating "
    "competitors this brand would realistically face given its positioning and "
    "those personas. Return only genuine companies you are confident exist. For "
    "each: a short website domain (or empty string if unsure) and a one-sentence "
    "description of what they do and why they compete."
)

_SYSTEM_GENERAL = (
    "You are a market-research analyst. Identify the major, well-known competitors "
    "and market leaders in this brand's overall product category / industry that "
    "operate in the given regions — the broad competitive set, NOT narrowed to the "
    "specific personas. Return only genuine companies you are confident exist. For "
    "each: a short website domain (or empty string if unsure) and a one-sentence "
    "description of what they do and why they compete."
)


def _persona_line(p) -> str:
    bits = [p.name]
    meta = [x for x in (p.user_type, p.business_size, p.region) if x]
    if meta:
        bits.append("(" + ", ".join(meta) + ")")
    if p.pain_points:
        bits.append(f"— pain: {p.pain_points}")
    return " ".join(bits)


async def fetch_competitors(
    *,
    brand_name: str,
    vision: str | None,
    goal: str | None,
    moat: str | None,
    personas: list,
    regions: list[str],
    exclude_names: set[str],
    general: bool = False,
    limit: int = 8,
) -> list[dict]:
    settings = get_settings()
    if not settings.openai_api_key:
        raise LLMNotConfigured(
            "OPENAI_API_KEY is not set. Add it to backend/.env to enable fetching."
        )

    persona_text = "\n".join(f"- {_persona_line(p)}" for p in personas) or "- (none provided)"
    region_text = ", ".join(regions) if regions else "(no regions specified)"
    exclude_text = ", ".join(sorted(exclude_names)) if exclude_names else "(none)"

    ask = (
        f"List up to {limit} of the biggest, most established competitors in this "
        f"brand's category operating in those regions."
        if general
        else f"Suggest up to {limit} competitors this brand would realistically "
        f"face in those regions."
    )
    user = f"""Brand: {brand_name}
Vision: {vision or "—"}
Goal: {goal or "—"}
Moat / edge: {moat or "—"}
Operating region(s): {region_text}

Target personas:
{persona_text}

{ask} Exclude these already-listed competitors: {exclude_text}."""

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    resp = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": _SYSTEM_GENERAL if general else _SYSTEM_TAILORED},
            {"role": "user", "content": user},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "competitors",
                "strict": True,
                "schema": _COMPETITOR_SCHEMA,
            },
        },
    )
    content = resp.choices[0].message.content or "{}"
    items = json.loads(content).get("competitors", [])

    cleaned: list[dict] = []
    seen = {n.lower() for n in exclude_names}
    for it in items:
        name = (it.get("name") or "").strip()
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())
        cleaned.append(
            {
                "name": name,
                "website": (it.get("website") or "").strip() or None,
                "description": (it.get("description") or "").strip() or None,
            }
        )
    return cleaned


_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "revenue_usd": {"type": "string"},
        "revenue_inr": {"type": "string"},
        "revenue_source": {"type": "string"},
        "users": {"type": "string"},
        "users_source": {"type": "string"},
        "moats": {"type": "array", "items": {"type": "string"}},
        "social": {
            "type": "object",
            "properties": {
                "instagram": {"type": "boolean"},
                "blog": {"type": "boolean"},
                "facebook": {"type": "boolean"},
                "x": {"type": "boolean"},
                "thirdparty": {"type": "string"},
            },
            "required": ["instagram", "blog", "facebook", "x", "thirdparty"],
            "additionalProperties": False,
        },
        "features": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "feature": {"type": "string"},
                    "sample_marketing": {"type": "string"},
                    "source": {"type": "string"},
                },
                "required": ["feature", "sample_marketing", "source"],
                "additionalProperties": False,
            },
        },
    },
    "required": [
        "name", "revenue_usd", "revenue_inr", "revenue_source",
        "users", "users_source", "moats", "social", "features",
    ],
    "additionalProperties": False,
}

_ANALYSIS_SYSTEM = (
    "You are a competitive-intelligence analyst with web search. For REVENUE and "
    "NUMBER OF USERS/CUSTOMERS you MUST look them up from a reputable source "
    "(annual report / SEC or regulatory filing, Bloomberg, Reuters, Statista, or "
    "the company's official site) — do not answer these two from memory.\n"
    "- revenue: find the latest annual revenue, then express THE SAME figure in "
    "both US dollars (revenue_usd, e.g. '$9.4B (FY2025)') and Indian rupees "
    "(revenue_inr, e.g. '₹78,000 crore') — convert using a recent exchange rate. "
    "Put the publisher + URL in revenue_source. If not found, use 'NA' for both.\n"
    "- users: the best sourced figure/estimate of users or customers; put the "
    "publisher + URL in users_source.\n"
    "- If, after searching, a figure genuinely cannot be found, set that field and "
    "its source to the exact string \"NA\". Never invent numbers.\n"
    "- moats: up to 5 primary defensible advantages (most important first).\n"
    "- social: true/false for a known presence on instagram, blog, facebook, x "
    "(twitter); thirdparty = name of any other notable channel (YouTube, LinkedIn, "
    "TikTok, …) or \"NA\".\n"
    "- features: the key features/products the company markets, each with a "
    "one-line sample marketing message in their style, and a `source` = the "
    "publisher + URL of the page where that feature/message is found (the "
    "product, landing, pricing or docs page, e.g. 'Zoho Books "
    "(https://www.zoho.com/books/features/)'). Use \"NA\" only if no source "
    "URL can be found.\n"
    "Keep revenue and users as clean values with no inline citation markup — the "
    "citation belongs only in the *_source fields."
)


# --- Content generation (stage 4) --------------------------------------

# Posting guidelines the model must respect per target platform.
_PLATFORM_GUIDELINES = {
    "whatsapp": (
        "WhatsApp Business message. Warm, personal, 1:1 conversational tone. Keep "
        "it short (ideally under ~700 characters). Open with a hook line, use short "
        "line breaks (NO markdown headings or tables), emojis are fine in "
        "moderation, and end with ONE clear call to action or link. Avoid ALL-CAPS "
        "and spammy phrasing."
    ),
    "rcs": (
        "RCS Business Message. A short, branded rich message: a bold title line, "
        "1-3 short benefit-led paragraphs, and a suggested action/button label such "
        "as 'Get started'. Concise, friendly and mobile-first."
    ),
    "google ad": (
        "Google Responsive Search Ad. Output EXACTLY as labelled lines: 3-5 "
        "'Headline N:' lines (each <= 30 characters) and 2-4 'Description N:' lines "
        "(each <= 90 characters). Benefit-led, keyword-relevant, each with a clear "
        "CTA. No emojis and no excessive punctuation."
    ),
}


def _platform_guideline(platform: str) -> str:
    key = platform.strip().lower()
    if key in _PLATFORM_GUIDELINES:
        return _PLATFORM_GUIDELINES[key]
    return (
        f"Follow the standard best practices and format conventions for {platform}: "
        "match the tone, length and structure typical of high-performing content "
        "there, and end with a clear call to action."
    )


_CONTENT_SYSTEM = (
    "You are a senior brand marketing copywriter. You write publish-ready content "
    "grounded in the brand's strategy, its target personas, and how it is "
    "differentiated from its competitors. You strictly follow the target "
    "platform's guidelines and the requested format and length. Write in the "
    "brand's voice, make specific and credible claims (never invent statistics), "
    "and return ONLY the content itself — ready to paste — using light markdown "
    "for structure where the platform allows it. No preamble, notes or explanations."
)


async def generate_content(
    *,
    brand_name: str,
    vision: str | None,
    goal: str | None,
    moat: str | None,
    personas: list,
    competitors: list[dict],
    form: str,
    content_format: str,
    platform: str,
) -> str:
    settings = get_settings()
    if not settings.openai_api_key:
        raise LLMNotConfigured(
            "OPENAI_API_KEY is not set. Add it to backend/.env to enable generation."
        )

    persona_text = "\n".join(f"- {_persona_line(p)}" for p in personas) or "- (none captured)"

    comp_lines = []
    for c in competitors:
        tag = " (primary)" if c.get("is_primary") else ""
        moats = ", ".join((c.get("moats") or [])[:3])
        extra = f" — strengths: {moats}" if moats else ""
        comp_lines.append(f"- {c['name']}{tag}{extra}")
    comp_text = "\n".join(comp_lines) or "- (none shortlisted)"

    length_rule = (
        "LONG-FORM: develop the idea fully with a clear structure (headline, "
        "sections / paragraphs), depth and a strong close."
        if form == "long"
        else "SHORT-FORM: tight, punchy and scannable — every line earns its place."
    )

    user = f"""Write a {content_format} for the brand below, to be published on {platform}.

BRAND
Name: {brand_name}
Vision: {vision or "—"}
Goal: {goal or "—"}
Moat / differentiation: {moat or "—"}

TARGET PERSONAS
{persona_text}

COMPETITIVE CONTEXT (differentiate against these where relevant)
{comp_text}

FORMAT: {content_format}
LENGTH: {length_rule}
PLATFORM GUIDELINES ({platform}): {_platform_guideline(platform)}

Write the {content_format} now. Return only the content, ready to publish."""

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    resp = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": _CONTENT_SYSTEM},
            {"role": "user", "content": user},
        ],
    )
    return (resp.choices[0].message.content or "").strip()


async def analyze_competitor(
    *, name: str, website: str | None, description: str | None
) -> dict:
    settings = get_settings()
    if not settings.openai_api_key:
        raise LLMNotConfigured(
            "OPENAI_API_KEY is not set. Add it to backend/.env to enable analysis."
        )

    user = f"""Competitor to analyze: {name}
Website: {website or "unknown"}
Known context: {description or "—"}

Search the web for this company's most recent annual revenue and its number of
users/customers, and cite the source for each. Produce the full structured
analysis. Use "NA" only when a figure genuinely cannot be found."""

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    resp = await client.responses.create(
        model=settings.openai_model,
        tools=[{"type": "web_search"}],
        input=[
            {"role": "system", "content": _ANALYSIS_SYSTEM},
            {"role": "user", "content": user},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "competitor_analysis",
                "schema": _ANALYSIS_SCHEMA,
                "strict": True,
            }
        },
    )
    return json.loads(resp.output_text or "{}")
