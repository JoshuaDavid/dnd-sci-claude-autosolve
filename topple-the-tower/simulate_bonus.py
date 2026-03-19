#!/usr/bin/env python3
"""Simulate all paths through the BONUS tower."""
import pandas as pd
import numpy as np
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

# Build encounter database
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
    key = (hero_class, enemy, own, gen, other, campfires, enemies_fought)
    data = encounter_data[key]
    if data['total'] >= 20:
        return data['died'] / data['total']

    total_died = 0
    total_count = 0
    for c in range(max(0, campfires-1), campfires+2):
        k = (hero_class, enemy, own, gen, other, c, enemies_fought)
        d = encounter_data[k]
        total_count += d['total']
        total_died += d['died']
    if total_count >= 20:
        return total_died / total_count

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

    # Last resort
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
    return 0.5


# Bonus tower map
bonus_encounters = {
    2: ['ENEMY: Acid Slime', 'ENEMY: Gremlin'],
    3: ['ENEMY: Cultist', 'ENEMY: Acid Slime', 'ENEMY: Jaw Worm'],
    4: ['ENEMY: Cultist', 'ENEMY: Jaw Worm', 'CAMPFIRE', 'TREASURE: Adamant Armor'],
    5: ['CAMPFIRE', 'ENEMY: Sentries', 'CAMPFIRE', 'TREASURE: Enchanted Shield', 'ENEMY: Jaw Worm'],
    6: ['ENEMY: Gremlin Nob', 'CAMPFIRE', 'ENEMY: Sentries', 'ENEMY: Gremlin Nob'],
    7: ['TREASURE: Cloak of Protection', 'CAMPFIRE', 'ENEMY: Chosen'],
    8: ['TREASURE: Vanishing Powder', 'ENEMY: Gremlin Nob'],
    9: ['BOSS: The Champion'],
}

def get_next_positions_bonus(floor, pos):
    """Same graph structure as primary tower."""
    if floor <= 4:
        return [pos, pos + 1]
    elif floor == 5:
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
        return [1]
    return []


def enumerate_paths():
    paths = []

    def dfs(floor, pos, path):
        if floor == 8:
            path.append(1)
            paths.append(tuple(path))
            path.pop()
            return
        for next_pos in get_next_positions_bonus(floor, pos):
            path.append(next_pos)
            dfs(floor + 1, next_pos, path)
            path.pop()

    for start_pos in [1, 2]:
        dfs(2, start_pos, [start_pos])

    return paths


def simulate_path(hero_class, positions, tower_enc):
    items_held = set()
    campfire_count = 0
    enemy_count = 0
    survival_prob = 1.0
    encounter_log = []

    for floor_idx, pos in enumerate(positions):
        floor = floor_idx + 2
        encounter = tower_enc[floor][pos - 1]
        encounter_log.append(encounter)

        if encounter.startswith('ENEMY:') or encounter.startswith('BOSS:'):
            enemy = encounter.split(': ', 1)[1]
            own = sum(1 for it in items_held if get_item_class(it, hero_class) == 'own')
            gen = sum(1 for it in items_held if get_item_class(it, hero_class) == 'general')
            other = sum(1 for it in items_held if get_item_class(it, hero_class) == 'other')

            death_rate = get_death_rate(hero_class, enemy, own, gen, other, campfire_count, enemy_count)
            survival_prob *= (1 - death_rate)
            enemy_count += 1
        elif encounter.startswith('TREASURE:'):
            item = encounter.split(': ', 1)[1]
            items_held.add(item)
        elif encounter == 'CAMPFIRE':
            campfire_count += 1

    return survival_prob, encounter_log


paths = enumerate_paths()
print(f"Total valid paths: {len(paths)}")

results = []
for hero_class in ['Mage', 'Rogue', 'Warrior']:
    for path in paths:
        prob, enc_log = simulate_path(hero_class, path, bonus_encounters)
        results.append({
            'class': hero_class,
            'path': path,
            'encounters': enc_log,
            'win_prob': prob,
        })

results.sort(key=lambda x: -x['win_prob'])

print("\n" + "="*80)
print("BONUS TOWER: TOP 20 PATHS")
print("="*80)
for i, r in enumerate(results[:20]):
    print(f"\n#{i+1}: {r['class']} | P(win)={r['win_prob']:.4f} | Path: {r['path']}")
    enc_short = [e.replace('ENEMY: ', 'E:').replace('TREASURE: ', 'T:').replace('BOSS: ', 'B:') for e in r['encounters']]
    print(f"  {' → '.join(enc_short)}")

print("\n" + "="*80)
print("BONUS TOWER: BEST PER CLASS")
print("="*80)
for hero_class in ['Mage', 'Rogue', 'Warrior']:
    class_results = sorted([r for r in results if r['class'] == hero_class], key=lambda x: -x['win_prob'])
    print(f"\n{hero_class}:")
    for i, r in enumerate(class_results[:5]):
        print(f"  #{i+1}: P(win)={r['win_prob']:.4f} | Path: {r['path']}")
        enc_short = [e.replace('ENEMY: ', 'E:').replace('TREASURE: ', 'T:').replace('BOSS: ', 'B:') for e in r['encounters']]
        print(f"        {' → '.join(enc_short)}")
