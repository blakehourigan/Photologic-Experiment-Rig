import pandas as pd

def parse_file(filename):
    # Initialize lists to hold the lick values and times
    lick_values = []
    lick_times = []

    # Open the file and read it line by line
    with open(filename, 'r') as file:
        for line in file:
            # Check if line contains 'Right Lick'
            if 'Right Lick:' in line:
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

    # Create a DataFrame from the lists
    df = pd.DataFrame({
        'Lick Value': lick_values,
        'Lick Time': lick_times
    })

    return df
df = parse_file('rightLick.txt')


df.to_csv('output.csv', index=False)
