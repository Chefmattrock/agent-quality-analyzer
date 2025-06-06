import pandas as pd
import matplotlib.pyplot as plt
import argparse
import numpy as np

parser = argparse.ArgumentParser(description='Plot distribution of agent description lengths.')
parser.add_argument('--csv', default='description_lengths.csv', help='CSV file with desc_length and agent_count columns (default: description_lengths.csv)')
args = parser.parse_args()

# Read the data
try:
    df = pd.read_csv(args.csv)
except Exception as e:
    print(f"Error reading CSV file {args.csv}: {e}")
    exit(1)

# Group by description length rounded to nearest 10
bins = (np.round(df['desc_length'] / 10) * 10).astype(int)
df['desc_length_bin'] = bins
grouped = df.groupby('desc_length_bin', as_index=False)['agent_count'].sum()

# Write binned data to CSV
binned_csv = 'description_lengths_binned.csv'
grouped.to_csv(binned_csv, index=False)
print(f"Binned data written to {binned_csv}")

plt.figure(figsize=(10,6))
plt.scatter(grouped['desc_length_bin'], grouped['agent_count'], alpha=0.7)
plt.xlabel('Description Length (binned to nearest 10)')
plt.ylabel('Number of Agents')
plt.title('Distribution of Description Lengths for Public Agents (Binned)')
plt.grid(True)
plt.tight_layout()
plt.show() 