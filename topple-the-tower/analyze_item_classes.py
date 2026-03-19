#!/usr/bin/env python3
"""Analyze whether item CLASS matters (not just count) for enemy encounters."""
import pandas as pd
import numpy as np

df = pd.read_csv('player_log.csv')
floor_cols = ['Floor 2', 'Floor 3', 'Floor 4', 'Floor 5', 'Floor 6', 'Floor 7', 'Floor 8', 'Floor 9']

# Classify items by class affinity based on boss analysis
# Mage items: Staff of the Magi, Tome of Knowledge
# Rogue items: Dagger of Poison, Vanishing Powder
# Warrior items: Adamant Armor, Enchanted Shield
# General items: Boots of Swiftness, Cloak of Protection, Potion of Healing, Ring of Resistance

mage_items = {'Staff of the Magi', 'Tome of Knowledge'}
rogue_items = {'Dagger of Poison', 'Vanishing Powder'}
warrior_items = {'Adamant Armor', 'Enchanted Shield'}
general_items = {'Boots of Swiftness', 'Cloak of Protection', 'Potion of Healing', 'Ring of Resistance'}

def classify_items(items_held, hero_class):
    """Count own-class items, other-class items, and general items."""
    own = 0
    other = 0
    general = 0
    for item in items_held:
        if item in general_items:
            general += 1
        elif hero_class == 'Mage' and item in mage_items:
            own += 1
        elif hero_class == 'Rogue' and item in rogue_items:
            own += 1
        elif hero_class == 'Warrior' and item in warrior_items:
            own += 1
        else:
            other += 1  # wrong class item
    return own, other, general

# Build encounter-level data with item classification
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
            if floor_num == 9:
                died = not toppled
            else:
                died = (highest == floor_num)

            enemy_name = enc.split(': ', 1)[1]
            is_boss = enc.startswith('BOSS:')
            own, other, gen = classify_items(items_held, cls)

            rows.append({
                'class': cls,
                'floor': floor_num,
                'enemy': enemy_name,
                'is_boss': is_boss,
                'died': died,
                'campfires': campfire_count,
                'enemies_fought': enemy_count,
                'n_items': len(items_held),
                'own_items': own,
                'other_items': other,
                'general_items': gen,
            })

            if not died:
                enemy_count += 1
            else:
                break
        elif enc.startswith('TREASURE:'):
            item = enc.split(': ', 1)[1]
            items_held.add(item)
        elif enc == 'CAMPFIRE':
            campfire_count += 1

enc_df = pd.DataFrame(rows)

# Now analyze: for each enemy, does own vs other vs general items matter?
print("="*80)
print("ITEM CLASS ANALYSIS FOR ENEMY ENCOUNTERS")
print("="*80)

dangerous_enemies = ['Jaw Worm', 'Slaver', 'Sentries', 'Gremlin Nob', 'Chosen', 'Shelled Parasite']

for enemy in dangerous_enemies:
    sub = enc_df[(enc_df['enemy'] == enemy) & (~enc_df['is_boss'])]
    if len(sub) == 0:
        continue
    print(f"\n=== {enemy} ===")

    for cls in ['Mage', 'Rogue', 'Warrior']:
        cls_sub = sub[sub['class'] == cls]
        if cls_sub['died'].sum() < 10:
            continue
        print(f"\n  {cls} (n={len(cls_sub)}, death_rate={cls_sub['died'].mean():.4f}):")

        # By own items
        print(f"    By own-class items:")
        for n in sorted(cls_sub['own_items'].unique()):
            nsub = cls_sub[cls_sub['own_items'] == n]
            if len(nsub) >= 30:
                print(f"      {n}: death_rate={nsub['died'].mean():.4f} (n={len(nsub)})")

        # By other-class items
        print(f"    By other-class items:")
        for n in sorted(cls_sub['other_items'].unique()):
            nsub = cls_sub[cls_sub['other_items'] == n]
            if len(nsub) >= 30:
                print(f"      {n}: death_rate={nsub['died'].mean():.4f} (n={len(nsub)})")

        # By general items
        print(f"    By general items:")
        for n in sorted(cls_sub['general_items'].unique()):
            nsub = cls_sub[cls_sub['general_items'] == n]
            if len(nsub) >= 30:
                print(f"      {n}: death_rate={nsub['died'].mean():.4f} (n={len(nsub)})")

# Now do the same for bosses
print("\n\n" + "="*80)
print("ITEM CLASS ANALYSIS FOR BOSS ENCOUNTERS")
print("="*80)

for boss in ['Bronze Automaton', 'The Champion', 'The Collector']:
    sub = enc_df[(enc_df['enemy'] == boss) & (enc_df['is_boss'])]
    print(f"\n=== {boss} ===")

    for cls in ['Mage', 'Rogue', 'Warrior']:
        cls_sub = sub[sub['class'] == cls]
        if len(cls_sub) < 100:
            continue
        print(f"\n  {cls} (n={len(cls_sub)}, death_rate={cls_sub['died'].mean():.4f}):")

        # By own items
        print(f"    By own-class items:")
        for n in sorted(cls_sub['own_items'].unique()):
            nsub = cls_sub[cls_sub['own_items'] == n]
            if len(nsub) >= 30:
                print(f"      {n}: death_rate={nsub['died'].mean():.4f} (n={len(nsub)})")

        # By other-class items
        print(f"    By other-class items:")
        for n in sorted(cls_sub['other_items'].unique()):
            nsub = cls_sub[cls_sub['other_items'] == n]
            if len(nsub) >= 30:
                print(f"      {n}: death_rate={nsub['died'].mean():.4f} (n={len(nsub)})")

        # By general items
        print(f"    By general items:")
        for n in sorted(cls_sub['general_items'].unique()):
            nsub = cls_sub[cls_sub['general_items'] == n]
            if len(nsub) >= 30:
                print(f"      {n}: death_rate={nsub['died'].mean():.4f} (n={len(nsub)})")

        # By enemies fought
        print(f"    By enemies fought:")
        for n in sorted(cls_sub['enemies_fought'].unique()):
            nsub = cls_sub[cls_sub['enemies_fought'] == n]
            if len(nsub) >= 30:
                print(f"      {n}: death_rate={nsub['died'].mean():.4f} (n={len(nsub)})")

        # By campfires
        print(f"    By campfires:")
        for n in sorted(cls_sub['campfires'].unique()):
            nsub = cls_sub[cls_sub['campfires'] == n]
            if len(nsub) >= 30:
                print(f"      {n}: death_rate={nsub['died'].mean():.4f} (n={len(nsub)})")
