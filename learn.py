from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTableWidget, QTableWidgetItem
import sys


class TestWithClear(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Тест: С очисткой")
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout()

        btn_task1 = QPushButton("Задача 1: 2 переменные")
        btn_task1.clicked.connect(self.task1)
        layout.addWidget(btn_task1)

        btn_task2 = QPushButton("Задача 2: 3 переменные")
        btn_task2.clicked.connect(self.task2)
        layout.addWidget(btn_task2)

        self.tables_container = QWidget()
        self.tables_layout = QVBoxLayout(self.tables_container)
        layout.addWidget(self.tables_container)

        self.setLayout(layout)

    def clear_all_tables(self):
        """Очищает все старые таблицы"""
        print("Очищаем старые таблицы...")
        while self.tables_layout.count():
            item = self.tables_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def task1(self):
        print("=== Задача 1 ===")

        # ✅ ОЧИЩАЕМ старые таблицы
        self.clear_all_tables()

        # Создаем новую таблицу
        table = QTableWidget()
        table.setRowCount(3)
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["x1", "x2", "b"])
        table.setVerticalHeaderLabels(["x3", "x4", "F"])

        data = [[2, 1, 4],
                [1, 3, 5],
                [0, 0, 0]]

        for i in range(3):
            for j in range(3):
                item = QTableWidgetItem(str(data[i][j]))
                table.setItem(i, j, item)

        self.tables_layout.addWidget(QLabel("<b>Задача 1 (2 переменные)</b>"))
        self.tables_layout.addWidget(table)

    def task2(self):
        print("=== Задача 2 ===")

        # ✅ ОЧИЩАЕМ старые таблицы
        self.clear_all_tables()

        # Создаем новую таблицу
        table = QTableWidget()
        table.setRowCount(4)
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["x1", "x2", "x3", "b"])
        table.setVerticalHeaderLabels(["x4", "x5", "x6", "F"])

        data = [[2, 1, 1, 4],
                [1, 3, 2, 5],
                [1, 1, 1, 3],
                [0, 0, 0, 0]]

        for i in range(4):
            for j in range(4):
                item = QTableWidgetItem(str(data[i][j]))
                table.setItem(i, j, item)

        self.tables_layout.addWidget(QLabel("<b>Задача 2 (3 переменные)</b>"))
        self.tables_layout.addWidget(table)


app = QApplication(sys.argv)
window = TestWithoutClear()
window.show()
sys.exit(app.exec_())