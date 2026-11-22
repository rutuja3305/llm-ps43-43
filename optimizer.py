"""
Backend logic for the LinkedIn Profile Optimizer (PS43).

Flow: validate input -> build prompt -> call the LLM -> parse + validate JSON -> return a clean dict.
All three supported providers (Groq, Gemini, OpenAI) and local Ollama expose an
OpenAI-compatible API, so one client library (`openai`) handles every provider.
"""
from __future__ import annotations

import json
import re

from openai import (
    APIConnectionError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    OpenAI,
    RateLimitError,
)

HEADLINE_MAX = 220  # LinkedIn headline limit
ABOUT_MAX = 2600  # LinkedIn About limit

# Default model names can change over time. Override with LLM_MODEL in .env if a provider retires one.
PROVIDERS = {
    "groq": {
        "label": "Groq (free tier, fast)",
        "base_url": "https://api.groq.com/openai/v1",
        "model": "llama-3.3-70b-versatile",
    },
    "gemini": {
        "label": "Google Gemini (free tier)",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "model": "gemini-2.5-flash",
    },
    "openai": {
        "label": "OpenAI",
        "base_url": None,
        "model": "gpt-4o-mini",
    },
    "ollama": {
        "label": "Ollama (local, no key needed)",
        "base_url": "http://localhost:11434/v1",
        "model": "llama3.1",
    },
}


class OptimizerError(Exception):
    """Raised with a message that is safe to show directly to the user."""


# --------------------------------------------------------------------------- prompts
SYSTEM_PROMPT = f"""You are an expert LinkedIn profile writer for students and early-career professionals.

Rewrite the user's LinkedIn headline and About section so they are stronger and aimed at their target role.

Hard rules:
1. Use ONLY facts present in the user's input. Never invent employers, degrees, grades, numbers, certifications, projects or achievements.
   If the input is thin, write honestly around the skills and intent that were given.
2. Headline options: exactly 3, each at most {HEADLINE_MAX} characters, each taking a DIFFERENT angle
   (for example: role + core skills; value you bring; keyword-rich for recruiter search).
3. About section: first person, plain text, 110-180 words, short paragraphs separated by a blank line.
   Open with who the person is and what they are aiming for, then skills and evidence from the input,
   then close with what they are looking for. Never exceed {ABOUT_MAX} characters.
4. No emojis, no hashtags, no clichés such as "passionate", "hardworking", "go-getter", "ninja", "guru".
5. Weave in relevant keywords for the target role only when the user's skills support them.

Return ONLY a JSON object, with no markdown fences and no commentary, in exactly this shape:
{{
  "headline_options": [
    {{"headline": "string", "angle": "short label such as 'Role + skills'"}},
    {{"headline": "string", "angle": "string"}},
    {{"headline": "string", "angle": "string"}}
  ],
  "about": "string",
  "keywords_used": ["string", "..."],
  "tips": ["one short, specific improvement tip", "..."]
}}"""


def build_user_prompt(headline: str, about: str, skills: str, target_role: str, goals: str = "") -> str:
    def block(label: str, value: str) -> str:
        return f"{label}:\n{value.strip() if value and value.strip() else '(not provided)'}"

    return "\n\n".join(
        [
            block("Current headline", headline),
            block("Current About section", about),
            block("Skills", skills),
            block("Target role", target_role),
            block("Extra career goals (optional)", goals),
        ]
    )


# --------------------------------------------------------------------------- input checks
def validate_inputs(headline: str, about: str, skills: str, target_role: str) -> None:
    if not target_role.strip():
        raise OptimizerError("Please enter a target role, for example 'Data Analyst'.")
    if not (headline.strip() or about.strip() or skills.strip()):
        raise OptimizerError("Please enter at least one of: current headline, About section, or skills.")
    if len(about) > 6000 or len(skills) > 3000 or len(headline) > 600:
        raise OptimizerError("One of the inputs is too long. Please shorten it and try again.")


# --------------------------------------------------------------------------- parsing
def parse_json(text: str) -> dict:
    """Parse the model output, tolerating ```json fences or surrounding prose."""
    if not text or not text.strip():
        raise ValueError("empty response")
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start != -1 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise


def normalise(data: dict) -> dict:
    """Check the structure and return clean, predictable fields."""
    if not isinstance(data, dict):
        raise ValueError("response is not a JSON object")

    options = []
    for item in data.get("headline_options") or []:
        if isinstance(item, str):
            item = {"headline": item, "angle": ""}
        if isinstance(item, dict) and str(item.get("headline", "")).strip():
            options.append(
                {"headline": str(item["headline"]).strip(), "angle": str(item.get("angle", "")).strip()}
            )
    if not options:
        raise ValueError("no headline options in response")

    about = str(data.get("about", "")).strip()
    if not about:
        raise ValueError("no About section in response")

    def str_list(key: str) -> list[str]:
        raw = data.get(key) or []
        return [str(x).strip() for x in raw if str(x).strip()] if isinstance(raw, list) else []

    return {
        "headline_options": options[:3],
        "about": about,
        "keywords_used": str_list("keywords_used"),
        "tips": str_list("tips"),
    }


# --------------------------------------------------------------------------- client + call
def get_client(provider: str, api_key: str, model: str | None = None) -> tuple[OpenAI, str]:
    if provider not in PROVIDERS:
        raise OptimizerError(f"Unknown provider '{provider}'. Choose one of: {', '.join(PROVIDERS)}.")
    cfg = PROVIDERS[provider]
    if provider == "ollama":
        api_key = api_key or "ollama"  # Ollama ignores the key but the client requires one
    if not api_key or not api_key.strip():
        raise OptimizerError(
            "No API key found. Add LLM_API_KEY to your .env file, or paste a key in the sidebar."
        )
    client = OpenAI(api_key=api_key.strip(), base_url=cfg["base_url"], timeout=60.0)
    return client, (model or "").strip() or cfg["model"]


def _complete(client, model: str, messages: list[dict]) -> str:
    kwargs = dict(model=model, messages=messages, temperature=0.6)
    try:
        resp = client.chat.completions.create(response_format={"type": "json_object"}, **kwargs)
    except BadRequestError:
        # Some models reject JSON mode; the prompt already demands JSON, so retry without it.
        resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content or ""


def optimize_profile(
    client,
    model: str,
    headline: str,
    about: str,
    skills: str,
    target_role: str,
    goals: str = "",
) -> dict:
    validate_inputs(headline, about, skills, target_role)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(headline, about, skills, target_role, goals)},
    ]
    try:
        text = _complete(client, model, messages)
        try:
            return normalise(parse_json(text))
        except (ValueError, json.JSONDecodeError):
            # One repair attempt: show the model its own bad output and ask for valid JSON only.
            messages += [
                {"role": "assistant", "content": text},
                {
                    "role": "user",
                    "content": "That was not valid JSON in the required shape. Return ONLY the JSON object.",
                },
            ]
            text = _complete(client, model, messages)
            try:
                return normalise(parse_json(text))
            except (ValueError, json.JSONDecodeError):
                raise OptimizerError(
                    "The model did not return a usable result. Please try again, or switch model/provider."
                )
    except AuthenticationError:
        raise OptimizerError("The API key was rejected. Check that it is correct and for the selected provider.")
    except RateLimitError:
        raise OptimizerError("Rate limit or quota reached. Wait a minute and retry, or switch provider.")
    except NotFoundError:
        raise OptimizerError(f"Model '{model}' was not found. Set a valid LLM_MODEL in .env.")
    except APIConnectionError:
        raise OptimizerError("Could not connect to the provider. Check your internet (or that Ollama is running).")
