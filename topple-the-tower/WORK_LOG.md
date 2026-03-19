# Work Log: Topple the Tower D&D.Sci Challenge

## Understanding the Problem

The challenge is a Slay-the-Spire-themed puzzle. We have:
- A dataset of ~140K past hero runs through towers
- Each run has a class (Mage/Rogue/Warrior), encounters on each floor, and outcome
- We need to choose a class and a path (left/right at each fork) through a specific tower map
- Goal: maximize probability of toppling the tower

The tower map has 9 floors. Floor 1 is START, Floor 9 is the boss (The Collector).
At each floor we go left or right, encountering different things.

Encounter types visible: ENEMY, TREASURE, CAMPFIRE, BOSS

## Plan
1. Load and explore the dataset
2. Understand what factors affect success/failure
3. Figure out how each encounter type affects hero survival
4. Model the probability of surviving each encounter given class and prior encounters
5. Find the optimal path through the specific tower map

## Actions

### Step 1: Explore the dataset

**Command:** `python3 explore.py`
**Expected:** Overview of dataset shape, class distribution, outcomes
**Result (as expected):**
- 139,828 rows, 12 columns
- ~46K runs per class (balanced)
- Overall topple rate ~41% (similar across classes)
- ~76% of heroes reach floor 9 (the boss)
- 3 bosses: Bronze Automaton, The Champion, The Collector
- Enemies: Acid Slime, Cultist, Gremlin, Jaw Worm, Slaver, Sentries, Gremlin Nob, Chosen, Shelled Parasite
- 10 treasure types, plus Campfire

### Step 2: Analyze death rates by encounter type and class

**Command:** `python3 analyze.py`
**Expected:** Death rates broken down by enemy type, floor, and class
**Result (as expected, with interesting findings):**

**Key enemy danger (death rates by class):**
- **Acid Slime, Cultist, Gremlin:** 0% death rate for all classes (safe enemies)
- **Jaw Worm:** Only kills Mages (~10-30% on different floors), Rogues and Warriors immune
- **Slaver:** Kills Mages (~16-32%) and Rogues (~3-6%), Warriors immune
- **Sentries:** Kills all classes. Mage 17%, Rogue 9%, Warrior 2%
- **Gremlin Nob:** Kills all. Mage 16%, Rogue 14%, Warrior 9%
- **Chosen:** Very dangerous. All ~21-33%
- **Shelled Parasite:** Very dangerous. All ~35-40%

**Boss win rates:**
- Bronze Automaton: Mage 90%, Rogue 84%, Warrior 77%
- The Collector: Mage 67%, Rogue 53%, Warrior 49%
- The Champion: Mage 34%, Rogue 21%, Warrior 21%

### Step 3: Analyze item effects

**Command:** `python3 analyze_items.py`
**Expected:** How items affect boss win rates
**Result (key findings):**
- More treasures → much higher win rate (especially Warriors: 15% with 0 → 97% with 5)
- Campfires: diminishing returns, too many actually hurt (especially Mages)
- More enemy fights → better for Mages (XP), worse for Warriors/Rogues (cumulative damage)
- Items are class-specific: wrong-class items can hurt

### Step 4: Analyze item class interactions

**Command:** `python3 analyze_item_classes.py`
**Expected:** Whether own-class vs other-class items matter
**Result (critical finding):**

Items classified into:
- **Mage items:** Staff of the Magi, Tome of Knowledge
- **Rogue items:** Dagger of Poison, Vanishing Powder
- **Warrior items:** Adamant Armor, Enchanted Shield
- **General items:** Boots of Swiftness, Cloak of Protection, Potion of Healing, Ring of Resistance

Effects:
- **Own-class items:** Strongly reduce death rate (e.g., Warriors with 2 own items: 12.6% boss death vs 92.5% with 0)
- **Other-class items:** Can INCREASE death rate (harmful)
- **General items:** Help all classes

The model is essentially: heroes have a "power" that depends on their class, accumulated own-class items, general items, campfires, and enemy fight history. Each encounter checks power against difficulty.

### Step 5: Simulate all paths through the primary tower

**Command:** `python3 simulate.py`
**Expected:** Win probability for each class × path combination
**Result:**

**Best path overall: Warrior with 94.7% win probability!**

Path (positions): (1, 1, 2, 3, 3, 2, 1, 1)
- Floor 2: Enchanted Shield (Warrior own-class item)
- Floor 3: Campfire
- Floor 4: Jaw Worm (safe for Warriors)
- Floor 5: Campfire
- Floor 6: Campfire
- Floor 7: Campfire
- Floor 8: Campfire
- Floor 9: The Collector (boss)

Why this works:
1. Picks up own-class item (Enchanted Shield) immediately
2. Only fights 1 enemy (Jaw Worm = harmless to Warriors)
3. With 1 own item + only 1 enemy fought, the boss is very beatable
4. Campfires provide healing/rest

Best per class:
- Warrior: 94.7%
- Mage: 69.6% (Tome of Knowledge → enemies → Sentries → Chosen → Collector)
- Rogue: 48.8% (Tome of Knowledge → Jaw Worms → Dagger of Poison → Cloak → Chosen → Shelled Parasite → Collector)

### Step 6: Verify the result

**Command:** `python3 verify.py`
**Expected:** Confirmation that the data supports the 94.7% estimate
**Result:**
- Exact data match (own=1,gen=0,other=0,camp=5,enemies=1): only n=6 (100% win, small sample)
- But broader data (Warrior vs Collector with enemies=1): death rate = 5.5% (n=403), consistent with ~94.5%
- Warriors with 1 own item and 1 enemy fought are extremely likely to beat The Collector

### Step 7: Solve the bonus tower

**Command:** `python3 simulate_bonus.py`
**Expected:** Optimal path for the bonus tower (boss: The Champion)
**Result:**

**Best: Warrior with 85.7% win probability**

Path (positions): (2, 3, 4, 4, 3, 2, 1, 1)
- Floor 2: Gremlin (safe)
- Floor 3: Jaw Worm (safe for Warriors)
- Floor 4: Adamant Armor (Warrior own-class item)
- Floor 5: Enchanted Shield (Warrior own-class item)
- Floor 6: Sentries (with 2 own items → very low death rate)
- Floor 7: Campfire
- Floor 8: Vanishing Powder (Rogue item, but it's a treasure slot)
- Floor 9: The Champion (boss)

Why this works: Warrior with 2 own-class items has ~87.4% win rate vs The Champion (from 12.6% death rate with 2 own items, n=438).

## Summary of Findings

### Key Mechanics Discovered:
1. **Class-specific items are crucial.** Own-class items dramatically reduce death rates; other-class items can hurt.
2. **Enemies provide XP to Mages** (more fights → stronger vs boss) but **deal cumulative damage to Warriors/Rogues.**
3. **Safe enemies exist:** Acid Slime, Cultist, Gremlin never kill. Jaw Worm only kills Mages.
4. **Warriors dominate both towers** because they can collect own-class items and minimize enemy fights.
5. **Campfires have diminishing returns** and can be detrimental with too many (especially for Mages).
