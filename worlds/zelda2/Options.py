from dataclasses import dataclass
from Options import (Toggle, DefaultOnToggle, Choice, Range, PerGameCommonOptions, StartInventoryPool,
                     OptionGroup, FreeText, Visibility)


class RequiredCrystals(Range):
    """How many Crystals need to be set in Palaces in order
       to unlock the Great Palace"""
    display_name = "Required Crystals"
    range_start = 0
    range_end = 6
    default = 6

class RandomTunicColor(Toggle):
    """Randomizes Link's normal and Shield tunic color."""
    display_name = "Random Tunic Color"

class EarlyCandle(Toggle):
    """Ensures that the Candle will be accessible early on."""
    display_name = "Early Candle"

class RequireCandle(DefaultOnToggle):
    """If enabled, you will be logically expected to have the Candle before going inton any caves.
       This does not include the Parapa cave, as the original game expects you to traverse this cave
       in the dark."""
    display_name = "Candle Logic"

class RequireCross(DefaultOnToggle):
    """If enabled, you will be logically expected to have the Cross before going to Old Kasuto
       or Death Valley."""
    display_name = "Cross Logic"

class KeyShuffle(Choice):
    """Vanilla: All dungeon keys will be found at their vanilla locations.
       Shuffled In Dungeon: Keys will be shuffled amongst their original dungeon checks.
       Keysanity: Keys will be able to be found anywhere.
       Regardless of the option chosen, Keys will only be usable in their respective dungeon."""
    display_name = "Key Shuffle"
    option_vanilla = 0
    option_shuffled_in_dungeon = 1
    option_keysanity = 2
    default = 1

class SpellLocations(Choice):
    """Vanilla: Spells will be found at their normal locations.
       Shuffled: Spells will be randomized amongst all of the Wise Men.
       Anywhere: Spells can be found anywhere."""
    display_name = "Spell Locations"
    option_vanilla = 0
    option_shuffled = 1
    option_anywhere = 2
    default = 2

class EncounterRate(Choice):
    """The rate at which random enemy encounters spawn. """
    display_name = "Encounter Rate"
    option_quarter = 0
    option_half = 1
    option_1x = 2
    option_2x = 3
    default = 1

class DropTable(Choice):
    """Randomizes what can be dropped from enemies.
       Normalized: blue/red jars, 50 pbag, 100 pbag, and 200 pbag
       Full: adds 500 pbag plus Normalized
       High Value: red jar, 200 pbag, 500 pbag"""
    display_name = "Randomize Drop Table"
    option_vanilla = 0
    option_normalized = 1
    option_full = 2
    option_high_value = 3
    default = 1

class RandomizePbagXpRewards(Toggle):
    """Randomizes the xp rewarded by pbags to roughly +-50-67% of vanilla values
       50 pbag: 20, 50, 70, 100
       100 pbag: 50, 70, 100, 200
       200 pbag: 50, 100, 200, 301, 500
       500 pbag: 200, 301, 500, 700, 1000"""
    display_name = "Randomize Pbag XP Rewards"

class RemoveEarlyBoulder(Toggle):
    """Removes the boulder blocking the south part of the western continent."""
    display_name = "Remove Early Boulder"

class StartingLife(Range):
    """What your starting Life level is."""
    display_name = "Starting Life Level"
    range_start = 1
    range_end = 8
    default = 2

class RandomizeLifeEffectiveness(Toggle):
    """Randomizes how effective life levels are by +/- 50% of vanilla values"""
    display_name = "Randomize Life Effectiveness"

class StartingAttack(Range):
    """What your starting Attack level is."""
    display_name = "Starting Attack Level"
    range_start = 1
    range_end = 8
    default = 2

class RandomizeAttackEffectiveness(Toggle):
    """Randomizes how effective attack levels are from 67% to 150% of vanilla values"""
    display_name = "Randomize Life Effectiveness"

class StartingMagic(Range):
    """What your starting Magic level is."""
    display_name = "Starting Magic Level"
    range_start = 1
    range_end = 8
    default = 2

class RandomizeSpellCosts(Toggle):
    """Randomizes how much each spell costs by +/- 50% of vanilla values
       Each spell is randomized independently"""
    display_name = "Randomize Life Effectiveness"

class RandomizeEnemyHealth(Toggle):
    """Randomizes enemy health to roughly +-50% of vanilla values"""
    display_name = "Randomize Enemy Health"

class RandomizeEnemyXpRewards(Toggle):
    """Randomizes enemy xp rewards to roughly +-50% of vanilla values"""
    display_name = "Randomize Enemy XP Rewards"

class RandomizeEnemiesThatStealXp(Toggle):
    """Randomizes which enemies steal XP"""
    display_name = "Randomize Enemies That Steal XP"

class RandomizeWhichEnemiesRequireFire(Toggle):
    """Randomizes which enemies that are immune to swords on East continent and Maze Island"""
    display_name = "Randomize Which Enemies Require Fire"

class Enemizer(Choice):
    """Vanilla: No enemizer, vanilla enemies in all encounters
       Simple: Shuffles enemies by type keeping small enemies separate from large enemies
       Mixed: Shuffles small and large enemies together"""
    display_name = "Enemizer"
    option_vanilla = 0
    option_simple = 1
    option_mixed = 2
    default = 0

class RandomPalaceGraphics(Toggle):
    """Randomizes the color and tiles of each Palace except the Great Palace."""
    display_name = "Random Palace Graphics"

class PalaceRespawn(DefaultOnToggle):
    """If enabled, you will respawn at the current Palace entrance if you continue,
       but not if you save and reset. If disabled, this only applies to the Great Palace."""
    display_name = "Respawn at Palaces"

class StartingLives(Range):
    """How many lives you will start with upon loading the game.
       This value will be permanently increased by one every time you find a
       1-Up Doll."""
    display_name = "Starting Lives"
    range_start = 0
    range_end = 255
    default = 3

class KeepExp(DefaultOnToggle):
    """If enabled, you will retain your EXP after continuing, and it will be saved to your file."""
    display_name = "Keep EXP"

class FastPalace(Toggle):
    """If enabled, most of the Great Palace will be skipped."""
    display_name = "Fast Great Palace"

class BetterBoots(Toggle):
    """If enabled, the water near Saria Town will be changed so that it can be walked on using the Boots."""
    display_name = "Better Boots"

@dataclass
class Z2Options(PerGameCommonOptions):
    required_crystals: RequiredCrystals
    key_shuffle: KeyShuffle
    drop_table: DropTable
    randomize_pbag_xp_rewards: RandomizePbagXpRewards
    spell_locations: SpellLocations
    early_candle: EarlyCandle
    candle_required: RequireCandle
    cross_required: RequireCross
    remove_early_boulder: RemoveEarlyBoulder
    better_boots: BetterBoots
    palace_respawn: PalaceRespawn
    fast_great_palace: FastPalace
    starting_life: StartingLife
    randomize_life_effectiveness: RandomizeLifeEffectiveness
    starting_magic: StartingMagic
    randomize_spell_costs: RandomizeSpellCosts
    starting_attack: StartingAttack
    randomize_attack_effectiveness: RandomizeAttackEffectiveness
    starting_lives: StartingLives
    encounter_rate: EncounterRate
    enemizer: Enemizer
    randomize_enemy_health: RandomizeEnemyHealth
    randomize_enemy_xp_rewards: RandomizeEnemyXpRewards
    randomize_enemies_that_steal_xp: RandomizeEnemiesThatStealXp
    randomize_which_enemies_require_fire: RandomizeWhichEnemiesRequireFire
    keep_exp: KeepExp
    random_tunic_color: RandomTunicColor
    random_palace_graphics: RandomPalaceGraphics

z2_option_groups = [
    OptionGroup("Game Settings", [
        RequiredCrystals
    ]),

    OptionGroup("Item Settings", [
        EarlyCandle,
        KeyShuffle,
        SpellLocations
    ]),

    OptionGroup("Logic Settings", [
        RequireCandle,
        RequireCross,
        RemoveEarlyBoulder,
        BetterBoots
    ]),

    OptionGroup("Convenience Settings", [
        PalaceRespawn,
        FastPalace,
        StartingLives,
        KeepExp,
        EncounterRate
    ]),

    OptionGroup("Starting Stats", [
        StartingAttack,
        StartingMagic,
        StartingLife
    ]),

    OptionGroup("Cosmetic Settings", [
        RandomTunicColor,
        RandomPalaceGraphics
    ]),
]
