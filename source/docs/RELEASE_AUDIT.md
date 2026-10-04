# LOG READER 1.0 — Release Audit

## Current validation

- Python compilation: passed.
- Analyzer regression suite: 9 tests passed.
- Real-log audit: passed on the supplied `latest.log`, `latest2.log`, `latest3.log`, `latest4.log` and the real crash log `2026-05-24-3.log`.
- Analyzer performance: all supplied logs completed below 2 seconds in the audit environment.
- Confirmed crash regression: `2026-05-24-3.log` now detects the Forge/Minecraft crash markers, `java.lang.NullPointerException`, `Rendering overlay`, and the first mod-owned frame `com.simibubi.create.infrastructure.gui.OpenCreateMenuButton`.
- Chat false-positive regression: a real chat line containing `HER GAME CRASHED` is not classified as a crash.
- GUI source: compiles successfully; visual execution requires a Windows/PySide6 environment and was not performed in this Linux audit environment.
- Windows executable: packaging configuration is present, but the final `.exe` still requires a Windows build and smoke test before release.

## Changes made in this audit

1. Expanded crash detection to the structured markers actually emitted by Forge/Minecraft.
2. Added crash evidence and confidence fields to the analyzer result.
3. Added extraction of the immediate crash exception, description and first mod-owned stack frame.
4. Prevented distant startup warnings from automatically becoming the root cause of a later crash.
5. Preserved crash-specific metadata during problem grouping.
6. Added real crash and chat false-positive regression fixtures.
7. Kept severity/level/order combo boxes click-only.
8. Kept result-page widgets free of per-widget opacity effects to avoid scroll/repaint instability.
9. Added PyInstaller to the pinned release dependencies.
10. Updated the Windows workflow to include `docs/` in the release artifact.

## External comparison

The analyzer design was compared against public Minecraft log/crash-analysis projects and PyInstaller guidance. Common release-quality practices include structured parsing, rule-based classification, explicit confidence, real sample-log regression tests, and treating crash reports as multi-line structures rather than relying on the last line of a log. The current implementation follows those principles while keeping the 1.0 scope offline and deterministic.

## GUI: expandable problem cards

The card mechanism (`CollapsibleGroup`, `ProblemCard`, filter/sort via `setVisible`) is the one from the Release Candidate, confirmed working by manual testing. A later version replaced it with a layout-rebuilding approach (`set_children`, `SetMinAndMaxSize`, manual ancestor `activate()`), which left expanded cards cramped and overlapping the next card. Do not reintroduce those.

Guards: `tests/test_gui_static.py` (AST checks) and `tests/test_gui_layout.py` (headless Qt geometry; skipped without PySide6).

## Visual theme: Graphite

The GUI follows the Graphite style reference (near-black canvas, 1px #262626 hairline borders, Paper White primary buttons, Inter typography with Segoe UI fallback, 10px card / 8px button radii). Only stylesheets, tokens and font sizes changed; layout and card-expansion logic are untouched. Severity colors (error/warning/success/info) intentionally stay saturated because they carry meaning. All frame stylesheets are scoped by `objectName` so borders do not leak onto child labels.
