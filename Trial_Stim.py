# -*- coding: utf-8 -*-


from init_stimulator import (
    Serial_Connection1,
    Serial_Connection2,
    MSGTYPES,
    STIMULATION_STATE,
    STIMULATION_ERRORS,
    Message_Factory,
)

# import pyfirmata # version 1.1.0
import serial    # version 3.5
import pandas as pd # version 1.5.3
import numpy as np  # version 1.26.2
from time import localtime, strftime
import time
import glob
import os
import random
import logging  # version 0.5.1.2
logger = logging.getLogger(__name__)
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from gui_test import SettingsForm, SessionSettings
from Stim_type import group_assignment


# Create the application and the main window
app = QApplication(sys.argv)
window = SettingsForm()
window.show()

# Run the application's event loop
app.exec_()

window.stim_port_entry.setText("/dev/tty.usbserial-1410")
window.trigger_port_entry.setText("/dev/tty.usbmodem1201")
window.sham_port_entry.setText("/dev/tty.usbserial-1110") # TO DO

calibration_id = window.participant_id
electrode = window.electrode
stim_com = window.stim_port
sham_com = window.sham_port
trigger_com = window.trigger_port

print(calibration_id)
print(electrode)
print(stim_com)
print(sham_com)
print(trigger_com)

group_assignment(calibration_id)

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

# current date
date = time.strftime("%Y%m%d")

# get relevant data paths
file_directory = os.path.abspath(os.path.dirname(__file__)) # directory of this script
data_path = os.path.abspath(os.path.join(file_directory, os.path.pardir, "Data")) # path to data folder
raw_data_path = os.path.abspath(os.path.join(data_path, os.path.pardir, "Raw_Data")) # path to Raw_Data folder
print(f"Resolved file path: {raw_data_path}")
print(data_path)

# _____________________________ things to change ____________________________

baseline_duration = 3  # time before first stimulations
wait_duration = 2     # qqtime after the stimulation


# get path for calibration files

# all files within the stimulation_config folder
all_files = os.listdir(os.path.join(file_directory, 'stimulation_config'))

# get all files with todays date and right ID for Sham and aVNS
date = time.strftime("%Y%m%d")
calibration_sham_files = list(filter(lambda f: f.startswith(
            f"StimulationConfiguration_Sham_ID{calibration_id}_Date{date}"),
        all_files))
calibration_sham_file = calibration_sham_files[0]

calibration_avns_files = list(filter(lambda f: f.startswith(
            f"StimulationConfiguration_AVNS_ID{calibration_id}_Date{date}"),
        all_files))
calibration_avns_file = calibration_avns_files[0]


# used datetime
datetime = (
    [string for string in calibration_avns_file.split("_") if date in string][0]
    .replace(".csv", "")
    .replace("Date", ""))

#%% functions for later use
# _______________________________________________________________________


def close_all():
    '''
    Function to run when the experiment should be closed (usually when pressing q or esc)

    '''
    
    # wait 2s in case stimulation is happening
    end_time = time.time() + 2
    while time.time() < end_time:
        pass

    # close the connection to the sham and aVNS stimulator (including waiting time)
    deviceConnection1.close()
    end_time = time.time() + 2
    while time.time() < end_time:
        pass

    # this is for the sham controller important once sham is connected

    deviceConnection2.close()
    end_time = time.time() + 2
    while time.time() < end_time:
        pass
    
    # close the board used for triggers
    sys.exit()


def impedance_measure(sham_trial):
    '''
    Measures the impedance readout of the stimulator and returns it.
    Depending whether it is a sham or aVNS trial the other stimulator is used.

    '''
    imp = None
    # if it is not a sham trial the device is called "Device6" and the readout is done on the aVNS stimulator
    if not sham_trial:
        device_name = 'Device6'
        result = deviceConnection1.read()

    # IMPORTANT FOR SHAM

    # if it is a sham trial the device is called "Device3" and the readout is done on the Sham stimulator
    if sham_trial:
        device_name = 'Device3'
        result = deviceConnection2.read()
    
    if result != -1:
        res = msgFactory.decrypt_message(result)
        # the readout is sent to the logger
        logger.info(str(res)+device_name)
        # if the readout type is impedance the value is saved in imp which is returned afterwards
        if res["msgType"] == MSGTYPES.MSG_IMPEDANCEMEASUREMENT:
            imp = res["msgValue"]
        
    if imp != None:
        return imp


#%%

# ____________________________ get participant and session information ____________________
####### start second GUI to get informations about the recording session
# Create the application and the main window
app_2 = QApplication(sys.argv)
window_2 = SessionSettings()
window_2.show()
window_2.participant_entry.setText(calibration_id)
# Run the application's event loop and wait for the window to close
app_2.exec_()

id_subject = window_2.participant
exptype = window_2.experiment
session = window_2.session

print(id_subject)
print(exptype)
print(session)
# change the basline time and wait time in test trials to make it faster
if session == 'test':
    baseline_duration = 10
    wait_duration = 10

#_________ check for diary entry____________

# load the exp_diary excel file
diary = pd.read_excel(os.path.join(data_path, "exp_diary.xlsx"))
# check if there is an entry with matching datetime, ID and experiment
diary = diary.astype({"Date": str})
# if there is a matching entry, do nothing
if ((diary.ID == id_subject)
    & (diary.Experiment == exptype)
    & (diary.Date == date)).any():
    pass
# if there is no matching entry create one
else:
    temp = pd.DataFrame(np.reshape(np.array(
                [   len(diary) + 1,
                    id_subject,
                    session,
                    int(date),
                    exptype,
                    electrode,
                    None]),(1,7),), columns=diary.columns)
    diary = pd.concat([diary, temp], ignore_index=True)
    # save the new diary
    diary.to_excel(os.path.join(data_path, "exp_diary.xlsx"), index=False)
    
# create folder structure
new_raw_path = os.path.join(
    data_path,
    "Raw_Data",
    "Participant {id_subject}".format(id_subject=id_subject),
    "Session {session}".format(session=session))
# if path is not existing, create it and if it is existing -> error
if not os.path.exists(new_raw_path):
    os.makedirs(new_raw_path)
else:
    raise ValueError("Session folder already exists.")

# also make a folder "KINARM"
os.makedirs(os.path.join(new_raw_path, "KINARM"))

print 
#%%
#______________________ load the calibration files_________________

# get intensities from correct calibration file
print("AVNS:")
print(calibration_avns_file)

# load aVNS calibration file and extract the amplitude in first (and only) row
df_calibration_avns = pd.read_csv(os.path.join(file_directory, 'stimulation_config', f'{calibration_avns_file}'))
amplitude_avns = df_calibration_avns["Amplitude_Left [uA]"][0]

# save the aVNS calibration file for later analysis
write_calibration_avns_path = os.path.join(new_raw_path, "Calibration_avns.csv")
df_calibration_avns.to_csv(write_calibration_avns_path, index=False)


print("Sham:")
print(calibration_sham_file)

# load Sham calibration file and extract the amplitude in first (and only) row
df_calibration_sham = pd.read_csv(os.path.join(file_directory, 'stimulation_config', f'{calibration_sham_file}'))
amplitude_sham = df_calibration_sham["Amplitude_Left [uA]"][0]

# save the Sham calibration file
write_calibration_sham_path = os.path.join(new_raw_path, "Calibration_sham.csv")
df_calibration_sham.to_csv(write_calibration_sham_path, index=False)


#%%
# _____________________________________ initialize everything __________________________

# Set up the serial connection (make sure the correct port and baud rate are used)
ser = serial.Serial(trigger_com, 9600)  # Replace 'COM3' with your Arduino's port
sensorValue = 0

end_time = time.time() + 0.5
while time.time() < end_time:
    pass

# initialize stimulator

# inititialize message factory
msgFactory = Message_Factory()

# establish device connection
deviceConnection1 = Serial_Connection1()
deviceConnection1.serialPort = stim_com
deviceConnection1.MESSAGE_LENGTH = msgFactory.MESSAGE_LENGTH
deviceConnection1.serialDevice = serial.Serial(
    port=deviceConnection1.serialPort,
    baudrate=115200,
    bytesize=8,
    timeout=2,
    stopbits=serial.STOPBITS_ONE,
)

deviceConnection2 = Serial_Connection2()
deviceConnection2.serialPort = sham_com
deviceConnection2.MESSAGE_LENGTH = msgFactory.MESSAGE_LENGTH
deviceConnection2.serialDevice = serial.Serial(
    port=deviceConnection2.serialPort,
    baudrate=115200,
    bytesize=8,
    timeout=2,
    stopbits=serial.STOPBITS_ONE,
)

""" create stimulation pattern, list contains timestamp after start (s), msg type and value """
commandList = []  # command dictionary, time stamp and command to execute

# setup pulse pattern with all commands available

commandList.append([0.0, MSGTYPES.MSG_BURSTINTERVAL, 60000])  # not implemented error
commandList.append([0.1, MSGTYPES.MSG_NUMBURSTS, 3])  # not implemented error

commandList.append([0.2, MSGTYPES.MSG_REPORTINTERVAL, 500])  # 500 ms

commandList.append([0.3, MSGTYPES.MSG_PULSEWIDTH, 250])  # pulse width in us
commandList.append([0.4, MSGTYPES.MSG_FORWARDAMPLITUDE, int(amplitude_avns)])  # pulse amplitude in uA

commandList.append([0.45, MSGTYPES.MSG_PULSEINTERVAL, 40000]) # pulse width interval in us, 1000000us/desired frequenccy
commandList.append([0.5, MSGTYPES.MSG_STIMULATIONTIME, 500])  # stimulation time in ms

# validate all commands by requesting settings from device
# commandList.append([1, MSGTYPES.MSG_REQUEST_SETTINGS, 0])

# apply pulses
commandList.append([2, MSGTYPES.MSG_STIM_APPLY, 0])

# give short stimulation at aVNS and Sham
# give all the commands above to the stimulator with a 1s gap between them
for msg in commandList:
    deviceConnection1.send(msgFactory.encrypt_message(msg[1], msg[2]))
    end_time = time.time() + 0.5
    while time.time() < end_time:
        pass

# wait before switching to the other stimulator
end_time = time.time() + 2
while time.time() < end_time:
    pass

# give all the commands above to the stimulator with a 1s gap between them
for msg in commandList:
    deviceConnection2.send(msgFactory.encrypt_message(msg[1], msg[2]))
    end_time = time.time() + 0.5
    while time.time() < end_time:
        pass
    
# wait 2s before moving on
end_time = time.time() + 2
while time.time() < end_time:
    pass



#%% preparation for the actual measurements

# REVISIT --> MAYBE ADD STIM VS SHAM FILE HERE

# Load existing Excel file
file_location = os.path.join(data_path, 'Stim_type.xlsx')
df = pd.read_excel(file_location, engine='openpyxl')

# Extract the row where the participant ID matches
participant_row = df.loc[df.iloc[:, 0] == id_subject]
    
# Check the third column value ("sham", "control", "reward", "stim")
stim_type = participant_row.iloc[0, 1]  # Assuming the third column is at index 1

# %% ####################### start of the actual experiment #########################

print("-------------------------")
print("EXPERIMENT START")
print("Quit anytime with q")
print("-------------------------")

# ________________ baseline routine ___________________________

# wait for as long as baseline_duration is (defined above)
continueRoutine = True
start_time = time.time()
# while continueRoutine and time.time() - start_time < baseline_duration:

    # end routine if q is pressed
    # if keyboard.is_pressed("q"):
    #   close_all()



# ___________________ start testing the conditions __________________

######### here, only one intensity is used for aVNS and Sham:
# setting the calibrated sham and aVNS intensities for both of the stimulators once
deviceConnection2.send(
    msgFactory.encrypt_message(
        MSGTYPES.MSG_FORWARDAMPLITUDE, int(amplitude_sham)))
end_time = time.time() + 0.5
while time.time() < end_time:
    pass

deviceConnection1.send(
    msgFactory.encrypt_message(
        MSGTYPES.MSG_FORWARDAMPLITUDE, int(amplitude_avns)))
end_time = time.time() + 0.5
while time.time() < end_time:
    pass

# current_cond = cond_file.iloc[0]
# print(current_cond)

# predefine variables used later
no_stim_trial = False
sham_trial = False
stim_flag = False

amplitude = None
imp_list = []
stim_length = 0
stim_frequency = 0

# define the boolian variables depending on the current condition
if stim_type == 'control':
    no_stim_trial = True
if stim_type == 'sham':
    sham_trial = True          

########################## What is stim_length? ##########################

# TO DO: stim_length = # get info from current calibration
# stim_frequency = df_calibration_avns["Amplitude_Left [uA]"][0] # get info from current calibration


#_____________ set the parameters for the stimulation_______________

# first in Sham trials
# if sham_trial and not no_stim_trial:
    
#     # changing stimulation frequency and stimulation time (+0.5s wait time)
#     deviceConnection2.send(msgFactory.encrypt_message(
#             MSGTYPES.MSG_PULSEINTERVAL, 40000))  # pulse width interval in us, 1000000us/desired frequenccy
#     end_time = time.time() + 0.5
#     while time.time() < end_time:
#         pass

#     deviceConnection2.send(msgFactory.encrypt_message(
#         MSGTYPES.MSG_STIMULATIONTIME, 500))  # stimulation length in ms
#     end_time = time.time() + 0.5
#     while time.time() < end_time:
#         pass

    ############# potentially ad the stimulation intensity change in here
    ######################################################################

# second in aVNS trials
# if not sham_trial and not no_stim_trial:
#     # changing stimulation frequency and stimulation time (+0.5s wait time)
#     deviceConnection1.send(
#         msgFactory.encrypt_message(
#             MSGTYPES.MSG_PULSEINTERVAL, 40000))  # pulse width interval in us, 1000000us/desired frequenccy
#     end_time = time.time() + 0.5
#     while time.time() < end_time:
#         pass


#     deviceConnection1.send(
#         msgFactory.encrypt_message(MSGTYPES.MSG_STIMULATIONTIME, 500))   # stimulation length in ms
#     end_time = time.time() + 0.5
#     while time.time() < end_time:
#         pass

kinarm_stimnulation_timings_path = os.path.join(new_raw_path, 'Stim_timings.xlsx')
if not os.path.exists(kinarm_stimnulation_timings_path):
    df = pd.DataFrame(columns=["Trial", "KINARM Input Time", "Stimulation Time", "Impedance"])
    df.to_excel(kinarm_stimnulation_timings_path, index=False, engine='openpyxl')

df = pd.read_excel(kinarm_stimnulation_timings_path, engine='openpyxl')

trial_number = 1

while True: 
##### Read the input from the arduino to trigger the VNS/Sham
    if ser.in_waiting > 0:  # Check if data is available from Arduino
        try:
            raw_data = ser.readline().decode('utf-8').strip()
            sensorValue = int(raw_data)
        except ValueError:
            sensorValue = 0
            print(f"Error: Cannot convert {repr(raw_data)} to integer.")

        if sensorValue == 0:
            stim_flag = False

        if not stim_flag and sensorValue > 0:
            stim_flag = True
            KINARM_time = time.time() # Time at which the TTL was received
            # stimulation application either Sham or aVNS and save the amplitude
            if not sham_trial and not no_stim_trial:
                amplitude = amplitude_avns
                deviceConnection1.send(
                    msgFactory.encrypt_message(MSGTYPES.MSG_STIM_APPLY, 0))
            if sham_trial and not no_stim_trial:
                amplitude = amplitude_sham
                deviceConnection2.send(
                    msgFactory.encrypt_message(MSGTYPES.MSG_STIM_APPLY, 0))
            stim_time = time.time()  # save the stimulation time (time when the stimulation started)

            # impedance measure as soon as the stimulation started (and here only in during trials)
            imp_value = impedance_measure(sham_trial)
            if imp_value != None:
                # append the new impedance to the list and mean it afterwards
                imp_list.append(imp_value)
            # it there were no impedance readout (not working or no_stim_trial), impedance = None
            if len(imp_list) == 0:
                impedance = None

            new_data = pd.DataFrame([[trial_number, KINARM_time, stim_time, imp_value]],
                                columns=["Trial", "KINARM Input Time", "Stimulation Time", "Impedance"])
            df = pd.concat([df, new_data], ignore_index=True)

            # **Save the updated file**
            df.to_excel(kinarm_stimnulation_timings_path, index=False, engine='openpyxl')

            trial_number += 1

            # TO DO:
            # add line to stimulation_info and save it
            # impedance = 1
            # temp1 = np.reshape(np.append(
            
            #     [stim_time, KINARM_time, amplitude, impedance]))
            # temp1 = pd.DataFrame(temp1, columns=stimulation_info.columns)
            # stimulation_info = pd.concat([stimulation_info, temp1], ignore_index=True)
            # # stimulation_info = stimulation_info.append(pd.Series(temp1[0], index=stimulation_info.columns), ignore_index=True)
            
            # # save the new line to the stimulation_info
            # stimulation_info.to_csv(stimulation_info_path, index=False)
            # print("condition SAVED")

        # ___________________________________ wait routine ___________________