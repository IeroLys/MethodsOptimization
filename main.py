import sys
from fractions import Fraction
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QGridLayout, QLabel, QLineEdit,
                             QSpinBox, QPushButton, QTableWidget, QTableWidgetItem,
                             QRadioButton, QButtonGroup, QMessageBox, QGroupBox,
                             QFileDialog, QScrollArea, QFontComboBox)
from PyQt5.QtCore import Qt, QRegularExpression
from PyQt5.QtGui import QDoubleValidator, QRegularExpressionValidator

class LinearProblemInput(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ЗЛП лабараторная работа")
        self.setMinimumSize(1000, 900)

        # Хранилище данных
        self.n_vars = 0  # количество переменных
        self.m_constrs = 0  # количество ограничений
        self.c_coeffs = []  # коэффициенты целевой функции
        self.matrix_A = []  # матрица ограничений
        self.vector_b = []  # правые части
        self.is_minimization = True  # min или max

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        central_widget.setLayout(QVBoxLayout())
        central_widget.layout().addWidget(scroll)

        content_widget = QWidget()
        scroll.setWidget(content_widget)
        main_layout = QVBoxLayout(content_widget)

        # === Блок 1: Размерность задачи ===
        #layout = QVBoxLayout()
        self.font_combo = QFontComboBox()
        main_layout.addWidget(self.font_combo)

        dim_group = QGroupBox("Размерность задачи")
        dim_layout = QGridLayout()

        dim_layout.addWidget(QLabel("Количество переменных (n):"), 0, 0)
        self.n_spin = QSpinBox()
        self.n_spin.setRange(1, 16)
        self.n_spin.setValue(4)
        self.n_spin.valueChanged.connect(self.on_dimension_changed)
        dim_layout.addWidget(self.n_spin, 0, 1)

        dim_layout.addWidget(QLabel("Количество ограничений (m):"), 1, 0)
        self.m_spin = QSpinBox()
        self.m_spin.setRange(1, 16)
        self.m_spin.setValue(2)
        self.m_spin.valueChanged.connect(self.on_dimension_changed)
        dim_layout.addWidget(self.m_spin, 1, 1)

        dim_group.setLayout(dim_layout)
        main_layout.addWidget(dim_group)

        # === Блок 2: Целевая функция ===
        func_group = QGroupBox("Целевая функция")
        func_layout = QVBoxLayout()

        # Тип оптимизации
        opt_layout = QHBoxLayout()
        self.opt_group = QButtonGroup()
        self.min_radio = QRadioButton("min")
        self.max_radio = QRadioButton("max")
        self.min_radio.setChecked(True)
        self.opt_group.addButton(self.min_radio)
        self.opt_group.addButton(self.max_radio)
        opt_layout.addWidget(QLabel("Тип оптимизации:"))
        opt_layout.addWidget(self.min_radio)
        opt_layout.addWidget(self.max_radio)
        opt_layout.addStretch()
        func_layout.addLayout(opt_layout)

        # Коэффициенты c_j
        self.c_layout = QHBoxLayout()
        self.c_inputs = []
        func_layout.addWidget(QLabel("Коэффициенты целевой функции (c₁, c₂, ...):"))
        func_layout.addLayout(self.c_layout)

        func_group.setLayout(func_layout)
        main_layout.addWidget(func_group)

        # === Блок 3: Матрица ограничений ===
        matrix_group = QGroupBox("Матрица ограничений A и вектор b")
        matrix_layout = QVBoxLayout()

        self.table_widget = QTableWidget()
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        matrix_layout.addWidget(self.table_widget)

        matrix_group.setLayout(matrix_layout)
        main_layout.addWidget(matrix_group)

        # === Блок 4: Кнопки управления ===
        btn_layout = QHBoxLayout()

        self.btn_solve = QPushButton("✓ Решить задачу")
        self.btn_solve.clicked.connect(self.validate_and_save)

        self.btn_save = QPushButton("💾 Сохранить в файл")
        self.btn_save.clicked.connect(self.save_to_file)

        self.btn_load = QPushButton("📂 Загрузить из файла")
        self.btn_load.clicked.connect(self.load_from_file)

        self.btn_clear = QPushButton("🗑 Очистить")
        self.btn_clear.clicked.connect(self.clear_all)

        btn_layout.addWidget(self.btn_solve)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_load)
        btn_layout.addWidget(self.btn_clear)
        btn_layout.addStretch()

        main_layout.addLayout(btn_layout)

        # Инициализация таблицы при старте
        self.on_dimension_changed()

    def on_dimension_changed(self):
        """Пересоздание таблицы при изменении размерности"""
        self.n_vars = self.n_spin.value()
        self.m_constrs = self.m_spin.value()

        # Обновление полей целевой функции
        self._update_c_inputs()

        # Обновление таблицы ограничений
        self._update_matrix_table()

    def _update_c_inputs(self):
        """Обновление полей ввода коэффициентов целевой функции"""
        # Очистка старых полей
        while self.c_layout.count():
            item = self.c_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.c_inputs = []

        # Создание новых полей
        for j in range(self.n_vars):
            label = QLabel(f"c<sub>{j + 1}</sub>:")
            edit = QLineEdit()
            edit.setPlaceholderText("0")
            edit.setValidator(QRegularExpressionValidator(
                QRegularExpression(r"^-?\d*\.?\d*(/\d+)?$")))  # Поддержка дробей
            self.c_layout.addWidget(label)
            self.c_layout.addWidget(edit)
            self.c_inputs.append(edit)

    def _update_matrix_table(self):
        """Обновление таблицы матрицы ограничений"""
        self.table_widget.setRowCount(self.m_constrs)
        self.table_widget.setColumnCount(self.n_vars + 1)  # +1 для вектора b

        # Заголовки
        h_labels = [f"x<sub>{j + 1}</sub>" for j in range(self.n_vars)] + ["b"]
        self.table_widget.setHorizontalHeaderLabels(h_labels)

        v_labels = [f"огр. {i + 1}" for i in range(self.m_constrs)]
        self.table_widget.setVerticalHeaderLabels(v_labels)

        # Создание ячеек с валидатором
        validator = QRegularExpressionValidator(
            QRegularExpression(r"^-?\d*\.?\d*(/\d+)?$"))

        for i in range(self.m_constrs):
            for j in range(self.n_vars + 1):
                item = QTableWidgetItem()
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                self.table_widget.setItem(i, j, item)

    def parse_fraction(self, text):
        """Парсинг числа из строки (поддержка дробей)"""
        text = text.strip().replace(',', '.')
        if not text:
            return Fraction(0)
        try:
            if '/' in text:
                num, den = text.split('/')
                return Fraction(int(num), int(den))
            else:
                return Fraction(text)
        except:
            raise ValueError(f"Неверный формат числа: {text}")

    def validate_and_save(self):
        """Валидация и сохранение данных"""
        try:
            # Проверка размерности
            if self.n_vars > 16 or self.m_constrs > 16:
                raise ValueError("Размерность не должна превышать 16×16!")

            # Парсинг коэффициентов целевой функции
            self.c_coeffs = []
            for edit in self.c_inputs:
                self.c_coeffs.append(self.parse_fraction(edit.text()))

            # Парсинг матрицы A и вектора b
            self.matrix_A = []
            self.vector_b = []
            for i in range(self.m_constrs):
                row = []
                for j in range(self.n_vars):
                    item = self.table_widget.item(i, j)
                    val = self.parse_fraction(item.text() if item else "0")
                    row.append(val)
                self.matrix_A.append(row)

                item_b = self.table_widget.item(i, self.n_vars)
                self.vector_b.append(self.parse_fraction(item_b.text() if item_b else "0"))

            # Тип оптимизации
            self.is_minimization = self.min_radio.isChecked()

            # Успех
            QMessageBox.information(self, "Успех",
                                    f"Данные приняты!\nПеременных: {self.n_vars}\nОграничений: {self.m_constrs}")

            # Здесь можно вызвать решатель
            # self.run_simplex()

        except ValueError as e:
            QMessageBox.critical(self, "Ошибка ввода", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Неизвестная ошибка: {e}")

    def save_to_file(self):
        """Сохранение задачи в файл"""
        try:
            self.validate_and_save()  # Сначала валидация

            file_path, _ = QFileDialog.getSaveFileName(
                self, "Сохранить задачу", "", "JSON Files (*.json);;All Files (*)")

            if file_path:
                import json
                data = {
                    'n': self.n_vars,
                    'm': self.m_constrs,
                    'c': [str(c) for c in self.c_coeffs],
                    'A': [[str(val) for val in row] for row in self.matrix_A],
                    'b': [str(val) for val in self.vector_b],
                    'is_min': self.is_minimization
                }
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                QMessageBox.information(self, "Успех", "Файл сохранён!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка сохранения", str(e))

    def load_from_file(self):
        """Загрузка задачи из файла"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Загрузить задачу", "", "JSON Files (*.json);;All Files (*)")

            if file_path:
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Восстановление размерности
                self.n_spin.setValue(data['n'])
                self.m_spin.setValue(data['m'])
                self.on_dimension_changed()

                # Восстановление коэффициентов
                for i, val in enumerate(data['c']):
                    if i < len(self.c_inputs):
                        self.c_inputs[i].setText(val)

                # Восстановление матрицы
                for i, row in enumerate(data['A']):
                    for j, val in enumerate(row):
                        item = self.table_widget.item(i, j)
                        if item:
                            item.setText(val)

                # Восстановление вектора b
                for i, val in enumerate(data['b']):
                    item = self.table_widget.item(i, self.n_vars)
                    if item:
                        item.setText(val)

                # Тип оптимизации
                self.min_radio.setChecked(data['is_min'])
                self.max_radio.setChecked(not data['is_min'])

                QMessageBox.information(self, "Успех", "Файл загружен!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка загрузки", str(e))

    def clear_all(self):
        """Очистка всех полей"""
        reply = QMessageBox.question(self, "Подтверждение",
                                     "Очистить все данные?", QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.n_spin.setValue(4)
            self.m_spin.setValue(2)
            self.min_radio.setChecked(True)
            for edit in self.c_inputs:
                edit.clear()
            for i in range(self.table_widget.rowCount()):
                for j in range(self.table_widget.columnCount()):
                    item = self.table_widget.item(i, j)
                    if item:
                        item.setText("")


def main():
    myapp = QApplication(sys.argv)

    font = myapp.font()
    font.setPointSize(10)
    myapp.setFont(font)

    window = LinearProblemInput()
    window.show()

    sys.exit(myapp.exec_())


if __name__ == "__main__":
    main()