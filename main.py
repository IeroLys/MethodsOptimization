import sys
from fractions import Fraction
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QGridLayout, QLabel, QLineEdit,
                             QSpinBox, QPushButton, QTableWidget, QTableWidgetItem,
                             QRadioButton, QButtonGroup, QMessageBox, QGroupBox,
                             QFileDialog, QScrollArea, QTabWidget, QTextEdit)
from PyQt5.QtCore import Qt, QRegularExpression
from PyQt5.QtGui import QRegularExpressionValidator


class LinearProblemInput(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ЗЛП - Лабораторная работа")
        self.setMinimumSize(1200, 900)

        # === Хранилище данных ===
        self.n_vars = 0
        self.m_constrs = 0
        self.c_coeffs = []
        self.matrix_A = []
        self.vector_b = []
        self.is_minimization = True

        self.init_ui()

    def init_ui(self):
        """Создание главного интерфейса с вкладками"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # === Создаём вкладки ===
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # === Вкладка 1: Условия задачи ===
        self.tab_conditions = QWidget()
        self.tabs.addTab(self.tab_conditions, "Условия задачи")
        self._init_conditions_tab()

        # === Вкладка 2: Метод искусственного базиса ===
        self.tab_artificial = QWidget()
        self.tabs.addTab(self.tab_artificial, "Метод искусственного базиса")
        self._init_artificial_tab()

        # === Вкладка 3: Графический метод ===
        self.tab_graphic = QWidget()
        self.tabs.addTab(self.tab_graphic, "Графический метод")
        self._init_graphic_tab()

    # === ВКЛАДКА 1: УСЛОВИЯ ЗАДАЧИ ===
    def _init_conditions_tab(self):
        """Инициализация первой вкладки с условиями задачи"""
        layout = QVBoxLayout(self.tab_conditions)

        # Верхняя часть: слева ввод, справа отображение задачи
        top_layout = QHBoxLayout()

        # === ЛЕВАЯ ПАНЕЛЬ: Ввод параметров ===
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMaximumWidth(500)

        # Блок размерности
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
        left_layout.addWidget(dim_group)

        # Блок типа оптимизации
        opt_group = QGroupBox("Тип оптимизации")
        opt_layout = QVBoxLayout()

        self.opt_group = QButtonGroup()
        self.min_radio = QRadioButton("min (минимизация)")
        self.max_radio = QRadioButton("max (максимизация)")
        self.min_radio.setChecked(True)
        self.opt_group.addButton(self.min_radio)
        self.opt_group.addButton(self.max_radio)

        self.min_radio.toggled.connect(self.update_problem_text)
        self.max_radio.toggled.connect(self.update_problem_text)

        opt_layout.addWidget(self.min_radio)
        opt_layout.addWidget(self.max_radio)
        opt_group.setLayout(opt_layout)
        left_layout.addWidget(opt_group)

        # Блок коэффициентов целевой функции
        func_group = QGroupBox("Коэффициенты целевой функции")
        func_layout = QVBoxLayout()
        func_layout.addWidget(QLabel("c₁, c₂, ... cₙ:"))

        self.c_layout = QHBoxLayout()
        self.c_inputs = []
        func_layout.addLayout(self.c_layout)

        func_group.setLayout(func_layout)
        left_layout.addWidget(func_group)

        left_layout.addStretch()
        top_layout.addWidget(left_panel)

        # === ПРАВАЯ ПАНЕЛЬ: Отображение задачи ===
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        right_layout.addWidget(QLabel("Постановка задачи:"))

        self.problem_text = QTextEdit()
        self.problem_text.setReadOnly(True)
        self.problem_text.setMinimumHeight(200)
        self.problem_text.setFontFamily("Consolas")
        self.problem_text.setStyleSheet("QTextEdit { background-color: #f5f5f5; border: 1px solid #ccc; }")
        right_layout.addWidget(self.problem_text)

        top_layout.addWidget(right_panel)
        layout.addLayout(top_layout)

        # === НИЖНЯЯ ЧАСТЬ: Матрица ограничений ===
        matrix_group = QGroupBox("Матрица ограничений A и вектор b")
        matrix_layout = QVBoxLayout()

        self.table_widget = QTableWidget()
        self.table_widget.horizontalHeader().setStretchLastSection(True)

        self.table_widget.cellChanged.connect(self.update_problem_text)

        matrix_layout.addWidget(self.table_widget)

        matrix_group.setLayout(matrix_layout)
        layout.addWidget(matrix_group)

        # === Кнопки управления ===
        btn_layout = QHBoxLayout()

        self.btn_solve = QPushButton("✓ Решить задачу")
        self.btn_solve.clicked.connect(self.validate_and_save)
        self.btn_solve.setMinimumHeight(40)

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

        layout.addLayout(btn_layout)

        # Инициализация при старте
        self.on_dimension_changed()

    # === ВКЛАДКА 2: МЕТОД ИСКУССТВЕННОГО БАЗИСА ===
    def _init_artificial_tab(self):
        """Инициализация вкладки с симплекс-таблицами"""
        layout = QVBoxLayout(self.tab_artificial)

        # КНОПКИ
        control_group = QGroupBox("Управление решением")
        control_layout = QHBoxLayout()

        self.btn_step_forward = QPushButton("➡ Шаг вперёд")
        self.btn_step_forward.clicked.connect(self.on_step_forward)
        self.btn_step_forward.setEnabled(False)

        self.btn_step_back = QPushButton("⬅ Шаг назад")
        self.btn_step_back.clicked.connect(self.on_step_back)
        self.btn_step_back.setEnabled(False)

        self.btn_auto_solve = QPushButton("🚀 Автоматическое решение")
        self.btn_auto_solve.clicked.connect(self.on_auto_solve)
        self.btn_auto_solve.setEnabled(False)

        self.btn_select_pivot = QPushButton("🎯 Выбрать опорный элемент")
        self.btn_select_pivot.clicked.connect(self.on_select_pivot)
        self.btn_select_pivot.setEnabled(False)

        control_layout.addWidget(self.btn_step_forward)
        control_layout.addWidget(self.btn_step_back)
        control_layout.addWidget(self.btn_auto_solve)
        control_layout.addWidget(self.btn_select_pivot)
        control_layout.addStretch()

        control_group.setLayout(control_layout)
        layout.addWidget(control_group)

        # Таблица
        # инициализация
        #self.simplex_table = QTableWidget()
        #self.simplex_table.setMinimumHeight(400)
        #layout.addWidget(self.simplex_table)

        fisrt_table_isc_group = QGroupBox("Вспомогательная задача")
        newf_layout = QVBoxLayout()

        # F = x5 + x6 -> min
        self.newF = QLabel()
        newf_layout.addWidget(self.newF)

        # x* = (0,0,0,0,4,1)
        self.newF_res = QLabel()
        newf_layout.addWidget(self.newF_res)

        # Первая x*0 таблица
        self.x0isc_group = QGroupBox("X*0 таблица")
        self.x0isc_table_layout = QVBoxLayout()

        self.x0isc_table = QTableWidget()
        newf_layout.addWidget(self.x0isc_table)
        layout.addWidget(fisrt_table_isc_group)

        fisrt_table_isc_group.setLayout(newf_layout)
        newf_layout.addWidget(self.x0isc_group)

        layout.addStretch()

    # === ВКЛАДКА 3: ГРАФИЧЕСКИЙ МЕТОД ===
    def _init_graphic_tab(self):
        """Инициализация вкладки с графиками"""
        layout = QVBoxLayout(self.tab_graphic)

        header_label = QLabel("📊 Графический метод решения")
        header_label.setFont(QApplication.font())
        header_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header_label)

        mode_group = QGroupBox("Режим отображения")
        mode_layout = QHBoxLayout()

        self.graph_2d_radio = QRadioButton("2D (две переменные)")
        self.graph_3d_radio = QRadioButton("3D (три переменные)")
        self.graph_2d_radio.setChecked(True)

        mode_layout.addWidget(self.graph_2d_radio)
        mode_layout.addWidget(self.graph_3d_radio)
        mode_layout.addStretch()

        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        self.graph_placeholder = QLabel("🖼 Здесь будет отображаться график области допустимых решений")
        self.graph_placeholder.setAlignment(Qt.AlignCenter)
        self.graph_placeholder.setMinimumHeight(500)
        self.graph_placeholder.setStyleSheet("QLabel { background-color: #e0e0e0; border: 2px dashed #999; }")
        layout.addWidget(self.graph_placeholder)

        self.graph_info = QTextEdit()
        self.graph_info.setReadOnly(True)
        self.graph_info.setMaximumHeight(100)
        self.graph_info.setPlaceholderText("Здесь будет отображено графическое решение...")
        layout.addWidget(self.graph_info)

        layout.addStretch()

    # === ЛОГИКА ПЕРВОЙ ВКЛАДКИ ===
    def on_dimension_changed(self):
        """Пересоздание таблицы и обновление текста задачи при изменении размерности"""
        self.n_vars = self.n_spin.value()
        self.m_constrs = self.m_spin.value()

        self._update_c_inputs()
        self._update_matrix_table()
        self.update_problem_text()

    def _update_c_inputs(self):
        """Обновление полей ввода коэффициентов целевой функции"""
        while self.c_layout.count():
            item = self.c_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.c_inputs = []

        for j in range(self.n_vars):
            label = QLabel(f"c{j + 1}:")
            edit = QLineEdit()
            edit.setPlaceholderText("0")
            edit.setValidator(QRegularExpressionValidator(
                QRegularExpression(r"^-?\d*\.?\d*(/\d+)?$")))

            # 🔥 Подключаем обновление текста при вводе коэффициентов
            edit.textChanged.connect(self.update_problem_text)

            self.c_layout.addWidget(label)
            self.c_layout.addWidget(edit)
            self.c_inputs.append(edit)

    def _update_matrix_table(self):
        """Обновление таблицы матрицы ограничений"""
        self.table_widget.setRowCount(self.m_constrs)
        self.table_widget.setColumnCount(self.n_vars + 1)

        h_labels = [f"x{j + 1}" for j in range(self.n_vars)] + ["b"]
        self.table_widget.setHorizontalHeaderLabels(h_labels)

        v_labels = [f"огр. {i + 1}" for i in range(self.m_constrs)]
        self.table_widget.setVerticalHeaderLabels(v_labels)

        # 🔥 Отключаем сигнал на время создания ячеек, чтобы не было лишних вызовов
        self.table_widget.blockSignals(True)

        for i in range(self.m_constrs):
            for j in range(self.n_vars + 1):
                item = QTableWidgetItem()
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                self.table_widget.setItem(i, j, item)

        # 🔥 Включаем сигнал обратно
        self.table_widget.blockSignals(False)

        # Обновляем текст один раз после создания таблицы
        self.update_problem_text()

    def update_problem_text(self):
        """Генерация текста постановки задачи в математическом виде"""
        # Собираем коэффициенты целевой функции
        c_values = []
        for edit in self.c_inputs:
            text = edit.text().strip()
            c_values.append(text if text else "0")

        # Тип оптимизации
        opt_type = "min" if self.min_radio.isChecked() else "max"

        # Формируем целевую функцию
        f_parts = []
        for j, c in enumerate(c_values):
            if c == "0":
                continue
            if j == 0:
                f_parts.append(f"{c}x{j + 1}")
            else:
                if c.startswith("-"):
                    f_parts.append(f" - {c[1:]}x{j + 1}")
                else:
                    f_parts.append(f" + {c}x{j + 1}")

        f_string = " ".join(f_parts) if f_parts else "0"

        # Формируем ограничения
        constr_lines = []
        for i in range(self.m_constrs):
            row_parts = []
            for j in range(self.n_vars):
                item = self.table_widget.item(i, j)
                val = item.text().strip() if item else "0"
                if val == "0":
                    continue
                if j == 0:
                    row_parts.append(f"{val}x{j + 1}")
                else:
                    if val.startswith("-"):
                        row_parts.append(f" - {val[1:]}x{j + 1}")
                    else:
                        row_parts.append(f" + {val}x{j + 1}")

            row_string = " ".join(row_parts) if row_parts else "0"

            # Правая часть
            item_b = self.table_widget.item(i, self.n_vars)
            b_val = item_b.text().strip() if item_b else "0"

            constr_lines.append(f"{row_string} = {b_val}")

        # Формируем условия неотрицательности
        x_nonneg = ", ".join([f"x{j + 1}" for j in range(self.n_vars)])

        # Собираем всё вместе
        problem_html = f"""
        <div style="font-size: 14px; line-height: 1.8;">
            <p><b>C целевая функция:</b><br>
            F = {f_string} → {opt_type}</p>

            <p><b>Ограничения:</b><br>
            {'<br>'.join(constr_lines)}</p>

            <p><b>Условия неотрицательности:</b><br>
            {x_nonneg} ≥ 0</p>
        </div>
        """

        self.problem_text.setHtml(problem_html)

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

# Кнопка решить задачу
    def validate_and_save(self):
        """Валидация и сохранение данных"""
        try:
            if self.n_vars > 16 or self.m_constrs > 16:
                raise ValueError("Размерность не должна превышать 16×16!")

            self.c_coeffs = []
            for edit in self.c_inputs:
                self.c_coeffs.append(self.parse_fraction(edit.text()))

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

            self.is_minimization = self.min_radio.isChecked()

            self.update_newf()
            self.update_newf_res()
            self.update_x0isc_table()

            self.btn_step_forward.setEnabled(True)
            self.btn_step_back.setEnabled(True)
            self.btn_auto_solve.setEnabled(True)
            self.btn_select_pivot.setEnabled(True)

            QMessageBox.information(self, "Успех",
                                    f"Данные приняты!\nПеременных: {self.n_vars}\nОграничений: {self.m_constrs}")

        except ValueError as e:
            QMessageBox.critical(self, "Ошибка ввода", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Неизвестная ошибка: {e}")

    def save_to_file(self):
        """Сохранение задачи в файл"""
        try:
            self.validate_and_save()

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

                self.n_spin.setValue(data['n'])
                self.m_spin.setValue(data['m'])
                self.on_dimension_changed()

                for i, val in enumerate(data['c']):
                    if i < len(self.c_inputs):
                        self.c_inputs[i].setText(val)

                for i, row in enumerate(data['A']):
                    for j, val in enumerate(row):
                        item = self.table_widget.item(i, j)
                        if item:
                            item.setText(val)

                for i, val in enumerate(data['b']):
                    item = self.table_widget.item(i, self.n_vars)
                    if item:
                        item.setText(val)

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

            # 🔥 Отключаем сигнал перед очисткой таблицы
            self.table_widget.blockSignals(True)
            for i in range(self.table_widget.rowCount()):
                for j in range(self.table_widget.columnCount()):
                    item = self.table_widget.item(i, j)
                    if item:
                        item.setText("")
            # 🔥 Включаем сигнал и обновляем текст один раз
            self.table_widget.blockSignals(False)
            self.update_problem_text()

            self.btn_step_forward.setEnabled(False)
            self.btn_step_back.setEnabled(False)
            self.btn_auto_solve.setEnabled(False)
            self.btn_select_pivot.setEnabled(False)

# Вторая вкладка
    def update_newf(self):
        # F = x5 + x6 -> min
        opt_type = "min"
        artificial_vars = []
        for j in range(self.m_constrs):
            var_index = self.n_vars + j + 1
            artificial_vars.append(f"x{var_index}")
        vars_string = " + ".join(artificial_vars)
        if not vars_string:
            vars_string = "0"
        formula = f"F = {vars_string} -> {opt_type}"
        self.newF.setText(formula)

    def update_newf_res(self):
        # x* = (0,0,0,0,4,1)
        solution = ["0"] * self.n_vars
        for i in range(len(self.vector_b)):
            solution.append(str(self.vector_b[i]))
        vars_string2 = ", ".join(solution)
        formula2 = f"x*0 = ({vars_string2})"
        self.newF_res.setText(formula2)

    def update_x0isc_table(self):

        #self.x0isc_table = QTableWidget()
        # newf_layout.addWidget(self.x0isc_table)

        """Обновление таблицы x*0"""
        self.x0isc_table.setRowCount(self.m_constrs + 1)
        self.x0isc_table.setColumnCount(self.n_vars + 1)

        h_labels = [f"x{j + 1}" for j in range(self.n_vars)] + ["b"]
        self.x0isc_table.setHorizontalHeaderLabels(h_labels)

        v_labels = [f"x{self.n_vars + i + 1}" for i in range(self.m_constrs)]
        v_labels.append("f")
        self.x0isc_table.setVerticalHeaderLabels(v_labels)


        # Заполняем матрицу А
        for i in range(self.m_constrs):
            for j in range(self.n_vars):
                value = self.matrix_A[i][j]
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.x0isc_table.setItem(i, j, item)

            b_value = self.vector_b[i]
            item_b = QTableWidgetItem(str(b_value))
            item_b.setFlags(item_b.flags() & ~Qt.ItemIsEditable)
            self.x0isc_table.setItem(i, self.n_vars, item_b)

    # ============================================================

    # === ЗАГЛУШКИ ДЛЯ ВТОРОЙ И ТРЕТЬЕЙ ВКЛАДОК ===
    def on_step_forward(self):
        self.step_info.append("➡ Переход к следующей итерации...")

    def on_step_back(self):
        self.step_info.append("⬅ Возврат к предыдущей итерации...")

    def on_auto_solve(self):
        self.step_info.append("🚀 Запуск автоматического решения...")

    def on_select_pivot(self):
        self.step_info.append("🎯 Выберите опорный элемент в таблице...")


def main():
    app = QApplication(sys.argv)

    font = app.font()
    font.setPointSize(10)
    app.setFont(font)

    window = LinearProblemInput()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()