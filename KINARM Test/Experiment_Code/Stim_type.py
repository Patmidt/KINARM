import random
import pandas as pd
import os
import sys  # Import sys module to exit the script

def group_assignment(participant_to_update):
    # Load existing Excel file
    file_directory = os.path.abspath(os.path.dirname(__file__)) # directory of this script
    file_path = os.path.abspath(os.path.join(file_directory, os.path.pardir, 'Data')) # path to data folder
    file_location = os.path.join(file_path, 'Stim_type.xlsx')
    df = pd.read_excel(file_location, engine='openpyxl')

    # Specify participant ID to update
    # participant_to_update = "P009"  # Change this value to select a specific participant
    group_dict = {'paired': 1, 'reward': 2, 'sham': 3, 'control': 4}
    # Check if the participant exists in the file
    if participant_to_update in df.iloc[:, 0].values:

        # Extract the row where the participant ID matches
        participant_row = df.loc[df.iloc[:, 0] == participant_to_update]
        
        # Check the third column value ("sham", "control", "reward", "paired")
        third_column_value = participant_row.iloc[0, 1]  # Assuming the third column is at index 1
        
        if third_column_value in ['sham', 'paired', 'reward', 'control']:
            group = group_dict[third_column_value]
            print(f"Participant {participant_to_update} is already assigned to group {group}.")
            # if third_column_value == 'paired':
            #     group = '1'
            #     print(f"Participant {participant_to_update} is assigned to group {group}")
            # elif third_column_value == 'reward':
            #     group = '2'
            #     print(f"Participant {participant_to_update} is assigned to group {group}")
            # elif third_column_value == 'sham':
            #     group = '3'
            #     print(f"Participant {participant_to_update} is assigned to group {group}")
            # elif third_column_value == 'control':
            #     group = '4'
            #     print(f"Participant {participant_to_update} is assigned to group {group}")

    else:
        # Count current "paired" and "sham" entries
        stim_count = (df["Stim_type"] == "paired").sum()
        sham_count = (df["Stim_type"] == "sham").sum()
        control_count = (df["Stim_type"] == "control").sum()
        reward_count = (df["Stim_type"] == "reward").sum()
        total_count = stim_count + sham_count + control_count + reward_count

        new_stim_type = random.choice(["sham", "paired", "reward", "control"]) # Random assignment initially


        # Determine the appropriate assignment
        if total_count >= 8:  # Only start balancing after 4 entries
            stim_ratio = stim_count / total_count
            sham_ratio = sham_count / total_count
            reward_ratio = reward_count / total_count
            control_ratio = control_count / total_count

            if stim_ratio < 0.25:
                new_stim_type = "paired"
            elif reward_ratio < 0.25:
                new_stim_type = "reward"
            elif sham_ratio < 0.25:
                new_stim_type = "sham"
            elif control_ratio < 0.25:
                new_stim_type = "control"

        group = group_dict[new_stim_type]
            
        # Add new participant
        new_row = pd.DataFrame({df.columns[0]: [participant_to_update], "Stim_type": [new_stim_type]})
        df = pd.concat([df, new_row], ignore_index=True)
        print(f"Participant {participant_to_update} was not found and has been assigned to group {group}.")

        # Save the updated Excel file
        df.to_excel(file_location, index=False, engine='openpyxl')

    
