import pandas as pd
import argparse

parser = argparse.ArgumentParser(description='Compute decile analysis of agent description lengths.')
parser.add_argument('--csv', default='description_lengths_raw.csv', help='CSV file with desc_length column (default: description_lengths_raw.csv)')
args = parser.parse_args()

# Load the raw description lengths
df = pd.read_csv(args.csv)

# Remove NaN or zero-length descriptions
df = df[df['desc_length'].notna()]
df = df[df['desc_length'] > 0]

# Compute decile bins
df['decile'] = pd.qcut(df['desc_length'], 10, labels=False, duplicates='drop')

# Group by decile and get min/max/count
summary = df.groupby('decile')['desc_length'].agg(['count', 'min', 'max']).reset_index()

print('Decile analysis of description lengths:')
print(summary)

summary.to_csv('description_length_deciles.csv', index=False)
print('Decile summary written to description_length_deciles.csv') 