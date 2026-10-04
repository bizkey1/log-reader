# LOG READER 1.0

Desktop diagnostic tool for Minecraft logs. Log Reader analyzes a `latest.log` without modifying it and turns raw log signals into grouped, searchable diagnostics.

## 1.0 scope

- Minecraft / loader / Java metadata extraction
- Fabric, Forge and NeoForge-oriented mod detection
- Error and warning classification with specific-rule priority
- Problem grouping and occurrence counts
- Severity: Critical / High / Medium / Low
- Evidence extracted from the original log
- Crash detection using structured Minecraft/Forge crash-report markers
- Probable root-cause analysis with explicit confidence
- "Why This Matters?" explanations
- Action-oriented recommendations
- Related mods, exceptions, dependencies and references
- Analysis Summary
- Search, severity/level filters and problem sorting
- Copy Diagnostic action for individual problems
- Responsive PySide6 GUI using a worker thread
- Real analysis progress
- Analysis cancellation
- Empty, invalid-file and failure states
- Regression tests and real-log performance checks
- Windows executable packaging through PyInstaller

## Crash detection

A log is considered to contain a confirmed crash only when Log Reader finds strong crash-report evidence such as:

- `Preparing crash report with UUID ...`
- `---- Minecraft Crash Report ----`
- `#@!@# Game crashed! Crash report saved to: ...`
- `#@!@# Server crashed! ...`
- `This crash report has been saved to: ...`

Generic `ERROR`, `Exception`, or chat text containing "game crashed" is not enough on its own. This prevents ordinary warnings and player chat from being reported as crashes.

When a crash report is available, Log Reader extracts the immediate exception, description, evidence and first mod-owned stack frame when possible. A probable mod cause is evidence-based, not proof of sole responsibility.

## Intentionally outside 1.0

- HTML/JSON export
- Local analysis history
- Automatic mod installation or repair
- CurseForge / Modrinth integration
- Real-time log monitoring
- Dependency graph
- Hardware benchmarking or launcher functionality

## Run from source

Requires Python 3.11 on Windows for the 1.0 release environment.

```powershell
python -m pip install -r source/requirements.txt
python source/src/main.py
```

## Run tests

```powershell
python -m unittest discover -s source/tests -v
```

or:

```powershell
pytest source/tests -q
```

## Build the Windows executable

The release build uses PyInstaller 6.22.3 and PySide6 6.11.2.

From the repository root:

```powershell
python -m pip install -r source/requirements.txt
pyinstaller --clean --noconfirm source/LogReader.spec
```

The resulting executable is `dist/LogReader.exe`. For the final repository release, place it at the repository root as `LogReader.exe` so non-technical users can find it immediately.

The GitHub Actions workflow in `.github/workflows/build-windows.yml` performs the same Windows build and assembles a release artifact with the executable plus the source tree.

## Architecture

```text
LOG READER 1.0/
├── LogReader.exe                 # final release executable
└── source/
    ├── src/
    │   ├── main.py
    │   ├── gui.py
    │   └── analyzer.py
    ├── tests/
    │   ├── test_analyzer.py
    │   └── fixtures/
    ├── docs/
    ├── LogReader.spec
    ├── requirements.txt
    ├── README.md
    └── .gitignore
```

`__pycache__`, virtual environments, build artifacts and user logs are intentionally excluded from source control.

## Root-cause limitation

Root-cause analysis is evidence-based and probabilistic. Log Reader does not guarantee that the identified probable cause is the sole underlying cause of a crash or malfunction. Confidence indicates how directly the available log evidence supports the displayed explanation.
