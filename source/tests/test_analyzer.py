import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT.parent / "src"
sys.path.insert(0, str(SRC))

from analyzer import analizar_log, detectar_crash, detectar_tipo


class AnalyzerTests(unittest.TestCase):
    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            analizar_log(ROOT / "__missing_test_log__.log")

    def test_progress_callback(self):
        sample = ROOT / "sample_test.log"
        sample.write_text(
            "[12:00:00] [main/INFO]: Loading Minecraft 1.20.1\n"
            "[12:00:01] [main/WARN]: Missing texture: test:item\n"
            "[12:00:02] [main/ERROR]: Failed to load mod example\n",
            encoding="utf-8",
        )
        try:
            progress = []
            result = analizar_log(sample, progress_callback=lambda value, message: progress.append((value, message)))
            self.assertTrue(progress)
            self.assertEqual(progress[-1][0], 100)
            self.assertIn("estadisticas", result)
            self.assertGreaterEqual(result["estadisticas"]["problemas"], 1)
        finally:
            sample.unlink(missing_ok=True)

    def test_severity_and_evidence(self):
        sample = ROOT / "severity_test.log"
        sample.write_text(
            "[12:00:00] [main/ERROR]: ModLoadingException: missing required dependency: geckolib\n"
            "[12:00:01] [main/ERROR]: java.lang.NoClassDefFoundError: com/example/MissingClass\n"
            "[12:00:02] [main/WARN]: Missing texture: example:item\n",
            encoding="utf-8",
        )
        try:
            result = analizar_log(sample)
            self.assertTrue(result["problemas"])
            dependency = next(p for p in result["problemas"] if p["tipo"] == "DEPENDENCIA_REQUERIDA")
            self.assertEqual(dependency["severity"], "HIGH")
            self.assertTrue(dependency["evidence"])
            self.assertIn("geckolib", dependency["evidence"][0]["text"].lower())
            self.assertEqual(result["root_cause"]["problem_type"], "DEPENDENCIA_REQUERIDA")
            self.assertEqual(result["root_cause"]["confidence"], "HIGH")
        finally:
            sample.unlink(missing_ok=True)

    def test_crash_does_not_automatically_win_root_cause(self):
        sample = ROOT / "crash_root_test.log"
        sample.write_text(
            "[12:00:00] [main/ERROR]: ModLoadingException: missing required dependency: cloth_config\n"
            "---- Minecraft Crash Report ----\n"
            "Description: Rendering failure\n"
            "java.lang.RuntimeException: crash\n",
            encoding="utf-8",
        )
        try:
            result = analizar_log(sample)
            self.assertTrue(result["crash"])
            self.assertEqual(result["root_cause"]["problem_type"], "DEPENDENCIA_REQUERIDA")
            self.assertIn("dependency", result["analysis_summary"]["headline"].lower())
        finally:
            sample.unlink(missing_ok=True)

    def test_specific_classification_precedes_generic_exception(self):
        self.assertEqual(detectar_tipo("java.lang.NoClassDefFoundError: test.Example"), "CLASS_NOT_FOUND")
        self.assertEqual(detectar_tipo("ModLoadingException: missing required dependency: test"), "DEPENDENCIA_REQUERIDA")

    def test_real_crash_fixture_is_detected_and_highlightable(self):
        sample = ROOT / "fixtures" / "crash_rendering_overlay.log"
        result = analizar_log(sample)

        self.assertTrue(result["crash"])
        self.assertEqual(result["crash_confidence"], "HIGH")
        self.assertTrue(result["crash_evidence"])
        crash = next(p for p in result["problemas"] if p["tipo"] == "CRASH")
        self.assertEqual(crash["crash_exception"], "java.lang.NullPointerException")
        self.assertEqual(crash["crash_description"], "Rendering overlay")
        self.assertEqual(crash["crash_mod"], "create")
        self.assertIn("OpenCreateMenuButton", crash["crash_stack_frame"])
        self.assertEqual(result["root_cause"]["problem_type"], "CRASH")
        self.assertEqual(result["root_cause"]["confidence"], "MEDIUM")
        self.assertIn("create", result["root_cause"]["mods"])

    def test_chat_message_does_not_count_as_crash(self):
        sample = ROOT / "fixtures" / "chat_game_crashed.log"
        self.assertFalse(detectar_crash(sample.read_text(encoding="utf-8").splitlines()))
        result = analizar_log(sample)
        self.assertFalse(result["crash"])

    def test_nearby_explicit_failure_can_override_generic_crash_root(self):
        sample = ROOT / "nearby_crash_root_test.log"
        sample.write_text(
            "[12:00:00] [main/ERROR]: ModLoadingException: missing required dependency: cloth_config\n"
            "[12:00:01] [main/FATAL]: Preparing crash report with UUID 12345678-1234-1234-1234-123456789abc\n"
            "---- Minecraft Crash Report ----\n"
            "Description: Initializing game\n"
            "java.lang.RuntimeException: crash\n",
            encoding="utf-8",
        )
        try:
            result = analizar_log(sample)
            self.assertTrue(result["crash"])
            self.assertEqual(result["root_cause"]["problem_type"], "DEPENDENCIA_REQUERIDA")
        finally:
            sample.unlink(missing_ok=True)

    def test_included_logs_if_available(self):
        logs = [path for path in (ROOT / "fixtures").glob("*.log") if path.is_file()]
        if not logs:
            self.skipTest("No sample logs are present.")
        for path in logs:
            started = time.perf_counter()
            result = analizar_log(path)
            elapsed = time.perf_counter() - started
            self.assertIsInstance(result, dict)
            self.assertIn("metadata", result)
            self.assertIn("mods", result)
            self.assertIn("problemas", result)
            self.assertIn("estadisticas", result)
            self.assertIn("analysis_summary", result)
            self.assertLess(elapsed, 15, f"Analyzer exceeded 15 seconds on {path.name}: {elapsed:.2f}s")


if __name__ == "__main__":
    unittest.main(verbosity=2)
