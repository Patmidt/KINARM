import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QFileDialog

class FileSelector(QWidget):
    def __init__(self):
        super().__init__()
        self.input_file_path = None
        self.output_file_name = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Input file selection
        self.input_label = QLabel('Select Input File:')
        layout.addWidget(self.input_label)
        self.input_line = QLineEdit(self)
        layout.addWidget(self.input_line)
        self.input_button = QPushButton('Browse', self)
        self.input_button.clicked.connect(self.select_input_file)
        layout.addWidget(self.input_button)

        # Output file name
        self.output_label = QLabel('Enter Output File Name:')
        layout.addWidget(self.output_label)
        self.output_line = QLineEdit(self)
        layout.addWidget(self.output_line)

        # Confirm button
        self.confirm_button = QPushButton('Confirm', self)
        self.confirm_button.clicked.connect(self.confirm_selection)
        layout.addWidget(self.confirm_button)

        self.setLayout(layout)
        self.setWindowTitle('File Selector')
        self.resize(400, 200)

    def select_input_file(self):
        initial_folder = '/Volumes/green_groups_re_public/SHARED STUDENTS/SmartVNS/Motor_Learning/Kinarm/Data/KIN_DATA'
        file_name, _ = QFileDialog.getOpenFileName(self, 'Select Input File', initial_folder, 'All Files (*);;Text Files (*.txt)')
        if file_name:
            self.input_file_path = file_name
            self.input_line.setText(file_name)

    def confirm_selection(self):
        self.output_file_name = self.output_line.text().strip()
        if not self.input_file_path or not self.output_file_name:
            print("Please select an input file and enter an output file name.")
        else:
            self.close()

def get_file_info():
    app = QApplication(sys.argv)
    window = FileSelector()
    window.show()
    app.exec_()  # Start GUI event loop

    return window.input_file_path, window.output_file_name
