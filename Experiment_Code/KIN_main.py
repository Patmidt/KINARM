from exam_load import ExamLoad
from time import perf_counter
import os
import pandas as pd
import numpy as np
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from file_selector_GUI import get_file_info

# Get file names from GUI
input_file, output_file_name = get_file_info()

# Check if user provided values
if input_file and output_file_name:
    print(f"Selected Input File: {input_file}")
    print(f"Entered Output File Name: {output_file_name}")
else:
    print("No valid input received.")

# Define the directory and file path
file_directory = '/Volumes/green_groups_re_public/SHARED STUDENTS/SmartVNS/Motor_Learning/Kinarm/Experiment_Code' # os.path.abspath(os.path.dirname(__file__))  # Directory of the script
file_path = os.path.abspath(os.path.join(file_directory, os.path.pardir, "Data", "Preprocessed_Data"))  # Modify as needed


# Ensure the directory exists
os.makedirs(file_path, exist_ok=True)

# Automatically append '.csv' if the output file name doesn't have it
if not output_file_name.endswith('.csv'):
    output_file_name += '.csv'

full_file_path = os.path.join(file_path, output_file_name)


if os.path.exists(full_file_path):
    print(f'File {output_file_name} already exists in this folder!')
    sys.exit()

# if there is no matching entry create one
else:

    if __name__ == "__main__":
        s = perf_counter()
        
        # Load the exam data from the ZIP file
        exam = ExamLoad(input_file)

        trial_success = {}
        trial_feedback = {}
        right_hand_position = {}
        left_hand_position = {}
        hvx = {}
        hvy= {}
        
        for trial, trial_object in exam.trials.items():
            # if trial.startswith('01_01_'): # files of session x start with 0x_01_01
            try:
                trial_number = int(trial.split('_')[-1])
            except ValueError:
                continue

            ## Check if trial was a success ##

            success = 0
            feedback = 'empty'
            for index, event in enumerate(exam.trials[trial].events):
                if event.label == 'ON_TGT':
                    success = 1
                    feedback = 'hit'
                    break
                elif event.label == 'TOO_FAST':
                    success = 1
                    feedback = 'too fast'
                elif event.label == 'TOO_SLOW':
                    success = 1
                    feedback = 'too slow'
                elif event.label == 'MISS_TGT':
                    success = 0
                    feedback = 'miss'
                elif event.label == 'STUCK':
                    success = 0
                    feedback = 'incomplete'
                # else:
                #     print(f'Unknown Event in index: {index}')
            trial_success[trial_number] = success
            trial_feedback[trial_number] = feedback

            ## Read handpositions for left and right hand and store them in an array
            right_hand_position[trial_number] = exam.trials[trial].positions['Right_Hand'].values
            left_hand_position[trial_number] = exam.trials[trial].positions['Left_Hand'].values

            ## Read HVX and HVY and store them

            hvx[trial_number] = exam.trials[trial].kinematics['HVX'].values
            hvy[trial_number] = exam.trials[trial].kinematics['HVY'].values

        ## Sort the data numerically after the trial number
        sorted_trial_success = sorted(trial_success.items(), key=lambda x: x[0])
        sorted_trial_feedback = sorted(trial_feedback.items(), key=lambda x: x[0])
        sorted_left_hand_position = sorted(left_hand_position.items(), key=lambda x: x[0])
        sorted_right_hand_position = sorted(right_hand_position.items(), key=lambda x: x[0])
        sorted_hvx = sorted(hvx.items(), key=lambda x: x[0])
        sorted_hvy = sorted(hvy.items(), key=lambda x: x[0])

    ### safe all in a single .csv file ###
    #------------------------------------#

    # Extract only the values from the sorted lists
    trial_numbers = [x[0] for x in sorted_trial_success]
    feedback_values = [x[1] for x in sorted_trial_feedback]
    success_values = [x[1] for x in sorted_trial_success]
    left_hand_values = [x[1] for x in sorted_left_hand_position]
    right_hand_values = [x[1] for x in sorted_right_hand_position]
    hvx_values = [x[1] for x in sorted_hvx]
    hvy_values = [x[1] for x in sorted_hvy]

    # Create DataFrame
    df = pd.DataFrame({
        "Trial": trial_numbers,
        "Feedback": feedback_values,
        "Success": success_values,
        "Left_Hand_Position": left_hand_values,
        "Right_Hand_Position": right_hand_values,
        "Hand_Velocity_X": hvx_values,
        "Hand_Velocity_Y": hvy_values
    })

    # Save to CSV
    df.to_csv(full_file_path, index=False) # ATTENTION: switch back to file_path
    print(f"CSV file '{output_file_name}' successfully created at: {file_path}")