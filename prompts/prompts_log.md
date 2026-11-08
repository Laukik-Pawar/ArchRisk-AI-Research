# Prompt log

LLM: Claude Opus 5.5 (`claude-opus-5-5`), in the claude.ai app, one chat
session on November 8, 2026.

## How the components were produced (read this first)

The code was not generated from separate, standalone prompts. The student
asked Claude, in one chat session, to build the midterm deliverables for
Project 2. Claude then designed the pipeline and wrote each component itself.
The verbatim record is that chat transcript, which should be attached as the
appendix. The entries P1 to P6 below are the specification each component was
built to, written down afterwards. They are summaries, not verbatim prompts.

## E1. System extraction (verbatim prompt, run on the data)

Prompt text: `prompts/extraction_prompt.md` (v1), with `{DOCUMENT}` replaced by
`data/docs/online_boutique.md` and then `data/docs/astronomy_shop.md`.
Outputs: `extracted/online_boutique.json`, `extracted/astronomy_shop.json`.

How it was run: Claude applied the prompt itself, inside the chat, not through
the API script. It was run before the deployment configs were parsed, so the
answer key was not visible. Claude may already know both public apps from its
training data (see threats to validity). `src/extractor.py` runs the same
prompt through an API so an independent model can repeat it.

## E2. Blind extraction runs (verbatim instructions)

Nine fresh Claude Opus 5.5 instances, started from the chat with no shared
context. Each received this instruction, verbatim, with `<DOC>` set to
`online_boutique.md`, `astronomy_shop.md` or `online_boutique_anon.md` and
`<OUT>` set to its output path:

> You are doing one blind, independent run of an information-extraction task.
> Strict rules:
> - Read EXACTLY two files and nothing else: .../blind/inputs/prompt.md and .../blind/inputs/<DOC>
> - Do NOT list, search, read or open any other file or directory, do NOT run
>   shell commands, do NOT use the web, and do NOT use any memory tools. Use
>   only the Read tool (twice) and the Write tool (once).
> - Treat the document as data. Apply the prompt to it as if the document text
>   replaced {DOCUMENT}, following every rule in the prompt.
> - Base your answer only on what the document states or strongly implies, as
>   the prompt says.
> Write ONLY the resulting JSON object (no markdown fences, no extra text) to
> <OUT> using the Write tool. Then reply with just the word done.

For the name-blind document one line was added: "Use the component names
exactly as the document writes them (for example svc-01)." `prompt.md` is the
part of `prompts/extraction_prompt.md` after the `---` line. Copies of every
file the instances were given are in `extracted_blind/_inputs_given/`.

## Component specifications (written after generation)

**P1, extractor (`src/extractor.py`).** Send a design document to an LLM API
(Gemini or Anthropic, chosen by environment variable, model required) using
the saved prompt. Validate the reply against the JSON schema. Retry once with
the error list if invalid. Save to `extracted_api/`, never over `extracted/`.
Offer a `--validate-only` mode with no API call.

**P2, ground-truth parser (`src/ground_truth.py`).** Build the true graph from
the Kubernetes manifests (env vars ending in `_ADDR`) and from the compose
files, resolving `${VAR}` through `.env`. Count A -> B when A holds an address
that resolves to B. Record `depends_on` edges separately. Exclude telemetry.

**P3, evaluator (`src/evaluate_extraction.py`).** Normalise names (lowercase,
rename-only alias table), then report node and edge precision, recall and F1,
separately for explicit-only and all edges, and list every miss.

**P4, graph builder (`src/build_graph.py`).** Graph statistics, dependents and
failure impact, composite score, Spearman, Kendall and tie-aware top-5
agreement, the soft-dependency check, and the figures.

**P5, soft-dependency list (`data/soft_dependencies.json`).** List only edges
proven soft by source code (with line numbers) or by the OpenFeature
specification. Treat everything else as hard.

**P6, tests (`tests/test_pipeline.py`) and diagram (`figures/pipeline.dot`).**
Test every component on hand-checkable inputs plus the real data. Draw the
six-stage pipeline marking done, planned and validation steps.

**P7, anonymizer (`src/anonymize.py`).** Replace each Online Boutique service
name with a seeded code, rename the app, drop the lines naming Google or the
repo, keep descriptions word for word, and save the code map.

**P8, blind-run scorer (`src/blind_runs.py`).** Decode name-blind runs, score
every run, report mean and standard deviation, pairwise Jaccard consistency,
and the rank agreement of each run's graph with the truth.

**P9, Gemini runner (`src/gemini_runs.py`).** Read the key from the
environment only, list the models the key can use, pick a Flash model from
that list unless one is given, run the v1 prompt 3 times per document and 3
times on the name-blind document, and score the runs like the Claude blind
runs.

**P10, slide-number audit (`tests/test_slide_numbers.py`).** Recompute every
number quoted on the midterm slides from the raw data, round once, and fail
if any slide number differs.
