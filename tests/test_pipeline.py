"""Automated tests for every pipeline component.

Run from the project folder:   python -m pytest -v
Unit tests use small hand-made inputs whose answers can be checked by hand.
Integration tests use the real data and are skipped if the two app repos
are not cloned next to the project folder.
"""
import json
import re
import sys
from pathlib import Path

import networkx as nx
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import build_graph as bg            # noqa: E402
import evaluate_extraction as ev    # noqa: E402
import extractor as ex              # noqa: E402
import ground_truth as gtp          # noqa: E402

REPO_OB = ROOT.parent / "microservices-demo"
REPO_OTEL = ROOT.parent / "opentelemetry-demo"
needs_repos = pytest.mark.skipif(not (REPO_OB.exists() and REPO_OTEL.exists()),
                                 reason="app repos not cloned next to the project")


# ---------------------------------------------------------------- extractor
def good_obj():
    return {"components": [{"id": "a", "type": "service", "stateful": False},
                           {"id": "db", "type": "datastore", "stateful": True}],
            "dependencies": [{"source": "a", "target": "db", "evidence": "explicit",
                              "reason": "a stores data in db"}]}


def test_validate_accepts_good_json():
    assert ex.validate(good_obj()) == []


@pytest.mark.parametrize("mutate,expected", [
    (lambda o: o["components"].append({"id": "a", "type": "service", "stateful": False}), "duplicate"),
    (lambda o: o["components"][0].update(type="database"), "bad type"),
    (lambda o: o["components"][0].update(stateful="no"), "stateful"),
    (lambda o: o["dependencies"][0].update(target="zzz"), "unknown component"),
    (lambda o: o["dependencies"][0].update(target="a"), "self-loop"),
    (lambda o: o["dependencies"].append(dict(o["dependencies"][0])), "duplicate edge"),
    (lambda o: o["dependencies"][0].update(evidence="maybe"), "evidence"),
    (lambda o: o["dependencies"][0].update(reason="word " * 16), "longer than 15"),
])
def test_validate_rejects_each_problem(mutate, expected):
    o = good_obj()
    mutate(o)
    errs = ex.validate(o)
    assert any(expected in e for e in errs), errs


def test_parse_json_strips_surrounding_text():
    assert ex.parse_json('Here you go:\n{"x": 1}\nThanks') == {"x": 1}


def test_build_prompt_inserts_document(tmp_path):
    doc = tmp_path / "doc.md"
    doc.write_text("UNIQUE-DOC-TEXT")
    p = ex.build_prompt(doc, ROOT / "prompts" / "extraction_prompt.md")
    assert "UNIQUE-DOC-TEXT" in p and "{DOCUMENT}" not in p and "Rules:" in p


def test_extract_retries_once_then_succeeds(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    replies = iter(["not json at all", json.dumps(good_obj())])
    calls = []
    def fake_llm(prompt):
        calls.append(prompt)
        return next(replies), "fake-model"
    obj = ex.extract("t", "data/docs/online_boutique.md", tmp_path, llm=fake_llm)
    assert obj["attempts"] == 2 and obj["llm"] == "fake-model"
    assert "previous reply was invalid" in calls[1]
    assert json.loads((tmp_path / "t.json").read_text())["components"]


def test_extract_fails_after_two_invalid_replies(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    with pytest.raises(RuntimeError):
        ex.extract("t", "data/docs/online_boutique.md", tmp_path,
                   llm=lambda p: ("{}", "fake-model"))


def test_call_llm_requires_provider_and_model(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    with pytest.raises(SystemExit):
        ex.call_llm("hi")


def test_saved_extractions_are_valid():
    for key in ex.SYSTEMS:
        assert ex.validate(json.loads((ROOT / "extracted" / f"{key}.json").read_text())) == []


# ---------------------------------------------------------------- ground truth
@pytest.mark.parametrize("value,expected", [
    ("cart:7070", {"cart"}),
    ("valkey-cart:6379", {"valkey-cart"}),           # must not also match "cart"
    ("http://frontend-proxy:8080", {"frontend-proxy"}),  # must not match "frontend"
    ("postgres://u:pw@astronomy-db/astronomy_db", {"astronomy-db"}),
    ("frontend", {"frontend"}),
    ("0.0.0.0", set()),
])
def test_hosts_in_respects_name_boundaries(value, expected):
    services = {"cart", "valkey-cart", "frontend", "frontend-proxy", "astronomy-db"}
    assert gtp.hosts_in(value, services) == expected


def test_resolve_substitutes_nested_variables():
    env = {"HOST": "kafka", "PORT": "9092", "ADDR": "${HOST}:${PORT}"}
    assert gtp.resolve("${ADDR}", env) == "kafka:9092"


@needs_repos
def test_ground_truth_counts_match_configs():
    ob, otel = gtp.online_boutique(REPO_OB), gtp.astronomy_shop(REPO_OTEL)
    assert (len(ob["nodes"]), len(ob["edges"])) == (12, 16)
    assert (len(otel["nodes"]), len(otel["edges"])) == (21, 37)
    assert ["frontend", "cartservice"] in [list(e) for e in ob["edges"]]
    assert ["checkout", "kafka"] in [list(e) for e in otel["edges"]]
    assert "otel-collector" not in otel["nodes"]          # telemetry excluded


# ---------------------------------------------------------------- evaluator
def test_prf_hand_example():
    r = ev.prf({1, 2, 3, 4}, {3, 4, 5})
    assert (r["tp"], r["precision"], r["recall"]) == (2, 0.5, 0.667)
    assert r["f1"] == round(2 * 0.5 * (2 / 3) / (0.5 + 2 / 3), 3)


def test_prf_empty_sets_do_not_crash():
    assert ev.prf(set(), {1})["f1"] == 0.0


def test_canonical_lowercases_and_renames_only():
    assert ev.canonical("astronomy_shop", " Valkey ") == "valkey-cart"
    assert ev.canonical("astronomy_shop", "Cart") == "cart"


def test_saved_extraction_scores():
    r = ev.evaluate("astronomy_shop", ROOT)
    assert r["edges_all"]["tp"] == 28 and r["edges_all"]["true"] == 37
    assert r["edges_all"]["precision"] == 1.0
    assert r["missed_nodes"] == ["flagd-ui", "image-provider"]


# ---------------------------------------------------------------- graph builder
def chain():
    g = nx.DiGraph()
    g.add_edges_from([("a", "b"), ("b", "c"), ("d", "c")])   # a->b->c, d->c
    return g


def test_dependents_counts_transitive_consumers():
    assert bg.dependents(chain()) == {"a": 0, "b": 1, "c": 3, "d": 0}


def test_failure_impact_is_share_of_other_nodes():
    imp = bg.failure_impact(chain())
    assert imp["c"] == 1.0 and imp["b"] == pytest.approx(1 / 3)


def test_composite_gives_sinks_zero_betweenness():
    # c is a sink: no shortest path passes THROUGH it, so its betweenness is 0
    assert nx.betweenness_centrality(chain())["c"] == 0
    comp = bg.composite(chain())
    assert comp["c"] == pytest.approx(0.4)   # only the in-degree term


def test_top_k_with_ties_keeps_tied_nodes():
    s = {"a": 5, "b": 4, "c": 4, "d": 4, "e": 1}
    assert bg.top_k_with_ties(s, k=2) == {"a", "b", "c", "d"}


def test_agreement_identical_rankings():
    s = {"a": 3, "b": 2, "c": 1}
    r = bg.agreement(s, s)
    assert r["spearman"] == 1.0 and r["kendall_tau_b"] == 1.0 and r["top5_jaccard"] == 1.0


def test_hard_only_removes_soft_edges():
    h = bg.hard_only(chain(), {("d", "c")})
    assert bg.dependents(h)["c"] == 2


def test_soft_edges_exist_in_true_graph():
    _, gt = bg.load_graphs("astronomy_shop", ROOT)
    soft = bg.load_soft_edges("astronomy_shop", ROOT)
    assert len(soft) == 13 and all(gt.has_edge(*e) for e in soft)


# ---------------------------------------------------------------- extractor API path, real SDKs, simulated network
def _reply_json():
    return json.dumps(good_obj())


def test_anthropic_path_with_real_sdk(monkeypatch):
    """Runs the real anthropic SDK; only the network is simulated."""
    anthropic = pytest.importorskip("anthropic")
    httpx = pytest.importorskip("httpx2")
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={
            "id": "msg_test", "type": "message", "role": "assistant", "model": "test-model",
            "content": [{"type": "text", "text": _reply_json()}],
            "stop_reason": "end_turn", "stop_sequence": None,
            "usage": {"input_tokens": 1, "output_tokens": 1}})

    client = anthropic.Anthropic(api_key="test", base_url="https://api.test",
                                 http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    monkeypatch.setattr(ex, "make_anthropic_client", lambda: client)
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    text, model = ex.call_llm("PROMPT-TEXT")
    assert seen["url"].endswith("/v1/messages")
    assert seen["body"]["model"] == "test-model"
    assert seen["body"]["messages"][0]["content"] == "PROMPT-TEXT"
    assert ex.validate(ex.parse_json(text)) == [] and model == "test-model"


def test_gemini_path_with_real_sdk(monkeypatch):
    """Runs the real google-genai SDK; only the network is simulated."""
    httpx = pytest.importorskip("httpx2")
    genai = pytest.importorskip("google.genai")
    from google.genai import types
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"candidates": [{"content": {
            "role": "model", "parts": [{"text": _reply_json()}]}, "finishReason": "STOP"}]})

    client = genai.Client(api_key="test", http_options=types.HttpOptions(
        base_url="https://gemini.test/",
        httpx_client=httpx.Client(transport=httpx.MockTransport(handler))))
    monkeypatch.setattr(ex, "make_gemini_client", lambda: client)
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    text, _ = ex.call_llm("PROMPT-TEXT")
    assert "test-model:generateContent" in seen["url"]
    assert seen["body"]["generationConfig"]["temperature"] == 0
    assert seen["body"]["generationConfig"]["responseMimeType"] == "application/json"
    assert seen["body"]["contents"][0]["parts"][0]["text"] == "PROMPT-TEXT"
    assert ex.validate(ex.parse_json(text)) == []


# ---------------------------------------------------------------- anonymizer and blind-run scoring
import anonymize as an   # noqa: E402
import blind_runs as br  # noqa: E402


def test_anonymize_hides_every_service_name():
    code_map = an.make_map()
    text = (ROOT / "data" / "docs" / "online_boutique.md").read_text()
    anon = an.anonymize(text, code_map)
    for name in an.SERVICES:
        assert not re.search(rf"\b{name}\b", anon), name
    assert "Online Boutique" not in anon and "Google" not in anon
    assert len(set(code_map)) == len(an.SERVICES) == 11


def test_anonymize_keeps_descriptions_word_for_word():
    anon = an.anonymize((ROOT / "data" / "docs" / "online_boutique.md").read_text(), an.make_map())
    assert "Retrieves user cart, prepares order and orchestrates the payment, shipping and the email notification." in anon


def test_saved_anon_doc_matches_script():
    code_map = json.loads((ROOT / "data" / "anon_map.json").read_text())
    assert code_map == an.make_map()
    fresh = an.anonymize((ROOT / "data" / "docs" / "online_boutique.md").read_text(), code_map)
    assert fresh == (ROOT / "data" / "docs" / "online_boutique_anon.md").read_text()


def test_decode_maps_codes_back_case_insensitively():
    obj = {"components": [{"id": "SVC-01"}, {"id": "redis"}],
           "dependencies": [{"source": "svc-01", "target": "redis"}]}
    dec = br.decode(obj, {"svc-01": "cartservice"})
    assert [c["id"] for c in dec["components"]] == ["cartservice", "redis"]
    assert dec["dependencies"][0]["source"] == "cartservice"
    assert br.leftover_codes(dec) == []


def test_jaccard_hand_example():
    assert br.jaccard({1, 2, 3}, {2, 3, 4}) == 0.5


def test_blind_outputs_are_valid():
    for folder in ["run1", "run2", "run3"]:
        for key in ex.SYSTEMS:
            assert ex.validate(json.loads((ROOT / "extracted_blind" / folder / f"{key}.json").read_text())) == []
    for folder in ["anon_run1", "anon_run2", "anon_run3"]:
        assert ex.validate(json.loads((ROOT / "extracted_blind" / folder / "online_boutique.json").read_text())) == []


# ---------------------------------------------------------------- Gemini second-model script
import gemini_runs as gr  # noqa: E402


def test_pick_model_prefers_plain_flash():
    names = ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite",
             "gemini-2.5-flash-image", "gemini-3.0-flash", "gemini-3.0-flash-tts"]
    assert gr.pick_model(names) == "gemini-3.0-flash"
    assert gr.pick_model(["gemini-2.5-pro"]) is None


def test_gemini_runs_end_to_end_with_real_sdk(tmp_path, monkeypatch):
    """Whole script through the real google-genai SDK; network simulated.
    The fake model answers with the saved v1 extraction for each document."""
    httpx = pytest.importorskip("httpx2")
    genai = pytest.importorskip("google.genai")
    from google.genai import types
    monkeypatch.chdir(ROOT)
    v1 = {k: (ROOT / "extracted" / f"{k}.json").read_text() for k in ex.SYSTEMS}
    calls = {"list": 0, "generate": 0}

    def handler(request):
        if request.method == "GET" and request.url.path.endswith("/models"):
            calls["list"] += 1
            return httpx.Response(200, json={"models": [
                {"name": "models/gemini-9.9-flash", "supportedGenerationMethods": ["generateContent"]},
                {"name": "models/gemini-9.9-flash-lite", "supportedGenerationMethods": ["generateContent"]},
                {"name": "models/text-embedding-9", "supportedGenerationMethods": ["embedContent"]}]})
        calls["generate"] += 1
        assert "gemini-9.9-flash:generateContent" in str(request.url)
        prompt = json.loads(request.content)["contents"][0]["parts"][0]["text"]
        reply = v1["astronomy_shop"] if "Astronomy Shop" in prompt else v1["online_boutique"]
        return httpx.Response(200, json={"candidates": [{"content": {
            "role": "model", "parts": [{"text": reply}]}, "finishReason": "STOP"}]})

    client = genai.Client(api_key="FAKE-KEY-9431", http_options=types.HttpOptions(
        base_url="https://gemini.test/", httpx_client=httpx.Client(transport=httpx.MockTransport(handler))))
    monkeypatch.setattr(ex, "make_gemini_client", lambda: client)
    monkeypatch.setenv("GEMINI_API_KEY", "FAKE-KEY-9431")
    res = gr.main(["--runs", "2", "--sleep", "0", "--out-root", str(tmp_path / "api"),
                   "--results", str(tmp_path / "res.json")])
    assert res["model"] == "gemini-9.9-flash"
    assert calls["list"] == 1 and calls["generate"] == 2 * 3     # 2 runs x (2 docs + names-hidden doc)
    assert res["astronomy_shop"]["summary"]["edge_recall"]["mean"] == pytest.approx(0.757, abs=1e-3)
    assert res["online_boutique"]["summary"]["edge_f1"]["mean"] == 1.0
    assert json.loads((tmp_path / "res.json").read_text())["model"] == "gemini-9.9-flash"
    saved = list((tmp_path / "api").rglob("*.json")) + [tmp_path / "res.json"]
    assert saved and not any("FAKE-KEY-9431" in p.read_text() for p in saved)   # key never written


def test_canonical_cycles_ignore_starting_node():
    a, b = nx.DiGraph([("y", "x"), ("x", "y")]), nx.DiGraph([("x", "y"), ("y", "x")])
    assert bg.canonical_cycles(a) == bg.canonical_cycles(b) == [["x", "y"]]
