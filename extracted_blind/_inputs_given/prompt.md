You are a systems engineer analyzing a software architecture.

Read the design document below and extract the system's components and the
dependencies between them.

Rules:
1. Components: include application services, datastores (databases, caches)
   and message queues. Exclude end users, external third-party websites, and
   observability or telemetry infrastructure (collectors, metrics, tracing,
   dashboards).
2. A dependency A -> B means "A calls, reads from, writes to, or publishes to B,
   so A needs B to do its job". Direction always goes from consumer to provider.
3. Use only what the document states or strongly implies. For every
   dependency, set "evidence" to "explicit" if the document says it directly,
   or "implied" if you inferred it from the described behavior. Quote the
   supporting phrase in "reason" (at most 15 words).
4. For each component give: id (lowercase, as named in the document), type
   (one of: gateway, frontend, service, datastore, cache, queue, config,
   load_generator), stateful (true or false), and a one-sentence description.
5. Return JSON only, with no text before or after it, matching this schema:

{
  "system": "<name>",
  "components": [
    {"id": "...", "type": "...", "stateful": false, "description": "..."}
  ],
  "dependencies": [
    {"source": "...", "target": "...", "evidence": "explicit|implied", "reason": "..."}
  ]
}

DOCUMENT:
{DOCUMENT}
