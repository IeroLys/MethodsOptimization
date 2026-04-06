import sys
from fractions import Fraction
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QGridLayout, QLabel, QLineEdit,
                             QSpinBox, QPushButton, QTableWidget, QTableWidgetItem,
                             QRadioButton, QButtonGroup, QMessageBox, QGroupBox,
                             QFileDialog, QScrollArea, QTabWidget, QTextEdit, QSizePolicy)
from PyQt5.QtCore import Qt, QRegularExpression
from PyQt5.QtGui import QRegularExpressionValidator, QColor


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

        self.btn_test = QPushButton("test")
        self.btn_test.clicked.connect(self.x0_table)
        self.btn_test.setEnabled(True)

        control_layout.addWidget(self.simplex_btn_back)
        control_layout.addWidget(self.simplex_btn_select)
        control_layout.addWidget(self.simplex_btn_auto)
        control_layout.addWidget(self.btn_test)
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

        n = self.n_vars
        m = self.m_constrs
        table = self.last_artificial_table

        # 1. Собираем коэффициенты ограничений из последней таблицы
        A_new = [[Fraction(0) for _ in range(n)] for _ in range(m)]
        b_new = [Fraction(0) for _ in range(m)]

        # Сопоставляем заголовки столбцов с индексами
        col_index = {}
        for c in range(table.columnCount()):
            header = table.horizontalHeaderItem(c).text()
            col_index[header] = c

        # Определяем, какие переменные базисные в каждой строке
        basis_vars = []  # список базисных переменных для каждой строки
        for r in range(m):
            basis_var = table.verticalHeaderItem(r).text()
            basis_vars.append(basis_var)

            # Заполняем коэффициенты при x1..xn
            for j in range(1, n + 1):
                var_name = f"x{j}"
                if var_name in col_index:
                    col = col_index[var_name]
                    item = table.item(r, col)
                    val = self.parse_fraction(item.text()) if item else Fraction(0)
                    A_new[r][j - 1] = val

            # Столбец b
            b_item = table.item(r, table.columnCount() - 1)
            b_new[r] = self.parse_fraction(b_item.text()) if b_item else Fraction(0)

        # 2. Вычисляем целевую функцию через подстановку базисных переменных
        # Выражаем базисные переменные через небазисные

        # Сначала определим, какие переменные входят в базис
        is_basic = [False] * n
        basic_row_for_var = [-1] * n  # для каждой переменной - номер строки, где она базисная

        for r in range(m):
            basis_name = basis_vars[r]
            if basis_name.startswith('x'):
                try:
                    var_num = int(basis_name[1:])
                    if 1 <= var_num <= n:
                        is_basic[var_num - 1] = True
                        basic_row_for_var[var_num - 1] = r
                except:
                    pass

        # 3. Строим выражение для F через небазисные переменные
        # F = sum(c_j * x_j)
        # Для базисных переменных подставляем их выражения через небазисные

        # Создаем коэффициенты при небазисных переменных
        F_coeff = [Fraction(0) for _ in range(n)]  # коэффициенты при x1..xn
        F_const = Fraction(0)  # свободный член

        # Для каждой переменной x_j
        for j in range(n):
            if is_basic[j]:
                # Это базисная переменная, подставляем ее выражение
                row = basic_row_for_var[j]
                # x_j = b_new[row] - sum(A_new[row][k] * x_k) для небазисных k
                # Вносим вклад в F: c_j * x_j = c_j * b_new[row] - c_j * sum(A_new[row][k] * x_k)

                # Свободный член
                F_const += self.c_coeffs[j] * b_new[row]

                # Коэффициенты при небазисных переменных
                for k in range(n):
                    if not is_basic[k]:  # только небазисные
                        # Вычитаем c_j * A_new[row][k]
                        F_coeff[k] -= self.c_coeffs[j] * A_new[row][k]
            else:
                # Небазисная переменная, просто добавляем c_j * x_j
                F_coeff[j] += self.c_coeffs[j]

        # 4. Теперь F_coeff содержит коэффициенты при небазисных переменных,
        # а F_const - свободный член

        # Для симплекс-таблицы нам нужна строка F в виде:
        # F + сумма(коэффициенты * небазисные) = const
        # или F = const - сумма(коэффициенты * небазисные)
        # В классической симплекс-таблице в строке F записывают коэффициенты с обратным знаком

        # В правом нижнем углу будет -const (для min)
        F_right = -F_const

        # А в строке F будут коэффициенты с противоположным знаком
        F_row = [-F_coeff[j] for j in range(n)]

        # Если задача на max, преобразуем к min
        if not self.is_minimization:
            # Умножаем все на -1
            F_row = [-coef for coef in F_row]
            F_right = -F_right

        # 5. Создаем новую симплекс-таблицу
        simplex_table = QTableWidget()
        simplex_table.setRowCount(m + 1)
        simplex_table.setColumnCount(n + 1)

        # Заголовки столбцов
        h_labels = [f"x{j + 1}" for j in range(n)] + ["b"]
        simplex_table.setHorizontalHeaderLabels(h_labels)

        # Заголовки строк (базисные переменные из последней таблицы)
        v_labels = []
        for r in range(m):
            basis_var = basis_vars[r]
            # Проверяем, не искусственная ли переменная
            if basis_var.startswith('x'):
                try:
                    num = int(basis_var[1:])
                    if num > n:
                        # Искусственная переменная - заменяем на свободный член?
                        # В правильном решении искусственные должны выйти из базиса
                        QMessageBox.critical(self, "Ошибка",
                                             "Искусственная переменная в базисе! Задача несовместна или решение не найдено.")
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

        # Отображаем таблицу
        while self.simplex_iterations_layout.count():
            item = self.simplex_iterations_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.simplex_tables.clear()

        self.simplex_iterations_layout.addWidget(QLabel("<b>Итерация 0 (начальная симплекс-таблица)</b>"))
        self.simplex_iterations_layout.addWidget(simplex_table)
        self.simplex_tables.append(simplex_table)

        # Подключаем обработчик
        simplex_table.itemClicked.connect(self.simplex_on_cell_clicked)

        # Активируем кнопки
        self.simplex_btn_back.setEnabled(True)
        self.simplex_btn_select.setEnabled(True)
        self.simplex_btn_auto.setEnabled(True)

        # Сбрасываем выбор
        self.simplex_selected_row = -1
        self.simplex_selected_col = -1
        self.simplex_selected_table = None

        # Выводим информацию о полученном выражении
        QMessageBox.information(self, "Симплекс-таблица построена",
                                f"F = {F_const} + " + " + ".join(
                                    [f"({F_coeff[j]})*x{j + 1}" for j in range(n) if F_coeff[j] != 0]) + "\n" +
                                f"В таблице: F = {F_right} - " + " - ".join(
                                    [f"({-F_row[j]})*x{j + 1}" for j in range(n) if F_row[j] != 0]))

    def x0_tableO(self):
        if self.last_artificial_table is None:
            print("Нет таблицы")
            return
        last_table = self.last_artificial_table

        # копируем таблицу
        rows = last_table.rowCount()
        cols = last_table.columnCount()
        last_data = []
        for r in range(rows):
            row_vals = []
            for c in range(cols):
                item = last_table.item(r, c)
                try:
                    val = self.parse_fraction(item.text()) if item and item.text() else Fraction(0)
                except (ValueError, ZeroDivisionError):
                    val = Fraction(0)
                row_vals.append(val)
            last_data.append(row_vals)

        h_labels = [last_table.horizontalHeaderItem(c).text() for c in range(cols)]
        print(h_labels)
        v_labels = [last_table.verticalHeaderItem(r).text() for r in range(rows)]
        print(v_labels)

        new_data = []
        '''

        h_labels = ["x3", "x4", "b"]
        v_labels = ["x2", "x1", "F"]

        last_data = [
            [2, -1, 1],  # строка x2
            [-1, 1, 2],  # строка x1
            [0, 0, 0]  # строка F
        ]
        n = 3
        m = 3

        print("Все заголовки: ")
        print(h_labels)
        print(v_labels)
        print()

        # -1*x3 + 1*x4 = 2
        for i in range(m):
            bas_var = v_labels[i] #Xn
            st = ""
            for j in range(n):
                if j == n-1:
                    st += f"= {last_data[i][j]}"
                    break
                if j == n-2:
                    st += f"{last_data[i][j]}*{h_labels[j]} "
                else:
                    st += f"{last_data[i][j]}*{h_labels[j]} +"
            print(st)

        b_vector = []
        for i in range(m):
            for j in range(n):
                if j == n-1:
                    b_vector.append(last_data[i][j])
        print(b_vector)

        for i in range(m):
            st = f"{v_labels[i]} = {b_vector[i]}"
            for j in range(n-1):
                st += f" - {last_data[i][j]}*{h_labels[j]}"
            print(st)

        # 3. Пересчитываем строку c опорным элементом
        # for c in range(cols):
        #     if c != c_opor:
        #         new_data[r_opor][c] = table_data[r_opor][c] / opor_el

        # x2 = 1 - 0*x1 - 2*x3 + 1*x4
        # x2 = b -
        '''

        basic_vars = []
        for i in range(len(v_labels) - 1):
            basic_vars.append(v_labels[i])

        n = self.n_vars
        m = self.m_constrs

        b_values = [] # b
        for i in range(rows):
            for j in range(cols):
                if j == cols - 1:
                    b_values.append(last_data[i][j])

        print("b:", b_values)

        # СОЗДАЁМ ДВУМЕРНЫЙ МАССИВ СРАЗУ!
        basic_coeffs = [[Fraction(0) for _ in range(n)] for _ in range(m)]

        # Заполняем его
        for i in range(m):  # строки
            for j in range(cols - 1):  # столбцы с переменными
                var_name = h_labels[j]
                if var_name.startswith('x'):
                    try:
                        var_num = int(var_name[1:]) - 1
                        if 0 <= var_num < n:
                            # Ставим минус, потому что переносим в правую часть
                            basic_coeffs[i][var_num] = -last_data[i][j]
                    except:
                        pass

        # Проверяем, что получилось
        print("Матрица коэффициентов:")
        for i in range(m):
            print(f"{basic_vars[i]}: {basic_coeffs[i]}")

    def x0_tableA(self):
        # Вместо отдельных переменных используем списки
        b = [1, 2]  # для x2 и x1
        coeff = [
            [0, 0, 2, -1],  # для x2: [при x1, при x2, при x3, при x4]
            [0, 0, 1, 1]  # для x1: [при x1, при x2, при x3, при x4]
        ]

        # Коэффициенты F
        F = [-2, -1, -3, -1]  # при x1, x2, x3, x4
        F_const = 0

        # Подстановка x1 (индекс 1 в F, строка 1 в coeff)
        coeff_in_f = F[1]  # -2
        b_value = b[1]  # 2
        F_const += coeff_in_f * b_value  # -2 * 2 = -4

        for j in range(4):  # по всем переменным
            F[j] += coeff_in_f * coeff[1][j]  # -2 * coeff[1][j]

        F[1] = 0  # обнуляем x1

        # Подстановка x2 (индекс 0 в F, строка 0 в coeff)
        coeff_in_f = F[0]  # -1
        b_value = b[0]  # 1
        F_const += coeff_in_f * b_value  # -1 * 1 = -1

        for j in range(4):
            F[j] += coeff_in_f * coeff[0][j]

        F[0] = 0

        # Результат
        print(f"F = {F_const} + {F[0]}*x1 + {F[1]}*x2 + {F[2]}*x3 + {F[3]}*x4")

    def x0_table(self):
        """Строит первую симплекс-таблицу для исходной задачи на основе последней таблицы искусственного метода."""

        if self.last_artificial_table is None:
            QMessageBox.warning(self, "Нет данных",
                                "Сначала решите задачу методом искусственного базиса до конца.")
            return

        n = self.n_vars
        m = self.m_constrs
        table = self.last_artificial_table
        rows = table.rowCount()
        cols = table.columnCount()

        # ========== 1. Получаем данные из таблицы ==========
        # Заголовки
        h_labels = []
        for c in range(cols):
            h_labels.append(table.horizontalHeaderItem(c).text())

        v_labels = []
        for r in range(rows):
            v_labels.append(table.verticalHeaderItem(r).text())

        # Данные в виде дробей
        last_data = []
        for r in range(rows):
            row_data = []
            for c in range(cols):
                item = table.item(r, c)
                val = self.parse_fraction(item.text()) if item and item.text() else Fraction(0)
                row_data.append(val)
            last_data.append(row_data)

        # ========== 2. Определяем базисные и небазисные переменные ==========
        # Базисные переменные - заголовки строк (кроме последней строки F)
        basic_vars = []
        for r in range(m):
            basic_vars.append(v_labels[r])

        # Небазисные переменные - заголовки столбцов (кроме b), которых нет среди базисных
        nonbasic_vars = []
        for c in range(cols - 1):  # все столбцы кроме b
            var_name = h_labels[c]
            if var_name not in basic_vars:
                nonbasic_vars.append(var_name)

        # ========== 3. Собираем b и коэффициенты для базисных переменных ==========
        b_values = []  # свободные члены
        basic_coeffs = []  # коэффициенты при небазисных переменных

        for i in range(m):
            # Свободный член b
            b_values.append(last_data[i][cols - 1])

            # Коэффициенты при небазисных переменных (с МИНУСОМ из-за переноса)
            coeff_row = []
            for nb_var in nonbasic_vars:
                # Находим индекс этого столбца
                for c in range(cols - 1):
                    if h_labels[c] == nb_var:
                        coeff_row.append(-last_data[i][c])
                        break
            basic_coeffs.append(coeff_row)

        # ========== 4. Вычисляем коэффициенты F по формуле ==========
        # const = sum(c_basic * b)
        # coeffs[nb] = sum(c_basic * коэффициент_при_nb) + c_nb

        const = Fraction(0)
        coeffs = [Fraction(0) for _ in range(n)]

        # Проходим по каждой базисной переменной
        for i in range(m):
            basic_var = basic_vars[i]
            # Получаем номер базисной переменной (x1 -> 0, x2 -> 1, ...)
            if basic_var.startswith('x'):
                basic_num = int(basic_var[1:]) - 1
                c_basic = self.c_coeffs[basic_num]

                # Добавляем вклад от b
                const += c_basic * b_values[i]

                # Добавляем вклад от небазисных переменных
                for j, nb_var in enumerate(nonbasic_vars):
                    nb_num = int(nb_var[1:]) - 1
                    coeffs[nb_num] += c_basic * basic_coeffs[i][j]

        # Добавляем небазисные переменные (те, что не в базисе)
        for j in range(n):
            var_name = f"x{j + 1}"
            if var_name not in basic_vars:
                coeffs[j] += self.c_coeffs[j]

        # ========== 5. Преобразуем для симплекс-таблицы ==========
        # В симплекс-таблице: F + сумма(коэффициенты * переменные) = const
        # Поэтому меняем знаки
        F_row = [-coeffs[j] for j in range(n)]
        F_right = -const

        # Если задача на max, преобразуем к min
        if not self.is_minimization:
            F_row = [-coef for coef in F_row]
            F_right = -F_right

        # ========== 6. Собираем небазисные переменные (у которых коэффициент не 0) ==========
        nonbasic_with_coeff = []
        nonbasic_indices = []
        for j in range(n):
            if coeffs[j] != 0:
                nonbasic_with_coeff.append(f"x{j + 1}")
                nonbasic_indices.append(j)

        # Если все коэффициенты нулевые - задача решена
        if len(nonbasic_with_coeff) == 0:
            QMessageBox.information(self, "Оптимум найден",
                                    f"Оптимальное решение: F = {const}")
            return

        # ========== 7. Создаём новую симплекс-таблицу ==========
        simplex_table = QTableWidget()
        simplex_table.setRowCount(m + 1)
        simplex_table.setColumnCount(len(nonbasic_with_coeff) + 1)

        # Заголовки столбцов (только небазисные переменные с ненулевыми коэффициентами)
        col_labels = nonbasic_with_coeff + ["b"]
        simplex_table.setHorizontalHeaderLabels(col_labels)

        # Заголовки строк
        row_labels = basic_vars + ["F"]
        simplex_table.setVerticalHeaderLabels(row_labels)

        # Заполняем строки ограничений
        for i in range(m):
            # Коэффициенты при небазисных переменных
            for col_idx, nb_var in enumerate(nonbasic_with_coeff):
                # Находим коэффициент в basic_coeffs[i]
                coeff = Fraction(0)
                for j, nb in enumerate(nonbasic_vars):
                    if nb == nb_var:
                        coeff = basic_coeffs[i][j]
                        break
                item = QTableWidgetItem(str(coeff))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                simplex_table.setItem(i, col_idx, item)

            # Столбец b
            item = QTableWidgetItem(str(b_values[i]))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            simplex_table.setItem(i, len(nonbasic_with_coeff), item)

        # Заполняем строку F
        for col_idx, nb_var in enumerate(nonbasic_with_coeff):
            nb_num = int(nb_var[1:]) - 1
            coeff_in_table = F_row[nb_num]
            item = QTableWidgetItem(str(coeff_in_table))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            simplex_table.setItem(m, col_idx, item)

        # Правый нижний угол
        item = QTableWidgetItem(str(F_right))
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        simplex_table.setItem(m, len(nonbasic_with_coeff), item)

        # ========== 8. Отображаем таблицу ==========
        while self.simplex_iterations_layout.count():
            item = self.simplex_iterations_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.simplex_tables.clear()

        self.simplex_iterations_layout.addWidget(QLabel("<b>Итерация 0 (начальная симплекс-таблица)</b>"))
        self.simplex_iterations_layout.addWidget(simplex_table)
        self.simplex_tables.append(simplex_table)

        # Подключаем обработчик
        simplex_table.itemClicked.connect(self.simplex_on_cell_clicked)

        # Активируем кнопки
        self.simplex_btn_back.setEnabled(True)
        self.simplex_btn_select.setEnabled(True)
        self.simplex_btn_auto.setEnabled(True)

        # Сбрасываем выбор
        self.simplex_selected_row = -1
        self.simplex_selected_col = -1
        self.simplex_selected_table = None

        # Выводим информацию
        expr_str = f"F = {const}"
        for j in range(n):
            if coeffs[j] != 0:
                sign = "+" if coeffs[j] > 0 else ""
                expr_str += f" {sign}{coeffs[j]}*x{j + 1}"

        QMessageBox.information(self, "Симплекс-таблица построена", expr_str)

    def build_x0_tableGPT(self):
        """Построение симплекс-таблицы из последней таблицы искусственного метода"""

        if self.last_artificial_table is None:
            QMessageBox.warning(self, "Нет данных", "Сначала решите задачу искусственным методом")
            return

        # ========== 1. Забираем данные из последней таблицы ==========
        table = self.last_artificial_table
        rows = table.rowCount()
        cols = table.columnCount()

        # Заголовки
        h_labels = [table.horizontalHeaderItem(c).text() for c in range(cols)]
        v_labels = [table.verticalHeaderItem(r).text() for r in range(rows)]

        # Данные в виде дробей
        data = []
        for r in range(rows):
            row_data = []
            for c in range(cols):
                item = table.item(r, c)
                val = self.parse_fraction(item.text()) if item and item.text() else Fraction(0)
                row_data.append(val)
            data.append(row_data)

        # ========== 2. Выражаем базисные переменные из строк ограничений ==========
        # Базисные переменные - это заголовки строк (кроме последней строки F)
        basic_vars = v_labels[:-1]  # например ["x2", "x1"]
        m = len(basic_vars)  # количество ограничений

        # Для каждой базисной переменной запоминаем её выражение
        # Выражение храним как: (свободный_член, {переменная: коэффициент})
        basic_expr = {}

        for i in range(m):
            var_name = basic_vars[i]  # например "x2"
            b_val = data[i][cols - 1]  # свободный член

            # Собираем коэффициенты при переменных
            coeffs = {}
            for j in range(cols - 1):  # все столбцы кроме b
                var_in_col = h_labels[j]
                coeff = data[i][j]
                if coeff != 0:
                    # В выражении: var_name = b - coeff * var_in_col
                    coeffs[var_in_col] = -coeff

            basic_expr[var_name] = {"b": b_val, "coeffs": coeffs}
            print(f"{var_name} = {b_val}", end="")
            for v, c in coeffs.items():
                print(f" {c:+}*{v}", end="")
            print()

        # ========== 3. Начинаем с целевой функции ==========
        # F = c1*x1 + c2*x2 + ...
        F_const = Fraction(0)
        F_coeffs = {}

        for j in range(self.n_vars):
            var_name = f"x{j + 1}"
            coeff = self.c_coeffs[j]
            if coeff != 0:
                F_coeffs[var_name] = coeff

        print(f"\nНачальная F = {F_const}", end="")
        for v, c in F_coeffs.items():
            print(f" {c:+}*{v}", end="")
        print()

        # ========== 4. Подставляем базисные переменные ==========
        # Подставляем каждую базисную переменную, пока они есть в F
        changed = True
        while changed:
            changed = False
            for basic_var, expr in basic_expr.items():
                if basic_var in F_coeffs:
                    print(f"\nПодставляем {basic_var} = {expr['b']}", end="")
                    for v, c in expr['coeffs'].items():
                        print(f" {c:+}*{v}", end="")
                    print()

                    # Коэффициент при подставляемой переменной
                    coeff_to_sub = F_coeffs[basic_var]

                    # Добавляем вклад от b (свободного члена)
                    F_const += coeff_to_sub * expr['b']

                    # Добавляем вклад от коэффициентов
                    for var_in_expr, coeff_in_expr in expr['coeffs'].items():
                        if var_in_expr not in F_coeffs:
                            F_coeffs[var_in_expr] = Fraction(0)
                        F_coeffs[var_in_expr] += coeff_to_sub * coeff_in_expr

                    # Удаляем подставленную переменную
                    del F_coeffs[basic_var]
                    changed = True
                    break  # начинаем заново, так как словарь изменился

        # ========== 5. Выводим результат ==========
        print(f"\nИтоговая F = {F_const}", end="")
        for var, coeff in sorted(F_coeffs.items()):
            if coeff != 0:
                print(f" {coeff:+}*{var}", end="")
        print()

        # ========== 6. Создаём симплекс-таблицу ==========
        # Небазисные переменные - это те, что остались в F_coeffs
        nonbasic_vars = list(F_coeffs.keys())
        n_nonbasic = len(nonbasic_vars)

        # Создаём таблицу
        simplex_table = QTableWidget()
        simplex_table.setRowCount(m + 1)  # строки ограничений + строка F
        simplex_table.setColumnCount(n_nonbasic + 1)  # небазисные переменные + b

        # Заголовки столбцов
        col_labels = nonbasic_vars + ["b"]
        simplex_table.setHorizontalHeaderLabels(col_labels)

        # Заголовки строк
        row_labels = basic_vars + ["F"]
        simplex_table.setVerticalHeaderLabels(row_labels)

        # Заполняем строки ограничений
        for i in range(m):
            basic_var = basic_vars[i]
            expr = basic_expr[basic_var]

            # Заполняем коэффициенты при небазисных переменных
            for j, nb_var in enumerate(nonbasic_vars):
                coeff = expr['coeffs'].get(nb_var, Fraction(0))
                item = QTableWidgetItem(str(coeff))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                simplex_table.setItem(i, j, item)

            # Заполняем столбец b
            item = QTableWidgetItem(str(expr['b']))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            simplex_table.setItem(i, n_nonbasic, item)

        # Заполняем строку F
        for j, nb_var in enumerate(nonbasic_vars):
            # В симплекс-таблице коэффициент с противоположным знаком
            coeff_in_table = -F_coeffs[nb_var]
            item = QTableWidgetItem(str(coeff_in_table))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            simplex_table.setItem(m, j, item)

        # Правый нижний угол
        right_value = -F_const
        item = QTableWidgetItem(str(right_value))
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        simplex_table.setItem(m, n_nonbasic, right_value)

        # ========== 7. Отображаем таблицу ==========
        # Очищаем старые таблицы
        while self.simplex_iterations_layout.count():
            item = self.simplex_iterations_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.simplex_tables.clear()

        # Добавляем новую таблицу
        self.simplex_iterations_layout.addWidget(QLabel("<b>Итерация 0 (начальная симплекс-таблица)</b>"))
        self.simplex_iterations_layout.addWidget(simplex_table)
        self.simplex_tables.append(simplex_table)

        # Подключаем обработчик клика
        simplex_table.itemClicked.connect(self.simplex_on_cell_clicked)

        # Активируем кнопки
        self.simplex_btn_back.setEnabled(True)
        self.simplex_btn_select.setEnabled(True)
        self.simplex_btn_auto.setEnabled(True)

        # Сбрасываем выбор
        self.simplex_selected_row = -1
        self.simplex_selected_col = -1
        self.simplex_selected_table = None

        QMessageBox.information(self, "Готово", "Начальная симплекс-таблица построена!")

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