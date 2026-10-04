"""Runtime layout regression test for expandable problem cards.

Needs PySide6 (skipped otherwise). Runs headless via the offscreen platform.
Checks that after expanding a card, it grows and the next card moves below it.
"""
import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

try:
    from PySide6.QtWidgets import QApplication, QScrollArea, QWidget, QVBoxLayout
    from PySide6.QtTest import QTest
    import gui
    HAVE_QT = True
except ImportError:  # pragma: no cover
    HAVE_QT = False


def make_problem(i):
    return {
        "nivel": "ERROR", "severity": "HIGH", "tipo": "EXCEPTION",
        "mensaje_normalizado": f"Problem {i}", "mensaje": f"Problem {i}",
        "diagnostico": "Diagnostic text " * 40, "ocurrencias": 3,
        "evidence": [{"line": n, "text": "evidence " * 8} for n in range(1, 12)],
    }


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class CardLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.cards = [gui.ProblemCard(make_problem(i)) for i in range(4)]
        self.group = gui.CollapsibleGroup(
            "Errors", 4, "#ff6b7a", self.cards, initially_open=True
        )
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.addWidget(self.group)
        layout.addStretch()
        self.scroll.setWidget(content)
        self.scroll.resize(900, 700)
        self.scroll.show()
        QTest.qWait(50)

    def tearDown(self):
        self.scroll.close()

    def test_expanding_card_pushes_next_card_down(self):
        first, second = self.cards[0], self.cards[1]
        before_height = first.height()
        before_y = second.geometry().y()
        first.toggle()
        QTest.qWait(600)  # let the maximumHeight animation finish
        self.assertGreater(first.height(), before_height + 150)
        self.assertGreaterEqual(
            second.geometry().y(), first.geometry().y() + first.height()
        )
        self.assertGreater(second.geometry().y(), before_y)

    def test_cards_do_not_overlap_when_several_are_open(self):
        for card in self.cards[:3]:
            card.toggle()
            QTest.qWait(600)
        for upper, lower in zip(self.cards, self.cards[1:]):
            self.assertGreaterEqual(
                lower.geometry().y(), upper.geometry().y() + upper.height()
            )


if __name__ == "__main__":
    unittest.main()
