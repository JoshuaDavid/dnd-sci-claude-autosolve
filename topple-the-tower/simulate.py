#!/usr/bin/env python3
"""
Simulate all possible paths through the tower and find the optimal class+path.

Model: For each encounter, estimate P(die | class, enemy_type, own_items, general_items, other_items, campfires, enemies_fought)
using empirical data from the dataset.
"""
import pandas as pd
import numpy as np
from collections import defaultdict
from itertools import product

df = pd.read_csv('player_log.csv')
floor_cols = ['Floor 2', 'Floor 3', 'Floor 4', 'Floor 5', 'Floor 6', 'Floor 7', 'Floor 8', 'Floor 9']

# Item classification
mage_items = {'Staff of the Magi', 'Tome of Knowledge'}
rogue_items = {'Dagger of Poison', 'Vanishing Powder'}
warrior_items = {'Adamant Armor', 'Enchanted Shield'}
general_items = {'Boots of Swiftness', 'Cloak of Protection', 'Potion of Healing', 'Ring of Resistance'}

def get_item_class(item, hero_class):
    """Returns 'own', 'other', or 'general'."""
    if item in general_items:
        return 'general'
    if hero_class == 'Mage' and item in mage_items:
        return 'own'
    if hero_class == 'Rogue' and item in rogue_items:
        return 'own'
    if hero_class == 'Warrior' and item in warrior_items:
        return 'own'
    return 'other'

# Build encounter-level data
print("Building encounter database...")
encounter_data = defaultdict(lambda: {'died': 0, 'total': 0})

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

            own = sum(1 for it in items_held if get_item_class(it, cls) == 'own')
            gen = sum(1 for it in items_held if get_item_class(it, cls) == 'general')
            other = sum(1 for it in items_held if get_item_class(it, cls) == 'other')

            key = (cls, enemy_name, own, gen, other, campfire_count, enemy_count)
            encounter_data[key]['total'] += 1
            if died:
                encounter_data[key]['died'] += 1

            if not died:
                enemy_count += 1
            else:
                break
        elif enc.startswith('TREASURE:'):
            item = enc.split(': ', 1)[1]
            items_held.add(item)
        elif enc == 'CAMPFIRE':
            campfire_count += 1

print(f"Built {len(encounter_data)} encounter state buckets")

def get_death_rate(hero_class, enemy, own, gen, other, campfires, enemies_fought):
    """Look up death rate from data, with fallback smoothing."""
    key = (hero_class, enemy, own, gen, other, campfires, enemies_fought)
    data = encounter_data[key]
    if data['total'] >= 20:
        return data['died'] / data['total']

    # Fallback: relax constraints
    # Try combining campfire values
    total_died = 0
    total_count = 0
    for c in range(max(0, campfires-1), campfires+2):
        k = (hero_class, enemy, own, gen, other, c, enemies_fought)
        d = encounter_data[k]
        total_count += d['total']
        total_died += d['died']
    if total_count >= 20:
        return total_died / total_count

    # Further fallback: also relax enemies_fought
    total_died = 0
    total_count = 0
    for c in range(max(0, campfires-1), campfires+2):
        for e in range(max(0, enemies_fought-1), enemies_fought+2):
            k = (hero_class, enemy, own, gen, other, c, e)
            d = encounter_data[k]
            total_count += d['total']
            total_died += d['died']
    if total_count >= 20:
        return total_died / total_count

    # Last resort: just use class + enemy + total items
    total_died = 0
    total_count = 0
    n_items = own + gen + other
    for key2, data2 in encounter_data.items():
        if key2[0] == hero_class and key2[1] == enemy:
            items2 = key2[2] + key2[3] + key2[4]
            if abs(items2 - n_items) <= 1:
                total_died += data2['died']
                total_count += data2['total']
    if total_count > 0:
        return total_died / total_count

    print(f"WARNING: No data for {key}")
    return 0.5  # pessimistic default


# Define the tower map
# Primary tower
tower_encounters = {
    2: ['TREASURE: Enchanted Shield', 'TREASURE: Tome of Knowledge'],
    3: ['CAMPFIRE', 'ENEMY: Cultist', 'ENEMY: Jaw Worm'],
    4: ['ENEMY: Slaver', 'ENEMY: Jaw Worm', 'ENEMY: Cultist', 'ENEMY: Jaw Worm'],
    5: ['ENEMY: Slaver', 'ENEMY: Sentries', 'CAMPFIRE', 'ENEMY: Sentries', 'TREASURE: Dagger of Poison'],
    6: ['ENEMY: Slaver', 'ENEMY: Sentries', 'CAMPFIRE', 'TREASURE: Cloak of Protection'],
    7: ['ENEMY: Chosen', 'CAMPFIRE', 'ENEMY: Chosen'],
    8: ['CAMPFIRE', 'ENEMY: Shelled Parasite'],
    9: ['BOSS: The Collector'],
}

# Define adjacency: from (floor, pos) to possible (floor+1, pos) values
# Floors 2-5: widening, from pos p → p or p+1
# Floors 5-8: narrowing, from pos p → p-1 or p (with edge constraints)
def get_next_positions(floor, pos):
    """Get valid positions on floor+1 from current floor,pos."""
    if floor <= 4:
        # Widening: pos → pos or pos+1
        return [pos, pos + 1]
    elif floor == 5:
        # Narrowing 5→4: pos maps to pos-1 or pos (1-indexed)
        # F5.1→F6.1, F5.2→F6.1,F6.2, F5.3→F6.2,F6.3, F5.4→F6.3,F6.4, F5.5→F6.4
        results = []
        if pos >= 2:
            results.append(pos - 1)
        if pos <= 4:
            results.append(pos)
        if pos == 1:
            results = [1]
        elif pos == 5:
            results = [4]
        return results
    elif floor == 6:
        # Narrowing 4→3
        # F6.1→F7.1, F6.2→F7.1,F7.2, F6.3→F7.2,F7.3, F6.4→F7.3
        results = []
        if pos >= 2:
            results.append(pos - 1)
        if pos <= 3:
            results.append(pos)
        if pos == 1:
            results = [1]
        elif pos == 4:
            results = [3]
        return results
    elif floor == 7:
        # Narrowing 3→2
        # F7.1→F8.1, F7.2→F8.1,F8.2, F7.3→F8.2
        results = []
        if pos >= 2:
            results.append(pos - 1)
        if pos <= 2:
            results.append(pos)
        if pos == 1:
            results = [1]
        elif pos == 3:
            results = [2]
        return results
    elif floor == 8:
        # All go to F9.1
        return [1]
    return []


def enumerate_paths():
    """Enumerate all valid paths through the tower. Returns list of position sequences."""
    paths = []

    def dfs(floor, pos, path):
        if floor == 8:
            # Floor 8 → Floor 9 (always pos 1)
            path.append(1)  # boss floor
            paths.append(tuple(path))
            path.pop()
            return
        for next_pos in get_next_positions(floor, pos):
            path.append(next_pos)
            dfs(floor + 1, next_pos, path)
            path.pop()

    # Start: floor 1 pos 1 → floor 2 pos 1 or 2
    for start_pos in [1, 2]:
        dfs(2, start_pos, [start_pos])

    return paths


def simulate_path(hero_class, positions):
    """Simulate a path and return P(survive all + beat boss)."""
    items_held = set()
    campfire_count = 0
    enemy_count = 0
    survival_prob = 1.0

    for floor_idx, pos in enumerate(positions):
        floor = floor_idx + 2
        encounter = tower_encounters[floor][pos - 1]

        if encounter.startswith('ENEMY:'):
            enemy = encounter.split(': ', 1)[1]
            own = sum(1 for it in items_held if get_item_class(it, hero_class) == 'own')
            gen = sum(1 for it in items_held if get_item_class(it, hero_class) == 'general')
            other = sum(1 for it in items_held if get_item_class(it, hero_class) == 'other')

            death_rate = get_death_rate(hero_class, enemy, own, gen, other, campfire_count, enemy_count)
            survival_prob *= (1 - death_rate)
            enemy_count += 1

        elif encounter.startswith('BOSS:'):
            boss = encounter.split(': ', 1)[1]
            own = sum(1 for it in items_held if get_item_class(it, hero_class) == 'own')
            gen = sum(1 for it in items_held if get_item_class(it, hero_class) == 'general')
            other = sum(1 for it in items_held if get_item_class(it, hero_class) == 'other')

            death_rate = get_death_rate(hero_class, boss, own, gen, other, campfire_count, enemy_count)
            survival_prob *= (1 - death_rate)

        elif encounter.startswith('TREASURE:'):
            item = encounter.split(': ', 1)[1]
            items_held.add(item)

        elif encounter == 'CAMPFIRE':
            campfire_count += 1

    return survival_prob


# Enumerate paths
paths = enumerate_paths()
print(f"Total valid paths: {len(paths)}")

# Simulate all paths for all classes
results = []
for hero_class in ['Mage', 'Rogue', 'Warrior']:
    for path in paths:
        prob = simulate_path(hero_class, path)
        encounters = []
        for floor_idx, pos in enumerate(path):
            floor = floor_idx + 2
            enc = tower_encounters[floor][pos - 1]
            encounters.append(enc)
        results.append({
            'class': hero_class,
            'path': path,
            'encounters': encounters,
            'win_prob': prob,
        })

# Sort by win probability
results.sort(key=lambda x: -x['win_prob'])

print("\n" + "="*80)
print("TOP 20 PATHS BY WIN PROBABILITY")
print("="*80)
for i, r in enumerate(results[:20]):
    print(f"\n#{i+1}: {r['class']} | P(win)={r['win_prob']:.4f} | Path: {r['path']}")
    for j, enc in enumerate(r['encounters']):
        floor = j + 2
        print(f"  Floor {floor}: {enc}")

print("\n" + "="*80)
print("BEST PATH PER CLASS")
print("="*80)
for hero_class in ['Mage', 'Rogue', 'Warrior']:
    best = max([r for r in results if r['class'] == hero_class], key=lambda x: x['win_prob'])
    print(f"\n{hero_class}: P(win)={best['win_prob']:.4f} | Path: {best['path']}")
    for j, enc in enumerate(best['encounters']):
        floor = j + 2
        print(f"  Floor {floor}: {enc}")

# Also show summary of top paths per class
print("\n" + "="*80)
print("TOP 5 PER CLASS")
print("="*80)
for hero_class in ['Mage', 'Rogue', 'Warrior']:
    class_results = sorted([r for r in results if r['class'] == hero_class], key=lambda x: -x['win_prob'])
    print(f"\n{hero_class}:")
    for i, r in enumerate(class_results[:5]):
        print(f"  #{i+1}: P(win)={r['win_prob']:.4f} | Path: {r['path']}")
        encounters_short = [enc.replace('ENEMY: ', 'E:').replace('TREASURE: ', 'T:').replace('BOSS: ', 'B:') for enc in r['encounters']]
        print(f"        {' → '.join(encounters_short)}")
