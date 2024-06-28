import csv
import os

# Mapping for IMUsensor to OpenSim
imu_to_opensim = {
    "L_Ankle": "talus_l_imu",
    "L_DorsalFoot": "calcn_l_imu",
    "L_LatShank": "tibia_l_imu",
    "L_MidLatThigh": "femur_l_imu",
    "L_Wrist": "radius_l_imu",
    "LowerBack": "pelvis_imu",
    "R_Ankle": "talus_r_imu",
    "R_DorsalFoot": "calcn_r_imu",
    "R_LatShank": "tibia_r_imu",
    "R_MidLatThigh": "femur_r_imu",
    "R_Wrist": "radius_r_imu",
    "Xiphoid": "torso_imu"
}

# Function to process the CSV file and generate the output text file
def reformat_data(input_csv, output_folder):
    # Check if the output folder exists, if not, create it
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    output_sto = os.path.join(output_folder, f'{SUBJ}_{TRIAL}.sto')

    with open(input_csv, mode='r') as infile, open(output_sto, mode='w') as outfile:
        reader = csv.DictReader(infile)
        
        # Writing the header lines
        outfile.write("DataRate=100.000000\n")
        outfile.write("DataType=Quaternion\n")
        outfile.write("version=3\n")
        outfile.write("OpenSimVersion=4.5\n")
        outfile.write("endheader\n")
        
        # Writing the column headers
        headers = ["time"] + list(imu_to_opensim.values())
        outfile.write("\t".join(headers) + "\n")
        
        # Writing the data rows
        for i, row in enumerate(reader):
            time = f"{i / 100:.6f}"
            data = [time]
            for imu, opensim in imu_to_opensim.items():
                q0 = f"{float(row[f'{imu}_OriInc_q0']):.10f}"
                q1 = f"{float(row[f'{imu}_OriInc_q1']):.10f}"
                q2 = f"{float(row[f'{imu}_OriInc_q2']):.10f}"
                q3 = f"{float(row[f'{imu}_OriInc_q3']):.10f}"
                quaternion = f"{q0},{q1},{q2},{q3}"
                data.append(quaternion)
            outfile.write("\t".join(data) + "\n")

SUBJ = 'HC100'
TRIAL = 'SelfPace'

input_folder = '/home/mebers/IMU_FDAtoOpenSense'
output_folder = os.path.join(input_folder, 'OpenSense', SUBJ)

input_csv = os.path.join(input_folder, SUBJ, f'{SUBJ}_{TRIAL}.csv')
reformat_data(input_csv, output_folder)
