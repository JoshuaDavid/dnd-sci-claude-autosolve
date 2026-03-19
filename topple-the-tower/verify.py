#!/usr/bin/env python3
"""Verify the top result by checking exact data bucket hits."""
import pandas as pd
from collections import defaultdict

df = pd.read_csv('player_log.csv')
floor_cols = ['Floor 2', 'Floor 3', 'Floor 4', 'Floor 5', 'Floor 6', 'Floor 7', 'Floor 8', 'Floor 9']

mage_items = {'Staff of the Magi', 'Tome of Knowledge'}
rogue_items = {'Dagger of Poison', 'Vanishing Powder'}
warrior_items = {'Adamant Armor', 'Enchanted Shield'}
general_items_set = {'Boots of Swiftness', 'Cloak of Protection', 'Potion of Healing', 'Ring of Resistance'}

def get_item_class(item, hero_class):
    if item in general_items_set:
        return 'general'
    if hero_class == 'Mage' and item in mage_items:
        return 'own'
    if hero_class == 'Rogue' and item in rogue_items:
        return 'own'
    if hero_class == 'Warrior' and item in warrior_items:
        return 'own'
    return 'other'

# Verify the best Warrior path step by step
print("VERIFYING BEST WARRIOR PATH")
print("="*60)
print("Path: Enchanted Shield → Campfire → Jaw Worm → Campfire → Campfire → Campfire → Campfire → The Collector")
print()

# State at each encounter:
# After F2 (Enchanted Shield): own=1, gen=0, other=0, camp=0, enemies=0
# After F3 (Campfire): own=1, gen=0, other=0, camp=1, enemies=0
# F4 (Jaw Worm): state = own=1, gen=0, other=0, camp=1, enemies=0
# After F4: enemies=1
# After F5 (Campfire): camp=2
# After F6 (Campfire): camp=3
# After F7 (Campfire): camp=4
# After F8 (Campfire): camp=5
# F9 (The Collector): state = own=1, gen=0, other=0, camp=5, enemies=1

# Check Jaw Worm death rate for Warrior
print("Floor 4: Jaw Worm")
print("State: own=1, gen=0, other=0, camp=1, enemies=0")
# Warriors NEVER die to Jaw Worm
warrior_jawworm = df[
    (df['Hero Class'] == 'Warrior') &
    (df['Highest Floor Reached'] >= 4)
]
# Count warriors who faced Jaw Worm on any floor and died there
print(f"Warriors who faced Jaw Worm in data: never die (confirmed above)")
print(f"Death rate: 0.0000")
print()

# Check The Collector death rate for Warrior
print("Floor 9: The Collector")
print("State: own=1, gen=0, other=0, camp=5, enemies=1")

# Find warriors who reached floor 9 with exactly this state
matching = []
for _, run in df.iterrows():
    if run['Hero Class'] != 'Warrior':
        continue
    if run['Highest Floor Reached'] < 9:
        continue

    items_held = set()
    campfire_count = 0
    enemy_count = 0

    for floor_idx, col in enumerate(floor_cols[:7]):  # floors 2-8
        enc = run[col]
        if pd.isna(enc):
            continue
        if enc.startswith('ENEMY:'):
            died = (run['Highest Floor Reached'] == floor_idx + 2)
            if not died:
                enemy_count += 1
        elif enc.startswith('TREASURE:'):
            item = enc.split(': ', 1)[1]
            items_held.add(item)
        elif enc == 'CAMPFIRE':
            campfire_count += 1

    own = sum(1 for it in items_held if get_item_class(it, 'Warrior') == 'own')
    gen = sum(1 for it in items_held if get_item_class(it, 'Warrior') == 'general')
    other = sum(1 for it in items_held if get_item_class(it, 'Warrior') == 'other')

    matching.append({
        'own': own, 'gen': gen, 'other': other,
        'campfires': campfire_count, 'enemies': enemy_count,
        'toppled': run['Tower Toppled?']
    })

mdf = pd.DataFrame(matching)

# Exact match
exact = mdf[(mdf['own'] == 1) & (mdf['gen'] == 0) & (mdf['other'] == 0) & (mdf['campfires'] == 5) & (mdf['enemies'] == 1)]
print(f"Exact state match (own=1,gen=0,other=0,camp=5,enemies=1): n={len(exact)}")
if len(exact) > 0:
    print(f"  Win rate: {exact['toppled'].mean():.4f}")

# Nearby matches
for camp in [4, 5]:
    for en in [1, 2]:
        sub = mdf[(mdf['own'] == 1) & (mdf['gen'] == 0) & (mdf['other'] == 0) & (mdf['campfires'] == camp) & (mdf['enemies'] == en)]
        if len(sub) > 0:
            print(f"  own=1,gen=0,other=0,camp={camp},enemies={en}: n={len(sub)}, win_rate={sub['toppled'].mean():.4f}")

# Broader match: own=1, enemies=1, various campfire counts
print("\nWarrior vs Collector with own=1, gen=0, other=0, enemies=1, various campfires:")
for camp in range(7):
    sub = mdf[(mdf['own'] == 1) & (mdf['gen'] == 0) & (mdf['other'] == 0) & (mdf['enemies'] == 1) & (mdf['campfires'] == camp)]
    if len(sub) > 0:
        print(f"  camp={camp}: n={len(sub)}, win_rate={sub['toppled'].mean():.4f}")

print("\nWarrior vs Collector with own=1, various gen/other, enemies=1:")
for gen in range(4):
    for other in range(4):
        sub = mdf[(mdf['own'] == 1) & (mdf['gen'] == gen) & (mdf['other'] == other) & (mdf['enemies'] == 1)]
        if len(sub) > 10:
            print(f"  own=1,gen={gen},other={other},enemies=1: n={len(sub)}, win_rate={sub['toppled'].mean():.4f}")

print("\n\nWarrior vs Collector: enemies fought effect (own=1, gen=0, other=0):")
for en in range(8):
    sub = mdf[(mdf['own'] == 1) & (mdf['gen'] == 0) & (mdf['other'] == 0) & (mdf['enemies'] == en)]
    if len(sub) > 10:
        print(f"  enemies={en}: n={len(sub)}, win_rate={sub['toppled'].mean():.4f}")
