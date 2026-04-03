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

        # Пошаговый режим
        self.selected_row = -1
        self.selected_col = -1
        self.solution_history = []

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

        self.btn_step_forward = QPushButton("-> Шаг вперёд")
        self.btn_step_forward.clicked.connect(self.on_step_forward)
        self.btn_step_forward.setEnabled(False)

        self.btn_step_back = QPushButton("<- Шаг назад")
        self.btn_step_back.clicked.connect(self.on_step_back)
        self.btn_step_back.setEnabled(False)

        self.btn_auto_solve = QPushButton("Автоматическое решение")
        self.btn_auto_solve.clicked.connect(self.on_auto_solve)
        self.btn_auto_solve.setEnabled(False)

        self.btn_select_pivot = QPushButton("Выбрать опорный элемент")
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


        layout.addWidget(fisrt_table_isc_group)
        fisrt_table_isc_group.setLayout(newf_layout)

        self.x0isc_table = QTableWidget()
        self.x0isc_table.setSelectionBehavior(QTableWidget.SelectItems)
        self.x0isc_table.itemClicked.connect(self.on_table_cell_clicked)
        self.x0isc_table_layout.addWidget(self.x0isc_table)
        self.x0isc_group.setLayout(self.x0isc_table_layout)
        layout.addWidget(self.x0isc_group)

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

            # item = self.x0isc_table.item(0, 1)
            # print(item.text())

        '''
        for r in range (self.x0isc_table.rowCount()):
            for c in range (self.x0isc_table.columnCount()):
                item = self.x0isc_table.item(r, c)
                if item is not None:
                    #print(item.text())
                else:
                    # print("None")
                    # item.setText("")
        '''

        # Высчитываем f как сумму столбца со знаком минус
        for c in range(self.x0isc_table.columnCount()):
            sum_of_cols = 0
            for r in range (self.m_constrs):
                item = self.x0isc_table.item(r, c)
                if item:
                    text = item.text()
                    if text:  # Проверка на пустую строку
                        sum_of_cols += float(text)
            f_row_index = self.m_constrs
            f_value = -sum_of_cols
            f_item = QTableWidgetItem(str(f_value))
            f_item.setFlags(f_item.flags() & ~Qt.ItemIsEditable)  # Делаем не редактируемым
            self.x0isc_table.setItem(f_row_index, c, f_item)



            # ============================================================

    # выбор опорной ячейки в таблице
    def on_table_cell_clicked(self, item):
        row = item.row()
        col = item.column()
        self.selected_row = row
        self.selected_col = col

        # выделяем выбранную ячейку
        item.setBackground(Qt.yellow)
        print(f"Выбран элемент: строка {row}, столбец {col}")

    # === ЗАГЛУШКИ ДЛЯ ВТОРОЙ И ТРЕТЬЕЙ ВКЛАДОК ===
    def on_step_forward(self):
        self.step_info.append("➡ Переход к следующей итерации...")

    def on_step_backOld(self):
        self.step_info.append("⬅ Возврат к предыдущей итерации...")

    # не мой код
    def on_step_back(self):
        """Возврат к предыдущей итерации (требование 6)"""

        if len(self.solution_history) <= 1:
            QMessageBox.information(self, "Инфо", "Нечего возвращать!")
            return

        # Удаляем текущее состояние
        self.solution_history.pop()

        # Восстанавливаем предыдущее
        prev_state = self.solution_history[-1]

        self.x0isc_table.setRowCount(prev_state['row_count'])
        self.x0isc_table.setColumnCount(prev_state['col_count'])

        for r in range(prev_state['row_count']):
            for c in range(prev_state['col_count']):
                item = self.x0isc_table.item(r, c)
                if not item:
                    item = QTableWidgetItem()
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.x0isc_table.setItem(r, c, item)

                value = prev_state['data'][r][c] if r < len(prev_state['data']) and c < len(
                    prev_state['data'][r]) else "0"
                item.setText(value)

        # Пересчитываем F для безопасности
        self.recalculate_f_row()

        QMessageBox.information(self, "Успех", "Возврат выполнен!")

    def on_auto_solve(self):
        self.step_info.append("🚀 Запуск автоматического решения...")

    def on_select_pivotOld(self):
        self.step_info.append("🎯 Выберите опорный элемент в таблице...")
        '''
        Для автоматического решения
        def select_pivot_element(self):
    """Выбор опорного элемента для текущей итерации"""
    
    # 1. Найти ведущий столбец (наиболее отрицательный в строке F)
    f_row = self.m_constrs  # Индекс строки F
    pivot_col = -1
    min_value = 0
    
    for j in range(self.n_vars + 1):  # +1 для столбца b
        item = self.x0isc_table.item(f_row, j)
        if item:
            value = float(item.text())
            if value < min_value:
                min_value = value
                pivot_col = j
    
    if pivot_col == -1:
        return None  # Решение найдено
    
    # 2. Найти ведущую строку (минимальное θ-отношение)
    pivot_row = -1
    min_ratio = float('inf')
    
    for i in range(self.m_constrs):  # Только строки ограничений
        item_coeff = self.x0isc_table.item(i, pivot_col)
        item_b = self.x0isc_table.item(i, self.n_vars)
        
        if item_coeff and item_b:
            coeff = float(item_coeff.text())
            b_val = float(item_b.text())
            
            if coeff > 0:
                ratio = b_val / coeff
                if ratio < min_ratio:
                    min_ratio = ratio
                    pivot_row = i
    
    if pivot_row == -1:
        return None  # Задача неограничена
    
    return (pivot_row, pivot_col)  # Опорный элемент найден
        
        '''

    # Писала не сама
    def on_select_pivot(self):
        """Обработка кнопки выбора опорного элемента"""
        # ячейка не выбрана
        if self.selected_row == -1 or self.selected_col == -1:
            QMessageBox.warning(self, "Внимание", "Сначала выберите ячейку в таблице!")
            return

        row, col = self.selected_row, self.selected_col
        # выбрали не ту ячейку, например в f строке
        if row >= self.m_constrs:
            QMessageBox.warning(self, "Внимание",
                                f"Опорный элемент должен быть в строке ограничений!")
            return

        # плохая ячейка
        pivot_itm = self.x0isc_table.item(row, col)
        if not pivot_itm or not pivot_itm.text():
            QMessageBox.warning(self, "Внимание", "Ячейка пуста или содержит некорректные данные!")
            return

        try:
            pivot_val = float(pivot_itm.text())
        except ValueError:
            QMessageBox.warning(self, "Внимание", "Неверное числовое значение!")
            return

        if pivot_val <= 0:
            QMessageBox.warning(self, "Внимание", "Опорный элемент должен быть > 0!")
            return

        f_itm = self.x0isc_table.item(self.m_constrs, col)
        if f_itm and f_itm.text():
            try:
                if float(f_itm.text()) >= 0:
                    QMessageBox.warning(self, "Внимание", "Коэффициент в строке F должен быть отрицательным!")
                    return
            except ValueError:
                pass

        try:
            self.save_table_state()
            self.perform_pivot(row, col)
            QMessageBox.information(self, "Успех", f"Итерация выполнена!\nОпорный: строка {row}, столбец {col}")
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Сбой симплекс-преобразования:\n{str(e)}")

    # Доп функции, не мои
    def save_table_state(self):
        """Сохранение текущего состояния таблицы для возврата назад"""
        state = {
            'row_count': self.x0isc_table.rowCount(),
            'col_count': self.x0isc_table.columnCount(),
            'data': []
        }

        for r in range(self.x0isc_table.rowCount()):
            row_data = []
            for c in range(self.x0isc_table.columnCount()):
                item = self.x0isc_table.item(r, c)
                row_data.append(item.text() if item and item.text() else "0")
            state['data'].append(row_data)

        self.solution_history.append(state)

        if len(self.solution_history) > 100:
            self.solution_history.pop(0)

    def perform_pivot(self, pivot_row, pivot_col):
        """Выполнение симплекс-преобразования (безопасная версия)"""
        self.x0isc_table.blockSignals(True)

        rows = self.x0isc_table.rowCount()
        cols = self.x0isc_table.columnCount()

        # 🔥 1. Считываем ВСЮ таблицу в память
        table_data = []
        for r in range(rows):
            row_vals = []
            for c in range(cols):
                itm = self.x0isc_table.item(r, c)
                try:
                    val = float(itm.text()) if itm and itm.text() else 0.0
                except ValueError:
                    val = 0.0
                row_vals.append(val)
            table_data.append(row_vals)

        pivot_val = table_data[pivot_row][pivot_col]
        if pivot_val == 0:
            self.x0isc_table.blockSignals(False)
            return

        # 🔥 2. Нормализуем ведущую строку
        for c in range(cols):
            table_data[pivot_row][c] /= pivot_val

        # 🔥 3. Обнуляем столбец в остальных строках
        for r in range(rows):
            if r == pivot_row:
                continue
            multiplier = table_data[r][pivot_col]
            for c in range(cols):
                table_data[r][c] -= multiplier * table_data[pivot_row][c]

        # 🔥 4. Записываем обратно
        for r in range(rows):
            for c in range(cols):
                val = round(table_data[r][c], 6)
                itm = self.x0isc_table.item(r, c)
                if not itm:
                    itm = QTableWidgetItem()
                    itm.setFlags(itm.flags() & ~Qt.ItemIsEditable)
                    self.x0isc_table.setItem(r, c, itm)
                itm.setText(str(val))

        self.x0isc_table.blockSignals(False)

        # Обновляем метки и строку F
        self.update_row_labels_after_pivot(pivot_row, pivot_col)
        self.recalculate_f_row()

        self.selected_row = -1
        self.selected_col = -1
        # Сброс подсветки
        for r in range(rows):
            for c in range(cols):
                itm = self.x0isc_table.item(r, c)
                if itm:
                    itm.setBackground(Qt.white)

    def recalculate_f_row(self):
        """Пересчёт строки F"""
        f_row = self.m_constrs
        cols = self.x0isc_table.columnCount()

        for c in range(cols):
            col_sum = 0.0
            for r in range(self.m_constrs):
                itm = self.x0isc_table.item(r, c)
                if itm and itm.text():
                    try:
                        col_sum += float(itm.text())
                    except ValueError:
                        pass
            f_val = round(-col_sum, 6)

            itm = self.x0isc_table.item(f_row, c)
            if not itm:
                itm = QTableWidgetItem()
                itm.setFlags(itm.flags() & ~Qt.ItemIsEditable)
                self.x0isc_table.setItem(f_row, c, itm)
            itm.setText(str(f_val))

    def update_row_labels_after_pivot(self, pivot_row, pivot_col):
        """Обновление заголовков строк после замены базисной переменной"""
        # 1. Собираем текущие вертикальные заголовки вручную
        v_labels = []
        for r in range(self.x0isc_table.rowCount()):
            item = self.x0isc_table.verticalHeaderItem(r)
            if item:
                v_labels.append(item.text())
            else:
                v_labels.append("")  # Резерв, если заголовок пуст

        # 2. Берем имя переменной из горизонтального заголовка выбранного столбца
        h_item = self.x0isc_table.horizontalHeaderItem(pivot_col)
        new_var_name = h_item.text() if h_item else ""

        # 3. Заменяем заголовок строки, где находится опорный элемент
        if 0 <= pivot_row < len(v_labels):
            v_labels[pivot_row] = new_var_name

        # 4. Устанавливаем обновленный список заголовков
        self.x0isc_table.setVerticalHeaderLabels(v_labels)

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