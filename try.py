from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QMainWindow, QLabel, QLineEdit, QVBoxLayout, QAction, \
    QMenu
from PyQt5.QtCore import QSize, Qt

import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("My App")
        button = QPushButton("Print 5 vars!")
        button.setCheckable(True)
        button.clicked.connect(self.the_button_was_clicked)

        self.setMinimumSize(QSize(500, 300))

        self.label = QLabel()

        self.input = QLineEdit()
        self.input.textChanged.connect(self.label.setText)

        layout = QVBoxLayout()
        layout.addWidget(self.input)
        layout.addWidget(self.label)

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_menu)

    def contextMenuEvent(self, e):
        context = QMenu(self)
        context.addAction(QAction("test 1", self))
        context.addAction(QAction("test 2", self))
        context.addAction(QAction("test 3", self))
        context.exec(e.globalPos())

    def the_button_was_clicked(self):
        for i in range(5):
            print("x" + str(i))
        self.button.setText("You already clicked me.")


myapp = QApplication(sys.argv)

window = MainWindow()
window.show()


myapp.exec()