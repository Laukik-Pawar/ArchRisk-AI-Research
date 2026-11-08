# Validation log

| # | Component | Test input | Expected | Actual | Fix |
|---|---|---|---|---|---|
| 1 | extractor schema check | both saved extraction JSONs | VALID | VALID (12 / 16 and 19 / 28) | none |
| 2 | extractor schema check | 8 broken variants (duplicate id, bad type, bad stateful, unknown node, self-loop, duplicate edge, bad evidence, long reason) | each rejected | each rejected (automated tests) | none |
| 3 | ground-truth parser | Online Boutique manifests | 11 deployments + redis-cart | 12 nodes, 16 edges | frontend also points to `shoppingassistantservice`, not deployed in the base manifests. Left out and noted. |
| 4 | ground-truth parser | Astronomy Shop `compose.yaml` only | kafka, accounting, fraud-detection present | missing | They live in `compose.full.yaml`. Parser merges both files. |
| 5 | ground-truth parser | Astronomy Shop address variables | real call wiring | 21 nodes, 37 edges | `depends_on` adds 4 startup-only edges (e.g. frontend -> quote). Kept separate: startup order is not a runtime call. |
| 6 | ground-truth parser | `valkey-cart:6379`, `http://frontend-proxy:8080` | match only the full name | correct (automated tests) | none |
| 7 | evaluator | extracted vs true names | `valkey` matches `valkey-cart` | counted as a miss at first | Added a rename-only alias table and lowercasing. |
| 8 | graph builder | Astronomy Shop true graph | a DAG | one cycle: frontend-proxy <-> load-generator | Real (the proxy serves the Locust UI, the load generator sends traffic through the proxy). Longest chain computed on the condensation graph. |
| 9 | graph builder | top-5 comparison | 5 nodes | several nodes tie at the 5th score | Top-5 now includes all ties; agreement reported as Jaccard overlap, plus Kendall tau-b. |
| 10 | graph builder | flagd impact, extracted vs true | comparable numbers | 0.50 vs 0.60 used different denominators (18 vs 20) | Compare dependent counts instead: 9 vs 12. |
| 11 | extractor API path | Anthropic SDK v2.6.0 signature | accepts `temperature` | it does not; the call would have failed | Removed `temperature` for Anthropic. Model name now required (no guessed default). Found by inspecting the installed SDK, not by a live call. |
| 12 | label assumption | flagd and checkout source + OpenFeature spec | all dependencies hard | 13 edges are soft (spec 1.4.10 default values; checkout logs email and Kafka failures and still returns the order) | Added `data/soft_dependencies.json` and a hard-only impact check. |
| 13 | slides | statement about missed nodes | accurate | claimed flagd-ui has no README; it has one, we did not include it | Corrected; input selection now stated in the README. |
| 14 | figures | rendered PNGs | readable labels | legend covered a label; two scatter labels overlapped | Moved legend, added label nudging. |
| 15 | extractor API path | real Gemini and Anthropic SDKs, network simulated | requests carry the model, prompt, temperature 0 (Gemini) and JSON mode; replies parse and validate | as expected (2 tests) | Tests first failed: the SDKs now use `httpx2`, not `httpx`. Switched the test transport to `httpx2`. |
| 16 | blind extraction | 9 fresh Claude instances given only prompt + one doc | valid JSON | 9 / 9 valid, each used exactly 3 tool calls | none |
| 17 | evaluator | blind Astronomy runs | no invented edges | every run adds load-generator -> frontend | The doc says browser users run "against the frontend"; the config routes traffic through frontend-proxy. Kept as an error under strict scoring and explained. |
| 18 | v1 vs blind | Astronomy edge recall | similar | v1 0.76, blind 0.65 to 0.73 | v1 had seen the repos' folder names before extracting. Blind runs are now the headline numbers. |
| 19 | anonymizer | name-blind Online Boutique doc | no service names left, descriptions unchanged | 0 leaks (automated tests) | none |
| 20 | Gemini runner | whole script through the real google-genai SDK, network simulated; fake model replies with the v1 JSON | picks a plain Flash model from the listed models, 3 calls per run, scores match v1 (Astronomy recall 0.757), key never written to disk | as expected (2 tests) | The Gemini endpoint is blocked from the build environment, so the live run is done on the student's laptop. |
| 21 | soft-dependency list | Kafka entry vs `src/checkout/main.go` | wording matches code | said "asynchronously"; the send is not in a goroutine, checkout waits for Kafka's answer or the request deadline | Reworded: the order still returns, but a Kafka outage can delay it. Line numbers re-checked. |
| 22 | slides | every quoted number, recomputed from raw data | slide = data | slide 12 said Spearman 0.67; raw value 0.6649 (rounded twice: 0.665 then 0.67) | Fixed to 0.66. Added `tests/test_slide_numbers.py` (9 tests) so every slide number is checked on each run. |
| 23 | whole pipeline | fresh clones of both apps at the pinned commits, project unzipped into a new folder, all outputs deleted, `python run_all.py` | same results | all 8 result and ground-truth files byte-for-byte identical | none |
| 24 | graph-model module | GCN and GraphGPS in PyTorch Geometric, to be initialised on the real graphs | runs | PyTorch could not be installed here: the Linux package needs several GB of NVIDIA GPU libraries that the network would not deliver, and the CPU-only download site is blocked | Model code removed from the midterm package so nothing unrun is shipped. Architectures stay a planned design (shown in the pipeline diagram); building them is the first post-midterm task, on a laptop where `pip install torch torch_geometric` works. |
| 25 | whole pipeline | second fresh rebuild compared byte for byte | identical files | `graph_stats.json` listed the one cycle from a different starting node (networkx's start depends on Python's per-run string hashing) | Cycles now stored in a fixed order. Output identical under PYTHONHASHSEED 0, 1 and 12345. Added a test. |

## Known limitations (still open)

- Claude may know both public apps from training data. Hiding the service
  names barely changed Online Boutique recall (0.94 vs 0.96), but the
  descriptions were kept word for word, so the app could still be recognised.
- All runs so far use one model family (Claude). A second model (Gemini, via
  `src/extractor.py` and the student's own key) is still to do.
- The extractor's API path is tested against the real SDKs with a simulated
  network, but has not made a live API call (no API key in this environment,
  and the Gemini endpoint is blocked from it).
- Soft dependencies were checked only where code or a spec proves them. The
  proxy routes and the frontend's backend calls are still treated as hard.
