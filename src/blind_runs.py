"""Score the blind extraction runs: accuracy, run-to-run variability,
the name-blind test, and the effect on the risk ranking.

LLM-generated component (Claude Opus 5.5). See prompts/prompts_log.md.

Inputs : extracted/ (v1), extracted_blind/run1..3, extracted_blind/anon_run1..3
Outputs: extracted_blind/anon_run*_decoded/, results/blind_runs.json,
         figures/blind_runs.png
"""
import json
import re
import statistics as st
from itertools import combinations
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import build_graph as bg
import evaluate_extraction as ev

RUNS = ["run1", "run2", "run3"]
ANON = ["anon_run1", "anon_run2", "anon_run3"]
SYSTEMS = ["online_boutique", "astronomy_shop"]
ROOT = Path(".")


def decode(obj, code_map):
    """Replace svc-NN codes with real service names (case-insensitive)."""
    lut = {k.lower(): v for k, v in code_map.items()}
    fix = lambda n: lut.get(str(n).strip().lower(), n)
    out = json.loads(json.dumps(obj))
    for c in out["components"]:
        c["id"] = fix(c["id"])
    for d in out["dependencies"]:
        d["source"], d["target"] = fix(d["source"]), fix(d["target"])
    return out


def leftover_codes(obj):
    ids = [c["id"] for c in obj["components"]]
    return [i for i in ids if re.fullmatch(r"svc-\d+", str(i).lower())]


def edge_set(key, folder):
    ext = json.loads((ROOT / folder / f"{key}.json").read_text())
    return {(ev.canonical(key, d["source"]), ev.canonical(key, d["target"]))
            for d in ext["dependencies"]}


def jaccard(a, b):
    return len(a & b) / len(a | b) if a | b else 1.0


def run_metrics(key, folder):
    r = ev.evaluate(key, ROOT, extracted_dir=folder)
    ge, gt = bg.load_graphs(key, ROOT, extracted_dir=folder)
    agr = bg.agreement(bg.dependents(gt), bg.dependents(ge))
    imp_ok, imp_n = map(int, r["implied_edges_correct"].split("/"))
    out = {
        "node_f1": r["nodes"]["f1"],
        "edge_precision": r["edges_all"]["precision"],
        "edge_recall": r["edges_all"]["recall"],
        "edge_f1": r["edges_all"]["f1"],
        "explicit_recall": r["edges_explicit_only"]["recall"],
        "implied_correct": imp_ok, "implied_total": imp_n,
        "n_edges": r["edges_all"]["pred"],
        "missed_edges": r["missed_edges"], "invented_edges": r["invented_edges"],
        "rank_spearman_vs_truth": agr["spearman"],
    }
    if key == "astronomy_shop":
        out["flagd_dependents"] = bg.dependents(ge).get("flagd")
    return out


def summary(rows, field):
    vals = [r[field] for r in rows]
    return {"mean": round(st.mean(vals), 3), "sd": round(st.stdev(vals), 3) if len(vals) > 1 else 0.0,
            "min": min(vals), "max": max(vals)}


def consistency(key, folders):
    sets = [edge_set(key, f) for f in folders]
    pair = [jaccard(a, b) for a, b in combinations(sets, 2)]
    return {"edges_in_every_run": len(set.intersection(*sets)),
            "edges_in_any_run": len(set.union(*sets)),
            "mean_pairwise_jaccard": round(st.mean(pair), 3)}


def draw(res, path):
    rows = [("Online Boutique · v1 run", res["online_boutique"]["v1"], "#898781"),
            ("Online Boutique · blind", res["online_boutique"]["blind_runs"], "#2a78d6"),
            ("Online Boutique · names hidden", res["online_boutique"]["anon_runs"], "#eb6834"),
            ("Astronomy Shop · v1 run", res["astronomy_shop"]["v1"], "#898781"),
            ("Astronomy Shop · blind", res["astronomy_shop"]["blind_runs"], "#2a78d6")]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
    for ax, field, title in [(axes[0], "edge_recall", "Edge recall: real dependencies found"),
                             (axes[1], "edge_precision", "Edge precision: found dependencies that are real")]:
        for i, (label, runs, color) in enumerate(rows):
            runs = runs if isinstance(runs, list) else [runs]
            xs = [r[field] for r in runs]
            ys = [len(rows) - 1 - i + (j - (len(xs) - 1) / 2) * 0.22 for j in range(len(xs))]
            ax.scatter(xs, ys, s=70, color=color, edgecolors="#fcfcfb", linewidths=2, zorder=3)
        ax.set_xlim(0.5, 1.03)
        ax.set_title(title, loc="left", fontsize=11.5, color="#0b0b0b")
        ax.xaxis.grid(True, color="#e6e5e0", linewidth=0.8)
        ax.set_axisbelow(True)
    axes[0].set_yticks(range(len(rows)), [r[0] for r in reversed(rows)])
    fig.suptitle("Each dot is one extraction. Blind runs saw only the prompt and the document.",
                 x=0.01, ha="left", fontsize=14, color="#0b0b0b")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main():
    code_map = json.loads((ROOT / "data" / "anon_map.json").read_text())
    for a in ANON:
        raw = json.loads((ROOT / "extracted_blind" / a / "online_boutique.json").read_text())
        dec = decode(raw, code_map)
        assert not leftover_codes(dec), f"{a}: undecoded ids {leftover_codes(dec)}"
        d = ROOT / "extracted_blind" / f"{a}_decoded"
        d.mkdir(exist_ok=True)
        (d / "online_boutique.json").write_text(json.dumps(dec, indent=2))

    res = {}
    for key in SYSTEMS:
        blind = [run_metrics(key, f"extracted_blind/{r}") for r in RUNS]
        res[key] = {
            "v1": run_metrics(key, "extracted"),
            "blind_runs": blind,
            "blind_summary": {f: summary(blind, f) for f in
                              ["node_f1", "edge_precision", "edge_recall", "edge_f1",
                               "explicit_recall", "rank_spearman_vs_truth"]},
            "blind_consistency": consistency(key, [f"extracted_blind/{r}" for r in RUNS]),
        }
        if key == "astronomy_shop":
            res[key]["blind_summary"]["flagd_dependents"] = summary(blind, "flagd_dependents")
    anon = [run_metrics("online_boutique", f"extracted_blind/{a}_decoded") for a in ANON]
    res["online_boutique"]["anon_runs"] = anon
    res["online_boutique"]["anon_summary"] = {f: summary(anon, f) for f in
                                              ["node_f1", "edge_precision", "edge_recall", "edge_f1"]}
    res["online_boutique"]["anon_consistency"] = consistency(
        "online_boutique", [f"extracted_blind/{a}_decoded" for a in ANON])

    Path("results").mkdir(exist_ok=True)
    Path("results/blind_runs.json").write_text(json.dumps(res, indent=2))
    draw(res, "figures/blind_runs.png")
    for key in SYSTEMS:
        print(f"\n{key}")
        print("  v1          ", {k: res[key]["v1"][k] for k in ("edge_precision", "edge_recall", "edge_f1")})
        for name, rows in [("blind", res[key]["blind_runs"])] + (
                [("names hidden", res[key]["anon_runs"])] if key == "online_boutique" else []):
            for i, r in enumerate(rows, 1):
                print(f"  {name} {i}".ljust(16), {k: r[k] for k in ("edge_precision", "edge_recall", "edge_f1",
                                                                    "explicit_recall", "rank_spearman_vs_truth")},
                      "missed", r["missed_edges"], "invented", r["invented_edges"],
                      f"implied {r['implied_correct']}/{r['implied_total']}",
                      ("flagd " + str(r["flagd_dependents"])) if "flagd_dependents" in r else "")
        print("  consistency  ", res[key]["blind_consistency"])
    print("  anon consistency", res["online_boutique"]["anon_consistency"])


if __name__ == "__main__":
    main()
