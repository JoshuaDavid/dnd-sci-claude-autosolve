#!/usr/bin/env python3
"""Initial exploration of the player_log dataset."""
import pandas as pd
import collections

df = pd.read_csv('player_log.csv')
print(f"Shape: {df.shape}")
print(f"\nColumns: {list(df.columns)}")
print(f"\nClass distribution:\n{df['Hero Class'].value_counts()}")
print(f"\nHighest Floor Reached distribution:\n{df['Highest Floor Reached'].value_counts().sort_index()}")
print(f"\nTower Toppled distribution:\n{df['Tower Toppled?'].value_counts()}")
print(f"\nTopple rate by class:")
for cls in df['Hero Class'].unique():
    sub = df[df['Hero Class'] == cls]
    rate = sub['Tower Toppled?'].mean()
    print(f"  {cls}: {rate:.4f} ({sub['Tower Toppled?'].sum()}/{len(sub)})")

# Unique encounter values
print("\n\nUnique encounters per floor:")
for col in ['Floor 2', 'Floor 3', 'Floor 4', 'Floor 5', 'Floor 6', 'Floor 7', 'Floor 8', 'Floor 9']:
    vals = df[col].dropna().unique()
    print(f"\n{col} ({len(vals)} unique):")
    for v in sorted(vals):
        print(f"  {v}")
