"""Every number quoted on the midterm slides, recomputed from the data.

If a result changes, the matching test fails, so the slides never drift away
from what the code produces. Values are recomputed from raw data and rounded
once, the way the slide shows them.
Run with the rest of the suite:  python -m pytest -v
"""
import json
import sys
from pathlib import Path

import networkx as nx
import pytest
from scipy.stats import kendalltau, spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import build_graph as bg            # noqa: E402
import evaluate_extraction as ev    # noqa: E402

pytestmark = pytest.mark.skipif(not (ROOT / "data" / "ground_truth" / "astronomy_shop.json").exists(),
                                reason="run `python run_all.py` first to build the ground truth")


def r2(x):
    return round(float(x), 2)


@pytest.fixture(scope="module")
def g():
    ob_e, ob_t = bg.load_graphs("online_boutique", ROOT)
    as_e, as_t = bg.load_graphs("astronomy_shop", ROOT)
    return {"ob_e": ob_e, "ob_t": ob_t, "as_e": as_e, "as_t": as_t}


@pytest.fixture(scope="module")
def blind():
    return json.loads((ROOT / "results" / "blind_runs.json").read_text())


def rho(a, b, nodes):
    nodes = sorted(nodes)
    return spearmanr([a[n] for n in nodes], [b[n] for n in nodes]).statistic


def test_slide4_data(g):
    assert (g["ob_t"].number_of_nodes(), g["ob_t"].number_of_edges()) == (12, 16)
    assert (g["as_t"].number_of_nodes(), g["as_t"].number_of_edges()) == (21, 37)
    assert len((ROOT / "data/docs/online_boutique.md").read_text().split()) == 352
    assert len((ROOT / "data/docs/astronomy_shop.md").read_text().split()) == 2090


def test_slide6_blind_accuracy(blind):
    ob, a = blind["online_boutique"]["blind_summary"], blind["astronomy_shop"]["blind_summary"]
    assert (r2(ob["edge_precision"]["mean"]), r2(ob["edge_precision"]["sd"])) == (1.00, 0.00)
    assert (r2(ob["edge_recall"]["mean"]), r2(ob["edge_recall"]["sd"])) == (0.96, 0.07)
    assert (r2(ob["edge_f1"]["mean"]), r2(ob["edge_f1"]["sd"])) == (0.98, 0.04)
    assert (r2(a["edge_precision"]["mean"]), r2(a["edge_precision"]["sd"])) == (0.96, 0.00)
    assert (r2(a["edge_recall"]["mean"]), r2(a["edge_recall"]["sd"])) == (0.69, 0.04)
    assert (r2(a["edge_f1"]["mean"]), r2(a["edge_f1"]["sd"])) == (0.80, 0.03)
    assert r2(blind["online_boutique"]["v1"]["edge_f1"]) == 1.00
    assert r2(blind["astronomy_shop"]["v1"]["edge_f1"]) == 0.86
    jac = [blind[k]["blind_consistency"]["mean_pairwise_jaccard"] for k in ("online_boutique", "astronomy_shop")]
    assert [round(100 * j) for j in jac] == [92, 93]
    # "one wrong edge": the same single invented edge in every blind Astronomy run
    assert all(r["invented_edges"] == [["load-generator", "frontend"]] for r in blind["astronomy_shop"]["blind_runs"])


def test_slide7_names_hidden(blind):
    s = blind["online_boutique"]["anon_summary"]
    assert (r2(s["edge_recall"]["mean"]), r2(s["edge_recall"]["sd"])) == (0.94, 0.06)
    precisions = [r["edge_precision"] for r in blind["online_boutique"]["anon_runs"] + blind["online_boutique"]["blind_runs"]]
    assert precisions == [1.0] * 6


def test_slide8_missed_edges(g, blind):
    r = ev.evaluate("astronomy_shop", ROOT)
    missed = [tuple(e) for e in r["missed_edges"]]
    into_flagd = {e for e in missed if e[1] == "flagd"}
    assert len(missed) == 9 and len(into_flagd) == 7
    assert g["as_t"].in_degree("flagd") == 12 and g["as_e"].in_degree("flagd") == 5
    for run in blind["astronomy_shop"]["blind_runs"]:
        assert {tuple(e) for e in run["missed_edges"] if e[1] == "flagd"} == into_flagd


def test_slide9_stats(g):
    assert (r2(nx.density(g["ob_t"])), r2(nx.density(g["as_t"]))) == (0.12, 0.09)
    ind_ob, ind_as = dict(g["ob_t"].in_degree()), dict(g["as_t"].in_degree())
    assert max(ind_ob, key=ind_ob.get) == "productcatalogservice" and max(ind_ob.values()) == 3
    assert max(ind_as, key=ind_as.get) == "flagd" and max(ind_as.values()) == 12
    for k in ("ob_t", "as_t"):
        assert nx.dag_longest_path_length(nx.condensation(g[k])) == 4
    assert len(list(nx.simple_cycles(g["ob_t"]))) == 0 and len(list(nx.simple_cycles(g["as_t"]))) == 1


def test_slide10_ranking(g, blind):
    dt, de = bg.dependents(g["as_t"]), bg.dependents(g["as_e"])
    nodes = set(dt) & set(de)
    xs, ys = [dt[n] for n in sorted(nodes)], [de[n] for n in sorted(nodes)]
    assert r2(spearmanr(xs, ys).statistic) == 1.00 and r2(kendalltau(xs, ys).statistic) == 1.00
    assert bg.top_k_with_ties(dt) == bg.top_k_with_ties(de) and len(bg.top_k_with_ties(dt)) == 6
    assert (dt["flagd"], de["flagd"]) == (12, 9)
    assert [r["flagd_dependents"] for r in blind["astronomy_shop"]["blind_runs"]] == [9, 9, 9]
    s = blind["astronomy_shop"]["blind_summary"]["rank_spearman_vs_truth"]
    assert (r2(s["mean"]), r2(s["sd"])) == (0.98, 0.02)


def test_slide11_composite(g):
    for key, expected in (("ob_t", 0.00), ("as_t", 0.09)):
        comp, imp = bg.composite(g[key]), bg.failure_impact(g[key])
        assert abs(r2(rho(comp, imp, g[key].nodes)) - expected) < 1e-9
    assert r2(bg.composite(g["as_t"])["astronomy-db"]) == 0.03
    assert bg.dependents(g["as_t"])["astronomy-db"] == 6


def test_slide12_soft_dependencies(g):
    soft = bg.load_soft_edges("astronomy_shop", ROOT)
    assert len(soft) == 13
    dt, dh = bg.dependents(g["as_t"]), bg.dependents(bg.hard_only(g["as_t"], soft))
    assert (dt["flagd"], dh["flagd"]) == (12, 2)
    assert (dt["kafka"], dh["kafka"]) == (6, 2)
    assert (dt["email"], dh["email"]) == (4, 0)
    assert max(dh, key=dh.get) == "astronomy-db" and dh["astronomy-db"] == 6
    assert r2(rho(dt, dh, g["as_t"].nodes)) == 0.66


def test_slide5_test_count():
    import subprocess
    out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q",
                          str(ROOT / "tests" / "test_pipeline.py")],
                         capture_output=True, text=True, cwd=ROOT).stdout
    assert sum(1 for line in out.splitlines() if "::" in line) == 45
