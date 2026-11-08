"""Score LLM-extracted graphs against ground-truth config graphs.

LLM-generated component (Claude Opus 5.5), see prompts/prompts_log.md P3.
Reports node and edge precision / recall / F1, both
for explicit-only edges and for explicit + implied edges, and lists every
missed and invented edge for the validation log.

Name resolution: the LLM uses the names written in the documents, the config
files use deployment names. A small alias table (below) maps one to the other.
It only renames; it never adds or removes a component.
"""
import json
from pathlib import Path

ALIASES = {
    "online_boutique": {"redis": "redis-cart"},
    "astronomy_shop": {"valkey": "valkey-cart", "postgresql": "astronomy-db",
                       "postgres": "astronomy-db", "featureflagservice": "flagd"},
}


def canonical(key, name):
    """Lowercase, trim, then apply the rename-only alias table."""
    n = str(name).strip().lower()
    return ALIASES.get(key, {}).get(n, n)


def prf(pred, true):
    tp = len(pred & true)
    p = tp / len(pred) if pred else 0.0
    r = tp / len(true) if true else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return {"tp": tp, "pred": len(pred), "true": len(true),
            "precision": round(p, 3), "recall": round(r, 3), "f1": round(f, 3)}


def evaluate(key, root=Path("."), extracted_dir="extracted"):
    ext = json.loads((root / extracted_dir / f"{key}.json").read_text())
    gt = json.loads((root / "data" / "ground_truth" / f"{key}.json").read_text())
    canon = lambda n: canonical(key, n)

    pred_nodes = {canon(c["id"]) for c in ext["components"]}
    true_nodes = set(gt["nodes"])
    true_edges = {tuple(e) for e in gt["edges"]}
    all_edges = {(canon(d["source"]), canon(d["target"])) for d in ext["dependencies"]}
    explicit = {(canon(d["source"]), canon(d["target"]))
                for d in ext["dependencies"] if d["evidence"] == "explicit"}
    implied = all_edges - explicit

    return {
        "system": gt["system"],
        "nodes": prf(pred_nodes, true_nodes),
        "edges_explicit_only": prf(explicit, true_edges),
        "edges_all": prf(all_edges, true_edges),
        "implied_edges_correct": f"{len(implied & true_edges)}/{len(implied)}",
        "missed_nodes": sorted(true_nodes - pred_nodes),
        "invented_nodes": sorted(pred_nodes - true_nodes),
        "missed_edges": sorted(true_edges - all_edges),
        "invented_edges": sorted(all_edges - true_edges),
    }


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--extracted", default="extracted", help="folder with <system>.json files")
    ap.add_argument("--out", default="results/extraction_eval.json")
    a = ap.parse_args()
    out = {k: evaluate(k, extracted_dir=a.extracted) for k in ["online_boutique", "astronomy_shop"]}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=2))
    print(f"Extraction from {a.extracted}/ scored -> {a.out}")
    for k, r in out.items():
        print(f"\n{r['system']}")
        print("  nodes            ", r["nodes"])
        print("  edges explicit   ", r["edges_explicit_only"])
        print("  edges all        ", r["edges_all"])
        print("  implied correct  ", r["implied_edges_correct"])
        print("  missed nodes     ", r["missed_nodes"])
        print("  invented nodes   ", r["invented_nodes"])
        print("  missed edges     ", r["missed_edges"])
        print("  invented edges   ", r["invented_edges"])
