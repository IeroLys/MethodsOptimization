import sys
from fractions import Fraction
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QGridLayout, QLabel, QLineEdit,
                             QSpinBox, QPushButton, QTableWidget, QTableWidgetItem,
                             QRadioButton, QButtonGroup, QMessageBox, QGroupBox,
                             QFileDialog, QScrollArea, QTabWidget, QTextEdit, QSizePolicy)
from PyQt5.QtCore import Qt, QRegularExpression
from PyQt5.QtGui import QRegularExpressionValidator, QBrush, QColor


class LinearProblemInput(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ЗЛП - Лабораторная работа")
        self.setMinimumSize(1200, 900)

        # Хранилища
        self.n_vars = 0
        self.m_constrs = 0
        self.c_coeffs = []
        self.matrix_A = []
        self.vector_b = []
        self.is_minimization = True

        # Пошаговый режим
        self.selected_row = -1
        self.selected_col = -1

        self.simplex_selected_row = -1
        self.simplex_selected_col = -1

        # Для хранения всех таблиц итераций и текущей выбранной таблицы
        self.iteration_tables = []
        self.selected_table_widget = None
        self.simplex_tables = []
        self.simplex_selected_table = None

        # Для хранения последней таблицы искусственного метода
        self.last_artificial_table = None  # QTableWidget
        self.last_artificial_basis = []  # список базисных переменных (например, ['x3','x4'])
        self.last_artificial_solution = []  # значения базисных переменных (Fraction)

        self.init_ui()

    def init_ui(self):
        """Создание главного интерфейса с вкладками"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Вкладка 1: Условия задачи
        self.tab_conditions = QWidget()
        self.tabs.addTab(self.tab_conditions, "Условия задачи")
        self._init_conditions_tab()

        # Вкладка 2: Метод искусственного базиса
        self.tab_artificial = QWidget()
        self.tabs.addTab(self.tab_artificial, "Метод искусственного базиса")
        self._init_artificial_tab()

        # Вкладка 3: Симплекс метод
        self.tab_simplex_method = QWidget()
        self.tabs.addTab(self.tab_simplex_method, "Симплекс метод")
        self._init_simplex_method_tab()

    # ВКЛАДКА 1: УСЛОВИЯ ЗАДАЧИ
    def _init_conditions_tab(self):
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
        self.n_spin.valueChanged.connect(self.on_razmernost_changed)
        dim_layout.addWidget(self.n_spin, 0, 1)

        dim_layout.addWidget(QLabel("Количество ограничений (m):"), 1, 0)
        self.m_spin = QSpinBox()
        self.m_spin.setRange(1, 16)
        self.m_spin.setValue(2)
        self.m_spin.valueChanged.connect(self.on_razmernost_changed)
        dim_layout.addWidget(self.m_spin, 1, 1)

        dim_group.setLayout(dim_layout)
        left_layout.addWidget(dim_group)

        # Блок типа оптимизации
        opt_group = QGroupBox("Тип оптимизации")
        opt_layout = QVBoxLayout()

        self.opt_group = QButtonGroup()
        self.min_radio = QRadioButton("min")
        self.max_radio = QRadioButton("max")
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

        # Матрица ограничений
        matrix_group = QGroupBox("Матрица ограничений A и вектор b")
        matrix_layout = QVBoxLayout()

        self.table_widget = QTableWidget()
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        # Текст постановки задачи - справа
        self.table_widget.cellChanged.connect(self.update_problem_text)

        matrix_layout.addWidget(self.table_widget)

        matrix_group.setLayout(matrix_layout)
        layout.addWidget(matrix_group)

        """ Кнопки управления """
        btn_layout = QHBoxLayout()

        self.btn_solve = QPushButton("Решить задачу")
        self.btn_solve.clicked.connect(self.validate_and_save)
        self.btn_solve.setMinimumHeight(40)

        self.btn_save = QPushButton("Сохранить в файл")
        self.btn_save.clicked.connect(self.save_to_file)

        self.btn_load = QPushButton("Загрузить из файла")
        self.btn_load.clicked.connect(self.load_from_file)

        self.btn_clear = QPushButton("Очистить")
        self.btn_clear.clicked.connect(self.clear_all)

        btn_layout.addWidget(self.btn_solve)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_load)
        btn_layout.addWidget(self.btn_clear)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        # создание таблиц и текста по размерности и её изменении
        self.on_razmernost_changed()

    # ВКЛАДКА 2: МЕТОД ИСКУССТВЕННОГО БАЗИСА
    def _init_artificial_tab(self):
        layout = QVBoxLayout(self.tab_artificial)
        layout.setContentsMargins(0, 0, 0, 0)

        # Скролл
        self.artificial_scroll = QScrollArea()
        self.artificial_scroll.setWidgetResizable(True)
        layout.addWidget(self.artificial_scroll)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setAlignment(Qt.AlignTop)
        self.artificial_scroll.setWidget(scroll_content)

        # Кнопки управления
        control_group = QGroupBox("")
        control_layout = QHBoxLayout()

        self.btn_step_back = QPushButton("Шаг назад")
        self.btn_step_back.clicked.connect(self.on_step_back)
        self.btn_step_back.setEnabled(False)

        self.btn_select_opor = QPushButton("Выбрать опорный элемент")
        self.btn_select_opor.clicked.connect(self.on_select_opor)
        self.btn_select_opor.setEnabled(False)

        self.btn_auto_solve = QPushButton("Автоматическое решение")
        self.btn_auto_solve.clicked.connect(self.on_auto_solve)
        self.btn_auto_solve.setEnabled(False)

        self.btn_to_simplex = QPushButton("Построить симплекс-таблицу")
        self.btn_to_simplex.clicked.connect(self.build_x0_table)
        self.btn_to_simplex.setEnabled(False)

        control_layout.addWidget(self.btn_step_back)
        control_layout.addWidget(self.btn_select_opor)
        control_layout.addWidget(self.btn_auto_solve)
        control_layout.addWidget(self.btn_to_simplex)
        control_layout.addStretch()
        control_group.setLayout(control_layout)
        scroll_layout.addWidget(control_group)

        # === ИНФОРМАЦИЯ О ВСПОМОГАТЕЛЬНОЙ ЗАДАЧЕ ===
        info_group = QGroupBox("Вспомогательная задача")
        info_layout = QVBoxLayout()
        # F = x5 + x6 -> min
        self.newF = QLabel()
        # x* = (0,0,0,0,4,1)
        self.newF_res = QLabel()
        info_layout.addWidget(self.newF)
        info_layout.addWidget(self.newF_res)
        info_group.setLayout(info_layout)
        scroll_layout.addWidget(info_group)

        # Таблицы итераций
        tables_group = QGroupBox("Итерации")
        tables_layout = QVBoxLayout()

        self.iterations_container = QWidget()
        self.iterations_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        self.iterations_layout = QVBoxLayout(self.iterations_container)
        self.iterations_layout.setSpacing(15)
        self.iterations_layout.setAlignment(Qt.AlignTop)

        tables_layout.addWidget(self.iterations_container)
        tables_group.setLayout(tables_layout)
        scroll_layout.addWidget(tables_group)

        scroll_layout.addStretch()

    # ВКЛАДКА 3: СИМПЛЕКС МЕТОД
    def _init_simplex_method_tab(self):
        """Инициализация вкладки симплекс-метода (минимальный вариант)"""
        layout = QVBoxLayout(self.tab_simplex_method)
        layout.setContentsMargins(0, 0, 0, 0)

        # Скролл-область
        self.simplex_scroll = QScrollArea()
        self.simplex_scroll.setWidgetResizable(True)
        layout.addWidget(self.simplex_scroll)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setAlignment(Qt.AlignTop)
        self.simplex_scroll.setWidget(scroll_content)

        # === КНОПКИ УПРАВЛЕНИЯ ===
        control_group = QGroupBox("")
        control_layout = QHBoxLayout()

        self.simplex_btn_back = QPushButton("Шаг назад")
        self.simplex_btn_back.clicked.connect(self.simplex_on_step_back)
        self.simplex_btn_back.setEnabled(False)

        self.simplex_btn_select = QPushButton("Выбрать опорный элемент")
        self.simplex_btn_select.clicked.connect(self.simplex_on_select_opor)
        self.simplex_btn_select.setEnabled(False)

        self.simplex_btn_auto = QPushButton("Автоматическое решение")
        self.simplex_btn_auto.clicked.connect(self.simplex_auto_solve)
        self.simplex_btn_auto.setEnabled(False)

        control_layout.addWidget(self.simplex_btn_back)
        control_layout.addWidget(self.simplex_btn_select)
        control_layout.addWidget(self.simplex_btn_auto)
        control_layout.addStretch()
        control_group.setLayout(control_layout)
        scroll_layout.addWidget(control_group)

        # === ТАБЛИЦЫ ИТЕРАЦИЙ ===
        tables_group = QGroupBox("Итерации")
        tables_layout = QVBoxLayout()

        self.simplex_iterations_container = QWidget()
        self.simplex_iterations_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        self.simplex_iterations_layout = QVBoxLayout(self.simplex_iterations_container)
        self.simplex_iterations_layout.setSpacing(15)
        self.simplex_iterations_layout.setAlignment(Qt.AlignTop)

        tables_layout.addWidget(self.simplex_iterations_container)
        tables_group.setLayout(tables_layout)
        scroll_layout.addWidget(tables_group)

        scroll_layout.addStretch()

    """ Первая вкладка """
    #+ обновление данных при изменении размерности
    def on_razmernost_changed(self):
        self.n_vars = self.n_spin.value()
        self.m_constrs = self.m_spin.value()

        self._update_c_inputs()
        self._update_matrix_table()
        self.update_problem_text()

    #+ Плашки с C коэффициентами
    def _update_c_inputs(self):
        # очищаем сначала
        while self.c_layout.count():
            item = self.c_layout.takeAt(0)
            item.widget().deleteLater()
        self.c_inputs = []

        for j in range(self.n_vars):
            label = QLabel(f"c{j + 1}:")
            edit = QLineEdit()
            edit.setPlaceholderText("0") # серым текстом
            edit.setValidator(QRegularExpressionValidator(
                QRegularExpression(r"^-?\d*\.?\d*(/\d+)?$")))

            # обновление постановки задачи при вводе коэффициентов
            edit.textChanged.connect(self.update_problem_text)

            # а теперь добавляем
            self.c_layout.addWidget(label)
            self.c_layout.addWidget(edit)
            self.c_inputs.append(edit)

    # обновление таблицы матрицы ограничений
    def _update_matrix_table(self):
        """Обновление таблицы матрицы ограничений"""
        self.table_widget.setRowCount(self.m_constrs)
        self.table_widget.setColumnCount(self.n_vars + 1)

        h_labels = [f"x{j + 1}" for j in range(self.n_vars)] + ["b"]
        self.table_widget.setHorizontalHeaderLabels(h_labels)

        v_labels = [f"огр. {i + 1}" for i in range(self.m_constrs)]
        self.table_widget.setVerticalHeaderLabels(v_labels)

        # отключаем сигнал на время создания ячеек, чтобы не было лишних вызовов
        self.table_widget.blockSignals(True)

        for i in range(self.m_constrs):
            for j in range(self.n_vars + 1):
                item = QTableWidgetItem()
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                self.table_widget.setItem(i, j, item)

        # включаем сигнал обратно
        self.table_widget.blockSignals(False)

        # Обновляем текст один раз после создания таблицы
        self.update_problem_text()

    # Текст постановки задачи - справа
    def update_problem_text(self):
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
        try:
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

            self.btn_step_back.setEnabled(True)
            self.btn_auto_solve.setEnabled(True)
            self.btn_select_opor.setEnabled(True)

            QMessageBox.information(self, "Успех", "Данные приняты! Решаем задачу во вкладке метода")

        # краказябра в ячейке вместо числа
        except ValueError as e:
            QMessageBox.critical(self, "Ошибка ввода", str(e))
        # что-то другое
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Неизвестная ошибка: {e}")

    # Кнопка Сохранить в файл
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

    # Кнопка Загрузить из файла
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
                self.on_razmernost_changed()

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

    # Кнопка Очистить
    def clear_all(self):
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

            self.btn_step_back.setEnabled(False)
            self.btn_auto_solve.setEnabled(False)
            self.btn_select_opor.setEnabled(False)

    """ Вторая вкладка """

    #+ F = x5 + x6 -> min
    def update_newf(self):
        opt_type = "min" # всегда min
        artificial_vars = []
        for j in range(self.m_constrs):
            var_index = self.n_vars + j + 1
            artificial_vars.append(f"x{var_index}")
        vars_string = " + ".join(artificial_vars)
        formula = f"F = {vars_string} -> {opt_type}"
        self.newF.setText(formula)

    #+ x* = (0,0,0,0,4,1)
    def update_newf_res(self):
        # массив с ноликами
        solution = ["0"] * self.n_vars
        # значения из вектора b
        for i in range(len(self.vector_b)):
            solution.append(str(self.vector_b[i]))
        vars_string = ", ".join(solution)
        formula = f"x*0 = ({vars_string})"
        self.newF_res.setText(formula)

    #Fraction Первая X*0 таблица, 0 итерация
    def update_x0isc_table(self):

        # очищаем всё насозданное
        while self.iterations_layout.count():
            item = self.iterations_layout.takeAt(0) # первый элемент из layout
            if item.widget():
                item.widget().deleteLater()
        self.iteration_tables.clear()

        # Создаём табличку
        new_table = QTableWidget()
        new_table.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        new_table.setSelectionBehavior(QTableWidget.SelectItems)
        new_table.itemClicked.connect(self.on_table_cell_clicked) # для выбора опорного элемента
        new_table.setRowCount(self.m_constrs + 1)
        new_table.setColumnCount(self.n_vars + 1)

        h_labels = [f"x{j + 1}" for j in range(self.n_vars)] + ["b"]
        new_table.setHorizontalHeaderLabels(h_labels)

        v_labels = [f"x{self.n_vars + i + 1}" for i in range(self.m_constrs)] + ["F"]
        new_table.setVerticalHeaderLabels(v_labels)

        for i in range(self.m_constrs):
            for j in range(self.n_vars):
                val = str(self.matrix_A[i][j])
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                new_table.setItem(i, j, item)

            # вектор b
            b_val = str(self.vector_b[i])
            item_b = QTableWidgetItem(b_val)
            item_b.setFlags(item_b.flags() & ~Qt.ItemIsEditable)
            new_table.setItem(i, self.n_vars, item_b)

        # сумма по столбцам
        for c in range(new_table.columnCount()):
            col_sum = Fraction(0, 1)
            for r in range(self.m_constrs):
                item = new_table.item(r, c)
                if item and item.text():
                    try:
                        val = self.parse_fraction(item.text())
                        col_sum += val
                    except (ValueError, ZeroDivisionError):
                        pass

            f_val = -col_sum
            if f_val.denominator == 1:
                text = str(f_val.numerator)
            else:
                text = str(f_val)
            f_item = QTableWidgetItem(text)
            f_item.setFlags(f_item.flags() & ~Qt.ItemIsEditable)
            new_table.setItem(self.m_constrs, c, f_item)

        self.iterations_layout.addWidget(QLabel(f"<b>Итерация *0</b>"))
        self.iterations_layout.addWidget(new_table)
        self.iteration_tables.append(new_table)

        self.selected_table_widget = None
        self.selected_row = -1
        self.selected_col = -1

    #+ выбор опорной ячейки в таблице
    def on_table_cell_clicked(self, item):
        row = item.row()
        col = item.column()
        self.selected_row = row
        self.selected_col = col
        self.selected_table_widget = item.tableWidget()

        # print(f"Выбран элемент: строка {row}, столбец {col} в таблице {id(self.selected_table_widget)}")

    # не готово
    def on_auto_solve(self):
        self.step_info.append("🚀 Запуск автоматического решения...")

    #+ Кнопка Шаг назад
    def on_step_back(self):
        if len(self.iteration_tables) <= 1:
            QMessageBox.information(self, "Инфо", "Нечего возвращать! Это начальная таблица.")
            return

        # удаляем таблицу
        last_item = self.iterations_layout.takeAt(self.iterations_layout.count() - 1)
        if last_item and last_item.widget():
            last_item.widget().deleteLater()

        # удаляем заголовок
        label_item = self.iterations_layout.takeAt(self.iterations_layout.count() - 1)
        if label_item and label_item.widget():
            label_item.widget().deleteLater()

        # удаляем из массива
        self.iteration_tables.pop()

        # сброс выбора
        self.selected_table_widget = None
        self.selected_row = -1
        self.selected_col = -1

        QMessageBox.information(self, "Готово", "Возврат выполнен!")

    #+ Кнопка Выбрать опорный элемент - проверки
    def on_select_opor(self):
        if self.selected_row == -1 or self.selected_col == -1:
            QMessageBox.warning(self, "Внимание", "Сначала выберите ячейку в таблице!")
            return

        if self.selected_table_widget != self.iteration_tables[-1]:
            QMessageBox.warning(self, "Внимание", "Выберите ячейку в последней (текущей) таблице!")
            return

        row, col = self.selected_row, self.selected_col
        if row >= self.m_constrs:
            QMessageBox.warning(self, "Внимание", "Опорный элемент должен быть в строке ограничений!")
            return

        current_table = self.iteration_tables[-1]
        opor_itm = current_table.item(row, col)
        if not opor_itm or not opor_itm.text():
            QMessageBox.warning(self, "Внимание", "Ячейка пуста!")
            return

        try:
            opor_val = self.parse_fraction(opor_itm.text())
        except (ValueError, ZeroDivisionError):
            QMessageBox.warning(self, "Внимание", "Неверное числовое значение!")
            return

        if opor_val <= 0:
            QMessageBox.warning(self, "Внимание", "Опорный элемент должен быть > 0!")
            return

        f_itm = current_table.item(self.m_constrs, col) # self.selected_col
        if f_itm and f_itm.text(): # защита от None
            try:
                if self.parse_fraction(f_itm.text()) >= 0:
                    QMessageBox.warning(self, "Внимание", "Коэффициент в строке F должен быть отрицательным!")
                    return
            except (ValueError, ZeroDivisionError):
                pass

        try:
            opor_itm.setBackground(QColor("pink"))
            current_table.clearSelection()
            QMessageBox.information(self, "Успех", f"Итерация выполнена!")
            self.perform_opor()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Сбой преобразования:\n{str(e)}")

    #+- Итерации
    def perform_opor(self):
        # копируем данные
        current_table = self.iteration_tables[-1]
        rows = current_table.rowCount()
        cols = current_table.columnCount()
        table_data = []
        for r in range(rows):
            row_vals = []
            for c in range(cols):
                item = current_table.item(r, c)
                try:
                    val = self.parse_fraction(item.text()) if item and item.text() else Fraction(0)
                except (ValueError, ZeroDivisionError):
                    val = Fraction(0)
                row_vals.append(val)
            table_data.append(row_vals)

        # 1. Меняем местами переменные - строки/столбцы
        old_h_labels = [current_table.horizontalHeaderItem(c).text() for c in range(cols)]
        # print(old_h_labels)
        old_v_labels = [current_table.verticalHeaderItem(r).text() for r in range(rows)]
        # print(old_v_labels)

        new_h_labels = []
        # print("Опорный:", self.selected_row, self.selected_col)
        for r in range (len(old_h_labels)):
            if r != self.selected_col:
                new_h_labels.append(old_h_labels[r])
            else:
                new_h_labels.append(old_v_labels[self.selected_row])
        # print(new_h_labels)

        new_v_labels = []
        for r in range(len(old_v_labels)):
            if r != self.selected_row:
                new_v_labels.append(old_v_labels[r])
            else:
                new_v_labels.append(old_h_labels[self.selected_col])
        # print(new_v_labels)


        new_data = []
        r_opor = self.selected_row
        c_opor = self.selected_col
        opor_el = table_data[r_opor][c_opor]

        # Создаем пустую матрицу того же размера
        new_data = []
        for r in range(rows):
            row = []
            for c in range(cols):
                row.append(Fraction(0))
            new_data.append(row)

        # 2. Новый "опорный"
        new_opor_el = Fraction(1) / opor_el
        new_data[r_opor][c_opor] = new_opor_el

        # print("Пустая с новым опорным")
        # for r in range(len(new_data)):
        #     print(new_data[r])
        # print()

        # 3. Пересчитываем строку c опорным элементом
        for c in range(cols):
            if c != c_opor:
                new_data[r_opor][c] = table_data[r_opor][c] / opor_el

        # print("Пересчёт строки")
        # for r in range(len(new_data)):
        #     print(new_data[r])
        # print()

        # 4. Пересчитываем столбец
        for r in range(rows):
            if r != r_opor:
                new_data[r][c_opor] = -(table_data[r][c_opor] / opor_el)

        # print("Пересчёт столбца")
        # for r in range(len(new_data)):
        #     print(new_data[r])
        # print()

        #5. Пересчитываем всё остальное
        for r in range(rows):
            if r == r_opor: continue # уже посчитали
            a_is = table_data[r][c_opor]
            for c in range(cols):
                if c == c_opor: continue  # уже посчитали
                else:
                    # row_i(1) = row_i(0) - a_is(0) * row_s(1)
                    old_val = table_data[r][c]
                    new_opor_row_val = new_data[r_opor][c]
                    new_data[r][c] = old_val - a_is * new_opor_row_val

        # print("Конечная таблица")
        # for r in range(len(new_data)):
        #     print(new_data[r])
        # print()

        # Рисуем таблицу

        new_table = QTableWidget()
        new_table.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        new_table.setSelectionBehavior(QTableWidget.SelectItems)
        new_table.itemClicked.connect(self.on_table_cell_clicked)
        new_table.setRowCount(rows)
        new_table.setColumnCount(cols)

        new_table.setHorizontalHeaderLabels(new_h_labels)
        new_table.setVerticalHeaderLabels(new_v_labels)

        # заполняем таблицу данными из new_data
        for r in range(rows):
            for c in range(cols):
                val = new_data[r][c]
                if val.denominator == 1: # чтоб 5/1 дробью не было (знаменатель)
                    text = str(val.numerator) # числитель
                else:
                    text = str(val)

                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                new_table.setItem(r, c, item)

        for col in range(new_table.columnCount() - 1, -1, -1):
            header = new_table.horizontalHeaderItem(col)
            if header and header.text().startswith('x'):
                try:
                    var_num = int(header.text()[1:])
                    if var_num > self.n_vars:
                        new_table.removeColumn(col)
                except ValueError:
                    pass

        # Добавляем таблицу в интерфейс
        iter_num = len(self.iteration_tables)  # Номер новой итерации
        self.iterations_layout.addWidget(QLabel(f"<b>Итерация *{iter_num}</b>"))
        self.iterations_layout.addWidget(new_table)
        self.iteration_tables.append(new_table)

        # Сбрасываем выбор
        self.selected_table_widget = None
        self.selected_row = -1
        self.selected_col = -1

        last_row = new_table.rowCount() - 1
        all_zero = True
        for col in range(new_table.columnCount()):
            item = new_table.item(last_row, col)
            if item and self.parse_fraction(item.text()) != 0:
                all_zero = False
                break
        if all_zero:
            self.last_artificial_table = new_table
            # Извлечём базисные переменные и их значения
            self._extract_basis_from_table(new_table)
            # Можно разблокировать кнопку перехода к симплексу
            self.btn_to_simplex.setEnabled(True)
            QMessageBox.information(self, "Искусственный метод завершён",
                                    "Получено допустимое базисное решение.\n"
                                    "Нажмите 'Построить симплекс-таблицу' для продолжения.")

    """ Третья вкладка """

    # построение x0 таблицы
    def build_x0_table(self):
        """Строит первую симплекс-таблицу для исходной задачи на основе последней таблицы искусственного метода."""

        if self.last_artificial_table is None:
            QMessageBox.warning(self, "Нет данных",
                                "Сначала решите задачу методом искусственного базиса до конца.")
            return

        # 1. Определяем, какие исходные переменные вошли в базис
        n = self.n_vars
        m = self.m_constrs

        # Из последней таблицы берём:
        # - коэффициенты при исходных переменных x1..xn в каждой строке ограничений
        # - столбец b
        # - информацию о базисных переменных

        # Создаём пустую матрицу A_new (m x n) и вектор b_new
        A_new = [[Fraction(0) for _ in range(n)] for _ in range(m)]
        b_new = [Fraction(0) for _ in range(m)]

        # Сопоставим номера исходных переменных с индексами столбцов в последней таблице
        # В последней таблице могут быть столбцы для x1..xn, а также для дополнительных переменных.
        # Нам нужны только те столбцы, заголовки которых начинаются с "x" и номер <= n.
        table = self.last_artificial_table
        cols = table.columnCount()
        rows = table.rowCount()

        # Словарь: имя переменной -> индекс столбца в последней таблице
        col_index = {}
        for c in range(cols):
            header = table.horizontalHeaderItem(c).text()
            col_index[header] = c

        # Для каждой строки ограничений (первые m строк) копируем коэффициенты
        for r in range(m):
            # Находим, какая базисная переменная соответствует этой строке
            basis_var = table.verticalHeaderItem(r).text()
            # Если базисная переменная – одна из исходных (x1..xn), то её значение в столбце b
            # и коэффициенты при небазисных исходных переменных берём из этой строки.
            # Но нам нужны коэффициенты при x1..xn, даже если они небазисные.
            for j in range(1, n + 1):
                var_name = f"x{j}"
                if var_name in col_index:
                    col = col_index[var_name]
                    item = table.item(r, col)
                    val = self.parse_fraction(item.text()) if item else Fraction(0)
                    A_new[r][j - 1] = val
            # Столбец b
            b_item = table.item(r, cols - 1)
            b_new[r] = self.parse_fraction(b_item.text()) if b_item else Fraction(0)

        # 2. Строим целевую строку для исходной задачи
        # Сначала вычислим значение целевой функции на текущем решении
        # Решение: x_j = b_new[i] если x_j в базисе строки i, иначе 0.
        # Но проще: значение F = sum(c_j * x_j), где x_j берутся из решения.
        # Заполним массив solution размером n
        solution = [Fraction(0)] * n
        # Определим, какая базисная переменная находится в каждой строке
        for r in range(m):
            basis_name = table.verticalHeaderItem(r).text()
            if basis_name.startswith('x'):
                try:
                    var_num = int(basis_name[1:])
                    if 1 <= var_num <= n:
                        solution[var_num - 1] = b_new[r]
                except:
                    pass

        # Значение F
        F_value = Fraction(0)
        for j in range(n):
            F_value += self.c_coeffs[j] * solution[j]

        # Теперь вычислим коэффициенты при небазисных переменных в выражении F
        # Для этого для каждой исходной переменной x_j (j=0..n-1) определим, является ли она базисной.
        # Если да, то её коэффициент в строке F = 0.
        # Если нет, то коэффициент = c_j - sum( c_{базисной} * a_{ij} ), где a_{ij} – коэффициент при x_j в i-й строке.
        # Но проще: мы можем построить строку F, используя текущую таблицу ограничений и формулу:
        # F = sum(c_j * x_j) = sum(c_j * (выражение через небазисные)).
        # Для этого пройдём по всем небазисным переменным и вычислим их коэффициенты.

        # Сначала определим, какие переменные базисные
        is_basic = [False] * n
        basic_row = [-1] * n  # для каждой переменной – номер строки, где она базисная
        for r in range(m):
            basis_name = table.verticalHeaderItem(r).text()
            if basis_name.startswith('x'):
                try:
                    var_num = int(basis_name[1:])
                    if 1 <= var_num <= n:
                        is_basic[var_num - 1] = True
                        basic_row[var_num - 1] = r
                except:
                    pass

        # Строка F: длина n+1 (n коэффициентов и b)
        F_row = [Fraction(0)] * (n + 1)
        # Коэффициент при x_j в строке F:
        # Если x_j базисная, то 0. Иначе: c_j - sum( c_{базисная} * a_{ij} ) по i, где a_{ij} – из A_new.
        # Но c_{базисная} для базисной переменной x_k – это c_k.
        # Поэтому проще: для каждого j небазисного:
        # coef = c_j - sum_{i=0}^{m-1} c_{basis_var_i} * A_new[i][j]
        # где basis_var_i – переменная, базисная в строке i.
        for j in range(n):
            if is_basic[j]:
                F_row[j] = Fraction(0)
            else:
                coef = self.c_coeffs[j]
                for i in range(m):
                    basis_var_name = table.verticalHeaderItem(i).text()
                    if basis_var_name.startswith('x'):
                        try:
                            bvar_num = int(basis_var_name[1:])
                            if 1 <= bvar_num <= n:
                                coef -= self.c_coeffs[bvar_num - 1] * A_new[i][j]
                        except:
                            pass
                F_row[j] = coef
        # Свободный член (столбец b)
        # F_value = sum(c_j * x_j) = sum(c_basic * b_new[i]) – уже посчитано.
        # Но в симплекс-таблице в правом нижнем углу обычно записывают -F_value (для min) или F_value (для max).
        # Для единообразия с искусственным методом, где в последней строке был -F, поступим так:
        # если у нас min, то в правом нижнем углу пишем -F_value, а коэффициенты при небазисных – со знаком минус (как в искусственном).
        # Чтобы не усложнять, оставим F_row[j] как есть, а в правом углу – F_value (со знаком +).
        # Но для работы кнопки выбора опорного элемента, которая ожидает отрицательные коэффициенты в строке F, нужно их инвертировать для min.
        # Упростим: будем хранить F_row как коэффициенты при **небазисных** переменных в выражении F = const + sum(...),
        # а в таблицу поместим их **со знаком минус** (как в искусственном базисе), чтобы выбор опорного столбца работал одинаково.
        # Тогда правый нижний угол = -const (т.е. -F_value) для min.
        if self.is_minimization:
            for j in range(n):
                F_row[j] = -F_row[j]  # инвертируем, чтобы в таблице были отрицательные коэффициенты для выбора
            F_right = -F_value
        else:
            # Для максимизации можно преобразовать к минимизации, либо оставить логику выбора по положительным коэффициентам.
            # Для простоты будем считать, что задача на min (преобразовать max в min умножением на -1).
            # Поэтому требовать от пользователя, чтобы он ввёл задачу на min.
            F_right = F_value  # не проверено для max

        # 3. Создаём новую таблицу QTableWidget для симплекс-метода
        simplex_table = QTableWidget()
        simplex_table.setRowCount(m + 1)
        simplex_table.setColumnCount(n + 1)

        # Заголовки столбцов: x1, x2, ..., xn, b
        h_labels = [f"x{j + 1}" for j in range(n)] + ["b"]
        simplex_table.setHorizontalHeaderLabels(h_labels)

        # Заголовки строк: базисные переменные (из последней таблицы) + "F"
        v_labels = []
        for r in range(m):
            basis_var = table.verticalHeaderItem(r).text()
            # Если базисная переменная – искусственная (x с номером > n), то заменяем её на соответствующую исходную?
            # По идее, искусственные должны выйти из базиса. Но на всякий случай проверим.
            if basis_var.startswith('x'):
                try:
                    num = int(basis_var[1:])
                    if num > n:
                        # Это искусственная переменная, но она не должна быть в базисе. Если оказалась, то задача несовместна.
                        QMessageBox.critical(self, "Ошибка", "Искусственная переменная в базисе! Задача несовместна.")
                        return
                except:
                    pass
            v_labels.append(basis_var)
        v_labels.append("F")
        simplex_table.setVerticalHeaderLabels(v_labels)

        # Заполняем коэффициенты ограничений
        for i in range(m):
            for j in range(n):
                item = QTableWidgetItem(str(A_new[i][j]))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                simplex_table.setItem(i, j, item)
            # Столбец b
            b_item = QTableWidgetItem(str(b_new[i]))
            b_item.setFlags(b_item.flags() & ~Qt.ItemIsEditable)
            simplex_table.setItem(i, n, b_item)

        # Заполняем строку F
        for j in range(n):
            f_item = QTableWidgetItem(str(F_row[j]))
            f_item.setFlags(f_item.flags() & ~Qt.ItemIsEditable)
            simplex_table.setItem(m, j, f_item)
        # Правый нижний угол
        f_right_item = QTableWidgetItem(str(F_right))
        f_right_item.setFlags(f_right_item.flags() & ~Qt.ItemIsEditable)
        simplex_table.setItem(m, n, f_right_item)

        # Отображаем таблицу на вкладке симплекс-метода
        # Очищаем старые таблицы
        while self.simplex_iterations_layout.count():
            item = self.simplex_iterations_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.simplex_tables.clear()

        self.simplex_iterations_layout.addWidget(QLabel("<b>Итерация 0 (начальная симплекс-таблица)</b>"))
        self.simplex_iterations_layout.addWidget(simplex_table)
        self.simplex_tables.append(simplex_table)

        # Подключаем обработчик клика по ячейке для выбора опорного элемента
        simplex_table.itemClicked.connect(self.simplex_on_cell_clicked)

        # Активируем кнопки
        self.simplex_btn_back.setEnabled(True)
        self.simplex_btn_select.setEnabled(True)
        self.simplex_btn_auto.setEnabled(True)

        # Сбрасываем выбор
        self.simplex_selected_row = -1
        self.simplex_selected_col = -1
        self.simplex_selected_table = None

    def _extract_basis_from_table(self, table):
        """Извлекает базисные переменные и их значения из последней симплекс-таблицы."""
        rows = table.rowCount()
        cols = table.columnCount()
        self.last_artificial_basis = []
        self.last_artificial_solution = []
        # Базисные переменные – это те, что в заголовках строк (кроме последней)
        for r in range(rows - 1):  # последняя строка – F
            var_name = table.verticalHeaderItem(r).text()
            self.last_artificial_basis.append(var_name)
            # Значение базисной переменной – в столбце "b"
            b_item = table.item(r, cols - 1)
            val = self.parse_fraction(b_item.text()) if b_item else Fraction(0)
            self.last_artificial_solution.append(val)

    #+ выбор опорной ячейки в симплекс таблице
    def simplex_on_cell_clicked(self, item):
        row = item.row()
        col = item.column()
        self.simplex_selected_row = row
        self.simplex_selected_col = col
        self.simplex_selected_table = item.tableWidget()

    #+ кнопка Выбрать опорный элемент - обработки
    def simplex_on_select_opor(self):
        if self.simplex_selected_row == -1 or self.simplex_selected_col == -1:
            QMessageBox.warning(self, "Внимание", "Сначала выберите ячейку в таблице!")
            return

        if self.simplex_selected_table != self.simplex_tables[-1]:
            QMessageBox.warning(self, "Внимание", "Выберите ячейку в последней (текущей) таблице!")
            return

        row, col = self.simplex_selected_row, self.simplex_selected_col
        if row >= self.m_constrs:
            QMessageBox.warning(self, "Внимание", "Опорный элемент должен быть в строке ограничений!")
            return

        current_table = self.simplex_tables[-1]
        opor_itm = current_table.item(row, col)
        if not opor_itm or not opor_itm.text():
            QMessageBox.warning(self, "Внимание", "Ячейка пуста!")
            return

        try:
            opor_val = self.parse_fraction(opor_itm.text())
        except:
            QMessageBox.warning(self, "Внимание", "Неверное числовое значение!")
            return

        if opor_val <= 0:
            QMessageBox.warning(self, "Внимание", "Опорный элемент должен быть > 0!")
            return

        # Для задачи на минимизацию: коэффициент в строке F должен быть отрицательным
        f_itm = current_table.item(self.m_constrs, col)
        if f_itm and f_itm.text():
            try:
                if self.parse_fraction(f_itm.text()) >= 0:
                    QMessageBox.warning(self, "Внимание", "Коэффициент в строке F должен быть отрицательным!")
                    return
            except (ValueError, ZeroDivisionError):
                pass

        try:
            opor_itm.setBackground(QColor("pink"))
            current_table.clearSelection()
            QMessageBox.information(self, "Успех", "Итерация выполнена!")
            self.simplex_perform_opor()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Сбой преобразования:\n{str(e)}")

    #+ кнопка Шаг назад
    def simplex_on_step_back(self):
        if len(self.simplex_tables) <= 1:
            QMessageBox.information(self, "Инфо", "Нечего возвращать! Это начальная таблица.")
            return

        last_item = self.simplex_iterations_layout.takeAt(self.simplex_iterations_layout.count() - 1)
        if last_item and last_item.widget():
            last_item.widget().deleteLater()

        label_item = self.simplex_iterations_layout.takeAt(self.simplex_iterations_layout.count() - 1)
        if label_item and label_item.widget():
            label_item.widget().deleteLater()

        self.simplex_tables.pop()

        self.simplex_selected_table = None
        self.simplex_selected_row = -1
        self.simplex_selected_col = -1

        QMessageBox.information(self, "Готово", "Возврат выполнен!")

    #+- итерации
    def simplex_perform_opor(self):
        current_table = self.simplex_tables[-1]
        rows = current_table.rowCount()
        cols = current_table.columnCount()

        # Считываем данные
        table_data = []
        for r in range(rows):
            row_vals = []
            for c in range(cols):
                item = current_table.item(r, c)
                try:
                    val = self.parse_fraction(item.text()) if item and item.text() else Fraction(0)
                except:
                    val = Fraction(0)
                row_vals.append(val)
            table_data.append(row_vals)

        # Меняем заголовки
        old_h_labels = [current_table.horizontalHeaderItem(c).text() for c in range(cols)]
        old_v_labels = [current_table.verticalHeaderItem(r).text() for r in range(rows)]

        new_h_labels = []
        for c in range(cols):
            if c != self.simplex_selected_col:
                new_h_labels.append(old_h_labels[c])
            else:
                new_h_labels.append(old_v_labels[self.simplex_selected_row])

        new_v_labels = []
        for r in range(rows):
            if r != self.simplex_selected_row:
                new_v_labels.append(old_v_labels[r])
            else:
                new_v_labels.append(old_h_labels[self.simplex_selected_col])

        r_opor = self.simplex_selected_row
        c_opor = self.simplex_selected_col
        opor_el = table_data[r_opor][c_opor]

        # Новая матрица
        new_data = []
        for r in range(rows):
            row = []
            for c in range(cols):
                row.append(Fraction(0))
            new_data.append(row)
        new_data[r_opor][c_opor] = Fraction(1) / opor_el

        # Строка опорного элемента
        for c in range(cols):
            if c != c_opor:
                new_data[r_opor][c] = table_data[r_opor][c] / opor_el

        # Столбец опорного элемента
        for r in range(rows):
            if r != r_opor:
                new_data[r][c_opor] = -(table_data[r][c_opor] / opor_el)

        # Остальные ячейки
        for r in range(rows):
            if r == r_opor:
                continue
            a_is = table_data[r][c_opor]
            for c in range(cols):
                if c == c_opor:
                    continue
                new_data[r][c] = table_data[r][c] - a_is * new_data[r_opor][c]

        # Создаём новую таблицу
        new_table = QTableWidget()
        new_table.setRowCount(rows)
        new_table.setColumnCount(cols)
        new_table.setHorizontalHeaderLabels(new_h_labels)
        new_table.setVerticalHeaderLabels(new_v_labels)
        new_table.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        new_table.setSelectionBehavior(QTableWidget.SelectItems)
        new_table.itemClicked.connect(self.simplex_on_cell_clicked)

        for r in range(rows):
            for c in range(cols):
                val = new_data[r][c]
                text = str(val.numerator) if val.denominator == 1 else str(val)
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                new_table.setItem(r, c, item)

        # Добавляем в интерфейс
        iter_num = len(self.simplex_tables)
        self.simplex_iterations_layout.addWidget(QLabel(f"<b>Итерация {iter_num}</b>"))
        self.simplex_iterations_layout.addWidget(new_table)
        self.simplex_tables.append(new_table)

        # Сбрасываем выбор
        self.simplex_selected_table = None
        self.simplex_selected_row = -1
        self.simplex_selected_col = -1

        # Проверка оптимальности (для min: все коэффициенты в строке F >= 0)
        last_row = new_table.rowCount() - 1
        all_non_negative = True
        for col in range(new_table.columnCount() - 1):  # кроме столбца b
            item = new_table.item(last_row, col)
            if item and self.parse_fraction(item.text()) < 0:
                all_non_negative = False
                break
        if all_non_negative:
            self.simplex_btn_select.setEnabled(False)
            self.simplex_btn_auto.setEnabled(False)
            QMessageBox.information(self, "Оптимум найден",
                                    "Симплекс-метод завершён. Достигнуто оптимальное решение.")

    # кнопка авто-решения
    def simplex_auto_solve(self):
        """Автоматически решает задачу симплекс-методом."""
        # Проверяем, что таблица есть
        if not self.simplex_tables:
            QMessageBox.warning(self, "Нет данных", "Сначала постройте начальную симплекс-таблицу.")
            return

        current_table = self.simplex_tables[-1]
        iteration = 0
        max_iter = 100  # защита от зацикливания

        while iteration < max_iter:
            # Ищем отрицательный коэффициент в строке F (для min)
            last_row = current_table.rowCount() - 1
            pivot_col = -1
            for col in range(current_table.columnCount() - 1):  # кроме b
                item = current_table.item(last_row, col)
                if item and self.parse_fraction(item.text()) < 0:
                    pivot_col = col
                    break

            if pivot_col == -1:
                QMessageBox.information(self, "Оптимум", "Достигнуто оптимальное решение.")
                break

            # Ищем опорную строку по минимальному отношению b / a_ij (a_ij > 0)
            pivot_row = -1
            min_ratio = None
            for row in range(self.m_constrs):
                a_ij_item = current_table.item(row, pivot_col)
                if not a_ij_item:
                    continue
                a_ij = self.parse_fraction(a_ij_item.text())
                if a_ij > 0:
                    b_item = current_table.item(row, current_table.columnCount() - 1)
                    b_val = self.parse_fraction(b_item.text()) if b_item else Fraction(0)
                    ratio = b_val / a_ij
                    if min_ratio is None or ratio < min_ratio:
                        min_ratio = ratio
                        pivot_row = row

            if pivot_row == -1:
                QMessageBox.warning(self, "Ошибка", "Целевая функция не ограничена (нет опорной строки).")
                return

            # Выбираем ячейку и выполняем шаг
            self.simplex_selected_row = pivot_row
            self.simplex_selected_col = pivot_col
            self.simplex_selected_table = current_table

            # Выполняем преобразование
            try:
                self.simplex_perform_opor()
                current_table = self.simplex_tables[-1]
                iteration += 1
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка на итерации {iteration}: {e}")
                return

        if iteration >= max_iter:
            QMessageBox.warning(self, "Предупреждение", "Достигнуто максимальное число итераций.")

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