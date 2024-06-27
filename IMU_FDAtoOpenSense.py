"""
This script is meant to preprocess csv files containing human motion data from the FDA Parkinson's Disease Dataset to be compatible with the OpenSim OpenSense software

The output of this script should return a folder per subject containing a text file per IMU sensor with the free accelerometry signals and the rotational matrices (calcualted from the sensor (**not segment**) quaterion data); the formatting of the txt file is consistent with what's exported from Xsens

Written by Megan Ebers (mebers@uw.edu) 6/20/24
"""
import os
import pandas as pd
import numpy as np

# Function to convert quaternion to rotation matrix
def quaternion_to_rotation_matrix(q):
    q0, q1, q2, q3 = q
    R = np.array([
        [1 - 2*(q2**2 + q3**2), 2*(q1*q2 - q0*q3), 2*(q1*q3 + q0*q2)],
        [2*(q1*q2 + q0*q3), 1 - 2*(q1**2 + q3**2), 2*(q2*q3 - q0*q1)],
        [2*(q1*q3 - q0*q2), 2*(q2*q3 + q0*q1), 1 - 2*(q1**2 + q2**2)]
    ])
    return R

# Function to process each DataFrame and save the output
def process_dataframe(df, imu_sensors, output_folder, SUBJ, TRIAL):
    for sensor in imu_sensors:

        # Filter columns for the specific IMU sensor
        sensor_columns = [col for col in df.columns if sensor in col]
        freeacc_columns = [col for col in sensor_columns if 'FreeAcc' in col]
        quat_columns = [col for col in sensor_columns if col.endswith('_q0') or col.endswith('_q1') or col.endswith('_q2') or col.endswith('_q3')]
        relevant_columns = freeacc_columns + quat_columns

        if not relevant_columns:
            raise ValueError(f"No data for Free Acceleration or Orientation were found for the {sensor} sensor.")

        # Extract relevant data
        data = df[relevant_columns].copy()

        # Convert quaternion columns to rotation matrices
        for i in range(data.shape[0]):
            q = data.loc[i, [col for col in quat_columns if col.endswith('_q0') or col.endswith('_q1') or col.endswith('_q2') or col.endswith('_q3')]].values
            R = quaternion_to_rotation_matrix(q)
            data.at[i, 'Mat[1][1]'] = R[0, 0]
            data.at[i, 'Mat[2][1]'] = R[1, 0]
            data.at[i, 'Mat[3][1]'] = R[2, 0]
            data.at[i, 'Mat[1][2]'] = R[0, 1]
            data.at[i, 'Mat[2][2]'] = R[1, 1]
            data.at[i, 'Mat[3][2]'] = R[2, 1]
            data.at[i, 'Mat[1][3]'] = R[0, 2]
            data.at[i, 'Mat[2][3]'] = R[1, 2]
            data.at[i, 'Mat[3][3]'] = R[2, 2]

        # Create the output DataFrame with the required OpenSense format, based on Xsens software output
        header_string = [
            'PacketCounter', 'SampleTimeFine', 'Year', 'Month', 'Day', 'Second', 'UTC_Nano', 'UTC_Year', 'UTC_Month',
            'UTC_Day', 'UTC_Hour', 'UTC_Minute', 'UTC_Second', 'UTC_Valid', 'Acc_X', 'Acc_Y', 'Acc_Z',
            'Mat[1][1]', 'Mat[2][1]', 'Mat[3][1]', 'Mat[1][2]', 'Mat[2][2]', 'Mat[3][2]', 'Mat[1][3]', 'Mat[2][3]', 'Mat[3][3]'
        ]

        output_data = pd.DataFrame(index=range(5+data.shape[0]), columns=range(len(header_string))) 
        output_data.loc[0, 0] = f"// Start Time: Unknown"
        output_data.loc[1, 0] = "// Update Rate: 100.00 Hz"
        output_data.loc[2, 0] = "// Filter Profile: human (46.1)"
        output_data.loc[3, 0] = "// Option Flags: AHS Disabled ICC Disabled"
        output_data.loc[4, 0] = "// Firmware Version: 4.0.2"
        output_data.loc[5, :] = header_string

        output_data = output_data.replace({np.nan: None})

        # Add sensor data
        for i in range(data.shape[0]):
            row = [
                data.at[i, 'PacketCounter'] if 'PacketCounter' in data.columns else i,
                data.at[i, 'SampleTimeFine'] if 'SampleTimeFine' in data.columns else None,
                data.at[i, 'Year'] if 'Year' in data.columns else None,
                data.at[i, 'Month'] if 'Month' in data.columns else None,
                data.at[i, 'Day'] if 'Day' in data.columns else None,
                data.at[i, 'Second'] if 'Second' in data.columns else None,
                data.at[i, 'UTC_Nano'] if 'UTC_Nano' in data.columns else None,
                data.at[i, 'UTC_Year'] if 'UTC_Year' in data.columns else None,
                data.at[i, 'UTC_Month'] if 'UTC_Month' in data.columns else None,
                data.at[i, 'UTC_Day'] if 'UTC_Day' in data.columns else None,
                data.at[i, 'UTC_Hour'] if 'UTC_Hour' in data.columns else None,
                data.at[i, 'UTC_Minute'] if 'UTC_Minute' in data.columns else None,
                data.at[i, 'UTC_Second'] if 'UTC_Second' in data.columns else None,
                data.at[i, 'UTC_Valid'] if 'UTC_Valid' in data.columns else None,
                data.at[i, 'FreeAcc_X'] if 'FreeAcc_X' in data.columns else None,
                data.at[i, 'FreeAcc_Y'] if 'FreeAcc_Y' in data.columns else None,
                data.at[i, 'FreeAcc_Z'] if 'FreeAcc_Z' in data.columns else None,
                data.at[i, 'Mat[1][1]'], data.at[i, 'Mat[2][1]'], data.at[i, 'Mat[3][1]'],
                data.at[i, 'Mat[1][2]'], data.at[i, 'Mat[2][2]'], data.at[i, 'Mat[3][2]'],
                data.at[i, 'Mat[1][3]'], data.at[i, 'Mat[2][3]'], data.at[i, 'Mat[3][3]']
            ]
            output_data.loc[i + 6, :] = row

        # Save to file
        output_file = os.path.join(output_folder, f"{SUBJ}_{TRIAL}_{sensor}.txt")
        output_data.to_csv(output_file, index=False, header=False, sep='\t')

# Main function to read CSV files and process them
def main(input_folder, imu_sensors, output_folder, SUBJ, TRIAL):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for file in os.listdir(input_folder):
        file_found = False

        if file.endswith('.csv') and TRIAL in file:
            file_path = os.path.join(input_folder, file)
            df = pd.read_csv(file_path)
            process_dataframe(df, imu_sensors, output_folder, SUBJ, TRIAL)

        if not file_found:
            raise FileNotFoundError(f"No CSV file matching the trial identifier '{TRIAL}' was found in the folder '{input_folder}'.")


# SETUP
SUBJ = 'NLS002'
TRIAL = 'SelfPace'
imu_sensors = ['LowerBack', 'R_DorsalFoot', 'R_Wrist', 'L_DorsalFoot', 'L_Wrist', 'R_Ankle', 'R_MidLatThigh', 'L_Ankle', 'L_MidLatThigh', 'Xiphoid', 'R_LatShank', 'Forehead', 'L_LatShank']  # List of IMU sensor names
input_folder = '/home/mebers/code/biomech/Parkinsons_Data/NLS002'
output_folder = os.path.join(input_folder, 'OpenSense', SUBJ)

main(input_folder, imu_sensors, output_folder, SUBJ, TRIAL)
