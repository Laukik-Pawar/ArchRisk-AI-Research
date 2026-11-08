"""Graph builder, statistics, risk labels, agreement analysis and figures.

LLM-generated component (Claude Opus 5.5). See prompts/prompts_log.md.

For each system it builds two directed graphs (edge = consumer -> provider):
  * extracted : from the LLM extraction (explicit + implied edges)
  * truth     : from the deployment config files
and computes
  * basic stats: nodes, edges, density, in/out degree distribution, longest
    chain, cycles
  * dependents(v): number of other components that transitively depend on v
  * failure impact(v) = dependents(v) / (N - 1), the simulation label, which
    assumes every dependency is HARD (consumer fails if provider fails)
  * the assignment's composite score: 0.4 in-degree + 0.2 out-degree
    + 0.4 betweenness, each min-max normalised (comparison only, never a
    model input)
  * agreement between rankings: Spearman, Kendall tau-b and a tie-aware
    top-5 overlap
  * a soft-dependency check (Astronomy Shop): impact recomputed after removing
    the edges that source code or the OpenFeature spec show to be soft
    (data/soft_dependencies.json)
"""
import json
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from scipy.stats import kendalltau, spearmanr

from evaluate_extraction import canonical

SYSTEMS = {"online_boutique": "Online Boutique",
           "astronomy_shop": "OpenTelemetry Astronomy Shop"}
TOP_K = 5

BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, INK2, MUTED, SURFACE, GRID = "#0b0b0b", "#52514e", "#898781", "#fcfcfb", "#e6e5e0"
SEQ = LinearSegmentedColormap.from_list(
    "seq", ["#cde2fb", "#86b6ef", "#3987e5", "#256abf", "#184f95", "#0d366b"])

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": MUTED,
    "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.dpi": 200,
})


# ------------------------------------------------------------------ analysis
def load_graphs(key, root=Path("."), extracted_dir="extracted"):
    ext = json.loads((root / extracted_dir / f"{key}.json").read_text())
    gt = json.loads((root / "data" / "ground_truth" / f"{key}.json").read_text())
    c = lambda n: canonical(key, n)
    ge = nx.DiGraph()
    for comp in ext["components"]:
        ge.add_node(c(comp["id"]), type=comp["type"], stateful=comp["stateful"])
    for d in ext["dependencies"]:
        ge.add_edge(c(d["source"]), c(d["target"]), evidence=d["evidence"])
    gtg = nx.DiGraph()
    gtg.add_nodes_from(gt["nodes"])
    gtg.add_edges_from(tuple(e) for e in gt["edges"])
    return ge, gtg


def dependents(g):
    """Number of other nodes that transitively depend on each node."""
    return {v: len(nx.ancestors(g, v)) for v in g}


def failure_impact(g):
    n = g.number_of_nodes()
    return {v: d / (n - 1) for v, d in dependents(g).items()}


def composite(g):
    def norm(d):
        lo, hi = min(d.values()), max(d.values())
        return {k: (x - lo) / (hi - lo) if hi > lo else 0.0 for k, x in d.items()}
    ind, outd = norm(dict(g.in_degree())), norm(dict(g.out_degree()))
    bet = norm(nx.betweenness_centrality(g))
    return {v: 0.4 * ind[v] + 0.2 * outd[v] + 0.4 * bet[v] for v in g}


def top_k_with_ties(scores, k=TOP_K):
    """All nodes scoring at least the k-th highest score (ties included)."""
    if not scores:
        return set()
    vals = sorted(scores.values(), reverse=True)
    cut = vals[min(k, len(vals)) - 1]
    return {n for n, s in scores.items() if s >= cut}


def agreement(a, b, nodes=None):
    """Rank agreement between two score dicts over shared nodes."""
    nodes = sorted(nodes or (set(a) & set(b)))
    x, y = [a[n] for n in nodes], [b[n] for n in nodes]
    ta, tb = top_k_with_ties({n: a[n] for n in nodes}), top_k_with_ties({n: b[n] for n in nodes})
    return {
        "n_nodes": len(nodes),
        "spearman": round(float(spearmanr(x, y).statistic), 3),
        "kendall_tau_b": round(float(kendalltau(x, y).statistic), 3),
        "top5_a": sorted(ta), "top5_b": sorted(tb),
        "top5_jaccard": round(len(ta & tb) / len(ta | tb), 3),
    }


def load_soft_edges(key, root=Path(".")):
    p = root / "data" / "soft_dependencies.json"
    if not p.exists():
        return set()
    d = json.loads(p.read_text())
    if d["system"] != key:
        return set()
    return {tuple(e) for grp in d["groups"] for e in grp["edges"]}


def hard_only(g, soft):
    h = g.copy()
    h.remove_edges_from([e for e in soft if h.has_edge(*e)])
    return h


def canonical_cycles(g):
    """Cycles in a run-independent form: each rotated to start at its
    alphabetically first node, then sorted. (networkx's starting node depends
    on Python's per-run string hashing.)"""
    out = []
    for c in nx.simple_cycles(g):
        i = c.index(min(c))
        out.append(c[i:] + c[:i])
    return sorted(out)


def stats(g):
    ind, outd = dict(g.in_degree()), dict(g.out_degree())
    return {
        "nodes": g.number_of_nodes(), "edges": g.number_of_edges(),
        "density": round(nx.density(g), 3),
        "mean_out_degree": round(float(np.mean(list(outd.values()))), 2),
        "max_in_degree": max(ind.values()),
        "max_in_degree_node": max(ind, key=ind.get),
        "max_out_degree": max(outd.values()),
        "max_out_degree_node": max(outd, key=outd.get),
        "in_degree_distribution": {int(k): int(v) for k, v in sorted(pd.Series(ind).value_counts().items())},
        "out_degree_distribution": {int(k): int(v) for k, v in sorted(pd.Series(outd).value_counts().items())},
        "longest_dependency_chain": nx.dag_longest_path_length(nx.condensation(g)),
        "cycles": canonical_cycles(g),
        "weakly_connected_components": nx.number_weakly_connected_components(g),
    }


# ------------------------------------------------------------------ figures
def dot_layout(g):
    """Layered layout from Graphviz `dot` (consumers on top, providers below)."""
    lines = ["digraph G { rankdir=TB; nodesep=0.5; ranksep=0.9;"]
    lines += [f'"{n}";' for n in g]
    lines += [f'"{u}" -> "{v}";' for u, v in g.edges()]
    lines.append("}")
    out = subprocess.run(["dot", "-Tplain"], input="\n".join(lines),
                         capture_output=True, text=True, check=True).stdout
    pos = {}
    for line in out.splitlines():
        p = line.split()
        if p[0] == "node":
            pos[p[1].strip('"')] = (float(p[2]), float(p[3]))
    return pos


def draw_graph(g, impact, title, path, missing=()):
    pos = dot_layout(g)
    fig, ax = plt.subplots(figsize=(12, 7.2))
    missing = set(missing)
    kw = dict(ax=ax, arrowsize=12, node_size=1600, connectionstyle="arc3,rad=0.06")
    nx.draw_networkx_edges(g, pos, edgelist=[e for e in g.edges() if e not in missing],
                           edge_color="#b9b8b2", width=1.2, **kw)
    if missing:
        nx.draw_networkx_edges(g, pos, edgelist=list(missing), edge_color=ORANGE,
                               width=1.6, style="dashed", **kw)
    nx.draw_networkx_nodes(g, pos, ax=ax, node_color=[impact[n] for n in g], cmap=SEQ,
                           vmin=0, vmax=1, node_size=[700 + 2600 * impact[n] for n in g],
                           edgecolors=SURFACE, linewidths=2)
    for n, (x, y) in pos.items():
        ax.annotate(n, (x, y), xytext=(0, -24 - 22 * impact[n]), textcoords="offset points",
                    ha="center", va="top", fontsize=9, color=INK)
    sm = plt.cm.ScalarMappable(cmap=SEQ, norm=plt.Normalize(0, 1))
    cb = fig.colorbar(sm, ax=ax, shrink=0.55, pad=0.01)
    cb.set_label("Simulated failure impact (all dependencies hard)", color=INK2)
    cb.outline.set_visible(False)
    handles = [Line2D([0], [0], color="#b9b8b2", lw=1.4, label="Dependency found by the LLM")]
    if missing:
        handles.append(Line2D([0], [0], color=ORANGE, lw=1.6, ls="--",
                              label=f"Dependency the LLM missed ({len(missing)})"))
    ax.legend(handles=handles, frameon=False, loc="upper left", fontsize=10)
    ax.set_title(title, loc="left", fontsize=14, color=INK, pad=12)
    ax.axis("off")
    ax.margins(0.08)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _grid(ax, axis):
    getattr(ax, f"{axis}axis").grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def draw_degree(all_stats, path):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for ax, (key, label) in zip(axes, SYSTEMS.items()):
        s = all_stats[key]["truth"]
        ind, outd = s["in_degree_distribution"], s["out_degree_distribution"]
        ks = range(0, max(max(ind), max(outd)) + 1)
        x, w = np.arange(len(ks)), 0.38
        ax.bar(x - w / 2 - 0.01, [ind.get(k, 0) for k in ks], w, color=BLUE, label="In-degree (used by)")
        ax.bar(x + w / 2 + 0.01, [outd.get(k, 0) for k in ks], w, color=ORANGE, label="Out-degree (depends on)")
        ax.set_xticks(x, [str(k) for k in ks])
        ax.set_xlabel("Degree")
        ax.set_title(f"{label}  ({s['nodes']} nodes, {s['edges']} edges)", loc="left",
                     fontsize=11.5, color=INK)
        _grid(ax, "y")
    axes[0].set_ylabel("Number of components")
    axes[0].legend(frameon=False, loc="upper right")
    fig.suptitle("Degree distribution of the true dependency graphs", x=0.01, ha="left",
                 fontsize=14, color=INK)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def draw_paired_bars(df, col_a, col_b, label_a, label_b, title, xlabel, path, top=12):
    d = df.sort_values([col_a, col_b], ascending=True).tail(top)
    y, h = np.arange(len(d)), 0.38
    fig, ax = plt.subplots(figsize=(9, 5.6))
    ax.barh(y + h / 2 + 0.01, d[col_a], h, color=BLUE, label=label_a)
    ax.barh(y - h / 2 - 0.01, d[col_b].fillna(0), h, color=ORANGE, label=label_b)
    ax.set_yticks(y, d.index)
    ax.set_xlabel(xlabel)
    ax.xaxis.get_major_locator().set_params(integer=True)
    _grid(ax, "x")
    ax.legend(frameon=False, loc="lower right")
    ax.set_title(title, loc="left", fontsize=13, color=INK)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def draw_composite_vs_impact(frames, path):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharex=True, sharey=True)
    for ax, (key, label) in zip(axes, SYSTEMS.items()):
        d = frames[key]
        ax.scatter(d["composite_truth"], d["impact_truth"], s=70, color=BLUE,
                   edgecolors=SURFACE, linewidths=2, zorder=3)
        lab = set(d["impact_truth"].nlargest(3).index) | set(d["composite_truth"].nlargest(3).index)
        placed = []
        for n in sorted(lab, key=lambda n: (d.loc[n, "impact_truth"], d.loc[n, "composite_truth"])):
            x, y = d.loc[n, "composite_truth"], d.loc[n, "impact_truth"]
            dy = 4 - 14 * sum(abs(px - x) < 0.12 and abs(py - y) < 0.03 for px, py in placed)
            placed.append((x, y))
            ax.annotate(n, (x, y), xytext=(6, dy), textcoords="offset points", fontsize=9, color=INK)
        rho = spearmanr(d["composite_truth"], d["impact_truth"]).statistic
        ax.set_title(f"{label}   Spearman = {rho:.2f}", loc="left", fontsize=11.5, color=INK)
        ax.set_xlabel("Composite score (0.4 in-deg + 0.2 out-deg + 0.4 betweenness)")
        ax.grid(True, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        ax.set_xlim(-0.03, 0.6)
        ax.set_ylim(-0.03, 0.7)
    axes[0].set_ylabel("Simulated failure impact")
    fig.suptitle("The assignment's composite formula barely agrees with simulated failure impact",
                 x=0.01, ha="left", fontsize=14, color=INK)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


# ------------------------------------------------------------------ main
def analyse(key):
    ge, gt = load_graphs(key)
    dt, de = dependents(gt), dependents(ge)
    df = pd.DataFrame({
        "type": pd.Series(nx.get_node_attributes(ge, "type")),
        "in_degree_truth": pd.Series(dict(gt.in_degree())),
        "out_degree_truth": pd.Series(dict(gt.out_degree())),
        "dependents_truth": pd.Series(dt),
        "dependents_extracted": pd.Series(de),
        "impact_truth": pd.Series(failure_impact(gt)),
        "impact_extracted": pd.Series(failure_impact(ge)),
        "composite_truth": pd.Series(composite(gt)),
    })
    result = {
        "extracted_vs_truth_dependents": agreement(dt, de),
        "composite_vs_impact_truth": agreement(composite(gt), failure_impact(gt)),
    }
    soft = load_soft_edges(key)
    if soft:
        missing_soft = [e for e in soft if not gt.has_edge(*e)]
        assert not missing_soft, f"soft edges not in truth graph: {missing_soft}"
        gh = hard_only(gt, soft)
        df["dependents_hard_only"] = pd.Series(dependents(gh))
        df["impact_hard_only"] = pd.Series(failure_impact(gh))
        result["soft_edges_removed"] = len(soft)
        result["all_hard_vs_code_verified"] = agreement(dt, dependents(gh))
    df = df.sort_values(["dependents_truth", "composite_truth"], ascending=False)
    missing = [e for e in gt.edges() if not ge.has_edge(*e)]
    return ge, gt, df, result, missing


def main():
    Path("results").mkdir(exist_ok=True)
    Path("figures").mkdir(exist_ok=True)
    all_stats, results, frames = {}, {}, {}
    for key, label in SYSTEMS.items():
        ge, gt, df, res, missing = analyse(key)
        all_stats[key] = {"extracted": stats(ge), "truth": stats(gt)}
        results[key] = res
        frames[key] = df
        df.round(3).to_csv(f"results/risk_scores_{key}.csv", index_label="component")
        draw_graph(gt, df["impact_truth"].to_dict(),
                   f"{label}: true dependency graph, coloured by simulated failure impact",
                   f"figures/graph_{key}.png", missing)
        draw_paired_bars(df, "dependents_truth", "dependents_extracted",
                         "True graph (config files)", "LLM-extracted graph",
                         f"{label}: dependents per component, extracted vs. true",
                         "Number of components that transitively depend on it",
                         f"figures/impact_compare_{key}.png")
        if "dependents_hard_only" in df:
            draw_paired_bars(df, "dependents_truth", "dependents_hard_only",
                             "All dependencies treated as hard", "Soft dependencies removed (code-verified)",
                             f"{label}: who really goes down?",
                             "Number of components that transitively depend on it",
                             f"figures/soft_vs_hard_{key}.png")
    draw_degree(all_stats, "figures/degree_distribution.png")
    draw_composite_vs_impact(frames, "figures/composite_vs_impact.png")
    Path("results/graph_stats.json").write_text(json.dumps(all_stats, indent=2))
    Path("results/ranking_agreement.json").write_text(json.dumps(results, indent=2))
    for key in SYSTEMS:
        t, e = all_stats[key]["truth"], all_stats[key]["extracted"]
        print(f"\n{SYSTEMS[key]}")
        print(f"  truth    : {t['nodes']} nodes, {t['edges']} edges, density {t['density']}, "
              f"max in-degree {t['max_in_degree']} ({t['max_in_degree_node']}), "
              f"longest chain {t['longest_dependency_chain']}, cycles {t['cycles']}")
        print(f"  extracted: {e['nodes']} nodes, {e['edges']} edges, "
              f"max in-degree {e['max_in_degree']} ({e['max_in_degree_node']})")
        print("  " + json.dumps(results[key]))
        print(frames[key].round(3).head(8).to_string())


if __name__ == "__main__":
    main()
