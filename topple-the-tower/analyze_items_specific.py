#!/usr/bin/env python3
"""Analyze how SPECIFIC items affect survival at enemy encounters, not just boss."""
import pandas as pd
import numpy as np

df = pd.read_csv('player_log.csv')
floor_cols = ['Floor 2', 'Floor 3', 'Floor 4', 'Floor 5', 'Floor 6', 'Floor 7', 'Floor 8', 'Floor 9']

treasures = ['Adamant Armor', 'Boots of Swiftness', 'Cloak of Protection',
             'Dagger of Poison', 'Enchanted Shield', 'Potion of Healing',
             'Ring of Resistance', 'Staff of the Magi', 'Tome of Knowledge',
             'Vanishing Powder']

# For each enemy encounter, compute state: class, items held, campfires, enemies fought
# Then look at death rate

# Let's build a row per enemy encounter
rows = []
for _, run in df.iterrows():
    cls = run['Hero Class']
    highest = run['Highest Floor Reached']
    toppled = run['Tower Toppled?']

    items_held = set()
    campfire_count = 0
    enemy_count = 0

    for floor_idx, col in enumerate(floor_cols):
        floor_num = floor_idx + 2
        enc = run[col]
        if pd.isna(enc):
            continue

        if enc.startswith('ENEMY:') or enc.startswith('BOSS:'):
            # Did they die here?
            if floor_num == 9:  # boss floor
                died = not toppled
            else:
                died = (highest == floor_num)

            enemy_name = enc.split(': ', 1)[1]
            is_boss = enc.startswith('BOSS:')

            rows.append({
                'class': cls,
                'floor': floor_num,
                'enemy': enemy_name,
                'is_boss': is_boss,
                'died': died,
                'campfires': campfire_count,
                'enemies_fought': enemy_count,
                'n_items': len(items_held),
                'items': frozenset(items_held),
                **{f'has_{t}': (t in items_held) for t in treasures}
            })

            if not died:
                enemy_count += 1
            else:
                break  # hero is dead
        elif enc.startswith('TREASURE:'):
            item = enc.split(': ', 1)[1]
            items_held.add(item)
        elif enc == 'CAMPFIRE':
            campfire_count += 1

enc_df = pd.DataFrame(rows)
print(f"Total encounter records: {len(enc_df)}")
print(f"Enemy encounters: {len(enc_df[~enc_df['is_boss']])}")
print(f"Boss encounters: {len(enc_df[enc_df['is_boss']])}")

# Now analyze: for each enemy type, how do items affect death rate?
print("\n" + "="*80)
print("ENEMY-BY-ENEMY ANALYSIS: EFFECT OF ITEMS ON SURVIVAL")
print("="*80)

enemies = enc_df[~enc_df['is_boss']]['enemy'].unique()
for enemy in sorted(enemies):
    sub = enc_df[(enc_df['enemy'] == enemy) & (~enc_df['is_boss'])]
    print(f"\n--- {enemy} (n={len(sub)}, death_rate={sub['died'].mean():.4f}) ---")

    for cls in ['Mage', 'Rogue', 'Warrior']:
        cls_sub = sub[sub['class'] == cls]
        if len(cls_sub) < 100:
            continue
        print(f"\n  {cls} (n={len(cls_sub)}, death_rate={cls_sub['died'].mean():.4f}):")

        # Effect of number of items
        for n in sorted(cls_sub['n_items'].unique()):
            nsub = cls_sub[cls_sub['n_items'] == n]
            if len(nsub) >= 50:
                print(f"    {n} items: death_rate={nsub['died'].mean():.4f} (n={len(nsub)})")

        # Effect of campfire count
        print(f"    By campfires:")
        for n in sorted(cls_sub['campfires'].unique()):
            nsub = cls_sub[cls_sub['campfires'] == n]
            if len(nsub) >= 50:
                print(f"      {n} campfires: death_rate={nsub['died'].mean():.4f} (n={len(nsub)})")

        # Effect of enemies fought
        print(f"    By prior enemies fought:")
        for n in sorted(cls_sub['enemies_fought'].unique()):
            nsub = cls_sub[cls_sub['enemies_fought'] == n]
            if len(nsub) >= 50:
                print(f"      {n} enemies: death_rate={nsub['died'].mean():.4f} (n={len(nsub)})")

# Boss analysis
print("\n\n" + "="*80)
print("BOSS ANALYSIS: DETAILED")
print("="*80)

for boss in sorted(enc_df[enc_df['is_boss']]['enemy'].unique()):
    sub = enc_df[(enc_df['enemy'] == boss) & (enc_df['is_boss'])]
    print(f"\n--- {boss} (n={len(sub)}, death_rate={sub['died'].mean():.4f}) ---")

    for cls in ['Mage', 'Rogue', 'Warrior']:
        cls_sub = sub[sub['class'] == cls]
        if len(cls_sub) < 100:
            continue
        print(f"\n  {cls} (n={len(cls_sub)}, death_rate={cls_sub['died'].mean():.4f}):")

        # Effect of specific items
        for item in treasures:
            col = f'has_{item}'
            has = cls_sub[cls_sub[col] == True]
            hasnt = cls_sub[cls_sub[col] == False]
            if len(has) >= 50 and len(hasnt) >= 50:
                diff = has['died'].mean() - hasnt['died'].mean()
                print(f"    {item}: with={has['died'].mean():.4f} without={hasnt['died'].mean():.4f} diff={diff:+.4f} (n_with={len(has)}, n_without={len(hasnt)})")

        # By enemies fought
        print(f"    By prior enemies fought:")
        for n in sorted(cls_sub['enemies_fought'].unique()):
            nsub = cls_sub[cls_sub['enemies_fought'] == n]
            if len(nsub) >= 50:
                print(f"      {n}: death_rate={nsub['died'].mean():.4f} (n={len(nsub)})")

        # By campfires
        print(f"    By campfires:")
        for n in sorted(cls_sub['campfires'].unique()):
            nsub = cls_sub[cls_sub['campfires'] == n]
            if len(nsub) >= 50:
                print(f"      {n}: death_rate={nsub['died'].mean():.4f} (n={len(nsub)})")
