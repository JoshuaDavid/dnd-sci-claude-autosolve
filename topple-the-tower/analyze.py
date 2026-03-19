#!/usr/bin/env python3
"""Deeper analysis of survival mechanics."""
import pandas as pd
import collections

df = pd.read_csv('player_log.csv')

# Key insight: "Highest Floor Reached" tells us where a hero died.
# If highest_floor = 9 and toppled = True, they beat the boss
# If highest_floor = 9 and toppled = False, they died to the boss
# If highest_floor < 9, they died on that floor

# Let's compute: for each floor encounter, what's the death rate?
# A hero "died on floor X" if Highest Floor Reached == X and Tower Toppled? == False

print("="*80)
print("DEATH RATE BY ENCOUNTER TYPE AND CLASS")
print("="*80)

for floor_num in range(2, 10):
    col = f'Floor {floor_num}'
    print(f"\n--- {col} ---")

    # Heroes who reached this floor (highest_floor >= floor_num)
    reached = df[df['Highest Floor Reached'] >= floor_num]

    for encounter in sorted(reached[col].dropna().unique()):
        sub = reached[reached[col] == encounter]
        # Died on this floor
        died_here = sub[sub['Highest Floor Reached'] == floor_num]
        if floor_num == 9:
            # For floor 9, "died" means toppled = False
            died_here = sub[sub['Tower Toppled?'] == False]

        death_rate = len(died_here) / len(sub) if len(sub) > 0 else 0

        print(f"  {encounter}: death_rate={death_rate:.4f} (died={len(died_here)}, reached={len(sub)})")

        # Break down by class
        for cls in ['Mage', 'Rogue', 'Warrior']:
            cls_sub = sub[sub['Hero Class'] == cls]
            cls_died = died_here[died_here['Hero Class'] == cls]
            if len(cls_sub) > 0:
                cls_rate = len(cls_died) / len(cls_sub)
                print(f"    {cls}: {cls_rate:.4f} ({len(cls_died)}/{len(cls_sub)})")

print("\n\n" + "="*80)
print("BOSS DEATH RATES BY CLASS AND BOSS")
print("="*80)
floor9 = df[df['Highest Floor Reached'] >= 9]
for boss in sorted(floor9['Floor 9'].unique()):
    sub = floor9[floor9['Floor 9'] == boss]
    print(f"\n{boss}:")
    for cls in ['Mage', 'Rogue', 'Warrior']:
        cls_sub = sub[sub['Hero Class'] == cls]
        cls_toppled = cls_sub[cls_sub['Tower Toppled?'] == True]
        if len(cls_sub) > 0:
            print(f"  {cls}: win_rate={len(cls_toppled)/len(cls_sub):.4f} ({len(cls_toppled)}/{len(cls_sub)})")
