"""Build a name-blind copy of the Online Boutique design document.

LLM-generated component (Claude Opus 5.5). See prompts/prompts_log.md.

Purpose: test whether the LLM extracts the architecture by reading the text
or by recognising a famous app. Every service name is replaced by a neutral
code (svc-01 ... svc-11), the app name becomes "System X", and the three
promotional lines that name Google or the repository are dropped. Service
descriptions are kept word for word, so the document carries the same
dependency information. Technology names that are not service names (Redis,
gRPC, Locust) are kept.

Writes data/docs/online_boutique_anon.md and data/anon_map.json
(code -> real deployment name), used later to score the blind runs.
"""
import json
import random
import re
from pathlib import Path

SERVICES = ["frontend", "cartservice", "productcatalogservice", "currencyservice",
            "paymentservice", "shippingservice", "emailservice", "checkoutservice",
            "recommendationservice", "adservice", "loadgenerator"]
DROP_LINE_IF = ("Google", "Googlers", "Star**")
SEED = 7


def make_map(seed=SEED):
    order = SERVICES[:]
    random.Random(seed).shuffle(order)
    return {f"svc-{i + 1:02d}": name for i, name in enumerate(order)}


def anonymize(text, code_map):
    real_to_code = {v: k for k, v in code_map.items()}
    lines = [ln for ln in text.splitlines() if not any(w in ln for w in DROP_LINE_IF)]
    out = "\n".join(lines)
    out = out.replace("Online Boutique", "System X")
    # markdown links like [cartservice](/src/cartservice) -> svc-NN
    out = re.sub(r"\[([a-z]+)\]\(/src/[a-z]+\)",
                 lambda m: real_to_code.get(m.group(1), m.group(0)), out)
    # any remaining whole-word service name, e.g. "to the frontend"
    for name in sorted(SERVICES, key=len, reverse=True):
        out = re.sub(rf"\b{name}\b", real_to_code[name], out)
    return out + "\n"


if __name__ == "__main__":
    code_map = make_map()
    src = Path("data/docs/online_boutique.md").read_text()
    anon = anonymize(src, code_map)
    Path("data/docs/online_boutique_anon.md").write_text(anon)
    Path("data/anon_map.json").write_text(json.dumps(code_map, indent=2))
    leaks = [s for s in SERVICES if re.search(rf"\b{s}\b", anon)]
    print(f"{len(code_map)} services coded, {len(anon.split())} words, leaks: {leaks or 'none'}")
