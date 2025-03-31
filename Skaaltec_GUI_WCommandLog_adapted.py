import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QTextEdit,
    QLineEdit,
    QComboBox,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
)
from PyQt5.QtCore import QTimer, pyqtSignal, QObject, QThread
import os
import pandas as pd
import numpy as np
import time
import re
from stimulator_commands import *
import logging
from collections import deque
import PySimpleGUI as sg

comport = "/dev/tty.usbserial-1140" #before /dev/tty.usbserial-2110
# Create a logger
logger = logging.getLogger(__name__)

# Set the level of logging. DEBUG is the lowest level. 
# Higher levels are INFO, WARNING, ERROR and CRITICAL.
logger.setLevel(logging.DEBUG)

# Create a file handler for outputting log messages to a file
handler = logging.FileHandler('log.txt')

# Create a formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(handler)

class Stream(QObject):
    newText = pyqtSignal(str)

    def write(self, text):
        self.newText.emit(str(text))


class AppDemo(QWidget):
    def __init__(self):
        self.current_dir = os.path.dirname(os.path.realpath(__file__))

        self.stimulation = False
        self.start_stop_button_shown = False
        self.started_first_calibration = False
        self.stimulation_state = False
        self.condition_names = []
        self.ids_subject = []
        self.pulsewidths = []
        self.frequencies = []
        self.amplitudes_left = []
        self.amplitudes_right = []
        self.stim_on_times = []
        self.stim_off_times = []
        self.impedance_value_left = []
        self.impedance_value_right = []

        self.intensity = 100
        self.intensity_percent = (100 / 3000) * 100
        self.interval = 100
        self.impedance_left = 0.0
        self.impedance_right = 0.0
        self.message = []
        self.confirmMessage = False
        self.counter = 0
        self.message_counter =0
        
        self.message_buffer = deque(maxlen=2)
        
        self.newMessage = False
        df = pd.read_csv(
            os.path.join(
                self.current_dir, "stimulation_config", "StimulationConditions.csv"
            )
        )
        self.conditions = list(df["Condition"])
        self.pulse_widths = list(df["Pulsewidth"])
        self.freqs = list(df["Frequency"])
        super().__init__()
        self.initUI()

        self.update_datetime()

        commandList = []
        commandList.append([MSGTYPES.MSG_BURSTINTERVAL, 60000])  # not implemented error
        commandList.append([MSGTYPES.MSG_NUMBURSTS, 3])  # not implemented error
        commandList.append([MSGTYPES.MSG_REPORTINTERVAL, 500])  # 500 ms

        # now send the command:
        counter = 0
        for msg in commandList:
            deviceConnection.send(msgFactory.encrypt_message(msg[0], msg[1]))
            time.sleep(0.05)
            counter += 1

        self.start_measure = True
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(20)  # update every 5ms

    def initUI(self):
        left_layout = QVBoxLayout()

        self.id_label = QLabel("ID:")
        left_layout.addWidget(self.id_label)

        self.id_entry = QLineEdit()
        left_layout.addWidget(self.id_entry)

        self.avns_or_sham_dropdown = QComboBox()
        self.avns_or_sham_dropdown.addItems(["AVNS", "Sham"])
        left_layout.addWidget(self.avns_or_sham_dropdown)  
        
        self.frequency_label = QLabel("Frequency [Hz]:")
        left_layout.addWidget(self.frequency_label)

        self.frequency_dropdown = QComboBox()
        self.frequency_dropdown.addItems(["1", "5", "25", "50", "100"])
        left_layout.addWidget(self.frequency_dropdown)

        self.pulsewidth_label = QLabel("Pulsewidth [us]:")
        left_layout.addWidget(self.pulsewidth_label)

        self.pulsewidth_dropdown = QComboBox()
        self.pulsewidth_dropdown.addItems(["100", "250", "500"])
        left_layout.addWidget(self.pulsewidth_dropdown)

        self.stimulation_on_time_label = QLabel("Stimulation ON time:")
        left_layout.addWidget(self.stimulation_on_time_label)

        self.stimulation_on_time_dropdown = QComboBox()
        self.stimulation_on_time_dropdown.addItems(["5", "10", "15", "60"])
        left_layout.addWidget(self.stimulation_on_time_dropdown)

        self.stimulation_off_time_label = QLabel("Stimulation OFF time:")
        left_layout.addWidget(self.stimulation_off_time_label)

        self.stimulation_off_time_dropdown = QComboBox()
        self.stimulation_off_time_dropdown.addItems(["1", "2", "3", "4", "5"])
        left_layout.addWidget(self.stimulation_off_time_dropdown)
        left_layout.addStretch(1)

        middle_layout = QVBoxLayout()

        self.intensity_label = QLabel("Amplitude: 0% (1. 25%-50% / 2. 60%-90%)")
        self.intensity_label.show()
        middle_layout.addWidget(self.intensity_label)

        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start)
        middle_layout.addWidget(self.start_button)

        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.pause)
        middle_layout.addWidget(self.pause_button)
        self.pause_button.setEnabled(False)

        self.up_button = QPushButton("Up")
        self.up_button.clicked.connect(self.increase_intensity)
        self.up_button.show()
        middle_layout.addWidget(self.up_button)

        self.down_button = QPushButton("Down")
        self.down_button.clicked.connect(self.decrease_intensity)
        self.down_button.show()
        middle_layout.addWidget(self.down_button)

        self.save_button = QPushButton("Stop/Save")
        self.save_button.clicked.connect(self.save_calibration)
        self.save_button.show()
        self.save_button.setDisabled(True)

        middle_layout.addWidget(self.save_button)
        self.stream = Stream(newText=self.onUpdateText)
        sys.stdout = self.stream
        self._console = QTextEdit(self)
        self._console.setReadOnly(True)
        middle_layout.addWidget(self._console)

        layout_right = QVBoxLayout()
        # Create a QTableWidget widget
        self.table = QTableWidget(0, 4)  # rows, columns
        self.table.setHorizontalHeaderLabels(
            ["Index", "Frequency [Hz]", "Pulsewidth [us]", "Amplitude [uA]"]
        )
        self.table.show()
        layout_right.addWidget(self.table)

        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.export_calibration)
        self.export_button.show()
        layout_right.addWidget(self.export_button)
        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.close)
        layout_right.addWidget(self.exit_button)

        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(middle_layout, 2)
        main_layout.addLayout(layout_right, 2)
        self.setLayout(main_layout)

    # Print in console
    def onUpdateText(self, text):
        cursor = self._console.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(text + "\n")
        self._console.setTextCursor(cursor)
        self._console.ensureCursorVisible()

    def update_datetime(self):
        self.current_datetime = time.strftime("%Y%m%d%H%M%S")
        # self.datetime_label.config(text=current_datetime)

    def send_receive(self, message):
        # send the message out
        a = 1

    # _______________________________________________________________________________________________________________________________
    # This is the update loop. It is called every 5ms.
    # The update loop will check if there is a new message. If there is a new message, it will send it out and wait for a confirmation.
    # If there is no new message, it will read the stimulator.

    def update(self):
        if self.start_measure:
            if self.newMessage:
                # if the the size of self.message is 1dimensional, it is a single message
                for mes in self.message:
                    self.onUpdateText(str(mes))
                    logging.info(str(mes))
                    deviceConnection.send(msgFactory.encrypt_message(mes[0], mes[1]))
                    start = time.time()
                    while True:
                        if time.time() - start > 0.5:
                            break
                    while True:
                        result = deviceConnection.read()
                        
                        if result != -1:
                            res = msgFactory.decrypt_message(result)
                            self.message_counter += 1
                            logger.info(res)
                            self.onUpdateText(str(res))
                            self.message_buffer.append(res)
                            if res["msgType"] == MSGTYPES.MSG_ACK:
                                if (
                                    res["msgType"].value == 81
                                    and res["msgValue"] == mes[0].value
                                ):
                                    self.counter += 1
                                    self.onUpdateText("ACK")
                                    break

                                elif res["msgType"].value == 80:
                                    self.onUpdateText("ERROR")
                                    logger.info("ERROR")
                                    deviceConnection.send(
                                        msgFactory.encrypt_message(
                                            MSGTYPES.MSG_STIM_STOP, int(0)
                                        )
                                    )

                                    break
                            # print(str(msgFactory.decrypt_message(result)))
                            result = -1

                self.newMessage = False
                self.message = []

            # read stimulator
            result = deviceConnection.read()
            if result != -1:
                
                self.message_counter += 1
                self.onUpdateText(str(msgFactory.decrypt_message(result)))
                res = msgFactory.decrypt_message(result)
                logger.info(res)
                self.message_buffer.append(res)
                
                if res["msgType"] == MSGTYPES.MSG_IMPEDANCEMEASUREMENT:
                    self.impedance_left = res["msgValue"]
                    self.impedance_right = 0.0
                if self.message_counter>3:
                    
                    if self.message_buffer[0]["msgType"] == MSGTYPES.MSG_IMPEDANCEMEASUREMENT  and self.message_buffer[-1]["msgType"] == MSGTYPES.MSG_STIM_STATE and self.message_buffer[-1]["msgValue"] == 3:
                        print("Stimulation state updating")
                        # will update the stimulation state if the 3rd to last message is impedance measurement and the last two messages are stim state 3 and 4
                        logger.info("Stimulation state updated")
                        self.update_stimulation()
                # print(str(msgFactory.decrypt_message(result)))
                result = -1
                
    def update_stimulation(self):
        # call this when the stimulation is ended and rest for the stimulation off time then restart
        self.stimulation_state = False
        time_start = time.time()
        while True:
            if time.time() - time_start > int(self.stimulation_off_time_dropdown.currentText()):
                break
        self.message.append([MSGTYPES.MSG_STIM_APPLY, 0])
        self.newMessage = True
        
    def pause(self):
        # stop stimulation
        self.message = []
        self.message.append([MSGTYPES.MSG_STIM_STOP, 0])
        self.newMessage = True
        self.start_button.setEnabled(True)
        self.start_button.setText("Start")
        self.stimulation_state = False

    def increase_intensity(self):
        self.stimulation_state = False
        if self.intensity + self.interval <= 5000:
            self.intensity += self.interval
            self.intensity_percent = (self.intensity / 3000) * 100
        else:
            self.intensity = 5000
        self.intensity_label.setText(f"Amplitude: {self.intensity_percent} %")
        self.message = []

        self.message.append([MSGTYPES.MSG_STIMULATIONTIME, int(int(self.stimulation_on_time_dropdown.currentText())*1000)])
        self.message.append([MSGTYPES.MSG_FORWARDAMPLITUDE, int(self.intensity)])
        self.message.append([MSGTYPES.MSG_STIM_APPLY, 0])
        self.newMessage = True

    def decrease_intensity(self):
        self.stimulation_state = False
        if self.intensity - self.interval >= 100:
            self.intensity -= self.interval
            self.intensity_percent = (self.intensity / 3000) * 100
        else:
            self.intensity = 100
        self.intensity_label.setText(f"Amplitude: {self.intensity_percent} %")

        self.message = []

        self.message.append([MSGTYPES.MSG_STIMULATIONTIME,int(int(self.stimulation_on_time_dropdown.currentText())*1000)])
        self.message.append([MSGTYPES.MSG_FORWARDAMPLITUDE, int(self.intensity)])
        self.message.append([MSGTYPES.MSG_STIM_APPLY, 0])
        self.newMessage = True

    def update_table(self):
        self.table.setRowCount(0)  # Clear existing data from the table
        self.index = [i for i in range(1, len(self.pulsewidths) + 1)]
        # Insert new data into the table
        for i in range(len(self.pulsewidths)):
            self.table.insertRow(self.table.rowCount())
            self.table.setItem(i, 0, QTableWidgetItem(str(self.index[i])))
            self.table.setItem(i, 1, QTableWidgetItem(str(self.frequencies[i])))
            self.table.setItem(i, 2, QTableWidgetItem(str(self.pulsewidths[i])))
            self.table.setItem(i, 3, QTableWidgetItem(str(self.amplitudes_left[i])))

    def save_calibration(self):
        self.message = []
        self.message.append([MSGTYPES.MSG_STIM_STOP, 0])
        self.newMessage = True
        self.id_entry.setDisabled(True)
        self.save_button.setText("Saved")
        self.save_button.setDisabled(True)

        id_subject = str(self.id_entry.text())
        pulsewidth = int(self.pulsewidth_dropdown.currentText())
        frequency = int(self.frequency_dropdown.currentText())
        amplitude_left = self.intensity
        amplitude_right = 0
        stim_on_time = int(self.stimulation_on_time_dropdown.currentText())
        stim_off_time = int(self.stimulation_off_time_dropdown.currentText())

        condition_exists = False
        for condition, pw, freq in zip(self.conditions, self.pulse_widths, self.freqs):
            if pulsewidth == pw and frequency == freq:
                self.condition_names.append(condition)
                condition_exists = True

        if condition_exists == False:
            last_condition = str(self.conditions[(len(self.conditions) - 1)])
            match = re.search(r"\d+", last_condition)
            if match:
                condition_number = int(match.group())

            self.condition_names.append(f"Condition{condition_number + 1}")
            self.conditions.append(f"Condition{condition_number + 1}")
            self.pulse_widths.append(pulsewidth)
            self.freqs.append(frequency)

            dt = {
                "Condition": self.conditions,
                "Pulsewidth": self.pulse_widths,
                "Frequency": self.freqs,
            }
            df = pd.DataFrame(dt)
            df.to_csv(
                os.path.join(
                    self.current_dir, "stimulation_config", "StimulationConditions.csv"
                ),
                index=False,
            )

        self.ids_subject.append(id_subject)
        self.pulsewidths.append(pulsewidth)
        self.frequencies.append(frequency)
        self.amplitudes_left.append(amplitude_left)
        self.amplitudes_right.append(amplitude_right)
        self.stim_on_times.append(stim_on_time)
        self.stim_off_times.append(stim_off_time)
        self.impedance_value_left.append(self.impedance_left)
        self.impedance_value_right.append(self.impedance_right)

        self.update_table()
        self.start_button.setEnabled(True)
        self.start_button.setText("Start")
        self.intensity = 100
        self.intensity_percent = (100 / 3000) * 100
        self.intensity_label.setText(f"Amplitude: {self.intensity_percent} %")





    def export_calibration(self):
        id_subject = str(self.id_entry.text())
        datetime = self.current_datetime
        sham = str(self.avns_or_sham_dropdown.currentText())

        dt = {
            "Condition_Name": self.condition_names,
            "ID": self.ids_subject,
            "Pulsewidth [us]": self.pulsewidths,
            "Frequency [Hz]": self.frequencies,
            "stim_on_time": self.stim_on_times,
            "stim_off_time": self.stim_off_times,
            "Amplitude_Left [uA]": self.amplitudes_left,
            "Amplitude_Right [uA]": self.amplitudes_right,
            "Impedance_Left [kOhm]": self.impedance_value_left,
            "Impedance_Right [kOhm]": self.impedance_value_right,
        }
        df = pd.DataFrame(dt)
        df.to_csv(
            os.path.join(
                self.current_dir,
                "stimulation_config", f"StimulationConfiguration_{sham}_ID{id_subject}_Date{datetime}.csv",
            ),
            index=False,
        )

    def start(self):
        # Implement your start logic here.

        freq = 1000000 // int(self.frequency_dropdown.currentText())
        pulsewidth = int(self.pulsewidth_dropdown.currentText())
        self.start_button.setText("Started")
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.save_button.setEnabled(True)

        if not self.started_first_calibration:
            self.started_first_calibration = True
            self.start_measure = True

        else:
            self.save_button.setText("Stop/Save")
            self.save_button.setEnabled(True)
        self.message = []

        self.message.append([MSGTYPES.MSG_PULSEWIDTH, int(pulsewidth)])
        self.message.append([MSGTYPES.MSG_FORWARDAMPLITUDE, int(100)])
        self.message.append([MSGTYPES.MSG_PULSEINTERVAL, int(freq)])
        self.message.append([MSGTYPES.MSG_STIMULATIONTIME, int(int(self.stimulation_on_time_dropdown.currentText())*1000)])
        self.message.append([MSGTYPES.MSG_STIM_APPLY, 0])
        self.newMessage = True

        pass

    def closeEvent(self, event):
        self.start_measure = False
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Are you sure you want to exit the application?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            deviceConnection.send(
                msgFactory.encrypt_message(MSGTYPES.MSG_STIM_STOP, int(0))
            )
            deviceConnection.close()
            event.accept()
            sys.stdout = sys.__stdout__
            super().closeEvent(event)
        else:
            event.ignore()

        # deviceConnection.send(
        #     msgFactory.encrypt_message(MSGTYPES.MSG_STIM_STOP, 0))
        # deviceConnection.close()


if __name__ == "__main__":
    msgFactory = Message_Factory()

    # establish device connection
    ########################'/dev/tty.usbserial-2110',############################
    deviceConnection = Serial_Connection(
        sys.argv[1], msgFactory.MESSAGE_LENGTH
    )

    """ create stimulation pattern, list contains timestamp after start (s), msg type and value """

    # starttime to now when commands should be sent
    starttime = time.time()
    performedtime = 0

    app = QApplication(sys.argv)
    demo = AppDemo()
    demo.showMaximized()
    app.exec_()
