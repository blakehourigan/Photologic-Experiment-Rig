import pandas as pd

def parse_file(filename):
    # Initialize lists to hold the lick values and times
    lick_values = []
    lick_times = []
    lick_stamps = []

    # Open the file and read it line by line
    with open(filename, 'r') as file:
        for line in file:
            # Check if line contains 'Right Lick'
            if 'Stimulus One Lick:' in line:
                # Split the line at the colon and take the second part, then strip whitespace
                lick_value = line.split(':')[1].strip()
                # Append the lick value to the list
                lick_values.append(int(lick_value))
            # Check if line contains 'lick time'
            elif 'lick time:' in line:
                # Split the line at the colon and take the second part, then strip whitespace
                lick_time = line.split(':')[1].strip()
                # Append the lick time to the list
                lick_times.append(int(lick_time))
            elif 'Stamp:' in line:
                lick_stamp = line.split(':')[1].strip()
                lick_stamps.append(lick_stamp) 

    # Create a DataFrame from the lists
    df = pd.DataFrame({
        'Lick Value': lick_values,
        'Lick Time': lick_times,
        'Lick Stamp': lick_stamps
    })

    return df
df = parse_file('licks.txt')


df.to_excel('output_trial_2.xlsx', index=False)
