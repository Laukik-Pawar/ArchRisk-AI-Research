"""Stage 1: LLM extractor (components + dependencies) with schema validation.

LLM-generated component (Claude Opus 5.5).
See prompts/prompts_log.md, prompt P1.

Two modes:
  --validate-only : check saved extraction JSON files against the schema
                    (no API call, no key needed)
  default         : send each design document to an LLM API using
                    prompts/extraction_prompt.md, validate the reply, retry
                    once on invalid JSON, and save it under
                    extracted_api/<model>/run<N>/ (never over extracted/)

Provider is chosen with LLM_PROVIDER = gemini | anthropic, the model with
LLM_MODEL (required, no default), and the key with GEMINI_API_KEY or
ANTHROPIC_API_KEY, read from a local .env file that is never committed.
Gemini runs at temperature 0. The Anthropic SDK (v2.x) has no temperature
argument, so it runs at the model's default.
"""
import argparse
import json
import os
import re
from pathlib import Path

ALLOWED_TYPES = {"gateway", "frontend", "service", "datastore", "cache", "queue",
                 "config", "load_generator"}
SYSTEMS = {"online_boutique": "data/docs/online_boutique.md",
           "astronomy_shop": "data/docs/astronomy_shop.md"}


def validate(obj):
    """Return a list of schema problems (empty list = valid)."""
    errs = []
    comps = obj.get("components")
    deps = obj.get("dependencies")
    if not isinstance(comps, list) or not comps:
        return ["missing or empty 'components'"]
    if not isinstance(deps, list):
        return ["missing 'dependencies'"]
    ids = [c.get("id") for c in comps]
    if len(ids) != len(set(ids)):
        errs.append("duplicate component ids")
    for c in comps:
        if c.get("type") not in ALLOWED_TYPES:
            errs.append(f"{c.get('id')}: bad type {c.get('type')!r}")
        if not isinstance(c.get("stateful"), bool):
            errs.append(f"{c.get('id')}: 'stateful' must be true/false")
    seen = set()
    for d in deps:
        s, t = d.get("source"), d.get("target")
        if s not in ids or t not in ids:
            errs.append(f"edge {s}->{t} references an unknown component")
        if s == t:
            errs.append(f"self-loop on {s}")
        if (s, t) in seen:
            errs.append(f"duplicate edge {s}->{t}")
        seen.add((s, t))
        if d.get("evidence") not in {"explicit", "implied"}:
            errs.append(f"edge {s}->{t}: evidence must be explicit|implied")
        if len(str(d.get("reason", "")).split()) > 15:
            errs.append(f"edge {s}->{t}: reason longer than 15 words")
    return errs


def make_gemini_client():
    from google import genai
    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def make_anthropic_client():
    import anthropic
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def call_llm(prompt):
    """Send one prompt to the configured provider. Returns (reply_text, model)."""
    provider = os.getenv("LLM_PROVIDER")
    model = os.getenv("LLM_MODEL")
    if not provider or not model:
        raise SystemExit("Set LLM_PROVIDER (gemini or anthropic) and LLM_MODEL in .env. "
                         "Use a model name your API key can access.")
    if provider == "gemini":
        from google.genai import types
        client = make_gemini_client()
        r = client.models.generate_content(
            model=model, contents=prompt,
            config=types.GenerateContentConfig(temperature=0,
                                               response_mime_type="application/json"))
        return r.text, model
    if provider == "anthropic":
        # The Anthropic SDK (v2.x) has no temperature argument; the model's
        # default sampling is used, so repeat runs measure its variability.
        client = make_anthropic_client()
        r = client.messages.create(model=model, max_tokens=8000,
                                   messages=[{"role": "user", "content": prompt}])
        return "".join(b.text for b in r.content if b.type == "text"), model
    raise SystemExit(f"Unknown LLM_PROVIDER {provider!r}; use gemini or anthropic.")


def parse_json(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("no JSON object in reply")
    return json.loads(m.group(0))


def build_prompt(doc_path, prompt_path="prompts/extraction_prompt.md"):
    template = Path(prompt_path).read_text().split("\n---\n", 1)[1]
    return template.replace("{DOCUMENT}", Path(doc_path).read_text())


def extract(key, doc_path, out_dir, llm=call_llm):
    prompt = build_prompt(doc_path)
    for attempt in (1, 2):
        text, model = llm(prompt)
        try:
            obj = parse_json(text)
            errs = validate(obj)
        except (ValueError, json.JSONDecodeError) as e:
            errs = [str(e)]
        if not errs:
            break
        print(f"  attempt {attempt} invalid: {errs[:3]}")
        prompt += "\n\nYour previous reply was invalid: " + "; ".join(errs[:5]) + \
                  ". Return corrected JSON only."
    else:
        raise RuntimeError(f"{key}: extraction failed validation twice")
    obj.update({"llm": model, "prompt": "prompts/extraction_prompt.md v1", "input": doc_path,
                "attempts": attempt})
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    Path(out_dir, f"{key}.json").write_text(json.dumps(obj, indent=2))
    return obj


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--validate-only", action="store_true",
                    help="check saved JSON in --dir against the schema, no API call")
    ap.add_argument("--dir", default=None,
                    help="where to read (validate) or write (extract). Default: extracted/ "
                         "for validation, extracted_api/<model>/run<N>/ for new runs")
    ap.add_argument("--run", type=int, default=1, help="run number, for repeat runs")
    a = ap.parse_args()
    if a.validate_only:
        d = a.dir or "extracted"
        for key in SYSTEMS:
            obj = json.loads(Path(d, f"{key}.json").read_text())
            errs = validate(obj)
            print(f"{key}: {len(obj['components'])} components, "
                  f"{len(obj['dependencies'])} dependencies -> "
                  f"{'VALID' if not errs else errs}")
    else:
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        out = a.dir or f"extracted_api/{os.getenv('LLM_MODEL', 'model')}/run{a.run}"
        if Path(out).resolve() == Path("extracted").resolve():
            raise SystemExit("Refusing to overwrite extracted/ (the saved v1 extraction).")
        for key, doc in SYSTEMS.items():
            o = extract(key, doc, out)
            print(f"{key}: {len(o['components'])} components, "
                  f"{len(o['dependencies'])} dependencies -> {out}/{key}.json")
