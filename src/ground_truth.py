"""Build ground-truth dependency graphs from deployment config files.

LLM-generated component (Claude Opus 5.5), see prompts/prompts_log.md P2.
A dependency A -> B is counted when service A is
configured with a network address that resolves to service B (an *_ADDR,
*_HOST or connection-string variable). This captures runtime call wiring.
Startup-order entries (docker compose `depends_on`) are recorded separately
because they are not always runtime calls.

Scope rule (same as the extraction prompt): observability / telemetry
infrastructure is excluded.

Usage:
    python src/ground_truth.py --repo-ob ../microservices-demo --repo-otel ../opentelemetry-demo
"""
import argparse
import json
import re
from pathlib import Path

import yaml

TELEMETRY = {"otel-collector", "jaeger", "grafana", "prometheus", "opensearch",
             "opamp-server", "telemetry-docs", "firepit", "otel-ebpf-profiler"}

VAR = re.compile(r"\$\{([A-Z0-9_]+)\}")


def hosts_in(value, services):
    """Return services whose name appears as a hostname inside an address string."""
    found = set()
    for s in services:
        if re.search(r"(^|[/@=])" + re.escape(s) + r"($|[:/?])", value):
            found.add(s)
    return found


# ---------------------------------------------------------------- Kubernetes
def online_boutique(repo):
    mdir = Path(repo) / "kubernetes-manifests"
    docs = []
    for f in sorted(mdir.glob("*.yaml")):
        if f.name == "kustomization.yaml":
            continue
        docs += [d for d in yaml.safe_load_all(f.read_text()) if d]
    deployments = {d["metadata"]["name"]: d for d in docs if d["kind"] == "Deployment"}
    k8s_services = {d["metadata"]["name"] for d in docs if d["kind"] == "Service"}
    # a deployment is reachable under its Service name (frontend-external is the same pod)
    nodes = set(deployments)
    edges, unresolved = set(), []
    for name, dep in deployments.items():
        for c in dep["spec"]["template"]["spec"]["containers"]:
            for e in c.get("env", []) or []:
                val = str(e.get("value", ""))
                if not (e["name"].endswith("_ADDR")):
                    continue
                targets = hosts_in(val, k8s_services | nodes)
                if not targets:
                    unresolved.append((name, e["name"], val))
                for t in targets:
                    if t != name:
                        edges.add((name, t))
    return {"system": "Online Boutique",
            "source": "kubernetes-manifests/*.yaml (env *_ADDR)",
            "nodes": sorted(nodes),
            "edges": sorted(edges),
            "startup_only_edges": [],
            "notes": [f"{s}: {k}={v} points to a service not deployed in the base manifests"
                      for s, k, v in unresolved]}


# ---------------------------------------------------------------- Compose
def load_env(repo):
    env = {}
    for line in (Path(repo) / ".env").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k] = v
    return env


def resolve(v, env, depth=0):
    if depth > 10:
        return v
    out = VAR.sub(lambda m: env.get(m.group(1), ""), v)
    return out if out == v else resolve(out, env, depth + 1)


def astronomy_shop(repo):
    env = load_env(repo)
    merged = {}
    for f in ["compose.yaml", "compose.full.yaml"]:
        d = yaml.safe_load((Path(repo) / f).read_text())
        for name, svc in (d.get("services") or {}).items():
            m = merged.setdefault(name, {"env": [], "depends_on": set()})
            e = svc.get("environment", []) or []
            if isinstance(e, dict):
                e = [f"{k}={v}" for k, v in e.items()]
            m["env"] += e
            dep = svc.get("depends_on", []) or []
            m["depends_on"] |= set(dep)
    nodes = {n for n in merged if n not in TELEMETRY}
    addr_edges, startup = set(), set()
    for name in nodes:
        for item in merged[name]["env"]:
            key, _, inline = str(item).partition("=")
            if not re.search(r"(ADDR|HOST|CONNECTION_STRING)$", key):
                continue
            val = resolve(inline if inline else env.get(key, ""), env)
            for t in hosts_in(val, nodes):
                if t != name:
                    addr_edges.add((name, t))
        for t in merged[name]["depends_on"]:
            if t in nodes and t != name:
                startup.add((name, t))
    return {"system": "OpenTelemetry Astronomy Shop",
            "source": "compose.yaml + compose.full.yaml + .env (address variables)",
            "nodes": sorted(nodes),
            "edges": sorted(addr_edges),
            "startup_only_edges": sorted(startup - addr_edges),
            "notes": ["Excluded telemetry nodes: " + ", ".join(sorted(TELEMETRY & set(merged)))]}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-ob", required=True)
    ap.add_argument("--repo-otel", required=True)
    ap.add_argument("--out", default="data/ground_truth")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for key, g in [("online_boutique", online_boutique(a.repo_ob)),
                   ("astronomy_shop", astronomy_shop(a.repo_otel))]:
        (out / f"{key}.json").write_text(json.dumps(g, indent=2))
        print(f"{g['system']}: {len(g['nodes'])} nodes, {len(g['edges'])} edges"
              f" (+{len(g['startup_only_edges'])} startup-only)")
        for n in g["notes"]:
            print("   note:", n)
