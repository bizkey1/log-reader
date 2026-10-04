import ast
import re
from pathlib import Path
import unittest

GUI = Path(__file__).resolve().parent.parent / "src" / "gui.py"


class GuiStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = GUI.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)
        cls.classes = {node.name: node for node in cls.tree.body if isinstance(node, ast.ClassDef)}

    def test_gui_parses(self):
        self.assertTrue(self.source)

    def test_qwidget_api_methods_are_not_shadowed(self):
        forbidden = {"layout", "children", "window", "parentWidget", "show", "hide", "update", "resize", "move", "size", "geometry"}
        for class_name in ("Sidebar", "CollapsibleGroup", "ProblemCard", "LogReaderWindow"):
            node = self.classes[class_name]
            for child in ast.walk(node):
                if isinstance(child, (ast.Assign, ast.AnnAssign)):
                    targets = child.targets if isinstance(child, ast.Assign) else [child.target]
                    for target in targets:
                        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                            self.assertNotIn(
                                target.attr,
                                forbidden,
                                f"{class_name} shadows QWidget API: self.{target.attr}",
                            )

    def test_widget_layout_is_called_as_qt_method(self):
        bad = []
        for parent in ast.walk(self.tree):
            for child in ast.iter_child_nodes(parent):
                if isinstance(child, ast.Attribute) and child.attr == "layout":
                    if not (isinstance(parent, ast.Call) and parent.func is child):
                        bad.append(child.lineno)
        self.assertEqual(bad, [], f"Qt QWidget.layout used as a property on lines: {bad}")

    def test_no_layout_size_constraint_on_scroll_content(self):
        # SetMinAndMaxSize on the scroll content froze card expansion.
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Attribute):
                self.assertNotEqual(node.attr, "SetMinAndMaxSize")

    def test_no_manual_ancestor_layout_forcing(self):
        # Walking up parentWidget() calling activate()/invalidate() broke cards.
        self.assertNotIn("parentWidget()", self.source)

    def test_cards_expand_with_height_animation(self):
        # Known-working mechanism (Release Candidate): animate maximumHeight
        # and release it to "unlimited" when the animation finishes.
        for class_name in ("ProblemCard", "CollapsibleGroup"):
            node = self.classes[class_name]
            toggle = next(
                n for n in node.body
                if isinstance(n, ast.FunctionDef) and n.name == "toggle"
            )
            src = ast.get_source_segment(self.source, toggle)
            self.assertIn("QPropertyAnimation", src)
            self.assertIn("setMaximumHeight(16777215)", src)

    def test_filtering_uses_visibility_not_layout_rebuilds(self):
        self.assertNotIn("set_children", self.source)
        self.assertIn("card.setVisible(matches)", self.source)

    def test_worker_restores_switch_interval(self):
        self.assertIn("sys.setswitchinterval(previous_switch_interval)", self.source)

    def test_graphite_palette_and_scoped_frames(self):
        # No leftover violet tints from the old theme.
        self.assertNotIn("rgba(139,108,255", self.source)
        self.assertNotIn("#8b6cff", self.source.lower())
        # An unscoped "QFrame {" rule also hits every QLabel/QTextEdit inside.
        import re
        self.assertIsNone(re.search(r"QFrame\s*\{", self.source))

    def test_graphite_tokens(self):
        self.assertIn('COLOR_BG = "#0a0a0a"', self.source)
        self.assertIn('COLOR_TEXT = "#fafafa"', self.source)
        self.assertIn('COLOR_ORANGE = "#ff8833"', self.source)

    def test_navigation_and_cancel_copy_is_present(self):
        self.assertIn("Home", self.source)
        self.assertIn("Analyze Another Log", self.source)
        self.assertIn("Analysis cancelled", self.source)
        self.assertIn(":(", self.source)
        self.assertIn("Back to home", self.source)


if __name__ == "__main__":
    unittest.main()
