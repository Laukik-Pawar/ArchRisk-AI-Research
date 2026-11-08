# Blind extraction runs

Date: November 8, 2026. Model: Claude Opus 5.5 (`claude-opus-5-5`).

Each JSON file here was produced by a separate, fresh Claude instance that had
never seen this project, the deployment configs or the answer key. Each
instance was told to read exactly two files, the prompt and one document
(both copied in `_inputs_given/`), to use no other files, shell, web or
memory, and to write only the JSON. Each instance used exactly three tool
calls: read the prompt, read the document, write the JSON.

| Folder | Document given | Purpose |
|---|---|---|
| `run1`, `run2`, `run3` | `online_boutique.md`, `astronomy_shop.md` | repeat runs: accuracy and run-to-run variability |
| `anon_run1`, `anon_run2`, `anon_run3` | `online_boutique_anon.md` | name-blind test: service names replaced by codes (see `src/anonymize.py`) |

The files are stored exactly as the instances wrote them. The `anon_run*`
files use the codes `svc-01` to `svc-11`; `src/blind_runs.py` decodes them with
`data/anon_map.json` before scoring and saves the decoded copies in
`*_decoded/`.

Limits: these are repeat runs of the same model family that did the v1
extraction, not a different model. The anonymized document keeps the service
descriptions word for word, so a model could still recognise the app from
them.
