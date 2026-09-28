# Useful knowledge, visible traces

Use CLI v0.1.16+. No `init` is required: commands default to your Personal Space.
Respect explicit Space boundaries; installing or signing in does not upload it.

```sh
obsdog search --query "deploy rollback" --actor-type agent --actor my-agent
obsdog search open --run RUN_ID --rank 1 --actor-type agent --actor my-agent
# Only when the opened revision genuinely supported the task:
obsdog search use --run RUN_ID --rank 1 --actor-type agent --actor my-agent
obsdog feedback add --run RUN_ID --rank 1 --kind usefulness --value useful \
  --reason "State the actual outcome" --evaluator-type agent --evaluator my-agent
obsdog memory show --query "deploy rollback" --format json
obsdog search --ranking lexical --query "deploy rollback"
```

Do not rate every returned result or invent use. Keep the same real actor across
the acquisition and evaluation. Noise can be evaluated after inspecting a hit;
usefulness requires actual use. Agent judgments are not human certification.
Source/authoring quality reviews remain a separate workflow.

The default bounded rank adjustment uses only that compiled query cue's utility
for the current revision. It does not spread popularity to unrelated queries,
add graph-only candidates or claim an association is a factual citation. Query
nodes describe search context; they do not create new factual notes. Useful use
strengthens activation; fading moves weak old observations out of the default
map without deleting source knowledge. A new useful use can recover the path.

`memory show` reveals reasons, actors and raw queries: treat its output as private.
`--as-of` changes the scoring clock over current source state, not past source
reconstruction. Query-filtered output retains Space-wide node/summary totals.
The snapshot digest identifies the full projection, not a complete replay archive.
Same cue/block/day deduplication limits repetition but is not Sybil resistance.

Bounds are explicit: 32,768 relevant events, 32 MiB payloads, 10,000 blocks and
20,000 associations. Co-use is omitted for runs with more than eight used blocks.
If projection is invalid or exceeds a bound, `learning_status` reports lexical
fallback; raw knowledge remains available. No background pruning job is created.

On an already authorized connected Space, push/pull normal observations to see
them in the web's Living memory map. Server v0.1.27 is required for that view.
Current browser viewing itself writes no use or feedback. These beta mechanisms
are testable hypotheses, not a guarantee of better answers or fewer tokens.
