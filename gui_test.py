import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QComboBox

class SettingsForm(QWidget):
    def __init__(self):
        super().__init__()

        # Set the window title to "Settings"
        self.setWindowTitle("Settings")

        # Create the main layout
        layout = QVBoxLayout()

        # ID input (with default text)
        id_layout = QHBoxLayout()
        id_label = QLabel("ID:")
        self.id_entry = QLineEdit("Participant1 (stick to this format)")  # Default text "Participant1"
        id_layout.addWidget(id_label)
        id_layout.addWidget(self.id_entry)

        # Electrode input (with default text)
        electrode_layout = QHBoxLayout()
        electrode_label = QLabel("Electrode:")
        self.electrode_entry = QLineEdit("Skaaltec")  # Default text "Skaaltec"
        electrode_layout.addWidget(electrode_label)
        electrode_layout.addWidget(self.electrode_entry)

        # Stim_port input (with default text)
        stim_port_layout = QHBoxLayout()
        stim_port_label = QLabel("Stim port:")
        self.stim_port_entry = QLineEdit("COM3")  # Default text "COM3"
        stim_port_layout.addWidget(stim_port_label)
        stim_port_layout.addWidget(self.stim_port_entry)

        # Sham_port input (with default text)
        sham_port_layout = QHBoxLayout()
        sham_port_label = QLabel("Sham port:")
        self.sham_port_entry = QLineEdit("COM10")
        sham_port_layout.addWidget(sham_port_label)
        sham_port_layout.addWidget(self.sham_port_entry)

        # Trigger_port input (with default text)
        trigger_port_layout = QHBoxLayout()
        trigger_port_label = QLabel("Trigger port:")
        self.trigger_port_entry = QLineEdit("COM8")  # Default text "COM8"
        trigger_port_layout.addWidget(trigger_port_label)
        trigger_port_layout.addWidget(self.trigger_port_entry)

        # Submit button
        submit_button = QPushButton("Submit")
        submit_button.clicked.connect(self.on_submit)

        # Add all layouts to the main layout
        layout.addLayout(id_layout)
        layout.addLayout(electrode_layout)
        layout.addLayout(stim_port_layout)
        layout.addLayout(sham_port_layout)
        layout.addLayout(trigger_port_layout)
        layout.addWidget(submit_button)

        # Set the layout for the QWidget
        self.setLayout(layout)

    def on_submit(self):
        # Get values from input fields
        self.participant_id = self.id_entry.text()
        self.electrode = self.electrode_entry.text()
        self.stim_port = self.stim_port_entry.text()
        self.sham_port = self.sham_port_entry.text()
        self.trigger_port = self.trigger_port_entry.text()

        self.close()

# Create the application and the main window
# app = QApplication(sys.argv)
# window = SettingsForm()
# window.show()

# # Run the application's event loop
# app.exec_()

class SessionSettings(QWidget):
    def __init__(self):
        super().__init__()

        # Set the window title to "Kinearm"
        self.setWindowTitle("Kinearm")

        # Create the main layout
        layout = QVBoxLayout()


        # Participant input (with default text "1")
        participant_layout = QHBoxLayout()
        participant_label = QLabel("Participant:")
        self.participant_entry = QLineEdit("1")  # Default text "1"
        self.participant_entry.setReadOnly(True)
        participant_layout.addWidget(participant_label)
        participant_layout.addWidget(self.participant_entry)

        # Experiment input (with default options "Kinarm, other")
        experiment_layout = QHBoxLayout()
        experiment_label = QLabel("Experiment:")
        self.experiment_entry = QLineEdit("Kinarm")  # Default text "Kinarm, other"
        experiment_layout.addWidget(experiment_label)
        experiment_layout.addWidget(self.experiment_entry)

        # Session selection (with default sessions as dropdown options)
        session_layout = QHBoxLayout()
        session_label = QLabel("Session:")
        self.session_combo = QComboBox()
        session_list = [
            "test", "000", "001", "002", "003", "004", "005", "006", "007", "008", 
            "009", "010", "011", "012", "013", "014", "015"
        ]
        self.session_combo.addItems(session_list)  # Populate dropdown with session options
        session_layout.addWidget(session_label)
        session_layout.addWidget(self.session_combo)

        # Submit button
        submit_button = QPushButton("Submit")
        submit_button.clicked.connect(self.on_submit)

        # Add all layouts to the main layout
        layout.addLayout(participant_layout)
        layout.addLayout(experiment_layout)
        layout.addLayout(session_layout)
        layout.addWidget(submit_button)

        # Set the layout for the QWidget
        self.setLayout(layout)

    def on_submit(self):
        # Get values from input fields
        self.participant = self.participant_entry.text()
        self.experiment = self.experiment_entry.text()
        self.session = self.session_combo.currentText()

        self.close()

# # Create the application and the main window
# app = QApplication(sys.argv)
# window = SessionSettings()
# window.show()
# window.participant_entry.setText("2")
# # Run the application's event loop and wait for the window to close
# app.exec_()