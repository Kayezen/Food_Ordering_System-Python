import sys
import os
import csv
from collections import Counter

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout, QFrame, QMessageBox,
)
from PyQt6.QtCore import Qt

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


# ======================================================
# STORAGE FILE HANDLING
# ======================================================

STORAGE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "students.csv")
FIELDS = ["Name", "Age", "Course", "Year Level", "Grade"]

COURSES = ["BSIT", "BSCS", "BSED", "BSCpE", "BSBA"]
YEAR_LEVELS = ["1st Year", "2nd Year", "3rd Year", "4th Year"]


def read_students():
    """Read every student from the CSV file and return a list of dicts."""
    if not os.path.exists(STORAGE_FILE):
        return []

    students = []
    with open(STORAGE_FILE, "r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                row["Age"] = int(row["Age"])
                row["Grade"] = float(row["Grade"])
                students.append(row)
            except (ValueError, KeyError, TypeError):
                continue  # skip damaged rows
    return students


def write_students(students):
    """Overwrite the CSV file with the given list of student dicts."""
    with open(STORAGE_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(students)


# ======================================================
# MATPLOTLIB CANVAS
# ======================================================

class ChartCanvas(FigureCanvasQTAgg):

    def __init__(self):
        self.fig = Figure(figsize=(10, 4.5), constrained_layout=True)
        super().__init__(self.fig)

    def draw_charts(self, students):
        self.fig.clear()
        bar_ax = self.fig.add_subplot(121)
        pie_ax = self.fig.add_subplot(122)

        # ---------- Bar graph: Students and Grades ----------
        if students:
            names = [s["Name"] for s in students]
            grades = [s["Grade"] for s in students]
            bars = bar_ax.bar(names, grades, color="#4c78a8")
            bar_ax.bar_label(bars, fmt="%.1f", fontsize=8)
            bar_ax.set_ylim(0, 105)
            bar_ax.tick_params(axis="x", rotation=45, labelsize=8)
            for label in bar_ax.get_xticklabels():
                label.set_ha("right")
            bar_ax.set_xlabel("Student")
            bar_ax.set_ylabel("Grade")
        else:
            bar_ax.text(0.5, 0.5, "No Data", ha="center", va="center")
            bar_ax.set_axis_off()
        bar_ax.set_title("Student Grades")

        # ---------- Pie chart: Students per Course ----------
        counts = Counter(s["Course"] for s in students)
        if counts:
            pie_ax.pie(
                list(counts.values()),
                labels=list(counts.keys()),
                autopct="%1.0f%%",
                startangle=90,
            )
        else:
            pie_ax.text(0.5, 0.5, "No Data", ha="center", va="center")
            pie_ax.set_axis_off()
        pie_ax.set_title("Course Distribution")

        self.draw()


# ======================================================
# DASHBOARD WINDOW
# ======================================================

class DashboardWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Student Dashboard")
        self.resize(1000, 650)

        # four summary cards
        self.card_total = self.make_card("TOTAL STUDENTS")
        self.card_avg = self.make_card("AVERAGE GRADE")
        self.card_high = self.make_card("HIGHEST GRADE")
        self.card_low = self.make_card("LOWEST GRADE")

        cards = QHBoxLayout()
        for card in (self.card_total, self.card_avg, self.card_high, self.card_low):
            cards.addWidget(card[0])

        self.canvas = ChartCanvas()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)

        layout = QVBoxLayout(self)
        layout.addLayout(cards)
        layout.addWidget(self.canvas, 1)
        layout.addWidget(refresh_btn)

        self.refresh()

    def make_card(self, title):
        """Return (frame, value_label) for one summary box."""
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setStyleSheet(
            "QFrame { background: #f2f5fa; border: 1px solid #c8d1e0; border-radius: 8px; }"
        )
        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet("border: none; font-size: 11px; color: #555; font-weight: bold;")
        value_lbl = QLabel("0")
        value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_lbl.setStyleSheet("border: none; font-size: 24px; font-weight: bold; color: #1f3a5f;")

        box = QVBoxLayout(frame)
        box.addWidget(title_lbl)
        box.addWidget(value_lbl)
        return frame, value_lbl

    def refresh(self):
        # Storage file -> Dashboard
        students = read_students()
        grades = [s["Grade"] for s in students]

        total = len(students)
        average = sum(grades) / total if total else 0
        highest = max(grades) if grades else 0
        lowest = min(grades) if grades else 0

        self.card_total[1].setText(str(total))
        self.card_avg[1].setText(f"{average:.2f}")
        self.card_high[1].setText(f"{highest:.2f}")
        self.card_low[1].setText(f"{lowest:.2f}")

        # Dashboard -> Matplotlib graphs
        self.canvas.draw_charts(students)


# ======================================================
# MAIN WINDOW (RECORD MANAGEMENT)
# ======================================================

class StudentSystem(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Student Information System")
        self.resize(760, 640)
        self.students = read_students()
        self.dashboard = None

        # ----- input form -----
        self.name_in = QLineEdit()
        self.age_in = QLineEdit()
        self.course_in = QComboBox()
        self.course_in.addItems(COURSES)
        self.year_in = QComboBox()
        self.year_in.addItems(YEAR_LEVELS)
        self.grade_in = QLineEdit()
        self.grade_in.setPlaceholderText("0 - 100")

        form = QFormLayout()
        form.addRow("Student Name:", self.name_in)
        form.addRow("Age:", self.age_in)
        form.addRow("Course:", self.course_in)
        form.addRow("Year Level:", self.year_in)
        form.addRow("Grade:", self.grade_in)

        # ----- buttons -----
        self.btn_save = QPushButton("Save")
        self.btn_update = QPushButton("Update")
        self.btn_delete = QPushButton("Delete")
        self.btn_clear = QPushButton("Clear Form")
        self.btn_dash = QPushButton("Open Dashboard")

        self.btn_save.clicked.connect(self.add_student)
        self.btn_update.clicked.connect(self.update_student)
        self.btn_delete.clicked.connect(self.delete_student)
        self.btn_clear.clicked.connect(self.clear_form)
        self.btn_dash.clicked.connect(self.open_dashboard)

        buttons = QHBoxLayout()
        for b in (self.btn_save, self.btn_update, self.btn_delete, self.btn_clear):
            buttons.addWidget(b)

        # ----- record display (table) -----
        self.table = QTableWidget(0, len(FIELDS))
        self.table.setHorizontalHeaderLabels(FIELDS)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.itemSelectionChanged.connect(self.fill_form_from_selection)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(buttons)
        layout.addWidget(self.table, 1)
        layout.addWidget(self.btn_dash)

        self.show_students()

    # ---------- helpers ----------

    def read_form(self):
        """Validate the form. Return a student dict, or None if invalid."""
        name = self.name_in.text().strip()
        if not name:
            self.warn("Please enter the student's name.")
            return None

        try:
            age = int(self.age_in.text().strip())
            if not 10 <= age <= 100:
                raise ValueError
        except ValueError:
            self.warn("Age must be a whole number between 10 and 100.")
            return None

        try:
            grade = float(self.grade_in.text().strip())
            if not 0 <= grade <= 100:
                raise ValueError
        except ValueError:
            self.warn("Grade must be a number between 0 and 100.")
            return None

        return {
            "Name": name,
            "Age": age,
            "Course": self.course_in.currentText(),
            "Year Level": self.year_in.currentText(),
            "Grade": grade,
        }

    def warn(self, message):
        QMessageBox.warning(self, "Invalid Input", message)

    def selected_row(self):
        return self.table.currentRow()

    def clear_form(self):
        self.name_in.clear()
        self.age_in.clear()
        self.grade_in.clear()
        self.course_in.setCurrentIndex(0)
        self.year_in.setCurrentIndex(0)
        self.table.clearSelection()

    def save_to_file(self):
        """Save Data -> Storage File, then keep the dashboard in sync."""
        write_students(self.students)
        self.show_students()
        if self.dashboard is not None and self.dashboard.isVisible():
            self.dashboard.refresh()

    # ---------- READ ----------

    def show_students(self):
        self.table.setRowCount(len(self.students))
        for row, s in enumerate(self.students):
            values = [s["Name"], s["Age"], s["Course"], s["Year Level"], f"{s['Grade']:.2f}"]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(str(value)))

    def fill_form_from_selection(self):
        row = self.selected_row()
        if row < 0 or row >= len(self.students):
            return
        s = self.students[row]
        self.name_in.setText(s["Name"])
        self.age_in.setText(str(s["Age"]))
        self.course_in.setCurrentText(s["Course"])
        self.year_in.setCurrentText(s["Year Level"])
        self.grade_in.setText(str(s["Grade"]))

    # ---------- CREATE ----------

    def add_student(self):
        student = self.read_form()
        if student is None:
            return
        self.students.append(student)
        self.save_to_file()
        self.clear_form()

    # ---------- UPDATE ----------

    def update_student(self):
        row = self.selected_row()
        if row < 0:
            QMessageBox.information(self, "Update", "Select a student from the table first.")
            return
        student = self.read_form()
        if student is None:
            return
        self.students[row] = student
        self.save_to_file()
        self.table.selectRow(row)

    # ---------- DELETE ----------

    def delete_student(self):
        row = self.selected_row()
        if row < 0:
            QMessageBox.information(self, "Delete", "Select a student from the table first.")
            return
        name = self.students[row]["Name"]
        answer = QMessageBox.question(
            self, "Confirm Delete", f"Delete the record of {name}?"
        )
        if answer == QMessageBox.StandardButton.Yes:
            del self.students[row]
            self.save_to_file()
            self.clear_form()

    # ---------- DASHBOARD ----------

    def open_dashboard(self):
        if self.dashboard is None or not self.dashboard.isVisible():
            self.dashboard = DashboardWindow()
        else:
            self.dashboard.refresh()
        self.dashboard.show()
        self.dashboard.raise_()


# ======================================================
# MAIN PROGRAM
# ======================================================

def main():
    app = QApplication(sys.argv)
    window = StudentSystem()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
