#!/usr/bin/env python3
"""Analyze how items and campfires affect survival at each enemy encounter."""
import pandas as pd
import numpy as np
from collections import Counter

df = pd.read_csv('player_log.csv')

# For each run, extract the sequence of encounters and track state
# We want to understand: given a hero's class and accumulated items,
# what's their probability of dying at each enemy?

# First, let's categorize encounters
def parse_encounter(enc):
    if pd.isna(enc):
        return ('NONE', '')
    if enc.startswith('ENEMY:'):
        return ('ENEMY', enc.split(': ', 1)[1])
    elif enc.startswith('TREASURE:'):
        return ('TREASURE', enc.split(': ', 1)[1])
    elif enc.startswith('BOSS:'):
        return ('BOSS', enc.split(': ', 1)[1])
    elif enc == 'CAMPFIRE':
        return ('CAMPFIRE', '')
    else:
        return ('UNKNOWN', enc)

# For each run, compute the state before each floor:
# - number of campfires visited
# - set of treasures collected
# - number of enemies fought
# Then check if they died on that floor

floor_cols = ['Floor 2', 'Floor 3', 'Floor 4', 'Floor 5', 'Floor 6', 'Floor 7', 'Floor 8', 'Floor 9']

# Let's look at effect of specific items on boss fights
print("="*80)
print("EFFECT OF SPECIFIC ITEMS ON BOSS WIN RATES")
print("="*80)

# For heroes that reached floor 9, what items did they have?
reached_boss = df[df['Highest Floor Reached'] >= 9].copy()

# Collect all treasures for each run
treasures_list = ['Adamant Armor', 'Boots of Swiftness', 'Cloak of Protection',
                  'Dagger of Poison', 'Enchanted Shield', 'Potion of Healing',
                  'Ring of Resistance', 'Staff of the Magi', 'Tome of Knowledge',
                  'Vanishing Powder']

for treasure in treasures_list:
    has_item = reached_boss.apply(
        lambda row: any(f'TREASURE: {treasure}' == row[col] for col in floor_cols[:7]),  # floors 2-8
        axis=1
    )

    with_item = reached_boss[has_item]
    without_item = reached_boss[~has_item]

    if len(with_item) > 0 and len(without_item) > 0:
        rate_with = with_item['Tower Toppled?'].mean()
        rate_without = without_item['Tower Toppled?'].mean()
        print(f"\n{treasure}:")
        print(f"  With:    {rate_with:.4f} ({with_item['Tower Toppled?'].sum()}/{len(with_item)})")
        print(f"  Without: {rate_without:.4f} ({without_item['Tower Toppled?'].sum()}/{len(without_item)})")
        print(f"  Diff:    {rate_with - rate_without:+.4f}")

        # By class
        for cls in ['Mage', 'Rogue', 'Warrior']:
            wi = with_item[with_item['Hero Class'] == cls]
            wo = without_item[without_item['Hero Class'] == cls]
            if len(wi) > 0 and len(wo) > 0:
                rw = wi['Tower Toppled?'].mean()
                rwo = wo['Tower Toppled?'].mean()
                print(f"    {cls}: with={rw:.4f} without={rwo:.4f} diff={rw-rwo:+.4f}")

# Campfire count effect
print("\n\n" + "="*80)
print("EFFECT OF CAMPFIRE COUNT ON BOSS WIN RATE")
print("="*80)

campfire_count = reached_boss.apply(
    lambda row: sum(1 for col in floor_cols[:7] if row[col] == 'CAMPFIRE'),
    axis=1
)
reached_boss['campfire_count'] = campfire_count

for n_camp in sorted(reached_boss['campfire_count'].unique()):
    sub = reached_boss[reached_boss['campfire_count'] == n_camp]
    if len(sub) > 100:
        rate = sub['Tower Toppled?'].mean()
        print(f"\n{n_camp} campfires: win_rate={rate:.4f} ({sub['Tower Toppled?'].sum()}/{len(sub)})")
        for cls in ['Mage', 'Rogue', 'Warrior']:
            cls_sub = sub[sub['Hero Class'] == cls]
            if len(cls_sub) > 0:
                print(f"  {cls}: {cls_sub['Tower Toppled?'].mean():.4f} ({cls_sub['Tower Toppled?'].sum()}/{len(cls_sub)})")

# Number of treasures effect
print("\n\n" + "="*80)
print("EFFECT OF TREASURE COUNT ON BOSS WIN RATE")
print("="*80)

treasure_count = reached_boss.apply(
    lambda row: sum(1 for col in floor_cols[:7] if isinstance(row[col], str) and row[col].startswith('TREASURE:')),
    axis=1
)
reached_boss['treasure_count'] = treasure_count

for n_tr in sorted(reached_boss['treasure_count'].unique()):
    sub = reached_boss[reached_boss['treasure_count'] == n_tr]
    if len(sub) > 100:
        rate = sub['Tower Toppled?'].mean()
        print(f"\n{n_tr} treasures: win_rate={rate:.4f} ({sub['Tower Toppled?'].sum()}/{len(sub)})")
        for cls in ['Mage', 'Rogue', 'Warrior']:
            cls_sub = sub[sub['Hero Class'] == cls]
            if len(cls_sub) > 0:
                print(f"  {cls}: {cls_sub['Tower Toppled?'].mean():.4f} ({cls_sub['Tower Toppled?'].sum()}/{len(cls_sub)})")

# Number of enemy encounters before boss
print("\n\n" + "="*80)
print("EFFECT OF ENEMY COUNT BEFORE BOSS ON WIN RATE")
print("="*80)

enemy_count = reached_boss.apply(
    lambda row: sum(1 for col in floor_cols[:7] if isinstance(row[col], str) and row[col].startswith('ENEMY:')),
    axis=1
)
reached_boss['enemy_count'] = enemy_count

for n_en in sorted(reached_boss['enemy_count'].unique()):
    sub = reached_boss[reached_boss['enemy_count'] == n_en]
    if len(sub) > 100:
        rate = sub['Tower Toppled?'].mean()
        print(f"\n{n_en} enemies: win_rate={rate:.4f} ({sub['Tower Toppled?'].sum()}/{len(sub)})")
        for cls in ['Mage', 'Rogue', 'Warrior']:
            cls_sub = sub[sub['Hero Class'] == cls]
            if len(cls_sub) > 0:
                print(f"  {cls}: {cls_sub['Tower Toppled?'].mean():.4f} ({cls_sub['Tower Toppled?'].sum()}/{len(cls_sub)})")
