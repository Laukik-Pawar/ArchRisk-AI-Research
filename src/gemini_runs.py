"""Second-model check: run the same extraction with Gemini and score it.

LLM-generated component (Claude Opus 5.5). See prompts/prompts_log.md.

Runs the v1 prompt through Gemini three times on each document, plus three
times on the name-blind Online Boutique document, then scores every run the
same way as the Claude blind runs.

Usage (from the project folder, with your key only in the environment):
    macOS / Linux : GEMINI_API_KEY=your-key python src/gemini_runs.py
    Windows (PS)  : $env:GEMINI_API_KEY="your-key"; python src/gemini_runs.py

Without --model, the script lists the models your key can use and picks a
Flash model from that list (it prints the list and its choice). The key is
read from the environment and never written to disk.

Outputs: extracted_api/<model>/run1..3, anon_run1..3 (+ _decoded),
         results/gemini_runs.json
"""
import argparse
import json
import os
import time
from pathlib import Path

import blind_runs as br
import extractor as ex

DOCS = {"online_boutique": "data/docs/online_boutique.md",
        "astronomy_shop": "data/docs/astronomy_shop.md"}
ANON_DOC = "data/docs/online_boutique_anon.md"
SKIP_WORDS = ("lite", "image", "tts", "live", "audio", "embedding", "thinking")


def available_models(client):
    """Model ids (without the 'models/' prefix) that support generateContent."""
    out = []
    for m in client.models.list():
        if "generateContent" in (getattr(m, "supported_actions", None) or []):
            out.append(m.name.split("/")[-1])
    return out


def pick_model(names):
    """Highest-sorting Flash model, skipping lite, image, audio and similar variants."""
    flash = sorted(n for n in names if "flash" in n and not any(w in n for w in SKIP_WORDS))
    return flash[-1] if flash else None


def extract_with_retry(key, doc, out_dir, sleep):
    for attempt in (1, 2):
        try:
            return ex.extract(key, doc, out_dir)
        except Exception as e:      # rate limits or two invalid replies
            if attempt == 2:
                raise
            print(f"    {type(e).__name__}: {str(e)[:120]} -> retrying in {sleep * 6:.0f}s")
            time.sleep(sleep * 6)


def score(folders, key):
    rows = [br.run_metrics(key, f) for f in folders]
    fields = ["node_f1", "edge_precision", "edge_recall", "edge_f1", "rank_spearman_vs_truth"]
    return {"runs": rows,
            "summary": {f: br.summary(rows, f) for f in fields},
            "consistency": br.consistency(key, folders) if len(folders) > 1 else None}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", help="Gemini model id; default: picked from your key's model list")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--sleep", type=float, default=5.0, help="seconds between API calls")
    ap.add_argument("--out-root", default="extracted_api")
    ap.add_argument("--results", default="results/gemini_runs.json")
    a = ap.parse_args(argv)

    if not os.getenv("GEMINI_API_KEY"):
        raise SystemExit("Set GEMINI_API_KEY in your terminal first (see the top of this file).")
    names = available_models(ex.make_gemini_client())
    model = a.model or pick_model(names)
    print(f"Models your key can use for text: {', '.join(names) or 'none found'}")
    if not model:
        raise SystemExit("No suitable Flash model found. Rerun with --model <one of the names above>.")
    print(f"Using model: {model}")
    os.environ["LLM_PROVIDER"], os.environ["LLM_MODEL"] = "gemini", model

    base = Path(a.out_root) / model
    code_map = json.loads(Path("data/anon_map.json").read_text())
    named, anon = [], []
    for r in range(1, a.runs + 1):
        for key, doc in DOCS.items():
            out = base / f"run{r}"
            print(f"  run {r}: {key}")
            extract_with_retry(key, doc, out, a.sleep)
            time.sleep(a.sleep)
        named.append(str(base / f"run{r}"))
        print(f"  run {r}: online_boutique (names hidden)")
        raw_dir = base / f"anon_run{r}"
        extract_with_retry("online_boutique", ANON_DOC, raw_dir, a.sleep)
        dec = br.decode(json.loads((raw_dir / "online_boutique.json").read_text()), code_map)
        dec_dir = base / f"anon_run{r}_decoded"
        dec_dir.mkdir(parents=True, exist_ok=True)
        (dec_dir / "online_boutique.json").write_text(json.dumps(dec, indent=2))
        anon.append(str(dec_dir))
        time.sleep(a.sleep)

    res = {"model": model,
           "online_boutique": score(named, "online_boutique"),
           "online_boutique_names_hidden": score(anon, "online_boutique"),
           "astronomy_shop": score(named, "astronomy_shop")}
    Path(a.results).parent.mkdir(parents=True, exist_ok=True)
    Path(a.results).write_text(json.dumps(res, indent=2))

    print(f"\nGemini ({model}), mean ± sd over {a.runs} runs:")
    for name in ["online_boutique", "online_boutique_names_hidden", "astronomy_shop"]:
        s = res[name]["summary"]
        print(f"  {name:30s} precision {s['edge_precision']['mean']:.2f} ± {s['edge_precision']['sd']:.2f}"
              f"   recall {s['edge_recall']['mean']:.2f} ± {s['edge_recall']['sd']:.2f}"
              f"   F1 {s['edge_f1']['mean']:.2f} ± {s['edge_f1']['sd']:.2f}")
    print(f"Saved {a.results}. Send this file to Claude to add the comparison to the slides.")
    return res


if __name__ == "__main__":
    main()
