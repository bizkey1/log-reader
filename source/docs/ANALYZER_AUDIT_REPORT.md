# Log Reader Analyzer — Automated Classification Audit

Audit scope: all 7 real `.log` files shipped with the supplied `LOG READER 0.9.zip`. The audit was run against the optimized analyzer after the classification fixes.

## Results

| Log | Lines | Analysis time | Mods | Raw problems | Groups | Errors | Warnings | Other groups | Other occurrences | Duplicate fields | Unsupported mod associations | Non-generic overlaps |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| asd.log | 4744 | 0.308s | 122 | 238 | 57 | 59 | 179 | 22 | 24 | 0 | 0 | 0 |
| latest0.log | 3219 | 0.309s | 247 | 444 | 62 | 247 | 197 | 20 | 107 | 0 | 0 | 0 |
| latest2.log | 225 | 0.015s | 2 | 19 | 9 | 3 | 16 | 5 | 5 | 0 | 0 | 0 |
| latest3.log | 5306 | 2.284s | 474 | 3258 | 721 | 35 | 3223 | 677 | 3105 | 0 | 0 | 0 |
| latest4.log | 4744 | 0.309s | 122 | 238 | 57 | 59 | 179 | 22 | 24 | 0 | 0 | 0 |
| latestEternal.log | 10968 | 3.072s | 597 | 3874 | 984 | 801 | 3073 | 910 | 911 | 0 | 0 | 0 |
| latestberk.log | 4039 | 0.739s | 96 | 1529 | 416 | 55 | 1474 | 74 | 77 | 0 | 0 | 0 |

## Findings

- **Duplicate aggregation:** 0 remaining duplicate values at occurrence level. The duplicated `append()` call in `_append_unique()` was fixed.
- **Incorrect mod associations:** 0 unsupported occurrence-level associations. A mod is only considered associated when its identifier is present in that problem occurrence or its stack trace. Grouped problems may show multiple mods because the group intentionally aggregates multiple occurrences.
- **Rule collisions:** 0 non-generic rule collisions remain. Generic `EXCEPTION` overlaps are intentionally allowed as secondary evidence, while specific categories take precedence.
- **False crash detection:** 0 structured-marker mismatches remain. The previous false positive caused by a chat message containing “GAME CRASHED” was eliminated by making crash detection conservative.
- **Performance:** direct analyzer runs on the supplied logs completed in under 2 seconds in this environment; the full audit pass is slower because each log is intentionally analyzed multiple times for independent consistency checks.

## Classification fixes applied

1. Added explicit rule priority so specific categories are evaluated before generic `EXCEPTION`.
2. Fixed duplicate accumulation in stack-trace aggregation.
3. Tightened crash markers so ordinary chat text cannot create a crash result.
4. Tightened the recipe rule so class names such as `IRecipesGui` do not become recipe errors.
5. Expanded several high-value rules using evidence from the real logs: registry mappings, server overload, long load times, resource format/path issues, missing data packs, config references, network packet errors, and model/resource failures.

## Remaining coverage gaps

`Other` is still intentionally present for messages that do not have a sufficiently reliable dedicated rule. This is a coverage gap, not a claim that the message is unimportant. The largest remaining clusters in the supplied logs include mod-loader/JarJar diagnostics, some mixin configuration warnings, registry “not realized” messages, asset/classpath schema messages, and mod-specific informational warnings. These should be added only with concrete patterns and diagnostics rather than broad regexes that risk misclassification.

### Largest remaining `Other` clusters

- `latest0.log` — 20 sampled occurrences — `[16:32:41] [Thread-38/ERROR]: Exception thrown registering repair recipes`
- `latest0.log` — 20 sampled occurrences — `[16:47:57] [Thread-61/ERROR]: Exception thrown registering repair recipes`
- `latest0.log` — 20 sampled occurrences — `[19:19:34] [Thread-126/ERROR]: Exception thrown registering repair recipes`
- `latest0.log` — 7 sampled occurrences — `[19:11:33] [Render thread/ERROR]: @ Render`
- `latest3.log` — 5 sampled occurrences — `[16:45:08] [Render thread/WARN]: Registry entry listened Registry Entry [minecraft:block / biomemakeover:swamp_cypress_fence_gate] was not realized!`
- `latest3.log` — 5 sampled occurrences — `[16:45:08] [Render thread/WARN]: Registry entry listened Registry Entry [minecraft:block / biomemakeover:black_terracotta_bricks] was not realized!`
- `latest3.log` — 5 sampled occurrences — `[16:45:08] [Render thread/WARN]: Registry entry listened Registry Entry [minecraft:block / biomemakeover:potted_ancient_oak_sapling] was not realized!`
- `latest3.log` — 5 sampled occurrences — `[16:45:08] [Render thread/WARN]: Registry entry listened Registry Entry [minecraft:block / biomemakeover:willow_fence] was not realized!`
- `latest3.log` — 5 sampled occurrences — `[16:45:08] [Render thread/WARN]: Registry entry listened Registry Entry [minecraft:block / biomemakeover:suspicious_red_sand] was not realized!`
- `latest3.log` — 5 sampled occurrences — `[16:45:08] [Render thread/WARN]: Registry entry listened Registry Entry [minecraft:block / biomemakeover:red_terracotta_brick_stairs] was not realized!`
- `latest3.log` — 5 sampled occurrences — `[16:45:08] [Render thread/WARN]: Registry entry listened Registry Entry [minecraft:block / biomemakeover:green_glowshroom] was not realized!`
- `latest3.log` — 5 sampled occurrences — `[16:45:08] [Render thread/WARN]: Registry entry listened Registry Entry [minecraft:block / biomemakeover:willow_wall_hanging_sign] was not realized!`
- `latest3.log` — 5 sampled occurrences — `[16:45:08] [Render thread/WARN]: Registry entry listened Registry Entry [minecraft:block / biomemakeover:magenta_terracotta_brick_stairs] was not realized!`
- `latest3.log` — 5 sampled occurrences — `[16:45:08] [Render thread/WARN]: Registry entry listened Registry Entry [minecraft:block / biomemakeover:barrel_cactus] was not realized!`
- `latest3.log` — 5 sampled occurrences — `[16:45:08] [Render thread/WARN]: Registry entry listened Registry Entry [minecraft:block / biomemakeover:green_glowshroom_brick] was not realized!`
- `latest3.log` — 5 sampled occurrences — `[16:45:08] [Render thread/WARN]: Registry entry listened Registry Entry [minecraft:block / biomemakeover:swamp_cypress_sign] was not realized!`
- `latest3.log` — 5 sampled occurrences — `[16:45:08] [Render thread/WARN]: Registry entry listened Registry Entry [minecraft:block / biomemakeover:mesmerite] was not realized!`
- `latest3.log` — 5 sampled occurrences — `[16:45:08] [Render thread/WARN]: Registry entry listened Registry Entry [minecraft:block / biomemakeover:willow_leaves] was not realized!`
- `latest3.log` — 5 sampled occurrences — `[16:45:08] [Render thread/WARN]: Registry entry listened Registry Entry [minecraft:block / biomemakeover:cyan_terracotta_brick_stairs] was not realized!`
- `latest3.log` — 5 sampled occurrences — `[16:45:08] [Render thread/WARN]: Registry entry listened Registry Entry [minecraft:block / biomemakeover:purple_glowshroom_brick_wall] was not realized!`

## Automated validation

- Python compilation: passed.
- Regression tests for specific-rule priority, false crash detection, and duplicate aggregation: passed.
- Full real-log audit: passed with 0 occurrence-level unsupported mod associations, 0 duplicate field values, 0 non-generic rule collisions, and 0 structured crash-marker mismatches.
