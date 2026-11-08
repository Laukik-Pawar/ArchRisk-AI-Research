# EM 626 Project 2: LLM + graph learning for system integration risk

Midterm ("first evidences") version.

## What it does

An LLM reads a system's design documentation and extracts its components and
dependencies. The result becomes a directed graph (edge = consumer -> provider).
Each component gets a simulated failure-impact label: the share of other
components that transitively depend on it. Both systems are open-source apps
with deployment configs, so every extracted graph is checked against a true
graph built from those configs.

| System | LLM input | Answer key |
|---|---|---|
| Online Boutique (Google) | README intro + architecture table (352 words) | `kubernetes-manifests/*.yaml` |
| OpenTelemetry Astronomy Shop | main README + 16 service READMEs (2,090 words) | `compose.yaml` + `compose.full.yaml` + `.env` |

Input selection note: for the Astronomy Shop we used the READMEs of the 16
user-facing services. The `flagd-ui` README (an operator UI) was not included.
`image-provider` and `flagd` have no README.

## How to test it

### 1. Set up (once)

```bash
mkdir em626 && cd em626
git clone https://github.com/GoogleCloudPlatform/microservices-demo.git
git clone https://github.com/open-telemetry/opentelemetry-demo.git
(cd microservices-demo && git checkout c7cb6d5)
(cd opentelemetry-demo && git checkout e22afe5)
# unzip the project here so the layout is em626/project, em626/microservices-demo, ...
cd project
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Install Graphviz so the `dot` command works (`sudo apt install graphviz`,
`brew install graphviz`, or the Windows installer from graphviz.org).

### 2. Run the whole pipeline and the tests

```bash
python run_all.py
```

Expected output, in order:
- both saved extractions: `VALID`
- Online Boutique: `12 nodes, 16 edges`; Astronomy Shop: `21 nodes, 37 edges (+4 startup-only)`
- `11 services coded, 289 words, leaks: none`
- `54 passed`

### 3. Run only the tests

```bash
python -m pytest -v
```

The 54 tests check each component on small hand-made inputs with answers you
can verify by hand (for example, `valkey-cart:6379` must not match the `cart`
service), plus the real data. Two of them run the real Gemini and Anthropic
SDKs with a simulated network, so the extractor's API requests are checked
without an API key. Tests that need the two app repos are skipped if the repos
are missing.

`tests/test_slide_numbers.py` recomputes every number quoted on the midterm
slides from the raw data and fails if any slide number is wrong.

### 4. Check the numbers by hand (spot checks)

- Open `data/ground_truth/online_boutique.json`. Each edge should match an
  `*_ADDR` variable in `microservices-demo/kubernetes-manifests/`. Example:
  `checkoutservice.yaml` sets `PAYMENT_SERVICE_ADDR`, so
  `checkoutservice -> paymentservice` is an edge.
- Open `results/extraction_eval.json`. `missed_edges` lists exactly what the
  LLM missed.
- Open `results/risk_scores_astronomy_shop.csv`. `dependents_truth` for
  `kafka` is 6: accounting, fraud-detection and checkout use it, and frontend,
  frontend-proxy and load-generator reach it through checkout.

### 5. Second model: run the extraction with Gemini

Your key stays in the terminal session only. It is never written to a file.

```bash
# macOS / Linux
GEMINI_API_KEY=your-key python src/gemini_runs.py
# Windows PowerShell
$env:GEMINI_API_KEY="your-key"; python src/gemini_runs.py
```

The script lists the models your key can use, picks a Flash model from that
list (or use `--model <name>`), runs 3 extractions per document plus 3 on the
name-blind document, and scores them like the Claude blind runs. Output:
`results/gemini_runs.json` and `extracted_api/<model>/`. It takes a few
minutes because it pauses between calls to stay under rate limits.

### 6. Optional: a single extraction run with your own API key

```bash
cp .env.example .env          # fill in LLM_PROVIDER, LLM_MODEL and the key
python src/extractor.py --run 1
python src/evaluate_extraction.py --extracted extracted_api/<model>/run1 \
       --out results/extraction_eval_<model>_run1.json
```

New runs never overwrite `extracted/` (the saved v1 extraction). Running the
same command with `--run 2`, `--run 3` measures LLM variability.

## Blind extraction runs

`extracted/` holds the first (v1) extraction, made in the same chat that built
the pipeline. Before extracting, that chat had browsed the repositories'
folder names (but not the deployment configs), so v1 had some extra context.
`extracted_blind/` holds the cleaner evidence: nine extractions by fresh
Claude instances that saw only the prompt and one document. Three are repeat
runs per system; three use a copy of the Online Boutique document with every
service name replaced by a code. `src/blind_runs.py` scores them
(`results/blind_runs.json`, `figures/blind_runs.png`). See
`extracted_blind/MANIFEST.md`.

## Layout

```
data/docs/                 design documents given to the LLM (text only)
data/ground_truth/         true graphs parsed from deployment configs
data/soft_dependencies.json  13 edges shown by code or spec to be soft, with evidence
prompts/                   extraction prompt + prompt log
extracted/                 saved v1 LLM extraction (JSON)
extracted_blind/           9 blind extractions (3 repeat runs per system, 3 name-blind)
src/                       extractor, ground-truth parser, evaluator, graph builder,
                           anonymizer, blind-run scorer, Gemini runner
tests/                     automated tests (pytest)
results/                   metrics, stats, risk scores
figures/                   pipeline diagram and charts
validation_log.md          test inputs, expected vs actual, fixes
```

## Authorship

All code in `src/` and `tests/`, the pipeline diagram, and the v1 extraction
were produced with Claude Opus 5.5 (`claude-opus-5-5`). See
`prompts/prompts_log.md`.
