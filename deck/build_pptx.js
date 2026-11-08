// Builds deck/EM626_Project2_Midterm.pptx from the project's figures.
// Run from the project folder:  node deck/build_pptx.js
const path = require("path");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require(process.env.PPTX_SKILL_DIR + "/scripts/apply_theme.js");

const FIG = (f) => path.join(__dirname, "..", "figures", f);
const OUT = path.join(__dirname, "EM626_Project2_Midterm.pptx");

const THEME = {
  name: "EM626 Integration Risk",
  headFontFace: "Arial",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "13233A", lt1: "FFFFFF", dk2: "45546A", lt2: "F2F4F7",
    accent1: "2A78D6", accent2: "EB6834", accent3: "7FB2EE", accent4: "1E3554",
    accent5: "C9D3DF", accent6: "7A8597", hlink: "2A78D6", folHlink: "6250D6",
  },
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Knowledge Graphs for System Integration Risk: Midterm";
pres.author = "Sai Bhavesh Karnam, Laukik Nandkishor Pawar";
const C = pres.SchemeColor;
const W = 13.333, M = 0.6, CW = W - 2 * M;

// ---------------------------------------------------------------- layouts
function contentLayout(name, dark) {
  pres.defineSlideMaster({
    title: name,
    background: { color: dark ? C.text1 : C.background1 },
    objects: [
      { placeholder: { options: { name: "eyebrow", type: "body", x: M, y: 0.42, w: CW, h: 0.35,
          fontSize: 13, bold: true, color: dark ? C.accent3 : C.accent1, charSpacing: 2, margin: 0,
          valign: "top" }, text: "" } },
      { placeholder: { options: { name: "title", type: "title", x: M, y: 0.8, w: CW, h: 1.15,
          fontSize: 32, bold: true, color: dark ? C.background1 : C.text1, margin: 0,
          valign: "top", align: "left", fontFace: THEME.headFontFace }, text: "" } },
    ],
    slideNumber: { x: W - M - 0.6, y: 6.95, w: 0.6, h: 0.3, fontSize: 11,
                   color: dark ? C.accent5 : C.accent6, align: "right" },
  });
}
pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: C.text1 },
  objects: [
    { placeholder: { options: { name: "eyebrow", type: "body", x: M, y: 0.6, w: CW, h: 0.4,
        fontSize: 14, bold: true, color: C.accent3, charSpacing: 2, margin: 0 }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: M, y: 2.0, w: 11.2, h: 2.2,
        fontSize: 48, bold: true, color: C.background1, margin: 0, valign: "top",
        align: "left", fontFace: THEME.headFontFace }, text: "" } },
    { placeholder: { options: { name: "subtitle", type: "body", x: M, y: 4.35, w: 10.5, h: 0.9,
        fontSize: 20, color: C.accent5, margin: 0, valign: "top" }, text: "" } },
  ],
});
contentLayout("CONTENT_LIGHT", false);
contentLayout("CONTENT_DARK", true);

// ---------------------------------------------------------------- helpers
const T = (slide, text, o) => slide.addText(text, { isTextBox: true, margin: 0, valign: "top", ...o });
function head(slide, eyebrow, title) {
  slide.addText(eyebrow.toUpperCase(), { placeholder: "eyebrow" });
  slide.addText(title, { placeholder: "title" });
}
function source(slide, text, dark) {
  T(slide, text, { objectName: "Source", x: M, y: 6.95, w: CW - 1, h: 0.3, fontSize: 11,
                   color: dark ? C.accent5 : C.accent6 });
}
function card(slide, x, y, w, h, name, fill) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { objectName: name, x, y, w, h, rectRadius: 0.12,
    fill: { color: fill || C.background2 }, line: { color: fill || C.background2, width: 0.75 } });
}
function img(slide, file, x, y, w, ratio, alt, name) {
  slide.addImage({ path: FIG(file), x, y, w, h: w / ratio, altText: alt, objectName: name });
}
const tableOpts = (colW, extra = {}) => ({
  x: M, w: CW, colW, fontFace: THEME.bodyFontFace, fontSize: 15, color: C.text1,
  border: { type: "solid", pt: 0.75, color: "D9DDE3" }, margin: [4, 8, 4, 8], valign: "middle", ...extra,
});
const th = (t, align = "left") => ({ text: t, options: { bold: true, fill: { color: C.background2 }, align } });

// ---------------------------------------------------------------- sections + slides
pres.addSection({ title: "Question, pipeline and data" });
let s;

// 1 cover
s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Question, pipeline and data" });
s.addText("EM 626 · AI/ML FOR SYSTEMS · PROJECT 2 · MIDTERM", { placeholder: "eyebrow" });
s.addText("Knowledge Graphs for System Integration Risk", { placeholder: "title" });
s.addText("Can an LLM find a system’s weakest link before it breaks? First evidences from two open-source microservice apps", { placeholder: "subtitle" });
T(s, "Team: Sai Bhavesh Karnam, Laukik Nandkishor Pawar", { objectName: "Team", x: M, y: 6.45, w: 7.2, h: 0.4, fontSize: 18, color: C.background1 });
T(s, "Stevens Institute of Technology · November 2026", { objectName: "Date", x: 8.0, y: 6.5, w: CW - 7.4, h: 0.4, fontSize: 14, color: C.accent5, align: "right" });
s.addNotes("This is Project 2, Knowledge Graphs for System Integration Risk. Our project asks a simple question: if an engineer hands an LLM the design docs for a system, can the pipeline correctly find the components whose failure would hurt the system most? Today I’ll show what is built so far and what the first results say.");

// 2 question
s = pres.addSlide({ masterName: "CONTENT_LIGHT", sectionTitle: "Question, pipeline and data" });
head(s, "The question", "Which component would hurt the system most if it failed, and can the pipeline find it from the docs alone?");
[["1 · Read", "An LLM reads a system’s design documentation and lists its components and dependencies."],
 ["2 · Map and score", "The list becomes a directed graph. Each component is scored by how much of the system fails with it."],
 ["3 · Learn and advise", "A GNN and a graph Transformer learn to predict risk. An LLM turns results into design advice."]]
  .forEach(([h, b], i) => {
    const w = (CW - 0.6) / 3, x = M + i * (w + 0.3);
    card(s, x, 2.25, w, 2.25, `Step card ${i + 1}`);
    T(s, h, { objectName: `Step ${i + 1} title`, x: x + 0.3, y: 2.5, w: w - 0.6, h: 0.45, fontSize: 20, bold: true, color: C.text1, fontFace: THEME.headFontFace });
    T(s, b, { objectName: `Step ${i + 1} body`, x: x + 0.3, y: 3.05, w: w - 0.6, h: 1.3, fontSize: 16, color: C.text2 });
  });
card(s, M, 4.85, CW, 1.25, "Angle box", "E6F0FC");
T(s, [{ text: "Our angle: ", options: { bold: true } },
      { text: "we use real open-source apps whose deployment configs reveal the true wiring, so every stage can be checked against an answer key instead of eyeballed." }],
  { objectName: "Angle text", x: M + 0.35, y: 5.1, w: CW - 0.7, h: 0.85, fontSize: 18, color: C.text1 });
s.addNotes("Most versions of this project stop at a single hand-written system description. We picked systems that come with deployment configs, which list the real connections. That lets us measure how accurate each stage is.");

// 3 pipeline
s = pres.addSlide({ masterName: "CONTENT_LIGHT", sectionTitle: "Question, pipeline and data" });
head(s, "Pipeline design", "Six stages, with a validation check after each LLM step");
img(s, "pipeline.png", M, 2.2, CW, 4425 / 1594,
    "Pipeline diagram: design docs to LLM extractor with schema check and retry, extracted graph, and to blind repeat and names-hidden runs; deployment configs to ground-truth parser, true graph; precision and recall check; soft-dependency check, failure-impact label, composite heuristic; planned: variants, features, random forest on node features only, GCN baseline (2 GCNConv layers, 64 hidden), GraphGPS Transformer option (2 GPSConv layers: GIN + 4-head attention, random-walk encoding), K-means tiers, evaluation, fault injection, SME review, LLM advice",
    "Pipeline diagram");
source(s, "Solid blue = built for the midterm · grey dashed = planned · diamond = validation check");
s.addNotes("Blue boxes are built and running today. Grey dashed boxes are planned, including the chosen models: a GCN baseline with two layers, and GraphGPS as the graph Transformer, which adds global attention so it can follow long failure chains. Each diamond is a check: the JSON schema check with retry after extraction, precision and recall against the configs after graph building, and the model evaluation at the end. The soft-dependency check uses source code to mark connections that don’t actually take the caller down.");

// 4 data
s = pres.addSlide({ masterName: "CONTENT_LIGHT", sectionTitle: "Question, pipeline and data" });
head(s, "Data", "Two real systems, each with docs for the LLM and configs as the answer key");
s.addTable([
  [th(""), th("Online Boutique (Google)"), th("OpenTelemetry Astronomy Shop")],
  ["What it is", "E-commerce demo, 11 services over gRPC", "E-commerce demo with a Kafka queue and feature flags"],
  ["LLM input", "README architecture section, 352 words", "Main README + 16 service READMEs, 2,090 words"],
  ["Answer key", "Kubernetes manifests (*_ADDR variables)", "docker compose files + .env (address variables)"],
  ["True graph", "12 components, 16 dependencies", "21 components, 37 dependencies"],
  ["Final-stage role", "Training system", "Held-out test system with built-in fault injection"],
], tableOpts([2.4, 4.5, 5.233], { y: 2.2, objectName: "Data table" }));
T(s, "Scope rule, applied the same way to the LLM and the answer key: application services, datastores, queues and config services count. Telemetry infrastructure does not.",
  { objectName: "Scope note", x: M, y: 5.55, w: CW, h: 0.8, fontSize: 16, color: C.text2 });
source(s, "Repos: GoogleCloudPlatform/microservices-demo @ c7cb6d5 · open-telemetry/opentelemetry-demo @ e22afe5");
s.addNotes("The two docs are very different. Online Boutique has a short, clean architecture table. The Astronomy Shop docs are scattered across per-service READMEs that mostly describe how to build each service. That gives us an easy and a realistic case.");

// 5 components
pres.addSection({ title: "First evidences" });
s = pres.addSlide({ masterName: "CONTENT_LIGHT", sectionTitle: "First evidences" });
head(s, "Preliminary LLM-generated components", "Six components run end to end from one script");
s.addTable([
  [th("Component"), th("What it does"), th("Tested by")],
  ["Extractor", "Prompt v1 → JSON parts and edges, explicit or implied", "Schema check + 17 tests"],
  ["Ground-truth parser", "Builds the true graph from K8s and compose configs", "8 tests + spot checks"],
  ["Extraction evaluator", "Node and edge precision, recall, F1 vs. the truth", "4 tests"],
  ["Graph builder", "Stats, failure impact, composite, soft-edge check", "8 tests"],
  ["Anonymizer", "Replaces service names with codes for the blind test", "3 tests"],
  ["Blind-run scorer", "Scores 9 blind runs: mean ± sd and consistency", "3 tests"],
], tableOpts([2.8, 6.6, 2.733], { y: 2.2, objectName: "Components table" }));
T(s, [{ text: "54 automated tests pass", options: { bold: true, color: C.text1 } },
      { text: ": 9 recompute every number on these slides, 3 run the real Gemini and Anthropic SDKs with a simulated network. All code: Claude Opus 5.5." }],
  { objectName: "Authorship note", x: M, y: 5.6, w: CW, h: 0.8, fontSize: 16, color: C.text2 });
s.addNotes("Every component has automated tests on small inputs whose answers can be checked by hand. For example, the address valkey-cart colon 6379 must match the Valkey store, not the cart service. Three tests run the real Gemini and Anthropic SDKs with the network simulated, one of them the whole Gemini script, which checks the exact API requests without needing a key. Nine more tests recompute every number quoted on these slides from the raw data, which caught one rounding error before this talk. Checking the installed SDK also caught a bug before any live run: the current Anthropic SDK doesn’t accept a temperature setting.");

// 6 f1
s = pres.addSlide({ masterName: "CONTENT_LIGHT", sectionTitle: "First evidences" });
head(s, "Evidence 1 · Extraction accuracy, 3 blind runs per system", "The LLM almost never invents a dependency, but on realistic docs it misses a third");
[["0.96–1.00", "Edge precision. The one wrong edge comes from the doc’s own loose wording.", C.accent1],
 ["0.69", "Astronomy Shop edge recall (± 0.04). Online Boutique: 0.96 ± 0.07.", C.accent2],
 ["92–93%", "Edge overlap between blind runs (Jaccard). The extraction is stable.", C.accent1]]
  .forEach(([n, l, col], i) => {
    const w = (CW - 0.6) / 3, x = M + i * (w + 0.3);
    card(s, x, 2.2, w, 2.0, `Stat card ${i + 1}`);
    T(s, n, { objectName: `Stat ${i + 1} value`, x: x + 0.3, y: 2.35, w: w - 0.6, h: 0.85, fontSize: 40, bold: true, color: col, fontFace: THEME.headFontFace });
    T(s, l, { objectName: `Stat ${i + 1} label`, x: x + 0.3, y: 3.2, w: w - 0.6, h: 0.85, fontSize: 15, color: C.text2 });
  });
const R = (t) => ({ text: t, options: { align: "right" } });
s.addTable([
  [th("Mean ± sd, 3 blind runs"), th("Precision", "right"), th("Recall", "right"), th("Edge F1", "right"), th("v1 run F1", "right")],
  ["Online Boutique", R("1.00 ± 0.00"), R("0.96 ± 0.07"), R("0.98 ± 0.04"), R("1.00")],
  ["Astronomy Shop", R("0.96 ± 0.00"), R("0.69 ± 0.04"), R("0.80 ± 0.03"), R("0.86")],
], tableOpts([3.533, 2.15, 2.15, 2.15, 2.15], { y: 4.55, objectName: "Accuracy table" }));
source(s, "Blind run = fresh Claude instance that saw only the prompt and one doc. v1 had seen the repos’ folder names. Source: results/blind_runs.json");
s.addNotes("These numbers come from blind runs: fresh Claude instances that saw only the prompt and one document, never the answer key. Precision is essentially perfect. The one wrong Astronomy edge appears in every run: the doc says the load generator runs against the frontend, while the config routes it through the proxy. Recall is the problem on the realistic docs: about two thirds. My first run, v1, scored a bit higher, but it had seen the repository’s folder names first, so I treat the blind runs as the real measurement.");

// 6b f1b
s = pres.addSlide({ masterName: "CONTENT_LIGHT", sectionTitle: "First evidences" });
head(s, "Evidence 1b · Reading or remembering?", "Hiding every service name barely changed the result");
img(s, "blind_runs.png", 1.2, 2.0, 10.9, 2400 / 840,
    "Dot plot of edge recall and precision per extraction. Online Boutique: v1 recall 1.00; blind runs 0.88, 1.00, 1.00; names-hidden runs 0.88, 0.94, 1.00; precision 1.00 for all. Astronomy Shop: v1 recall 0.76; blind runs 0.65, 0.68, 0.73; blind precision about 0.96",
    "Blind runs chart");
T(s, [{ text: "Online Boutique names replaced by codes (svc-01 … svc-11): recall " }, { text: "0.94 ± 0.06", options: { bold: true, color: C.text1 } },
      { text: " vs. " }, { text: "0.96 ± 0.07", options: { bold: true, color: C.text1 } }, { text: " with names. Precision 1.00 in all 6 runs." }],
  { objectName: "Anon result", x: M, y: 5.95, w: 5.9, h: 0.9, fontSize: 16, color: C.text2 });
T(s, "Caveat: descriptions stayed word for word, so the app could still be recognised. A second model (Gemini) is the next check.",
  { objectName: "Anon caveat", x: 6.83, y: 5.95, w: 5.9, h: 0.9, fontSize: 16, color: C.text2 });
source(s, "Name-blind doc: src/anonymize.py · runs: extracted_blind/");
s.addNotes("The worry was that the model recognises these famous apps and recalls their wiring instead of reading the document. So I replaced every service name in the Online Boutique doc with a neutral code and ran three more blind extractions. Results barely moved, which suggests the model reads the descriptions. It is not proof: the descriptions themselves are the original text, and all runs used the same model family.");

// 7 f2
s = pres.addSlide({ masterName: "CONTENT_LIGHT", sectionTitle: "First evidences" });
head(s, "Evidence 2 · What was missed", "The misses are hidden configuration dependencies");
img(s, "graph_astronomy_shop.png", M, 1.95, 7.6, 2400 / 1440,
    "Astronomy Shop true dependency graph coloured by simulated failure impact; flagd is the largest node; nine dashed orange edges mark dependencies the LLM missed, seven into flagd and two from frontend-proxy to flagd-ui and image-provider",
    "Astronomy Shop graph");
T(s, [{ text: "7 of the 9", options: { bold: true, color: C.text1 } },
      { text: " missed edges point to " }, { text: "flagd", options: { bold: true, color: C.text1 } },
      { text: ", the feature-flag service. " }, { text: "All 3 blind runs missed the same 7.", options: { bold: true, color: C.text1 } },
      { text: " The configs show 12 users of flagd; the docs reveal 5." }],
  { objectName: "Finding text 1", x: 8.6, y: 2.3, w: 4.13, h: 2.4, fontSize: 18, color: C.text2 });
T(s, "The other 2 lead to flagd-ui (its README was not in our input) and image-provider (no README).",
  { objectName: "Finding text 2", x: 8.6, y: 4.85, w: 4.13, h: 1.4, fontSize: 18, color: C.text2 });
source(s, "Dashed orange = dependency the LLM missed · node size and colour = simulated failure impact");
s.addNotes("The LLM didn’t miss random edges. It missed configuration dependencies, because documentation rarely mentions that a service reads feature flags. This is not a one-off: all three blind runs missed exactly the same seven flagd edges, and the same two proxy edges. On paper flagd is the most depended-on component in the system. Slide 12 checks whether that actually makes it risky.");

// 8 stats
s = pres.addSlide({ masterName: "CONTENT_LIGHT", sectionTitle: "First evidences" });
head(s, "First graphs · basic statistics", "Most components are used by one other; a few hubs carry the load");
img(s, "degree_distribution.png", 1.95, 2.15, 9.4, 2200 / 800,
    "Degree distributions. Online Boutique, 12 nodes and 16 edges: in-degree mostly 1, maximum 3; frontend has out-degree 7 and checkout 6. Astronomy Shop, 21 nodes and 37 edges: 13 components have in-degree 1, and flagd has in-degree 12",
    "Degree distribution chart");
s.addTable([
  [th("True graph"), th("Density", "right"), th("Most used (in-degree)", "right"), th("Longest chain", "right"), th("Cycles", "right")],
  ["Online Boutique", { text: "0.12", options: { align: "right" } }, { text: "productcatalog (3)", options: { align: "right" } }, { text: "4 hops", options: { align: "right" } }, { text: "0", options: { align: "right" } }],
  ["Astronomy Shop", { text: "0.09", options: { align: "right" } }, { text: "flagd (12)", options: { align: "right" } }, { text: "4 hops", options: { align: "right" } }, { text: "1", options: { align: "right" } }],
], tableOpts([3.4, 1.7, 3.233, 2.2, 1.6], { y: 5.7, fontSize: 14, margin: [3, 8, 3, 8], objectName: "Stats table" }));
source(s, "Edges point consumer → provider · source: results/graph_stats.json");
s.addNotes("These are sparse graphs with a hub structure. Chains are up to four hops long, which matters for the model choice: a two-layer GCN only sees two hops, so it may miss cascades that GraphGPS’s global attention can capture. The one cycle is real: the proxy serves the load generator’s web UI, and the load generator sends traffic through the proxy.");

// 9 f3
s = pres.addSlide({ masterName: "CONTENT_LIGHT", sectionTitle: "First evidences" });
head(s, "Evidence 3 · Do misses change the ranking?", "The order survived, but the top component lost dependents");
T(s, [{ text: "Extracted vs. true graph: " }, { text: "Spearman 1.00, Kendall 1.00", options: { bold: true, color: C.text1 } },
      { text: ", and the same top-5 set (6 components, with ties)." }],
  { objectName: "Agreement text", x: M, y: 2.2, w: 5.2, h: 1.1, fontSize: 18, color: C.text2 });
T(s, [{ text: "flagd drops from " }, { text: "12 to 9", options: { bold: true, color: C.text1 } },
      { text: " dependents. 4 of the 7 missed consumers still reach it through other paths, so 3 are lost." }],
  { objectName: "flagd text", x: M, y: 3.5, w: 5.2, h: 1.4, fontSize: 18, color: C.text2 });
T(s, "The blind runs agree: flagd has 9 dependents in all 3, and rank agreement with the truth is Spearman 0.98 ± 0.02.",
  { objectName: "Caveat text", x: M, y: 5.1, w: 5.2, h: 1.2, fontSize: 18, color: C.text2 });
img(s, "impact_compare_astronomy_shop.png", 6.3, 2.15, 6.43, 1800 / 1120,
    "Dependents per component, true vs extracted graph: flagd 12 vs 9; astronomy-db and kafka 6 in both; valkey-cart, quote, product-catalog 5 in both; others 3 to 4 in both",
    "Extracted vs true chart");
source(s, "Dependents = components that transitively depend on it · source: results/ranking_agreement.json");
s.addNotes("This previews our second research question: if the LLM misreads the design, how wrong does the risk assessment get? Here the order holds, because missed services still reach flagd indirectly. But flagd’s count shrinks from 12 to 9. Ties matter: six components share the top five scores, so I report the top five as a set including ties.");

// 10 f4
s = pres.addSlide({ masterName: "CONTENT_LIGHT", sectionTitle: "First evidences" });
head(s, "Evidence 4 · Choosing the label", "The composite formula and the failure simulation barely agree");
img(s, "composite_vs_impact.png", M, 2.15, 8.2, 2400 / 960,
    "Composite score vs simulated failure impact. Online Boutique Spearman 0.00, Astronomy Shop 0.09. redis-cart and astronomy-db: low composite, high impact. frontend-proxy and checkoutservice: high composite, low impact",
    "Composite vs impact chart");
T(s, [{ text: "Spearman " }, { text: "0.00", options: { bold: true, color: C.text1 } }, { text: " and " },
      { text: "0.09", options: { bold: true, color: C.text1 } }, { text: "." }],
  { objectName: "Spearman text", x: 9.2, y: 2.2, w: 3.53, h: 0.5, fontSize: 18, color: C.text2 });
T(s, [{ text: "Betweenness is zero for a datastore at the bottom of the graph, so astronomy-db scores " },
      { text: "0.03", options: { bold: true, color: C.text1 } }, { text: " even though 6 components depend on it." }],
  { objectName: "Betweenness text", x: 9.2, y: 2.9, w: 3.53, h: 2.0, fontSize: 18, color: C.text2 });
card(s, M, 5.55, CW, 1.0, "Decision box", "E6F0FC");
T(s, [{ text: "Decision: ", options: { bold: true } }, { text: "failure simulation is the main label. The composite score stays only as a heuristic to compare against." }],
  { objectName: "Decision text", x: M + 0.35, y: 5.8, w: CW - 0.7, h: 0.6, fontSize: 18, color: C.text1 });
source(s, "Composite = 0.4 in-degree + 0.2 out-degree + 0.4 betweenness (min-max normalised)");
s.addNotes("The assignment offers two labels. We computed both and they barely agree. Betweenness counts paths that pass through a node, and none pass through a database at the bottom of the graph, so the formula calls it safe even though everything above it needs it. This disagreement is partly built into the formula, which is exactly why it shouldn’t be the label.");

// 11 f5
s = pres.addSlide({ masterName: "CONTENT_DARK", sectionTitle: "First evidences" });
head(s, "Evidence 5 · Hard vs. soft dependencies", "Checking the code changes who is really risky");
const darkTxt = { color: C.accent5, fontSize: 17 };
T(s, [{ text: "We verified " }, { text: "13 soft edges", options: { bold: true, color: C.background1 } },
      { text: ": flag reads fall back to defaults (OpenFeature spec 1.4.10), and checkout still completes the order if email or Kafka fails." }],
  { objectName: "Soft text 1", x: M, y: 2.15, w: 5.4, h: 1.6, ...darkTxt });
T(s, [{ text: "flagd drops from " }, { text: "12 to 2", options: { bold: true, color: C.background1 } },
      { text: " dependents and Kafka from " }, { text: "6 to 2", options: { bold: true, color: C.background1 } },
      { text: ". astronomy-db, at 6, becomes the top risk." }],
  { objectName: "Soft text 2", x: M, y: 3.9, w: 5.4, h: 1.2, ...darkTxt });
T(s, [{ text: "Rank agreement falls to " }, { text: "Spearman 0.66", options: { bold: true, color: C.background1 } },
      { text: ". Edge strength matters as much as edges." }],
  { objectName: "Soft text 3", x: M, y: 5.25, w: 5.4, h: 0.9, ...darkTxt });
img(s, "soft_vs_hard_astronomy_shop.png", 6.35, 1.95, 6.38, 1800 / 1120,
    "Dependents per component, all hard vs soft dependencies removed: flagd 12 to 2, kafka 6 to 2, email 4 to 0; astronomy-db stays 6; valkey-cart, quote, product-catalog stay 5",
    "Hard vs soft chart");
source(s, "Evidence for each soft edge, with file and line numbers: data/soft_dependencies.json", true);
s.addNotes("The simple simulation treats every connection as a hard requirement. I checked the source code. Services read feature flags through OpenFeature, whose spec requires returning default values when the flag service is down. And checkout only logs the failure if the email or Kafka step fails, then returns the order anyway, though a Kafka outage can delay it. Removing those 13 edges, flagd falls from the top to almost nothing, and the product database becomes the real top risk. This is why the final project adds real fault injection, and why the extractor should also capture how strong each dependency is.");

// 12 plan
pres.addSection({ title: "Status note" });
s = pres.addSlide({ masterName: "CONTENT_LIGHT", sectionTitle: "Status note" });
head(s, "Status note", "Labels, features, baselines and metrics");
[["Where labels come from", "Failure simulation using hard edges only (soft edges removed). Reality check: feature-flag fault injection on the Astronomy Shop."],
 ["Model inputs, no leakage", "Component type, stateful flag, number of interfaces and a description embedding. No degree, betweenness or centrality."],
 ["Baselines and models", "Random forest on node features (no graph), composite heuristic, 2-layer GCN, and GraphGPS. K-means on embeddings for risk tiers."],
 ["Evaluation metrics", "MAE, Spearman and Kendall on risk, tie-aware top-5 overlap, extraction P/R/F1. 5 seeds, mean ± std, split by system."]]
  .forEach(([h, b], i) => {
    const w = (CW - 0.3) / 2, x = M + (i % 2) * (w + 0.3), y = 2.15 + Math.floor(i / 2) * 2.3;
    card(s, x, y, w, 2.05, `Plan card ${i + 1}`);
    T(s, h, { objectName: `Plan ${i + 1} title`, x: x + 0.3, y: y + 0.25, w: w - 0.6, h: 0.45, fontSize: 20, bold: true, color: C.text1, fontFace: THEME.headFontFace });
    T(s, b, { objectName: `Plan ${i + 1} body`, x: x + 0.3, y: y + 0.8, w: w - 0.6, h: 1.1, fontSize: 16, color: C.text2 });
  });
s.addNotes("Each assignment rule maps to a choice here. No leakage: graph metrics never enter the model. Non-graph baseline: the random forest sees only node features, so any gain from the GNN shows what structure adds. Small data: we train and test on different systems and repeat with five seeds. The label now uses only hard dependencies, because slide 12 showed soft ones distort the ranking.");

// 13 threats
s = pres.addSlide({ masterName: "CONTENT_LIGHT", sectionTitle: "Status note" });
head(s, "Threats to validity so far", "What could make these results look better than they are");
s.addTable([
  [th("Threat"), th("How we will handle it")],
  ["LLM memory", "Hiding service names barely changed recall (0.94 vs. 0.96), but descriptions stayed verbatim. Add lesser-known systems."],
  ["One model family", "9 blind runs agree (92–93% overlap), but all are Claude. Next: Gemini runs with my own API key."],
  ["Hard vs. soft edges", "13 soft edges verified so far; proxy routes and frontend calls still assumed hard. Confirm with fault injection."],
  ["Small data", "2 systems so far. Add 3–4 more apps plus realistic architecture variants."],
], tableOpts([3.0, 9.133], { y: 2.2, fontSize: 16, objectName: "Threats table" }));
s.addNotes("I want to be upfront about what could inflate these numbers. The model may already know these famous apps. Hiding the service names barely changed the result, which is encouraging, but the descriptions were the original text. And every run so far is Claude, so a Gemini run through the extractor script is the first task after the midterm.");

// 14 next
s = pres.addSlide({ masterName: "CONTENT_DARK", sectionTitle: "Status note" });
head(s, "Next steps", "From first evidences to the final report");
[["Step 1", "Gemini extraction runs (second model). Add Sock Shop, DeathStarBench and more."],
 ["Step 2", "Architecture variants, node features, description embeddings."],
 ["Step 3", "Train random forest, GCN and GraphGPS. Seeds, clustering, attention."],
 ["Step 4", "Fault injection on the Astronomy Shop, SME review, LLM advice, report."]]
  .forEach(([h, b], i) => {
    const w = (CW - 0.9) / 4, x = M + i * (w + 0.3);
    card(s, x, 2.15, w, 2.4, `Next card ${i + 1}`, C.accent4);
    T(s, h, { objectName: `Next ${i + 1} title`, x: x + 0.25, y: 2.4, w: w - 0.5, h: 0.4, fontSize: 18, bold: true, color: C.accent3, fontFace: THEME.headFontFace });
    T(s, b, { objectName: `Next ${i + 1} body`, x: x + 0.25, y: 2.9, w: w - 0.5, h: 1.5, fontSize: 16, color: C.background1 });
  });
T(s, "Three questions the final will answer: how well an LLM reads system designs, how much its errors move the risk ranking, and whether predicted risk matches real failures.",
  { objectName: "Closing text", x: M, y: 4.95, w: CW, h: 1.2, fontSize: 20, color: C.background1 });
s.addNotes("That’s where we are. Extraction, ground truth, graphs, labels and the soft-dependency check are working, tested, and reproducible from one script. Nine blind extraction runs back up the first results. Next come a second model, more systems, the models, and the real fault-injection test. Thank you, happy to take questions.");

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
