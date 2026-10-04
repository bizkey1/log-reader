import os

from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QTimer, QThread, QObject, Signal, Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QScrollArea,
    QFrame,
    QStackedWidget,
    QTextEdit,
    QLineEdit,
    QComboBox,
    QProgressBar,
    QGraphicsOpacityEffect,
    QSpacerItem,
    QSizePolicy,
)

# --- Graphite design tokens -------------------------------------------------
COLOR_BG = "#0a0a0a"           # Obsidian Canvas: page / card interiors
COLOR_BG_2 = "#000000"         # True Black: deepest recesses (code areas)
COLOR_SURFACE = "#171717"      # Charcoal Surface: elevated dark surfaces
COLOR_SURFACE_2 = "#262626"    # Graphite Edge: borders, secondary fills
COLOR_SURFACE_3 = "#464646"    # Steel Border: emphasized borders
COLOR_TEXT = "#fafafa"         # Cloud White: primary text
COLOR_TEXT_2 = "#a1a1a1"       # Fog: secondary text
COLOR_TEXT_3 = "#737373"       # Ash: tertiary text
COLOR_ACCENT = "#e5e5e5"       # Paper White: primary (filled) controls
COLOR_ACCENT_HOVER = "#fafafa"
COLOR_ACCENT_BRIGHT = "#a1a1a1"  # eyebrow labels (Fog)
COLOR_ORANGE = "#ff8833"       # Signal Orange: directional accents only
# Functional signal colors (severity / status) stay saturated on purpose.
COLOR_ERROR = "#ff6b7a"
COLOR_WARNING = "#e7b75c"
COLOR_SUCCESS = "#67d99a"
COLOR_INFO = "#72a8ff"

BORDER = "1px solid #262626"
BORDER_STRONG = "1px solid #464646"

STYLESHEET = f"""
QMainWindow {{
    background: {COLOR_BG};
}}

QWidget {{
    color: {COLOR_TEXT};
}}

QScrollArea {{
    border: none;
    background: transparent;
}}

QScrollArea > QWidget {{
    background: transparent;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 8px 2px 8px 0;
}}

QScrollBar::handle:vertical {{
    background: #262626;
    border-radius: 4px;
    min-height: 45px;
}}

QScrollBar::handle:vertical:hover {{
    background: #464646;
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QLineEdit {{
    background: {COLOR_BG};
    border: 1px solid #262626;
    border-radius: 10px;
    padding: 11px 14px;
    color: {COLOR_TEXT};
    font-size: 14px;
    selection-background-color: #464646;
}}

QLineEdit:focus {{
    border: 1px solid #464646;
}}

QTextEdit {{
    background: {COLOR_BG_2};
    border: 1px solid #262626;
    border-radius: 10px;
    color: {COLOR_TEXT_2};
    padding: 12px;
    selection-background-color: #464646;
}}

QToolTip {{
    background: {COLOR_SURFACE};
    color: {COLOR_TEXT};
    border: 1px solid #262626;
}}

QPushButton {{
    border: none;
}}
"""


def fade_in(widget, duration=500, delay=0):
    effect = widget.graphicsEffect()

    if effect is None:
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)

    effect.setOpacity(0.0)

    animation = QPropertyAnimation(effect, b"opacity", widget)
    animation.setDuration(duration)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    if delay:
        QTimer.singleShot(delay, animation.start)
    else:
        animation.start()

    widget._fade_animation = animation


class AnimatedButton(QPushButton):
    """Pale conversion button (Paper White on dark)."""

    def __init__(self, text):
        super().__init__(text)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(44)

        self.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_ACCENT};
                color: {COLOR_SURFACE};
                border: 1px solid rgba(255,255,255,26);
                border-radius: 8px;
                padding: 0 20px;
                font-size: 14px;
                font-weight: 500;
            }}

            QPushButton:hover {{
                background: {COLOR_ACCENT_HOVER};
            }}

            QPushButton:pressed {{
                background: #d4d4d4;
            }}
        """)


SECONDARY_BUTTON_STYLE = f"""
    QPushButton {{
        background: {COLOR_SURFACE_2};
        color: {COLOR_TEXT};
        border: {BORDER_STRONG};
        border-radius: 8px;
        padding: 0 16px;
        font-size: 14px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background: #303030;
    }}
    QPushButton:disabled {{
        color: {COLOR_TEXT_3};
        background: {COLOR_SURFACE};
        border: {BORDER};
    }}
"""


class NavButton(QPushButton):
    def __init__(self, icon, text):
        super().__init__()

        self.setText(f"{icon}    {text}")
        self.setFixedHeight(43)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setProperty("active", False)

        self.update_style()

    def set_active(self, active):
        self.setProperty("active", active)
        self.update_style()

    def update_style(self):
        if self.property("active"):
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {COLOR_SURFACE_2};
                    color: {COLOR_TEXT};
                    border: {BORDER};
                    border-radius: 8px;
                    text-align: left;
                    padding-left: 13px;
                    font-size: 14px;
                    font-weight: 500;
                }}

                QPushButton:hover {{
                    background: #303030;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {COLOR_TEXT_2};
                    border: 1px solid transparent;
                    border-radius: 8px;
                    text-align: left;
                    padding-left: 13px;
                    font-size: 14px;
                    font-weight: 500;
                }}

                QPushButton:hover {{
                    background: {COLOR_SURFACE};
                    color: {COLOR_TEXT};
                }}
            """)


class ElidedLabel(QLabel):
    """Single-line label that shortens its text with "…" to fit the width.

    It can shrink below the natural text width (so it never forces its
    parent wider) and never wraps (so it never gets clipped vertically).
    The full text is available as a tooltip.
    """

    def __init__(self, text=""):
        super().__init__()
        self._full_text = str(text)
        self.setWordWrap(False)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setToolTip(self._full_text)
        super().setText(self._full_text)

    def setText(self, text):
        self._full_text = str(text)
        self.setToolTip(self._full_text)
        self._apply_elision()

    def minimumSizeHint(self):
        return QSize(24, super().minimumSizeHint().height())

    def sizeHint(self):
        return QSize(
            self.fontMetrics().horizontalAdvance(self._full_text) + 2,
            super().sizeHint().height(),
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_elision()

    def _apply_elision(self):
        width = self.width()
        if width <= 1:
            shown = self._full_text
        else:
            shown = self.fontMetrics().elidedText(
                self._full_text, Qt.TextElideMode.ElideRight, width
            )
        if shown != self.text():
            super().setText(shown)


class ClickOnlyComboBox(QComboBox):
    """Combo box whose selection changes only through an explicit click."""

    def wheelEvent(self, event):
        event.ignore()


class Sidebar(QFrame):
    def __init__(self, window):
        super().__init__()

        self._window = window
        self.setFixedWidth(250)

        self.setObjectName("sidebar")
        self.setStyleSheet("""
            QFrame#sidebar {
                background: #0a0a0a;
                border: none;
                border-right: 1px solid #262626;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 24, 20, 20)
        layout.setSpacing(5)

        logo = QLabel("LOG READER")
        logo.setStyleSheet(f"""
            color: {COLOR_TEXT};
            font-size: 18px;
            font-weight: 600;
            letter-spacing: 1px;
        """)

        subtitle = QLabel("MINECRAFT DIAGNOSTICS")
        subtitle.setStyleSheet(f"""
            color: {COLOR_TEXT_3};
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 1.2px;
        """)

        layout.addWidget(logo)
        layout.addWidget(subtitle)
        layout.addSpacing(34)

        workspace = QLabel("WORKSPACE")
        workspace.setStyleSheet(f"""
            color: {COLOR_TEXT_3};
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 1.2px;
            padding-left: 14px;
        """)

        layout.addWidget(workspace)
        layout.addSpacing(6)

        self._layout = layout
        self.btn_overview = NavButton("⌂", "Overview")
        self.btn_analysis = NavButton("◈", "Analyze log")
        self.btn_problems = NavButton("!", "Problems")
        self.btn_mods = NavButton("▦", "Mods")

        self._nav_buttons = [
            self.btn_overview,
            self.btn_analysis,
            self.btn_problems,
            self.btn_mods,
        ]

        for button in self._nav_buttons:
            layout.addWidget(button)

        self._bottom_spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        layout.addItem(self._bottom_spacer)

        self.status_text = QLabel("READY")
        self.status_text.setStyleSheet(f"""
            color: {COLOR_SUCCESS};
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 1.2px;
            padding-left: 14px;
        """)

        layout.addWidget(self.status_text)


    def set_loaded_state(self, loaded):
        """Switch the sidebar between welcome and post-analysis navigation."""
        for button in self._nav_buttons:
            self._layout.removeWidget(button)

        # Remove the existing stretch item so we can place Analyze Another Log
        # immediately above the status area in the loaded state.
        if self._bottom_spacer is not None:
            self._layout.removeItem(self._bottom_spacer)
            self._bottom_spacer = None

        if loaded:
            self.btn_overview.setText("⌂    Home")
            self.btn_analysis.setText("◈    Analyze Another Log")
            self.btn_problems.setText("!    Problems")
            self.btn_mods.setText("▦    Mods")

            self._layout.addWidget(self.btn_overview)
            self._layout.addWidget(self.btn_problems)
            self._layout.addWidget(self.btn_mods)
            self._bottom_spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
            self._layout.addItem(self._bottom_spacer)
            self._layout.addWidget(self.btn_analysis)
        else:
            self.btn_overview.setText("⌂    Overview")
            self.btn_analysis.setText("◈    Analyze log")
            self.btn_problems.setText("!    Problems")
            self.btn_mods.setText("▦    Mods")

            self._layout.addWidget(self.btn_overview)
            self._layout.addWidget(self.btn_analysis)
            self._layout.addWidget(self.btn_problems)
            self._layout.addWidget(self.btn_mods)
            self._bottom_spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
            self._layout.addItem(self._bottom_spacer)

        self.layout().activate()


class StatCard(QFrame):
    def __init__(self, title, value, accent):
        super().__init__()

        self.setMinimumHeight(82)

        self.setObjectName("statCard")
        self.setStyleSheet("""
            QFrame#statCard {
                background: #0a0a0a;
                border: 1px solid #262626;
                border-radius: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(2)

        title_label = QLabel(title.upper())
        title_label.setStyleSheet(f"""
            color: {COLOR_TEXT_3};
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 1.2px;
        """)

        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet(f"""
            color: {accent};
            font-size: 24px;
            font-weight: 600;
        """)

        layout.addWidget(title_label)
        layout.addWidget(self.value_label)

    def set_value(self, value):
        self.value_label.setText(str(value))


class SectionHeader(QFrame):
    def __init__(self, title, subtitle=""):
        super().__init__()

        self.setObjectName("sectionHeader")
        self.setStyleSheet("""
            QFrame#sectionHeader {
                background: transparent;
                border: none;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        left = QVBoxLayout()
        left.setSpacing(2)

        title_label = QLabel(title.upper())
        title_label.setStyleSheet(f"""
            color: {COLOR_TEXT};
            font-size: 14px;
            font-weight: 600;
            letter-spacing: 1px;
        """)

        left.addWidget(title_label)

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet(f"""
                color: {COLOR_TEXT_3};
                font-size: 12px;
            """)
            left.addWidget(subtitle_label)

        layout.addLayout(left)
        layout.addStretch()


class CollapsibleGroup(QFrame):
    def __init__(
        self,
        title,
        count,
        accent,
        children,
        initially_open=False
    ):
        super().__init__()

        self.expanded = initially_open
        self._children = children
        self.animation = None

        self.setObjectName("collapsibleGroup")
        self.setStyleSheet("""
            QFrame#collapsibleGroup {
                background: transparent;
                border: none;
            }
        """)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self.header = QPushButton()
        self.header.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header.setMinimumHeight(68)

        self.header.setStyleSheet("""
            QPushButton {
                background: #0a0a0a;
                border: 1px solid #262626;
                border-radius: 10px;
                text-align: left;
            }

            QPushButton:hover {
                background: #171717;
                border: 1px solid #464646;
            }
        """)

        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(17, 0, 17, 0)
        header_layout.setSpacing(12)

        indicator = QLabel("●")
        indicator.setStyleSheet(f"""
            color: {accent};
            font-size: 14px;
        """)

        header_layout.addWidget(indicator)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {COLOR_TEXT};
            font-size: 14px;
            font-weight: 600;
        """)

        subtitle_label = QLabel(
            "Click to expand" if count else "Nothing detected"
        )
        subtitle_label.setStyleSheet(f"""
            color: {COLOR_TEXT_3};
            font-size: 12px;
        """)

        text_layout.addWidget(title_label)
        text_layout.addWidget(subtitle_label)

        header_layout.addLayout(text_layout)
        header_layout.addStretch()

        count_label = QLabel(str(count))
        count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        count_label.setMinimumWidth(34)

        count_label.setStyleSheet(f"""
            color: {accent};
            background: #171717;
            border: 1px solid #262626;
            border-radius: 10px;
            padding: 5px 8px;
            font-size: 14px;
            font-weight: 600;
        """)

        header_layout.addWidget(count_label)

        self.arrow = QLabel("⌄" if initially_open else "›")
        self.arrow.setStyleSheet(f"""
            color: {COLOR_ORANGE};
            font-size: 20px;
        """)

        header_layout.addWidget(self.arrow)

        self._layout.addWidget(self.header)

        self.content = QWidget()
        self.content.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)
        self.content.setVisible(initially_open)

        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(12, 8, 12, 4)
        content_layout.setSpacing(7)

        for child in children:
            content_layout.addWidget(child)

        self._layout.addWidget(self.content)

        self.header.clicked.connect(self.toggle)

    def toggle(self):
        self.expanded = not self.expanded
        self.arrow.setText("⌄" if self.expanded else "›")

        if self.expanded:
            self.content.setMaximumHeight(0)
            self.content.setVisible(True)

            target = self.content.sizeHint().height()

            animation = QPropertyAnimation(
                self.content,
                b"maximumHeight",
                self
            )

            animation.setDuration(220)
            animation.setStartValue(0)
            animation.setEndValue(target)
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)

            def finish_expand():
                self.content.setMaximumHeight(16777215)
                self.updateGeometry()
                self.content.updateGeometry()

            animation.finished.connect(finish_expand)

            self.animation = animation
            animation.start()

        else:
            start = self.content.height()

            animation = QPropertyAnimation(
                self.content,
                b"maximumHeight",
                self
            )

            animation.setDuration(180)
            animation.setStartValue(start)
            animation.setEndValue(0)
            animation.setEasingCurve(QEasingCurve.Type.InCubic)

            def finish():
                self.content.setVisible(False)
                self.content.setMaximumHeight(16777215)
                self.updateGeometry()
                self.content.updateGeometry()

            animation.finished.connect(finish)

            self.animation = animation
            animation.start()


class ProblemCard(QFrame):
    def __init__(self, problem, crash_cause=False):
        super().__init__()

        self.problem = problem
        self.crash_cause = crash_cause
        self.expanded = False
        self.animation = None

        self.setObjectName("problemCard")
        self.setStyleSheet(f"""
            QFrame#problemCard {{
                background: {COLOR_BG};
                border: {BORDER_STRONG if crash_cause else BORDER};
                border-radius: 10px;
            }}
        """)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        level = problem.get("nivel", "ERROR").upper()

        severity = str(problem.get("severity") or problem.get("importancia") or "LOW").upper()
        severity_colors = {
            "CRITICAL": COLOR_ERROR,
            "HIGH": COLOR_ERROR,
            "MEDIUM": COLOR_WARNING,
            "LOW": COLOR_INFO,
            "INFO": COLOR_TEXT_3,
        }
        accent = severity_colors.get(severity, COLOR_WARNING)

        self.header = QPushButton()
        self.header.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header.setMinimumHeight(66)

        if crash_cause:
            header_background = "#171717"
            header_border = "none"
            header_hover = "#262626"
        else:
            header_background = "transparent"
            header_border = "none"
            header_hover = "#171717"

        self.header.setStyleSheet(f"""
            QPushButton {{
                background: {header_background};
                border: {header_border};
                border-radius: 10px;
                text-align: left;
            }}

            QPushButton:hover {{
                background: {header_hover};
            }}
        """)

        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(14, 0, 14, 0)
        header_layout.setSpacing(12)

        dot = QLabel("●")
        dot.setStyleSheet(f"""
            color: {accent};
            font-size: 12px;
        """)

        header_layout.addWidget(dot)

        info = QVBoxLayout()
        info.setSpacing(3)

        title = (
            problem.get("mensaje_normalizado")
            or problem.get("tipo_nombre")
            or problem.get("tipo")
            or problem.get("mensaje")
            or "Unknown problem"
        )

        title_label = ElidedLabel(str(title))
        title_label.setStyleSheet(f"""
            color: {COLOR_TEXT};
            font-size: 14px;
            font-weight: 600;
        """)

        occurrences = problem.get("ocurrencias", 1)

        meta = f"{occurrences} occurrence"

        if occurrences != 1:
            meta += "s"

        importance = problem.get("importancia")

        if importance:
            meta += f"  ·  {importance}"

        component = problem.get("componente")

        if component:
            meta += f"  ·  {component}"

        hour = problem.get("hora")

        if hour:
            meta += f"  ·  {hour}"

        meta_label = ElidedLabel(meta)
        meta_label.setStyleSheet(f"""
            color: {COLOR_TEXT_3};
            font-size: 12px;
        """)

        info.addWidget(title_label)
        info.addWidget(meta_label)

        # The text column takes all the free width; long titles are elided
        # (full text in the tooltip and in the expanded diagnostic).
        header_layout.addLayout(info, 1)

        if crash_cause:
            crash_badge = QLabel("PROBABLE CRASH CAUSE")
            crash_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            crash_badge.setStyleSheet(f"""
                color: {COLOR_TEXT};
                background: #262626;
                border: 1px solid #464646;
                border-radius: 10px;
                padding: 4px 8px;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 1.2px;
            """)
            header_layout.addWidget(crash_badge)

        self.arrow = QLabel("›")
        self.arrow.setStyleSheet(f"""
            color: {COLOR_TEXT_3};
            font-size: 18px;
        """)

        header_layout.addWidget(self.arrow)

        self._layout.addWidget(self.header)

        self.detail = QWidget()
        self.detail.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)
        self.detail.setVisible(False)

        detail_layout = QVBoxLayout(self.detail)
        detail_layout.setContentsMargins(14, 0, 14, 14)

        detail_text = QTextEdit()
        detail_text.setReadOnly(True)
        detail_text.setMinimumHeight(220)
        detail_text.setMaximumHeight(320)
        detail_text.setFont(QFont("Cascadia Mono", 9))
        detail_text.setStyleSheet(f"""
            QTextEdit {{
                background: {COLOR_BG_2};
                color: {COLOR_TEXT_2};
                border: 1px solid #262626;
                border-radius: 8px;
                padding: 12px;
                selection-background-color: #464646;
            }}
        """)
        detail_text.setPlainText(self.build_details())

        detail_layout.addWidget(detail_text)

        copy_button = QPushButton("Copy diagnostic")
        copy_button.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_button.setFixedHeight(34)
        copy_button.setStyleSheet(SECONDARY_BUTTON_STYLE)
        copy_button.clicked.connect(
            lambda: QApplication.clipboard().setText(self.build_details())
        )
        detail_layout.addWidget(copy_button, 0, Qt.AlignmentFlag.AlignLeft)
        self._layout.addWidget(self.detail)

        self.header.clicked.connect(self.toggle)

    def build_details(self):
        p = self.problem
        lines = []

        def add_section(title, value):
            if value is None:
                return

            if isinstance(value, list):
                if not value:
                    return

                lines.append("")
                lines.append(title)
                lines.append("-" * 60)

                for item in value:
                    if isinstance(item, dict):
                        if "tipo" in item:
                            relation = item.get("relacion")
                            if relation:
                                lines.append(f"{item['tipo']}  ·  {relation}")
                            else:
                                lines.append(str(item["tipo"]))
                        elif "nombre" in item:
                            lines.append(str(item["nombre"]))
                        else:
                            lines.append(str(item))
                    else:
                        lines.append(str(item))

            else:
                value = str(value)

                if not value:
                    return

                lines.append("")
                lines.append(title)
                lines.append("-" * 60)
                lines.append(value)

        lines.append("PROBLEM DETAILS")
        lines.append("=" * 60)

        add_section("TYPE", p.get("tipo_nombre") or p.get("tipo"))
        add_section("DESCRIPTION", p.get("mensaje"))
        add_section("NORMALIZED", p.get("mensaje_normalizado"))
        add_section("DIAGNOSTIC", p.get("diagnostico"))
        add_section("WHY THIS MATTERS", p.get("why_this_matters"))
        add_section("PROBABLE ROOT CAUSE", p.get("root_cause", {}).get("summary") if isinstance(p.get("root_cause"), dict) else None)
        if isinstance(p.get("root_cause"), dict):
            add_section("ROOT CAUSE CONFIDENCE", p["root_cause"].get("confidence"))
        add_section("EVIDENCE", [f'Line {e.get("line")}: {e.get("text")}' for e in p.get("evidence", [])])
        add_section("RECOMMENDATION", p.get("recomendacion"))
        add_section("SEVERITY", p.get("severity") or p.get("importancia"))
        add_section("COMPONENT", p.get("componente"))
        add_section("RELATED MODS", p.get("mods_relacionados"))
        add_section("EXCEPTIONS", p.get("excepciones"))
        add_section("CAUSES", p.get("causas"))
        add_section("DEPENDENCIES", p.get("dependencias"))
        add_section("REFERENCES", p.get("referencias"))
        add_section("STACK TRACE", p.get("stack_trace"))
        add_section("LOG LINES", p.get("lineas"))

        occurrences = p.get("ocurrencias")
        first = p.get("primera_aparicion")
        last = p.get("ultima_aparicion")

        if occurrences or first or last:
            lines.append("")
            lines.append("OCCURRENCE")
            lines.append("-" * 60)

            if occurrences:
                lines.append(f"Occurrences: {occurrences}")

            if first:
                lines.append(f"First appearance: {first}")

            if last:
                lines.append(f"Last appearance: {last}")

        return "\n".join(lines)

    def toggle(self):
        if self.animation:
            if self.animation.state() == QPropertyAnimation.State.Running:
                return

        if not self.expanded:
            self.detail.setVisible(True)
            self.detail.setMaximumHeight(0)

            target = self.detail.sizeHint().height()

            animation = QPropertyAnimation(
                self.detail,
                b"maximumHeight",
                self
            )

            animation.setDuration(190)
            animation.setStartValue(0)
            animation.setEndValue(target)
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)

            def finish_expand():
                self.detail.setMaximumHeight(16777215)
                self.updateGeometry()
                self.detail.updateGeometry()

            animation.finished.connect(finish_expand)

            self.arrow.setText("⌄")
            self.expanded = True
            self.animation = animation

            animation.start()

        else:
            start = self.detail.height()

            animation = QPropertyAnimation(
                self.detail,
                b"maximumHeight",
                self
            )

            animation.setDuration(170)
            animation.setStartValue(start)
            animation.setEndValue(0)
            animation.setEasingCurve(QEasingCurve.Type.InCubic)

            def finish():
                self.detail.setVisible(False)
                self.detail.setMaximumHeight(16777215)
                self.updateGeometry()
                self.detail.updateGeometry()

            animation.finished.connect(finish)

            self.arrow.setText("›")
            self.expanded = False
            self.animation = animation

            animation.start()


class AnalysisCancelled(Exception):
    pass


class AnalysisWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)
    cancelled = Signal()
    progress = Signal(int, str)

    def __init__(self, analyzer, path):
        super().__init__()
        self.analyzer = analyzer
        self.path = path
        self._cancel_requested = False

    def request_cancel(self):
        self._cancel_requested = True

    @Slot()
    def run(self):
        # The analyzer is Python code running in a QThread. Long CPU-bound
        # sections can otherwise hold the GIL long enough for the GUI thread
        # to feel frozen even though it is technically alive.
        import sys
        previous_switch_interval = sys.getswitchinterval()
        sys.setswitchinterval(0.001)
        try:
            result = self.analyzer(
                self.path,
                progress_callback=self.report_progress,
            )
            if self._cancel_requested:
                self.cancelled.emit()
                return
            self.finished.emit(result)
        except AnalysisCancelled:
            self.cancelled.emit()
        except Exception as error:
            self.failed.emit(str(error))
        finally:
            sys.setswitchinterval(previous_switch_interval)

    def report_progress(self, value, message):
        if self._cancel_requested:
            raise AnalysisCancelled()
        self.progress.emit(int(value), str(message))


class LogReaderWindow(QMainWindow):
    def __init__(self, analizar_log):
        super().__init__()

        self.analizar_log = analizar_log
        self.last_result = None
        self.last_path = None
        self.analysis_thread = None
        self.analysis_worker = None
        self.analysis_running = False
        self.cancel_requested = False

        self.setWindowTitle("Log Reader")
        self.resize(1280, 800)
        self.setMinimumSize(1050, 700)
        self.setStyleSheet(STYLESHEET)

        root = QWidget()
        root.setObjectName("appRoot")

        root.setStyleSheet("""
            QWidget#appRoot {
                background: #0a0a0a;
            }
        """)

        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = Sidebar(self)
        root_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("""
            QStackedWidget {
                background: transparent;
            }
        """)
        root_layout.addWidget(self.stack)

        self.home_page = self.create_home_page()
        self.analysis_page = self.create_analysis_page()
        self.mods_page = self.create_mods_page()

        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.analysis_page)
        self.stack.addWidget(self.mods_page)

        self.sidebar.btn_overview.clicked.connect(
            self.show_home_welcome
        )

        self.sidebar.btn_analysis.clicked.connect(
            self.select_file
        )

        self.sidebar.btn_problems.clicked.connect(
            self.show_problems
        )

        self.sidebar.btn_mods.clicked.connect(
            self.show_mods
        )

        self.sidebar.btn_overview.set_active(True)

        self.setCentralWidget(root)

        QTimer.singleShot(
            120,
            lambda: self.animate_home()
        )

    def show_home_welcome(self):
        """Return to the initial welcome screen and reset the loaded-log workspace."""
        if self.analysis_running:
            return

        self.last_result = None
        self.last_path = None
        self.cancel_requested = False
        self.sidebar.set_loaded_state(False)
        self.set_status("READY", COLOR_SUCCESS)

        old_page = self.home_page
        self.stack.removeWidget(old_page)
        old_page.deleteLater()
        self.home_page = self.create_home_page()
        self.stack.insertWidget(0, self.home_page)
        self.show_page(0, self.sidebar.btn_overview)
        QTimer.singleShot(0, self.animate_home)

    def show_overview(self):
        if self.last_result:
            self.build_overview(self.last_result, self.last_path)
        self.show_page(0, self.sidebar.btn_overview)

    def build_overview(self, result, path=None):
        # Rebuild the overview into a compact post-analysis dashboard.
        layout = self.home_page.layout()
        self.clear_layout(layout)
        layout.setContentsMargins(58, 45, 58, 45)
        layout.setSpacing(22)

        metadata = result.get("metadata", {})
        summary = result.get("analysis_summary", {})
        root = result.get("root_cause")
        stats = result.get("estadisticas", {})
        problemas = result.get("problemas", [])
        crash = result.get("crash", False)

        eyebrow = QLabel("LATEST ANALYSIS")
        eyebrow.setStyleSheet(f"color: {COLOR_ACCENT_BRIGHT}; font-size: 10px; font-weight: 600; letter-spacing: 1.2px;")
        title = QLabel("Analysis overview")
        title.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 36px; font-weight: 500;")
        filename = QLabel(os.path.basename(path) if path else "Analyzed log")
        filename.setStyleSheet(f"color: {COLOR_TEXT_3}; font-size: 12px;")
        layout.addWidget(eyebrow)
        layout.addWidget(title)
        layout.addWidget(filename)

        summary_frame = QFrame()
        summary_frame.setObjectName("summaryFrame")
        summary_frame.setStyleSheet("QFrame#summaryFrame { background: #171717; border: 1px solid #262626; border-radius: 10px; }")
        sl = QVBoxLayout(summary_frame)
        sl.setContentsMargins(22, 19, 22, 19)
        sl.setSpacing(7)
        st = QLabel("ANALYSIS SUMMARY")
        st.setStyleSheet(f"color: {COLOR_ACCENT_BRIGHT}; font-size: 10px; font-weight: 600; letter-spacing: 1.2px;")
        sh = QLabel(summary.get("headline") or "No summary available.")
        sh.setWordWrap(True)
        sh.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 14px; font-weight: 600;")
        sm = QLabel(f"{len(problemas)} grouped problems  ·  {stats.get('errores', 0)} error occurrences  ·  {stats.get('warnings', 0)} warnings  ·  {len(result.get('mods', []))} detected mods")
        sm.setStyleSheet(f"color: {COLOR_TEXT_3}; font-size: 12px;")
        sl.addWidget(st); sl.addWidget(sh); sl.addWidget(sm)
        layout.addWidget(summary_frame)

        cards = QHBoxLayout()
        cards.setSpacing(12)
        severity_counts = summary.get("severity_counts", {})
        for label, value, accent in (("CRITICAL", severity_counts.get("CRITICAL", 0), COLOR_ERROR), ("HIGH", severity_counts.get("HIGH", 0), COLOR_ERROR), ("MEDIUM", severity_counts.get("MEDIUM", 0), COLOR_WARNING), ("LOW", severity_counts.get("LOW", 0), COLOR_INFO)):
            cards.addWidget(StatCard(label, value, accent))
        layout.addLayout(cards)

        root_frame = QFrame()
        if root:
            confidence = str(root.get("confidence", "UNCERTAIN")).upper()
            accent = COLOR_SUCCESS if confidence == "HIGH" else COLOR_WARNING if confidence == "MEDIUM" else COLOR_TEXT_3
            border = "#464646" if confidence in ("HIGH", "MEDIUM") else "#262626"
            root_frame.setObjectName("rootFrame")
            root_frame.setStyleSheet(f"QFrame#rootFrame {{ background: #0a0a0a; border: 1px solid {border}; border-radius: 10px; }}")
            rl = QVBoxLayout(root_frame); rl.setContentsMargins(20, 17, 20, 17); rl.setSpacing(6)
            rt = QLabel("PROBABLE ROOT CAUSE")
            rt.setStyleSheet(f"color: {accent}; font-size: 10px; font-weight: 600; letter-spacing: 1.2px;")
            rr = QLabel(root.get("summary", "No root cause summary available.")); rr.setWordWrap(True)
            rr.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 14px; font-weight: 600;")
            rc = QLabel(f"Confidence: {confidence}" + (f"  ·  {', '.join(root.get('mods', []))}" if root.get('mods') else ""))
            rc.setStyleSheet(f"color: {COLOR_TEXT_3}; font-size: 12px;")
            rl.addWidget(rt); rl.addWidget(rr); rl.addWidget(rc)
        else:
            root_frame.setObjectName("rootFrame")
            root_frame.setStyleSheet("QFrame#rootFrame { background: #0a0a0a; border: 1px solid #262626; border-radius: 10px; }")
            rl = QVBoxLayout(root_frame); rl.setContentsMargins(20,17,20,17)
            rt = QLabel("PROBABLE ROOT CAUSE")
            rt.setStyleSheet(f"color: {COLOR_TEXT_3}; font-size: 10px; font-weight: 600; letter-spacing: 1.2px;")
            rr = QLabel("No single probable root cause was established from the available evidence.")
            rr.setWordWrap(True); rr.setStyleSheet(f"color: {COLOR_TEXT_2}; font-size: 14px;")
            rl.addWidget(rt); rl.addWidget(rr)
        layout.addWidget(root_frame)

        bottom = QHBoxLayout(); bottom.setSpacing(12)
        meta_frame = QFrame(); meta_frame.setObjectName("metaFrame"); meta_frame.setStyleSheet("QFrame#metaFrame { background: #0a0a0a; border: 1px solid #262626; border-radius: 10px; }")
        ml = QVBoxLayout(meta_frame); ml.setContentsMargins(18,15,18,15); ml.setSpacing(6)
        mt = QLabel("ENVIRONMENT"); mt.setStyleSheet(f"color: {COLOR_TEXT_3}; font-size: 10px; font-weight: 600; letter-spacing: 1.2px;")
        mv = QLabel(f"Minecraft {metadata.get('minecraft','Unknown')}  ·  {metadata.get('loader','Unknown')} {metadata.get('loader_version','')}  ·  Java {metadata.get('java','Unknown')}  ·  {len(result.get('mods', []))} mods")
        mv.setWordWrap(True); mv.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 12px; font-weight: 600;")
        ml.addWidget(mt); ml.addWidget(mv); bottom.addWidget(meta_frame, 1)
        crash_border = "rgba(255,107,122,90)" if crash else "#262626"
        crash_frame = QFrame(); crash_frame.setObjectName("crashFrame"); crash_frame.setStyleSheet(f"QFrame#crashFrame {{ background: #171717; border: 1px solid {crash_border}; border-radius: 10px; }}")
        cl = QVBoxLayout(crash_frame); cl.setContentsMargins(18,15,18,15); cl.setSpacing(5)
        ct = QLabel("CRASH STATUS"); ct.setStyleSheet(f"color: {COLOR_ERROR if crash else COLOR_SUCCESS}; font-size: 10px; font-weight: 600; letter-spacing: 1.2px;")
        cv = QLabel("Crash detected" if crash else "No crash detected"); cv.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 14px; font-weight: 600;")
        cl.addWidget(ct); cl.addWidget(cv); bottom.addWidget(crash_frame, 0)
        layout.addLayout(bottom)

        new_button = AnimatedButton("Analyze another log")
        new_button.setFixedWidth(200); new_button.clicked.connect(self.select_file)
        layout.addWidget(new_button, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addStretch()

    def create_home_page(self):
        page = QWidget()
        page.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)

        layout = QVBoxLayout(page)
        layout.setContentsMargins(58, 45, 58, 45)
        layout.setSpacing(25)

        eyebrow = QLabel("MINECRAFT LOG ANALYSIS")
        eyebrow.setStyleSheet(f"""
            color: {COLOR_ACCENT_BRIGHT};
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 1.2px;
        """)

        title = QLabel("Log Reader")
        title.setStyleSheet(f"""
            color: {COLOR_TEXT};
            font-size: 60px;
            font-weight: 500;
            letter-spacing: -1.5px;
        """)

        subtitle = QLabel(
            "Understand what happened inside your Minecraft instance."
        )

        subtitle.setStyleSheet(f"""
            color: {COLOR_TEXT_2};
            font-size: 14px;
        """)

        layout.addWidget(eyebrow)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        hero = QFrame()
        hero.setMinimumHeight(350)

        hero.setObjectName("heroFrame")
        hero.setStyleSheet("""
            QFrame#heroFrame {
                background: #0a0a0a;
                border: 1px solid #262626;
                border-radius: 10px;
            }
        """)

        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(38, 34, 38, 34)
        hero_layout.setSpacing(15)

        small = QLabel("START A NEW ANALYSIS")
        small.setStyleSheet(f"""
            color: {COLOR_ACCENT_BRIGHT};
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 1.2px;
        """)

        hero_title = QLabel(
            "Turn a raw Minecraft log into useful information."
        )

        hero_title.setWordWrap(True)
        hero_title.setStyleSheet(f"""
            color: {COLOR_TEXT};
            font-size: 36px;
            font-weight: 500;
        """)

        hero_text = QLabel(
            "Select your latest.log and let Log Reader extract "
            "metadata, installed mods, errors, warnings and recurring "
            "problems without modifying the original file."
        )

        hero_text.setWordWrap(True)
        hero_text.setMaximumWidth(720)

        hero_text.setStyleSheet(f"""
            color: {COLOR_TEXT_2};
            font-size: 14px;
        """)

        hero_layout.addWidget(small)
        hero_layout.addWidget(hero_title)
        hero_layout.addWidget(hero_text)
        hero_layout.addStretch()

        button = AnimatedButton("Select .log file")
        button.setFixedWidth(190)
        button.clicked.connect(self.select_file)

        hero_layout.addWidget(
            button,
            0,
            Qt.AlignmentFlag.AlignLeft
        )

        layout.addWidget(hero)

        info = QLabel(
            "PARSE     →     GROUP     →     INSPECT"
        )

        info.setStyleSheet(f"""
            color: {COLOR_TEXT_3};
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 1.2px;
        """)

        layout.addWidget(info)
        layout.addStretch()

        self.home_eyebrow = eyebrow
        self.home_title = title
        self.home_subtitle = subtitle
        self.home_hero = hero
        self.home_info = info

        return page

    def animate_home(self):
        fade_in(self.home_eyebrow, 350, 0)
        fade_in(self.home_title, 500, 100)
        fade_in(self.home_subtitle, 450, 200)
        fade_in(self.home_hero, 600, 300)
        fade_in(self.home_info, 450, 500)

    def create_analysis_page(self):
        page = QWidget()
        page.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)

        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)

        self.analysis_scroll = QScrollArea()
        self.analysis_scroll.setWidgetResizable(True)
        self.analysis_scroll.viewport().setStyleSheet(
            "background: transparent;"
        )

        self.analysis_content = QWidget()
        self.analysis_content.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)

        self.analysis_layout = QVBoxLayout(
            self.analysis_content
        )

        self.analysis_layout.setContentsMargins(
            48,
            40,
            48,
            55
        )

        self.analysis_layout.setSpacing(22)

        self.analysis_scroll.setWidget(
            self.analysis_content
        )

        outer.addWidget(self.analysis_scroll)

        return page

    def create_mods_page(self):
        page = QWidget()
        page.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)

        outer = QVBoxLayout(page)
        outer.setContentsMargins(45, 35, 45, 40)

        self.mods_scroll = QScrollArea()
        self.mods_scroll.setWidgetResizable(True)
        self.mods_scroll.viewport().setStyleSheet(
            "background: transparent;"
        )

        self.mods_content = QWidget()
        self.mods_content.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)

        self.mods_layout = QVBoxLayout(
            self.mods_content
        )

        self.mods_layout.setContentsMargins(
            0,
            0,
            0,
            30
        )

        self.mods_layout.setSpacing(18)

        self.mods_scroll.setWidget(
            self.mods_content
        )

        outer.addWidget(self.mods_scroll)

        return page

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)

            widget = item.widget()
            child_layout = item.layout()

            if widget:
                widget.deleteLater()
            elif child_layout:
                self.clear_layout(child_layout)

    def set_status(self, text, color):
        self.sidebar.status_text.setText(text)

        self.sidebar.status_text.setStyleSheet(f"""
            color: {color};
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 1.2px;
            padding-left: 14px;
        """)

    def select_file(self):
        if self.analysis_running:
            return

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Minecraft Log",
            "",
            "Log files (*.log);;Text files (*.txt);;All files (*)"
        )

        if not path:
            return

        self.start_analysis(path)

    def start_analysis(self, path):
        if self.analysis_running:
            return

        self.analysis_running = True
        self.set_status(
            "ANALYZING...",
            COLOR_ACCENT_BRIGHT,
        )

        self.show_loading_page(path)
        self.sidebar.btn_analysis.setEnabled(False)

        self.analysis_thread = QThread(self)
        self.analysis_worker = AnalysisWorker(
            self.analizar_log,
            path,
        )
        self.analysis_worker.moveToThread(
            self.analysis_thread
        )

        self.analysis_thread.started.connect(
            self.analysis_worker.run
        )
        self.analysis_worker.progress.connect(
            self.on_analysis_progress
        )
        self.analysis_worker.finished.connect(
            self.on_analysis_finished
        )
        self.analysis_worker.failed.connect(
            self.on_analysis_failed
        )
        self.analysis_worker.cancelled.connect(
            self.on_analysis_cancelled
        )

        self.analysis_worker.finished.connect(
            self.analysis_thread.quit
        )
        self.analysis_worker.failed.connect(
            self.analysis_thread.quit
        )
        self.analysis_worker.cancelled.connect(
            self.analysis_thread.quit
        )
        self.analysis_thread.finished.connect(
            self.analysis_worker.deleteLater
        )
        self.analysis_thread.finished.connect(
            self.on_analysis_thread_finished
        )

        self.analysis_thread.start()

    def cancel_analysis(self):
        if not self.analysis_running or not self.analysis_worker:
            return
        self.cancel_requested = True
        self.analysis_worker.request_cancel()
        self.set_status("CANCELLING...", COLOR_WARNING)
        if hasattr(self, "loading_status"):
            self.loading_status.setText("Cancelling analysis...")
        if hasattr(self, "cancel_button"):
            self.cancel_button.setEnabled(False)

    @Slot(int, str)
    def on_analysis_progress(self, value, message):
        if hasattr(self, "loading_progress"):
            self.loading_progress.setValue(value)

        if hasattr(self, "loading_status"):
            self.loading_status.setText(message)

        self.set_status(
            "ANALYZING...",
            COLOR_ACCENT_BRIGHT,
        )

    @Slot(object)
    def on_analysis_finished(self, result):
        self.last_result = result

        self.set_status(
            "BUILDING RESULTS...",
            COLOR_ACCENT_BRIGHT,
        )

        self.loading_status.setText(
            "Building results..."
        )
        self.loading_progress.setValue(100)

        self.last_path = self.analysis_worker.path

        self.build_analysis(
            result,
            self.last_path,
        )
        self.build_overview(result, self.last_path)

        self.sidebar.set_loaded_state(True)

        self.show_page(
            1,
            self.sidebar.btn_problems,
        )

        self.set_status(
            "ANALYSIS READY",
            COLOR_SUCCESS,
        )

        self.analysis_running = False
        self.cancel_requested = False
        self.sidebar.btn_analysis.setEnabled(True)

        # Result widgets live inside a QScrollArea. Applying
        # QGraphicsOpacityEffect to each child can leave stale/partially
        # repainted widgets after scrolling, so results remain static.
        QTimer.singleShot(0, self.reset_analysis_scroll)

    @Slot(str)
    def on_analysis_failed(self, error):
        self.analysis_running = False
        self.sidebar.btn_analysis.setEnabled(True)

        self.set_status(
            "ANALYSIS ERROR",
            COLOR_ERROR,
        )

        self.show_error(error)

    @Slot()
    def on_analysis_cancelled(self):
        self.analysis_running = False
        self.cancel_requested = False
        self.sidebar.btn_analysis.setEnabled(True)
        self.set_status("READY", COLOR_SUCCESS)
        self.show_cancelled_state()

    def show_cancelled_state(self):
        self.clear_layout(self.analysis_layout)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 70, 30, 70)
        layout.setSpacing(14)

        face = QLabel(":(")
        face.setAlignment(Qt.AlignmentFlag.AlignCenter)
        face.setStyleSheet(f"""
            color: {COLOR_TEXT};
            font-size: 64px;
            font-weight: 500;
        """)

        title = QLabel("Analysis cancelled")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"""
            color: {COLOR_TEXT};
            font-size: 36px;
            font-weight: 500;
        """)

        description = QLabel(
            "The analysis was cancelled before the log could be fully processed."
        )
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setWordWrap(True)
        description.setStyleSheet(f"""
            color: {COLOR_TEXT_2};
            font-size: 14px;
        """)

        home_button = AnimatedButton("Back to home")
        home_button.setFixedWidth(180)
        home_button.clicked.connect(self.show_home_welcome)

        layout.addStretch()
        layout.addWidget(face)
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addSpacing(12)
        layout.addWidget(home_button, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()

        self.analysis_layout.addWidget(container)
        self.show_page(1, None)

        fade_in(face, 350)
        fade_in(title, 400, 80)
        fade_in(description, 350, 160)
        fade_in(home_button, 350, 220)

    @Slot()
    def on_analysis_thread_finished(self):
        self.analysis_thread = None
        self.analysis_worker = None

    def show_loading_page(self, path):
        self.clear_layout(
            self.analysis_layout
        )

        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(
            30,
            100,
            30,
            100
        )
        layout.setSpacing(15)

        title = QLabel("Analyzing log")
        title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        title.setStyleSheet(f"""
            color: {COLOR_TEXT};
            font-size: 36px;
            font-weight: 500;
        """)

        filename = QLabel(
            os.path.basename(path)
        )

        filename.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        filename.setStyleSheet(f"""
            color: {COLOR_TEXT_3};
            font-size: 12px;
        """)

        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(0)
        progress.setFixedHeight(3)
        progress.setMaximumWidth(560)

        progress.setStyleSheet(f"""
            QProgressBar {{
                background: #262626;
                border: none;
                border-radius: 2px;
            }}

            QProgressBar::chunk {{
                background: {COLOR_TEXT};
                border-radius: 2px;
            }}
        """)

        status = QLabel(
            "Reading log file..."
        )

        status.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        status.setStyleSheet(f"""
            color: {COLOR_TEXT_3};
            font-size: 12px;
        """)

        cancel_button = QPushButton("Cancel analysis")
        cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_button.setFixedHeight(38)
        cancel_button.setMaximumWidth(180)
        cancel_button.setStyleSheet(SECONDARY_BUTTON_STYLE)
        cancel_button.clicked.connect(self.cancel_analysis)

        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(filename)
        layout.addSpacing(15)

        layout.addWidget(
            progress,
            0,
            Qt.AlignmentFlag.AlignHCenter
        )

        layout.addWidget(status)
        layout.addSpacing(8)
        layout.addWidget(cancel_button, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()

        self.loading_progress = progress
        self.loading_status = status
        self.cancel_button = cancel_button

        self.analysis_layout.addWidget(container)

        self.show_page(
            1,
            self.sidebar.btn_analysis
        )

        fade_in(container, 350)

    def build_analysis(self, result, path):
        self.clear_layout(
            self.analysis_layout
        )

        metadata = result.get(
            "metadata",
            {}
        )

        problemas = result.get(
            "problemas",
            []
        )

        errores = result.get(
            "errores",
            []
        )

        warnings = result.get(
            "warnings",
            []
        )

        excepciones = result.get(
            "excepciones",
            []
        )

        crash = result.get(
            "crash",
            False
        )

        estadisticas = result.get(
            "estadisticas",
            {}
        )

        filename = os.path.basename(path)

        eyebrow = QLabel("ANALYSIS")

        eyebrow.setStyleSheet(f"""
            color: {COLOR_ACCENT_BRIGHT};
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 1.2px;
        """)

        title = QLabel("Log analysis")

        title.setStyleSheet(f"""
            color: {COLOR_TEXT};
            font-size: 36px;
            font-weight: 500;
        """)

        file_label = QLabel(filename)

        file_label.setStyleSheet(f"""
            color: {COLOR_TEXT_3};
            font-size: 12px;
        """)

        title_row = QHBoxLayout()
        title_row.setSpacing(18)

        title_column = QVBoxLayout()
        title_column.setSpacing(4)

        title_column.addWidget(eyebrow)
        title_column.addWidget(title)
        title_column.addWidget(file_label)

        title_row.addLayout(title_column)
        title_row.addStretch()

        self.analysis_layout.addLayout(title_row)

        info = QFrame()

        info.setObjectName("infoFrame")
        info.setStyleSheet("""
            QFrame#infoFrame {
                background: #0a0a0a;
                border: 1px solid #262626;
                border-radius: 10px;
            }
        """)

        info_layout = QHBoxLayout(info)

        info_layout.setContentsMargins(
            18,
            14,
            18,
            14
        )

        info_layout.setSpacing(18)

        metadata_items = [
            (
                "MINECRAFT",
                metadata.get(
                    "minecraft",
                    "Unknown"
                )
            ),
            (
                "LOADER",
                metadata.get(
                    "loader",
                    "Unknown"
                )
            ),
            (
                "LOADER VERSION",
                metadata.get(
                    "loader_version",
                    "Unknown"
                )
            ),
            (
                "JAVA",
                metadata.get(
                    "java",
                    "Unknown"
                )
            ),
            (
                "MODS",
                metadata.get(
                    "mods",
                    0
                )
            ),
        ]

        for label, value in metadata_items:
            block = QVBoxLayout()
            block.setSpacing(3)

            l = QLabel(label)

            l.setStyleSheet(f"""
                color: {COLOR_TEXT_3};
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 1.2px;
            """)

            v = QLabel(str(value))
            v.setWordWrap(True)
            v.setMinimumWidth(70)

            v.setStyleSheet(f"""
                color: {COLOR_TEXT};
                font-size: 14px;
                font-weight: 600;
            """)

            block.addWidget(l)
            block.addWidget(v)

            info_layout.addLayout(block)

        self.analysis_layout.addWidget(info)

        summary = result.get("analysis_summary", {})
        summary_frame = QFrame()
        summary_frame.setObjectName("summaryFrame")
        summary_frame.setStyleSheet("""
            QFrame#summaryFrame {
                background: #171717;
                border: 1px solid #262626;
                border-radius: 10px;
            }
        """)
        summary_layout = QVBoxLayout(summary_frame)
        summary_layout.setContentsMargins(20, 17, 20, 17)
        summary_layout.setSpacing(7)
        summary_title = QLabel("ANALYSIS SUMMARY")
        summary_title.setStyleSheet(f"color: {COLOR_ACCENT_BRIGHT}; font-size: 10px; font-weight: 600; letter-spacing: 1.2px;")
        summary_headline = QLabel(summary.get("headline") or "No summary available.")
        summary_headline.setWordWrap(True)
        summary_headline.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 14px; font-weight: 600;")
        summary_meta = QLabel(
            f"{summary.get('problem_count', len(problemas))} grouped problems  ·  "
            f"{summary.get('error_occurrences', 0)} error occurrences  ·  "
            f"{summary.get('warning_occurrences', 0)} warnings"
        )
        summary_meta.setStyleSheet(f"color: {COLOR_TEXT_3}; font-size: 12px;")
        summary_layout.addWidget(summary_title)
        summary_layout.addWidget(summary_headline)
        summary_layout.addWidget(summary_meta)
        self.analysis_layout.addWidget(summary_frame)

        root = result.get("root_cause")
        if root:
            root_frame = QFrame()
            confidence = str(root.get("confidence", "UNCERTAIN")).upper()
            root_accent = COLOR_SUCCESS if confidence == "HIGH" else COLOR_WARNING if confidence == "MEDIUM" else COLOR_TEXT_3
            root_border = "#464646" if confidence in ("HIGH", "MEDIUM") else "#262626"
            root_frame.setObjectName("rootFrame")
            root_frame.setStyleSheet(f"QFrame#rootFrame {{ background: #0a0a0a; border: 1px solid {root_border}; border-radius: 10px; }}")
            root_layout = QVBoxLayout(root_frame)
            root_layout.setContentsMargins(20, 17, 20, 17)
            root_layout.setSpacing(6)
            root_title = QLabel("PROBABLE ROOT CAUSE")
            root_title.setStyleSheet(f"color: {root_accent}; font-size: 10px; font-weight: 600; letter-spacing: 1.2px;")
            root_text = QLabel(root.get("summary", "No root cause summary available."))
            root_text.setWordWrap(True)
            root_text.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 14px; font-weight: 600;")
            root_conf = QLabel(f"Confidence: {root.get('confidence', 'UNCERTAIN')}" + (f"  ·  {', '.join(root.get('mods', []))}" if root.get('mods') else ""))
            root_conf.setStyleSheet(f"color: {COLOR_TEXT_3}; font-size: 12px;")
            root_layout.addWidget(root_title)
            root_layout.addWidget(root_text)
            root_layout.addWidget(root_conf)
            self.analysis_layout.addWidget(root_frame)

        if crash:
            crash_banner = QFrame()

            crash_banner.setObjectName("crashBanner")
            crash_banner.setStyleSheet("""
                QFrame#crashBanner {
                    background: #171717;
                    border: 1px solid rgba(255,107,122,90);
                    border-radius: 10px;
                }
            """)

            crash_layout = QHBoxLayout(
                crash_banner
            )

            crash_layout.setContentsMargins(
                17,
                13,
                17,
                13
            )

            icon = QLabel("!")
            icon.setFixedSize(28, 28)
            icon.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            icon.setStyleSheet(f"""
                color: {COLOR_ERROR};
                background: rgba(255,107,122,30);
                border-radius: 14px;
                font-weight: 600;
            """)

            crash_text = QVBoxLayout()
            crash_text.setSpacing(2)

            crash_title = QLabel(
                "CRASH DETECTED"
            )

            crash_title.setStyleSheet(f"""
                color: {COLOR_ERROR};
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 1.2px;
            """)

            crash_description = QLabel(
                "The analyzed log indicates that Minecraft "
                "encountered a crash."
            )

            crash_description.setStyleSheet(f"""
                color: {COLOR_TEXT_2};
                font-size: 12px;
            """)

            crash_text.addWidget(
                crash_title
            )

            crash_text.addWidget(
                crash_description
            )

            crash_layout.addWidget(icon)
            crash_layout.addSpacing(10)
            crash_layout.addLayout(crash_text)
            crash_layout.addStretch()

            self.analysis_layout.addWidget(
                crash_banner
            )

        stats = QHBoxLayout()
        stats.setSpacing(10)

        stats_data = [
            (
                "Errors",
                estadisticas.get(
                    "errores",
                    len(errores)
                ),
                COLOR_ERROR,
            ),
            (
                "Warnings",
                estadisticas.get(
                    "warnings",
                    len(warnings)
                ),
                COLOR_WARNING,
            ),
            (
                "Problems",
                estadisticas.get(
                    "problemas",
                    len(problemas)
                ),
                COLOR_ACCENT,
            ),
            (
                "Exceptions",
                len(excepciones),
                COLOR_INFO,
            ),
        ]

        for title_text, value, accent in stats_data:
            stats.addWidget(
                StatCard(
                    title_text,
                    value,
                    accent
                )
            )

        self.analysis_layout.addLayout(stats)

        problems_title = SectionHeader(
            "Detected problems",
            "Search, filter and inspect grouped signals"
        )

        controls = QHBoxLayout()
        search = QLineEdit()
        search.setPlaceholderText("Search problems, mods, exceptions or diagnostics...")
        severity_filter = ClickOnlyComboBox()
        severity_filter.addItems(["All severity", "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"])
        severity_filter.setFixedWidth(150)
        level_filter = ClickOnlyComboBox()
        level_filter.addItems(["All levels", "ERROR", "FATAL", "WARN"])
        level_filter.setFixedWidth(125)
        sort_filter = ClickOnlyComboBox()
        sort_filter.addItems(["Default order", "Severity", "Occurrences", "First appearance"])
        sort_filter.setFixedWidth(155)
        for combo in (severity_filter, level_filter, sort_filter):
            combo.setStyleSheet(f"""
                QComboBox {{
                    background: {COLOR_BG};
                    border: 1px solid #262626;
                    border-radius: 10px;
                    padding: 9px 12px;
                    color: {COLOR_TEXT};
                    font-size: 14px;
                }}
                QComboBox:hover {{ border: 1px solid #464646; }}
                QComboBox QAbstractItemView {{
                    background: {COLOR_SURFACE};
                    color: {COLOR_TEXT};
                    border: 1px solid #262626;
                    selection-background-color: #262626;
                    selection-color: {COLOR_TEXT};
                    outline: 0;
                }}
            """)
        controls.addWidget(search, 1)
        controls.addWidget(severity_filter)
        controls.addWidget(level_filter)
        controls.addWidget(sort_filter)
        self.analysis_layout.addWidget(problems_title)
        self.analysis_layout.addLayout(controls)

        root_cause = result.get("root_cause") or {}
        root_type = root_cause.get("problem_type") if isinstance(root_cause, dict) else None
        root_message = root_cause.get("message") if isinstance(root_cause, dict) else None

        def is_error_level(problem):
            return str(problem.get("nivel", "ERROR")).upper() in {"ERROR", "FATAL"}

        def is_probable_crash_cause(problem):
            if not crash or not root_type:
                return False
            if problem.get("tipo") != root_type:
                return False
            if root_type == "CRASH":
                return True
            return not root_message or (
                problem.get("mensaje_normalizado") == root_message
                or problem.get("mensaje") == root_message
            )

        all_cards = []
        errors_cards = []
        warning_cards = []
        for problem in problemas:
            card = ProblemCard(problem, crash_cause=is_probable_crash_cause(problem))
            card._problem = problem
            all_cards.append(card)
            if is_error_level(problem):
                errors_cards.append(card)
            else:
                warning_cards.append(card)

        # Precompute the searchable representation once. Filtering a large
        # log should not rebuild strings containing evidence/stack data on
        # every combo-box change.
        for card in all_cards:
            problem = card._problem
            parts = [
                problem.get(key, "")
                for key in (
                    "mensaje",
                    "mensaje_normalizado",
                    "diagnostico",
                    "why_this_matters",
                    "recomendacion",
                    "tipo",
                    "tipo_nombre",
                    "componente",
                )
            ]
            parts.extend(str(x) for x in problem.get("mods_relacionados", []))
            parts.extend(str(x) for x in problem.get("excepciones", []))
            parts.extend(
                str(e.get("text", ""))
                for e in problem.get("evidence", [])
                if isinstance(e, dict)
            )
            root = problem.get("root_cause")
            if isinstance(root, dict):
                parts.append(root.get("summary", ""))
            card._search_text = " ".join(str(x) for x in parts).lower()

        def filter_cards():
            query = search.text().strip().lower()
            selected_severity = severity_filter.currentText()
            selected_level = level_filter.currentText()
            visible = 0
            for card in all_cards:
                problem = card._problem
                haystack = card._search_text
                severity = str(problem.get("severity") or problem.get("importancia") or "LOW").upper()
                level = str(problem.get("nivel", "WARN")).upper()
                matches = (not query or query in haystack) and (selected_severity == "All severity" or severity == selected_severity) and (selected_level == "All levels" or level == selected_level)
                card.setVisible(matches)
                if matches:
                    visible += 1

            order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
            mode = sort_filter.currentText()
            if mode != "Default order":
                if mode == "Severity":
                    all_cards.sort(key=lambda c: (order.get(str(c._problem.get("severity") or c._problem.get("importancia") or "LOW").upper(), 99), -int(c._problem.get("ocurrencias", 1))))
                elif mode == "Occurrences":
                    all_cards.sort(key=lambda c: -int(c._problem.get("ocurrencias", 1)))
                elif mode == "First appearance":
                    all_cards.sort(key=lambda c: int(c._problem.get("linea", 10**12) or 10**12))

                for group in (error_group, warning_group):
                    content_layout = group.content.layout()
                    for card in all_cards:
                        belongs = (
                            is_error_level(card._problem)
                            if group.title_level == "ERROR"
                            else not is_error_level(card._problem)
                        )
                        if belongs:
                            content_layout.removeWidget(card)
                    for card in all_cards:
                        belongs = (
                            is_error_level(card._problem)
                            if group.title_level == "ERROR"
                            else not is_error_level(card._problem)
                        )
                        if belongs:
                            content_layout.addWidget(card)

            self.problem_filter_count.setText(f"{visible} matching problem{'s' if visible != 1 else ''}")

        self.problem_filter_count = QLabel(f"{len(all_cards)} matching problems")
        self.problem_filter_count.setStyleSheet(f"color: {COLOR_TEXT_3}; font-size: 12px;")
        self.analysis_layout.addWidget(self.problem_filter_count)
        search.textChanged.connect(lambda _: filter_cards())
        severity_filter.currentTextChanged.connect(lambda _: filter_cards())
        level_filter.currentTextChanged.connect(lambda _: filter_cards())
        sort_filter.currentTextChanged.connect(lambda _: filter_cards())

        error_group = CollapsibleGroup(
            "Errors",
            len(errors_cards),
            COLOR_ERROR,
            errors_cards,
            initially_open=bool(crash and errors_cards)
        )

        warning_group = CollapsibleGroup(
            "Warnings",
            len(warning_cards),
            COLOR_WARNING,
            warning_cards,
            initially_open=False
        )
        error_group.title_level = "ERROR"
        warning_group.title_level = "WARN"

        self.analysis_layout.addWidget(
            error_group
        )

        self.analysis_layout.addWidget(
            warning_group
        )

        if not errors_cards and not warning_cards:
            empty = QLabel(
                "No grouped errors or warnings detected."
            )

            empty.setStyleSheet(f"""
                color: {COLOR_SUCCESS};
                font-size: 14px;
                padding: 15px 0;
            """)

            self.analysis_layout.addWidget(
                empty
            )

        self.problems_anchor = error_group

        self.add_log_summary(
            errores,
            warnings,
            excepciones
        )

        self.analysis_layout.addStretch()
        self.reset_analysis_scroll()

    def add_log_summary(
        self,
        errores,
        warnings,
        excepciones
    ):
        total = (
            len(errores)
            + len(warnings)
            + len(excepciones)
        )

        section = QFrame()

        section.setObjectName("logSignals")
        section.setStyleSheet("""
            QFrame#logSignals {
                background: transparent;
                border: none;
                border-top: 1px solid #262626;
                border-radius: 0px;
            }
        """)

        layout = QVBoxLayout(section)

        layout.setContentsMargins(
            0,
            18,
            0,
            10
        )

        title = QLabel("LOG SIGNALS")

        title.setStyleSheet(f"""
            color: {COLOR_TEXT};
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 1.2px;
        """)

        description = QLabel(
            f"{total} raw signals extracted before grouping."
        )

        description.setStyleSheet(f"""
            color: {COLOR_TEXT_3};
            font-size: 12px;
        """)

        layout.addWidget(title)
        layout.addWidget(description)

        self.analysis_layout.addWidget(
            section
        )

    def reset_analysis_scroll(self):
        """Restore a stable viewport after rebuilding analysis results."""
        scrollbar = self.analysis_scroll.verticalScrollBar()
        scrollbar.setValue(0)
        self.analysis_content.adjustSize()
        self.analysis_layout.activate()
        self.analysis_scroll.viewport().update()

    def animate_analysis(self):
        # Compatibility shim for older callers. Results intentionally do not
        # use opacity effects inside the scroll area.
        self.reset_analysis_scroll()

    def build_mods_page(self):
        self.clear_layout(
            self.mods_layout
        )

        if not self.last_result:
            title = QLabel("Mods")

            title.setStyleSheet(f"""
                color: {COLOR_TEXT};
                font-size: 36px;
                font-weight: 500;
            """)

            self.mods_layout.addWidget(title)
            self.mods_layout.addStretch()

            return

        mods = self.last_result.get(
            "mods",
            []
        )

        title = QLabel("Installed mods")

        title.setStyleSheet(f"""
            color: {COLOR_TEXT};
            font-size: 36px;
            font-weight: 500;
        """)

        subtitle = QLabel(
            f"{len(mods)} detected in the analyzed log"
        )

        subtitle.setStyleSheet(f"""
            color: {COLOR_TEXT_3};
            font-size: 12px;
        """)

        self.mods_layout.addWidget(title)
        self.mods_layout.addWidget(subtitle)

        search = QLineEdit()
        search.setPlaceholderText(
            "Search mods..."
        )

        self.mods_layout.addWidget(search)
        mod_count = QLabel(f"{len(mods)} matching mods")
        mod_count.setStyleSheet(f"color: {COLOR_TEXT_3}; font-size: 12px;")
        self.mods_layout.addWidget(mod_count)

        list_frame = QFrame()

        list_frame.setObjectName("modList")
        list_frame.setStyleSheet("""
            QFrame#modList {
                background: #0a0a0a;
                border: 1px solid #262626;
                border-radius: 10px;
            }
        """)

        list_layout = QVBoxLayout(list_frame)

        list_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        list_layout.setSpacing(0)

        mod_widgets = []

        for index, mod in enumerate(mods):
            if isinstance(mod, dict):
                mod_id = mod.get(
                    "id",
                    "Unknown"
                )

                version = mod.get(
                    "version",
                    "Unknown"
                )
            else:
                mod_id = str(mod)
                version = "Unknown"

            row = QFrame()

            row.setObjectName("modRow")
            row.setStyleSheet("""
                QFrame#modRow {
                    background: transparent;
                    border: none;
                    border-bottom: 1px solid #262626;
                }

                QFrame#modRow:hover {
                    background: #171717;
                }
            """)

            row_layout = QHBoxLayout(row)

            row_layout.setContentsMargins(
                16,
                9,
                16,
                9
            )

            number = QLabel(
                f"{index + 1:03d}"
            )

            number.setFixedWidth(35)

            number.setStyleSheet(f"""
                color: {COLOR_TEXT_3};
                font-family: "Cascadia Mono";
                font-size: 12px;
            """)

            name = QLabel(
                str(mod_id)
            )

            name.setStyleSheet(f"""
                color: {COLOR_TEXT};
                font-size: 12px;
                font-weight: 600;
            """)

            version_label = QLabel(
                str(version)
            )

            version_label.setStyleSheet(f"""
                color: {COLOR_TEXT_3};
                font-family: "Cascadia Mono";
                font-size: 12px;
            """)

            row_layout.addWidget(number)
            row_layout.addWidget(name)
            row_layout.addStretch()
            row_layout.addWidget(version_label)

            list_layout.addWidget(row)

            mod_widgets.append(
                (
                    row,
                    f"{mod_id} {version}".lower()
                )
            )

        self.mods_layout.addWidget(
            list_frame
        )

        def filter_mods(text):
            text = text.lower().strip()
            visible = 0
            for row, mod_name in mod_widgets:
                matches = text in mod_name
                row.setVisible(matches)
                if matches:
                    visible += 1
            mod_count.setText(f"{visible} matching mod{'s' if visible != 1 else ''}")

        search.textChanged.connect(
            filter_mods
        )

        self.mods_layout.addStretch()

        fade_in(title, 350)
        fade_in(subtitle, 350, 100)
        fade_in(search, 350, 150)
        fade_in(list_frame, 450, 220)

    def show_mods(self):
        if not self.last_result:
            self.show_page(
                2,
                self.sidebar.btn_mods
            )
            return

        self.build_mods_page()

        self.show_page(
            2,
            self.sidebar.btn_mods
        )

    def show_problems(self):
        if not self.last_result:
            self.show_page(
                0,
                self.sidebar.btn_overview
            )
            return

        self.show_page(
            1,
            self.sidebar.btn_problems
        )

        if hasattr(
            self,
            "problems_anchor"
        ):
            QTimer.singleShot(
                100,
                lambda: self.analysis_scroll.ensureWidgetVisible(
                    self.problems_anchor
                )
            )

    def show_error(self, error):
        self.clear_layout(
            self.analysis_layout
        )

        title = QLabel("Analysis failed")

        title.setStyleSheet(f"""
            color: {COLOR_ERROR};
            font-size: 36px;
            font-weight: 500;
        """)

        description = QLabel(
            "Log Reader could not analyze the selected file."
        )

        description.setStyleSheet(f"""
            color: {COLOR_TEXT_2};
            font-size: 14px;
        """)

        details = QTextEdit()
        details.setReadOnly(True)
        details.setPlainText(str(error))
        details.setMinimumHeight(150)

        self.analysis_layout.addWidget(title)
        self.analysis_layout.addWidget(description)
        self.analysis_layout.addWidget(details)
        self.analysis_layout.addStretch()

        self.show_page(
            1,
            self.sidebar.btn_analysis
        )

        fade_in(title, 350)
        fade_in(description, 350, 100)
        fade_in(details, 350, 180)

    def show_page(
        self,
        index,
        active_button
    ):
        self.stack.setCurrentIndex(index)

        buttons = [
            self.sidebar.btn_overview,
            self.sidebar.btn_analysis,
            self.sidebar.btn_problems,
            self.sidebar.btn_mods,
        ]

        for button in buttons:
            button.set_active(
                active_button is not None and button is active_button
            )


def iniciar_gui(analizar_log):
    app = QApplication.instance()

    if app is None:
        app = QApplication([])

    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)
    font = QFont("Inter", 10)
    font.setFamilies(["Inter", "Segoe UI", "Helvetica Neue", "Arial"])
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)

    window = LogReaderWindow(
        analizar_log
    )

    window.show()

    return app.exec()