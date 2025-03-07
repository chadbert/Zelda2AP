import hashlib
import os
from math import floor

import Utils
import typing
import struct
from worlds.Files import APProcedurePatch, APTokenMixin, APTokenTypes, APPatchExtension
from typing import TYPE_CHECKING, Optional
from logging import warning

from .Enemies import *
from .game_data import world_version, enemy_health, enemy_attribute_tables, enemy_encounter_tables
from .Options import DropTable, EncounterRate, Enemizer

if TYPE_CHECKING:
    from . import Z2World

md5 = "88c0493fb1146834836c0ff4f3e06e45"


class LocalRom(object):

    def __init__(self, file: bytes, name: Optional[str] = None) -> None:
        self.file = bytearray(file)
        self.name = name

    def read_byte(self, offset: int) -> int:
        return self.file[offset]

    def read_bytes(self, offset: int, length: int) -> bytes:
        return self.file[offset:offset + length]

    def write_byte(self, offset: int, value: int) -> None:
        self.file[offset] = value

    def write_bytes(self, offset: int, values) -> None:
        self.file[offset:offset + len(values)] = values

    def get_bytes(self) -> bytes:
        return bytes(self.file)

def prevent_stoning_of_palaces(rom):
    rom.write_bytes(0x47ba, bytearray([0xEA, 0xEA, 0xEA]))
    rom.write_bytes(0x87b3, bytearray([0xEA, 0xEA, 0xEA]))
    rom.write_bytes(0x1e02e, bytearray([0xEA, 0xEA, 0xEA]))

def disable_most_flashing(rom):
    rom.write_bytes(0x47ba, bytearray([0x12, 0x12, 0x12]))
    rom.write_bytes(0x1C9FA, bytearray([0x16]))
    rom.write_bytes(0x1C9FC, bytearray([0x16]))

def alter_encounter_table(world, rom):
    if world.options.encounter_rate == EncounterRate.option_half:
        rom.write_bytes(0x250, bytearray([0x40]))
        rom.write_bytes(0x251, bytearray([0x30]))
        rom.write_bytes(0x252, bytearray([0x30]))
        rom.write_bytes(0x253, bytearray([0x40]))
        rom.write_bytes(0x254, bytearray([0x12]))
        rom.write_bytes(0x255, bytearray([0x06]))
        rom.write_bytes(0x88A, bytearray([0x10]))

def randomize_drop_table(world, rom):
    if world.options.drop_table == DropTable.option_vanilla:
        return

    # Randomize enemy count between drops
    enemy_count = 4 + world.random.randint(0, 4)
    rom.write_bytes(0x1E8B0, bytearray([enemy_count]))

    blue_jar = 0x90
    red_jar = 0x91
    pbag_50 = 0x8a
    pbag_100 = 0x8b
    pbag_200 = 0x8c
    pbag_500 = 0x8d
    # "1up": 0x92, # does not work
    # "key": 0x88 # does not work

    possible_drops = [
        red_jar,
        pbag_200
    ]

    if world.options.drop_table == DropTable.option_high_value:
        possible_drops.append(pbag_500)
        # Adding duplicates of lower value ones in order to not make it ludicrous
        possible_drops.append(pbag_200)
        possible_drops.append(pbag_200)
        possible_drops.append(red_jar)
        possible_drops.append(red_jar)

    else:
        possible_drops.append(blue_jar)
        possible_drops.append(pbag_50)
        possible_drops.append(pbag_100)

        if world.options.drop_table == DropTable.option_full:
            possible_drops.append(pbag_500)

    for i in range(8):
        small_drop = world.random.randint(0, len(possible_drops) - 1)
        large_drop = world.random.randint(0, len(possible_drops) - 1)

        rom.write_bytes(0x1E880 + i, bytearray([possible_drops[small_drop]]))
        rom.write_bytes(0x1E888 + i, bytearray([possible_drops[large_drop]]))

#Shuffles pbag amounts to roughly + or - 66% of vanilla value
def randomize_pbag_amounts(world, rom):
    if world.options.randomize_pbag_xp_rewards:
        rom.write_bytes(0x1e800, bytearray([world.random.randint(5, 9)])) #20 - 100
        rom.write_bytes(0x1e801, bytearray([world.random.randint(7, 11)])) #50 - 301
        rom.write_bytes(0x1e802, bytearray([world.random.randint(9, 13)]))  #100 - 700
        rom.write_bytes(0x1e803, bytearray([world.random.randint(11, 15)]))  #200 - 1000

def randomize_enemy_health(world, rom):
    if not world.options.randomize_enemy_health:
        return

    enemy_health_pool_bank1 = enemy_health["bank1"].copy()
    enemy_health_pool_bank2 = enemy_health["bank2"].copy()
    enemy_health_pool_bank4_0 = enemy_health["bank4_0"].copy()
    enemy_health_pool_bank4_1 = enemy_health["bank4_1"].copy()
    enemy_health_pool_helmethead_gooma = enemy_health["bank4_helm_gooma"].copy()
    enemy_health_pool_bank5 = enemy_health["bank5"].copy()

    new_enemy_health_pool_bank1 = randomize_values(world, enemy_health_pool_bank1)
    rom.write_bytes(0x5434, bytearray(new_enemy_health_pool_bank1))

    new_enemy_health_pool_bank2 = randomize_values(world, enemy_health_pool_bank2)
    rom.write_bytes(0x9434, bytearray(new_enemy_health_pool_bank2))

    new_enemy_health_pool_bank4_0 = randomize_values(world, enemy_health_pool_bank4_0)
    rom.write_bytes(0x11434, bytearray(new_enemy_health_pool_bank4_0))

    new_enemy_health_pool_bank4_1 = randomize_values(world, enemy_health_pool_bank4_1)
    enemy_health_pool_bank4_1[1] = 0xFF
    rom.write_bytes(0x12935, bytearray(new_enemy_health_pool_bank4_1))

    enemy_health_pool_helmethead_gooma = randomize_values(world, enemy_health_pool_helmethead_gooma)
    rom.write_bytes(0x13C86, bytearray(enemy_health_pool_helmethead_gooma))

    new_enemy_health_pool_bank5 = randomize_values(world, enemy_health_pool_bank5)
    # Fix issues
    new_enemy_health_pool_bank5[2] = 0x00
    new_enemy_health_pool_bank5[13] = 0x00
    new_enemy_health_pool_bank5[21] = 0x00
    new_enemy_health_pool_bank5[22] = 0x02
    rom.write_bytes(0x15434, bytearray(new_enemy_health_pool_bank5))

def randomize_enemy_other_attributes(world, rom):
    if not world.options.randomize_enemy_xp_rewards and \
        not world.options.randomize_enemies_that_steal_xp and \
        not world.options.randomize_which_enemies_require_fire:
        print("No enemy attributes randomized")
        return

    # XX.. ....  Palette code
    # ..X. ....  Requires fire
    # ...X ....  Steals exp
    # .... XXXX  Experience code

    # bank1 is Western continent
    # bank2 is Eastern and Maze Island
    # bank3 is towns
    # bank4 is palaces
    # bank5 is GP
    enemy_attributes_bank1 = enemy_attribute_tables["bank1"].copy()
    enemy_attributes_bank2 = enemy_attribute_tables["bank2"].copy()
    enemy_attributes_bank4_0 = enemy_attribute_tables["bank4_0"].copy()
    enemy_attributes_bank4_1 = enemy_attribute_tables["bank4_1"].copy()
    helmethead_gooma = [0xCB, 0xCD]
    enemy_attributes_bank5 = enemy_attribute_tables["bank5"].copy()

    randomize_experience_stealing(world, enemy_attributes_bank1, 5)
    randomize_experience_stealing(world, enemy_attributes_bank2, 5)
    randomize_experience_stealing(world, enemy_attributes_bank4_0, 3)
    randomize_experience_stealing(world, enemy_attributes_bank4_1, 3)
    randomize_experience_stealing(world, enemy_attributes_bank5, 2)

    randomize_sword_immunity(world, enemy_attributes_bank2, 4)

    randomize_enemy_exp_in_bank(world, enemy_attributes_bank1)
    randomize_enemy_exp_in_bank(world, enemy_attributes_bank2)
    randomize_enemy_exp_in_bank(world, enemy_attributes_bank4_0)
    randomize_enemy_exp_in_bank(world, enemy_attributes_bank4_1)
    randomize_enemy_exp_in_bank(world, helmethead_gooma)
    randomize_enemy_exp_in_bank(world, enemy_attributes_bank5)

    # Preventing crashes and strange bugs
    enemy_attributes_bank2[16] = enemy_attribute_tables["bank1"][16] # Elevator

    enemy_attributes_bank1[2] = 0x40 # Don't want doors stealing experience
    enemy_attributes_bank1[6] = 0x90 # unknown enemy that likely should not be changed
    enemy_attributes_bank1[16] = 0x40 # Don't want to break elevators

    enemy_attributes_bank4_0[2] = enemy_attribute_tables["bank4_0"][2] # hidden red jar
    enemy_attributes_bank4_0[5] = enemy_attribute_tables["bank4_0"][5] # falling block generator
    enemy_attributes_bank4_0[6] = enemy_attribute_tables["bank4_0"][6] # falling block
    enemy_attributes_bank4_0[16] = enemy_attribute_tables["bank4_0"][16] # Elevator
    enemy_attributes_bank4_0[17] = enemy_attribute_tables["bank4_0"][17] # Crystal slot
    enemy_attributes_bank4_0[18] = enemy_attribute_tables["bank4_0"][18] # Crystal
    enemy_attributes_bank4_0[19] = enemy_attribute_tables["bank4_0"][19] # Energy ball shooter
    enemy_attributes_bank4_0[20] = enemy_attribute_tables["bank4_0"][20] # Energy ball shooter
    enemy_attributes_bank4_0[29] &= 0xEF # Horsehead - still randomize exp
    enemy_attributes_bank4_0[30] = enemy_attribute_tables["bank4_0"][30] # helmethead / Gooma - still randomize exp
    enemy_attributes_bank4_0[31] = enemy_attribute_tables["bank4_0"][31] # Floating helmet

    enemy_attributes_bank4_1[2] = enemy_attribute_tables["bank4_1"][2]  # hidden red jar
    enemy_attributes_bank4_1[5] = enemy_attribute_tables["bank4_1"][5]  # falling block generator
    enemy_attributes_bank4_1[6] = enemy_attribute_tables["bank4_1"][6]  # falling block
    enemy_attributes_bank4_1[11] = enemy_attribute_tables["bank4_1"][11]  # Fast bubble?
    enemy_attributes_bank4_1[15] = enemy_attribute_tables["bank4_1"][15]  # Crash
    enemy_attributes_bank4_1[16] = enemy_attribute_tables["bank4_1"][16]  # Elevator
    enemy_attributes_bank4_1[17] = enemy_attribute_tables["bank4_1"][17]  # Crystal slot
    enemy_attributes_bank4_1[18] = enemy_attribute_tables["bank4_1"][18]  # Crystal
    enemy_attributes_bank4_1[19] = enemy_attribute_tables["bank4_1"][19]  # Energy ball shooter
    enemy_attributes_bank4_1[20] = enemy_attribute_tables["bank4_1"][20]  # Energy ball shooter
    enemy_attributes_bank4_1[29] &= 0xEF  # Rebonack - still randomize exp
    enemy_attributes_bank4_1[30] &= 0xEF  # Barba - still randomize exp
    enemy_attributes_bank4_1[31] &= 0xEF  # Carock - still randomize exp

    # write attributes
    rom.write_bytes(0x54E8, bytearray(enemy_attributes_bank1))
    rom.write_bytes(0x94e8, bytearray(enemy_attributes_bank2))
    rom.write_bytes(0x114E8, bytearray(enemy_attributes_bank4_0))
    rom.write_bytes(0x129E8, bytearray(enemy_attributes_bank4_1))
    rom.write_bytes(0x13C88, bytearray(helmethead_gooma))

def randomize_experience_stealing(world, enemy_attribute_bank: [], max_number: int):
    if not world.options.randomize_enemies_that_steal_xp:
        return

    # Remove exp stealing from all enemies
    for i in range(len(enemy_attribute_bank)):
        enemy_attribute_bank[i] = enemy_attribute_bank[i] & 0xEF

    print("New enemies that steal experience")
    # Randomize enemies that steal exp, dups are just less enemies getting this annoyance
    for i in range(max_number):
        new_enemy = world.random.randint(0, len(enemy_attribute_bank) - 1)
        print(new_enemy)
        enemy_attribute_bank[new_enemy] = enemy_attribute_bank[new_enemy] | 0x10

    return enemy_attribute_bank

def randomize_sword_immunity(world, enemy_attribute_bank: [], max_number: int):
    if not world.options.randomize_which_enemies_require_fire:
        return

    # Remove sword immunity from all enemies
    for i in range(len(enemy_attribute_bank)):
        enemy_attribute_bank[i] = enemy_attribute_bank[i] & 0xDF

    for i in range(max_number):
        new_enemy = world.random.randint(0, len(enemy_attribute_bank) - 1)
        enemy_attribute_bank[new_enemy] = enemy_attribute_bank[new_enemy] | 0x20

    return enemy_attribute_bank

def randomize_enemy_exp_in_bank(world, enemy_attribute_bank: []):
    if not world.options.randomize_enemy_xp_rewards:
        return

    print("experience codes")
    for i in range(len(enemy_attribute_bank)):
        exp_code = enemy_attribute_bank[i] & 0x0F
        min_exp_code = round(exp_code - exp_code * 0.5)
        max_exp_code = round(exp_code + exp_code * 0.5)
        new_exp_code = world.random.randint(min_exp_code, max_exp_code)

        enemy_attribute_bank[i] = (enemy_attribute_bank[i] & 0xF0) | new_exp_code
        print(exp_code, min_exp_code, max_exp_code, new_exp_code, enemy_attribute_bank[i])

    return enemy_attribute_bank

def randomize_values(world, input_values: []):
    new_values = []
    for value in input_values:
        if value == 0:
            continue
        min_value = value - round(value * 0.5)
        max_value = value + round(value * 0.5)

        new_value = world.random.randint(min_value, max_value)
        print("Enemy: ", value, min_value, max_value)
        if new_value > 0xFF:
            print("limiting value to 0xFF")
            new_value = 0xFF
        elif new_value > max_value:
            print("underflow happened", value, min_value, max_value)
            new_value = 0x01
        new_values.append(new_value)

    return new_values

def randomize_enemy_health_internal(world, rom, start_address, end_address):
    for i in range(start_address, end_address):
        vanilla_health = rom.read_byte(i)
        new_health = world.random.randint(vanilla_health * 0.5, vanilla_health * 1.5)
        if new_health > 255:
            new_health = 255

        print(i)
        print(bytearray([new_health]))
        rom.write_bytes(i, bytearray([new_health]))

# Randomizes the attack effectiveness from 66% to 150% of vanilla per level
def randomize_attack_effectiveness(world, rom):
    if not world.options.randomize_attack_effectiveness:
        return

    print('randomizing attack')
    # address 0x1E67D with 8 bytes
    vanilla_values = [0x02, 0x03, 0x04, 0x06, 0x09, 0x0C, 0x12, 0x18]
    new_values = []
    previous = 0

    for attack in vanilla_values:

        min_attack = attack - round(attack * 0.333)
        max_attack = attack + round(attack * 0.5)

        new_attack = world.random.randint(min_attack, max_attack)

        # Do not allow attack to go down upon leveling up
        if new_attack < previous:
            new_attack = previous

        previous = new_attack
        new_values.append(new_attack)

    #print('vanilla attack effectiveness: ')
    #print(bytearray(vanilla_values))
    #print('Random attack effectiveness: ')
    #print(bytearray(new_values))
    rom.write_bytes(0x1E67D, bytearray(new_values))
    
def randomize_magic_cost(world, rom):
    if not world.options.randomize_spell_costs:
        return

    print("randomizing spells")
    shield_costs = [0x40, 0x30, 0x30, 0x20, 0x20, 0x20, 0x20, 0x20]
    jump_costs = [0x60, 0x50, 0x40, 0x40, 0x28, 0x20, 0x18, 0x10]
    life_costs = [0x8C, 0x8C, 0x78, 0x78, 0x64, 0x64, 0x64, 0x64]
    fairy_costs = [0xA0, 0xA0, 0x78, 0x78, 0x50, 0x50, 0x50, 0x50]
    fire_costs = [0xF0, 0xA0, 0x78, 0x3C, 0x20, 0x20, 0x20, 0x20]
    reflect_costs = [0xF0, 0xF0, 0xA0, 0x60, 0x50, 0x40, 0x30, 0x20]
    spell_costs = [0xF0, 0xE0, 0xC0, 0xA0, 0x60, 0x40, 0x30, 0x20]
    thunder_costs = [0xF0, 0xF0, 0xF0, 0xF0, 0xF0, 0xF0, 0xC8, 0x80]

    #print("shield")
    randomize_spell_cost(world, shield_costs)
    randomize_spell_cost(world, jump_costs)
    randomize_spell_cost(world, life_costs)
    randomize_spell_cost(world, fairy_costs)
    randomize_spell_cost(world, fire_costs)
    randomize_spell_cost(world, reflect_costs)
    randomize_spell_cost(world, spell_costs)
    randomize_spell_cost(world, thunder_costs)

    rom.write_bytes(0xD8B, bytearray(shield_costs))
    rom.write_bytes(0xd93, bytearray(jump_costs))
    rom.write_bytes(0xd9b, bytearray(life_costs))
    rom.write_bytes(0xda3, bytearray(fairy_costs))
    rom.write_bytes(0xdab, bytearray(fire_costs))
    rom.write_bytes(0xdb3, bytearray(reflect_costs))
    rom.write_bytes(0xdbb, bytearray(spell_costs))
    rom.write_bytes(0xdc3, bytearray(thunder_costs))

def randomize_spell_cost(world, costs: []):
    previous_cost = 120

    for i in range(len(costs)):
        cost = costs[i]
        high_part = (cost & 0xF0) >> 4
        low_part = cost & 0x0F
        actual_cost = floor(high_part * 8 + low_part / 2)

        min_cost = actual_cost - round(actual_cost * 0.5)
        max_cost = actual_cost + round(actual_cost * 0.5)

        new_cost = world.random.randint(min_cost, min(max_cost, 120))
        if new_cost > previous_cost:
            #print("new cost is greater than previous cost", new_cost, previous_cost)
            new_cost = previous_cost

        high_part = floor(new_cost / 8) << 4
        low_part = new_cost % 8
        costs[i] = high_part + (low_part * 2)

        #print("vanilla ", actual_cost, " new cost ", new_cost, "mem_value", costs[i])
        previous_cost = new_cost

def randomize_experience_requirements(world, rom):

    attack = [200, 500, 1000, 2000, 3000, 5000, 8000, 9000]
    magic = [100, 300, 700, 1200, 2200, 3500, 6000, 9000]
    life = [50, 150, 400, 800, 1500, 2500, 4000, 9000]

    randomize_exp_internal(world, rom, attack)
    randomize_exp_internal(world, rom, magic)
    randomize_exp_internal(world, rom, life)
    #print("attack exp requirements ", attack)
    #print("magic exp requirements ", magic)
    #print("life exp requirements ", life)

    write_exp_internal(rom, attack, 0x1669)
    write_exp_internal(rom, magic, 0x1671)
    write_exp_internal(rom, life, 0x1679)


def write_exp_internal(rom, values: [], address):
    low_bytes = []
    high_bytes = []
    for i in range(len(values)):
        low_bytes.append(values[i] % 256)
        high_bytes.append(int(values[i] / 256))

    rom.write_bytes(address, bytearray(high_bytes))
    rom.write_bytes(address + 24, bytearray(low_bytes))

    # Update display text
    zero = 0xD0 # First character value
    blank = 0xF4
    tens_offset = 0x7D9
    hundreds_offset = 0x7F1
    thousands_offset = 0x809
    thousands = []
    hundreds = []
    tens = []
    for i in range(len(values)):
        if (values[i] < 1000):
            thousands.append(blank)
        else:
            thousands.append(int(values[i] / 1000) + zero)
        if (values[i] < 100):
            hundreds.append(blank)
        else:
            hundreds.append(int((values[i] % 1000) / 100) + zero)
        tens.append(int((values[i] % 100) / 10) + zero)
    #print("1000s ", bytearray(thousands))
    #print(" 100s ", bytearray(hundreds))
    #print("  10s ", bytearray(tens))

    rom.write_bytes(address + tens_offset, bytearray(tens))
    rom.write_bytes(address + hundreds_offset, bytearray(hundreds))
    rom.write_bytes(address + thousands_offset, bytearray(thousands))

def randomize_exp_internal(world, rom, values: []):
    for i in range(len(values)):
        min_value = values[i] - round(values[i] * .25)
        max_value = values[i] + round(values[i] * .25)

        new_value = world.random.randint(min_value, max_value - 1)

        # make it only a multiple of 10 as the last 0 displayed cannot be changed
        new_value = floor(new_value / 10) * 10
        if new_value > 9999:
            new_value = 9999
        
        values[i] = new_value


def randomize_life_spell_amount(world, rom):
    containers = world.random.randint(1, 5)
    hp = containers * 16
    #print("Life spell effectiveness: ", hp)
    # TODO configure this
    rom.write_bytes(0xE7A, bytearray([hp]))

def shuffle_enemies(world, rom):
    if world.options.enemizer == Enemizer.option_vanilla:
        return

    west_flying_enemies = [moa, ache, acheman, red_deeler, blue_deeler]
    west_generators = [0x0B, 0x0C, 0x0F, 0x1D]
    west_small_enemies = [0x03, 0x04, 0x05, 0x11, 0x12, 0x1C, megmet]
    west_large_enemies = [geldarm, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x1B]

    west_enemy_encounter_bank = enemy_encounter_tables["bank1"].copy()
    randomize_overworld_enemies(world, 112, west_enemy_encounter_bank, west_small_enemies, west_large_enemies,
                                west_flying_enemies, west_generators)
    rom.write_bytes(0x48B2, bytearray(west_enemy_encounter_bank))

    east_flying_enemies = [moa, ache, acheman, red_deeler, blue_deeler, 0x15]
    east_generators = [0x0B, 0x0F, 0x17]
    east_small_enemies = [0x03, 0x04, 0x05, 0x11, 0x12, 0x16]
    east_large_enemies = [0x14, 0x18, 0x19, 0x1A, 0x1B, 0x1C]
    east_enemy_encounter_bank = enemy_encounter_tables["bank2"].copy()
    randomize_overworld_enemies(world, 126, east_enemy_encounter_bank, east_small_enemies,
                                east_large_enemies, east_flying_enemies, east_generators)
    rom.write_bytes(0x88B0, bytearray(east_enemy_encounter_bank))

    #108b0
    palace125_flying_enemies = [moa, blue_deeler]
    palace125_generators = [0x0B, 0x0F, 0x1B] #0x0A - causes scroll lock
    palace125_small_enemies = [0x03, 0x04, 0x11] #0x12 - causes crash
    palace125_large_enemies = [0x0C, 0x18, 0x19, 0x1A, 0x1D, 0x1E, 0x1F, 0x23]
    palace_enemy_bank = enemy_encounter_tables["palaces"].copy()
    randomize_palace_enemies(world, 123, palace_enemy_bank, palace125_small_enemies, palace125_large_enemies,
                             palace125_flying_enemies, palace125_generators)
    rom.write_bytes(0x108B0, bytearray(palace_enemy_bank))

    # Randomizes dripper
    palace125_enemies = palace125_small_enemies + palace125_large_enemies
    dripper_index = world.random.randint(0, len(palace125_enemies) - 1)
    #rom.write_bytes(0x11927, bytearray(palace125_enemies[dripper_index]))

    possible_spell_enemies = [0x3, 0x4, moa, ache, blue_deeler, 0x10, 0x11, 0x12, 0x18, 0x19, 0x1A]
    spell_enemy_index = world.random.randint(0, len(possible_spell_enemies) - 1)
    #rom.write_bytes(0x11EF, bytearray(possible_spell_enemies[spell_enemy_index]))

    gp_flying_enemies = [0x06, 0x14, 0x15, 0x17, 0x1E]
    gp_generators = [0x0B, 0x0C, 0x0F, 0x16]
    gp_small_enemies = [0x03, 0x04, 0x11, 0x12]
    gp_large_enemies = [0x18, 0x19, 0x1A, 0x1D]

def randomize_palace_enemies(world, room_count, encounter_bank: [], small_enemies: [], large_enemies: [], flying_enemies: [], generators: []):
    print("byte count", len(encounter_bank))
    small_and_large_enemies = small_enemies + large_enemies

    current_index = 0
    previous_index = 0
    for encounter_index in range(room_count):
        num_bytes = encounter_bank[current_index]
        print("number of bytes: ", num_bytes)
        current_index += 2
        first_generator = 0x0

        for enemy_index in range(floor(num_bytes / 2) - 1):
            enemy = encounter_bank[current_index] & 0x3F
            page_number = encounter_bank[current_index] & 0xC0

            # mixing small and large
            if enemy in small_and_large_enemies:
                new_enemy_index = world.random.randint(0, len(small_and_large_enemies) - 1)
                new_enemy = small_and_large_enemies[new_enemy_index]
                print("old enemy: ", bytearray([enemy]), "new enemy: ", bytearray([new_enemy]))
                encounter_bank[current_index] = new_enemy + page_number

                if enemy in small_enemies and new_enemy in large_enemies:
                    new_position = move_y_position(encounter_bank[current_index - 1], -16)
                    encounter_bank[current_index - 1] = new_position

            elif enemy in flying_enemies:
                new_enemy_index = world.random.randint(0, len(flying_enemies) - 1)
                new_enemy = flying_enemies[new_enemy_index]
                print("old enemy: ", bytearray([enemy]), "new enemy: ", bytearray([new_enemy]))
                encounter_bank[current_index] = new_enemy + page_number

            elif enemy in generators:
                new_enemy_index = world.random.randint(0, len(generators) - 1)
                new_enemy = generators[new_enemy_index]

                if first_generator != 0x0:
                    new_enemy = first_generator

                first_generator = new_enemy

                print("old generator: ", bytearray([enemy]), "new generator: ", bytearray([new_enemy]))
                encounter_bank[current_index] = new_enemy + page_number

            current_index += 2

        current_index = previous_index + num_bytes
        print("current index: ", current_index)
        previous_index = current_index

    #print("New encounter table")
    #print(bytearray(encounter_bank))
    for i in range(len(encounter_bank)):
        if encounter_bank[i] > 255 or encounter_bank[i] < 0:
            print("index ", i, " is out of range: ", encounter_bank[i])


def randomize_overworld_enemies(world, encounter_count, encounter_bank: [], small_enemies: [], large_enemies: [], flying_enemies: [], generators: []):
    small_and_large_enemies = small_enemies + large_enemies

    print("byte count", len(encounter_bank))

    current_index = 0
    previous_index = 0
    for encounter_index in range(encounter_count):
        num_bytes = encounter_bank[current_index]
        print("number of bytes: ", num_bytes)
        current_index += 2

        for enemy_index in range(floor(num_bytes / 2) - 1):
            enemy = encounter_bank[current_index] & 0x3F
            page_number = encounter_bank[current_index] & 0xC0

            #mixing small and large
            if enemy in small_and_large_enemies:
                new_enemy_index = world.random.randint(0, len(small_and_large_enemies) - 1)
                new_enemy = small_and_large_enemies[new_enemy_index]
                print("old enemy: ", bytearray([enemy]), "new enemy: ", bytearray([new_enemy]))
                encounter_bank[current_index] = new_enemy + page_number

                if enemy in small_enemies and new_enemy in large_enemies and new_enemy != geldarm:
                    new_position = move_y_position(encounter_bank[current_index - 1], -32)
                    encounter_bank[current_index - 1] = new_position
                elif new_enemy == geldarm and enemy != geldarm:
                    new_position = move_y_position(encounter_bank[current_index - 1], -48)
                    encounter_bank[current_index - 1] = new_position
                elif new_enemy == megmet and enemy != megmet:
                    new_position = move_y_position(encounter_bank[current_index - 1], -16)
                    encounter_bank[current_index - 1] = new_position

            elif enemy in flying_enemies:
                new_enemy_index = world.random.randint(0, len(flying_enemies) - 1)
                new_enemy = flying_enemies[new_enemy_index]
                print("old enemy: ", bytearray([enemy]), "new enemy: ", bytearray([new_enemy]))
                encounter_bank[current_index] = new_enemy + page_number

                if new_enemy in [ache, acheman, red_deeler, blue_deeler]:
                    y_pos = 0
                    x_pos = encounter_bank[current_index - 1] & 0x0F
                    encounter_bank[current_index - 1] = y_pos + x_pos

            elif enemy in generators:
                new_enemy_index = world.random.randint(0, len(generators) - 1)
                new_enemy = generators[new_enemy_index]
                print("old enemy: ", bytearray([enemy]), "new enemy: ", bytearray([new_enemy]))
                encounter_bank[current_index] = new_enemy + page_number

            current_index += 2

        current_index = previous_index + num_bytes
        print("current index: ", current_index)
        previous_index = current_index


    #print("New encounter table")
    #print(bytearray(encounter_bank))
    for i in range(len(encounter_bank)):
        if encounter_bank[i] > 255 or encounter_bank[i] < 0:
            print("index ", i, " is out of range: ", encounter_bank[i])


def move_y_position(position_byte, y_position_delta):
    y_pos = position_byte & 0xF0
    x_pos = position_byte & 0x0F
    if y_pos > (y_position_delta * -1):
        y_pos += y_position_delta
    print("input: ", position_byte, "y: ", y_pos, "x: ", x_pos, " together: ",y_pos + x_pos)
    return y_pos + x_pos

def patch_rom(world, rom, player: int):
    prevent_stoning_of_palaces(rom)
    #disable_most_flashing(rom)

    if world.options.random_tunic_color:
        shield_color = world.random.randint(0x10, 0x3E)
        tunic_color = world.random.randint(0x10, 0x3E)

        rom.write_bytes(0x00E8E, bytearray([shield_color])) #Shield palette
        rom.write_bytes(0x040B1, bytearray([tunic_color])) # Normal palette
        rom.write_bytes(0x040C1, bytearray([tunic_color])) # Normal palette
        rom.write_bytes(0x040D1, bytearray([tunic_color])) # Normal palette
        rom.write_bytes(0x040D1, bytearray([tunic_color])) # Normal palette
        rom.write_bytes(0x17C1B, bytearray([tunic_color])) # File select
        rom.write_bytes(0x1C466, bytearray([tunic_color])) # Loading
        rom.write_bytes(0x1C47E, bytearray([tunic_color])) # Map palette
        rom.write_bytes(0xC0B1, bytearray([tunic_color]))
        rom.write_bytes(0xC0C1, bytearray([tunic_color]))
        rom.write_bytes(0xC0D1, bytearray([tunic_color]))
        rom.write_bytes(0xC0E1, bytearray([tunic_color]))
        rom.write_bytes(0xC0F1, bytearray([tunic_color]))
        rom.write_bytes(0x100B1, bytearray([tunic_color]))
        rom.write_bytes(0x100C1, bytearray([tunic_color]))
        rom.write_bytes(0x100D1, bytearray([tunic_color]))
        rom.write_bytes(0x100E1, bytearray([tunic_color]))
        rom.write_bytes(0x80B1, bytearray([tunic_color]))
        rom.write_bytes(0x80C1, bytearray([tunic_color]))
        rom.write_bytes(0x80D1, bytearray([tunic_color]))
        rom.write_bytes(0x80E1, bytearray([tunic_color]))

    if world.options.random_palace_graphics:
        for i in range(6):
            base_color = world.random.randint(0x00, 0x0C)
            secondary_color = base_color + 0x20
            if base_color >= 0x10:
                tertiary_color = base_color - 0x10
            else:
                tertiary_color = 0x0F
            rom.write_bytes(0x10486 + (16 * i), bytearray([base_color, secondary_color]))
            rom.write_bytes(0x13F16 + (16 * i), bytearray([base_color, secondary_color]))
            rom.write_bytes(0x13F05 + (16 * i), bytearray([tertiary_color]))
            rom.write_bytes(0x13F19 + (16 * i), bytearray([base_color]))

        palace_tilesets = [0, 1, 2, 5, 6, 7, 8]
        base_tilesets = palace_tilesets.copy()
        world.random.shuffle(palace_tilesets)
        for i in range(9):
            rom.copy_bytes(0x29650 + (i * 0x2000), 0xC0, 0x3AB00 + (i * 0xC0)) # Bricks

        for i in range(9):
            rom.copy_bytes(0x298F0 + (i * 0x2000), 0x40, 0x3B1C0 + (i * 0x40)) # Pillar head

        for i in range(9):
            rom.copy_bytes(0x29A60 + (i * 0x2000), 0x20, 0x3B400 + (i * 0x20)) # Pillar Body

        for index, tileset in enumerate(base_tilesets):
            rom.copy_bytes(0x3AB00 + (palace_tilesets[index] * 0xC0), 0xC0, 0x29650 + (tileset * 0x2000))
            rom.copy_bytes(0x3B1C0 + (palace_tilesets[index] * 0x40), 0x40, 0x298F0 + (tileset * 0x2000))
            rom.copy_bytes(0x3B400 + (palace_tilesets[index] * 0x20), 0x20, 0x29A60 + (tileset * 0x2000))

    rom.write_bytes(0x17B10, bytearray([world.options.required_crystals.value]))
    rom.write_bytes(0x17AF3, bytearray([world.options.starting_attack.value]))
    rom.write_bytes(0x17AF4, bytearray([world.options.starting_magic.value]))
    rom.write_bytes(0x17AF5, bytearray([world.options.starting_life.value]))
    rom.write_bytes(0x2B70, bytearray([world.options.palace_respawn.value]))
    rom.write_bytes(0x2B70, bytearray([world.options.palace_respawn.value]))
    rom.write_bytes(0x17DB3, bytearray([world.options.starting_lives.value]))

    if world.options.fast_great_palace:
        rom.write_bytes(0x1472C, bytearray([0xAA]))
        rom.write_bytes(0x147D5, bytearray([0x03]))

    if world.options.keep_exp:
        rom.write_bytes(0x2C40, bytearray([0x01]))

    if world.options.remove_early_boulder:
        rom.write_bytes(0x05199, bytearray([0x09])) #Remove the boulder blocking the west coast

    if world.options.better_boots:
        rom.write_bytes(0x052F0, bytearray([0x7D]))
        rom.write_bytes(0x052FE, bytearray([0xFD]))
        rom.write_bytes(0x052F3, bytearray([0xFD]))
        rom.write_bytes(0x052E4, bytearray([0x7D]))
        rom.write_bytes(0x052F4, bytearray([0x0D]))
        rom.write_bytes(0x052FF, bytearray([0xBD]))
        rom.write_bytes(0x05309, bytearray([0x3D]))
        rom.write_bytes(0x0530B, bytearray([0xFD]))
        rom.write_bytes(0x05315, bytearray([0xBD]))
        rom.write_bytes(0x0531E, bytearray([0xAD]))
        rom.write_bytes(0x05327, bytearray([0xAD]))
        rom.write_bytes(0x05330, bytearray([0x9D]))
        rom.write_bytes(0x0533B, bytearray([0x8D]))
        rom.write_bytes(0x052CB, bytearray([0x1D]))
        rom.write_bytes(0x05277, bytearray([0x2D]))
        rom.write_bytes(0x05281, bytearray([0x1D]))
        rom.write_bytes(0x0528B, bytearray([0x1D]))
        rom.write_bytes(0x05294, bytearray([0x2D]))
        rom.write_bytes(0x0529E, bytearray([0x9D]))
        rom.write_bytes(0x052A0, bytearray([0x0D]))
        rom.write_bytes(0x052B5, bytearray([0x3D]))
        rom.write_bytes(0x052AA, bytearray([0x3D]))
        rom.write_bytes(0x052C0, bytearray([0x2D]))

    randomize_pbag_amounts(world, rom)
    randomize_drop_table(world, rom)
    randomize_enemy_health(world, rom)
    randomize_enemy_other_attributes(world, rom)
    randomize_attack_effectiveness(world, rom)
    randomize_magic_cost(world, rom)
    randomize_life_spell_amount(world, rom)
    shuffle_enemies(world, rom)
    alter_encounter_table(world, rom)
    randomize_experience_requirements(world, rom)

    #rom.write_bytes(0x48B0, bytearray([0x01, 0x01, 0x03, 0x7A, 0x52, 0x01, 0x0B, 0x6F, 0x05, 0x72, 0x45, 0x75, 0x5C, 0x7A, 0x5F, 0x77, 0x95, 0x01, 0x0B]))
    #rom.write_bytes(0x4959, bytearray([0x0F]))
    #rom.write_bytes(0x495B, bytearray([0x18]))
    #rom.write_bytes(0x495E, bytearray([0x15]))
 #   rom.write_bytes(0x48CE, bytearray([0x06, 0x09,0x0A, 0x0D, 0x0E]))
    
    rom.write_bytes(0x3A2B0, world.world_version.encode("ascii"))
    rom.write_bytes(0x3A2E0, bytearray([world.options.encounter_rate.value]))


    from Main import __version__
    rom.name = bytearray(f'ZELDA2AP{__version__.replace(".", "")[0:3]}_{player}_{world.multiworld.seed:11}\0', "utf8")[:21]
    rom.name.extend([0] * (21 - len(rom.name)))
    rom.write_bytes(0x3A290, rom.name)

    player_name_length = 0
    for i, byte in enumerate(world.multiworld.player_name[player].encode("utf-8")):
        rom.write_byte(0x3A2C1 + i, byte)
        player_name_length += 1
    rom.write_byte(0x3A2C0, player_name_length)

    rom.write_file("token_patch.bin", rom.get_token_binary())


class Z2ProcPatch(APProcedurePatch, APTokenMixin):
    hash = md5
    game = "Zelda II: The Adventure of Link"
    patch_file_ending = ".apz2"
    result_file_ending = ".nes"
    name: bytearray
    procedure = [
        ("apply_bsdiff4", ["z2_base.bsdiff4"]),
        ("apply_tokens", ["token_patch.bin"]),
        ("repoint_vanilla_tables", [])
    ]

    @classmethod
    def get_source_data(cls) -> bytes:
        return get_base_rom_bytes()

    def write_byte(self, offset, value):
        self.write_token(APTokenTypes.WRITE, offset, value.to_bytes(1, "little"))

    def write_bytes(self, offset, value: typing.Iterable[int]):
        self.write_token(APTokenTypes.WRITE, offset, bytes(value))
    
    def copy_bytes(self, source, amount, destination):
        self.write_token(APTokenTypes.COPY, destination, (amount, source))


class Z2PatchExtensions(APPatchExtension):
    game = "Zelda II: The Adventure of Link"

    @staticmethod
    def repoint_vanilla_tables(caller: APProcedurePatch, rom: LocalRom) -> bytes:
        rom = LocalRom(rom)
        version_check = rom.read_bytes(0x3A2B0, 16)
        version_check = version_check.split(b'\xFF', 1)[0]
        version_check_str = version_check.decode("ascii")
        client_version = world_version
        if client_version != version_check_str and version_check_str != "":
            raise Exception(f"Error! Patch generated on Zelda II APWorld version {version_check_str} doesn't match client version {client_version}! " +
                            f"Please use Zelda II APWorld version {version_check_str} for patching.")
        #multipliers = [2.5, 2, 1, 0.5, 0.3]
        #encounter_rate = multipliers[int.from_bytes(rom.read_bytes(0x3A2E0, 1))]
        #print(encounter_rate)
        #enemy_timer_table = list(rom.read_bytes(0x250, 6))
        #for timer in enemy_timer_table:
        #    print(hex(int(timer * encounter_rate)))

        return rom.get_bytes()

header = b"\x4E\x45\x53\x1A\x08\x10\x12\x00\x00\x00\x00\x00\x00\x00\x00\x00"


def read_headerless_nes_rom(rom: bytes) -> bytes:
    if rom[:4] == b"NES\x1A":
        return rom[16:]
    else:
        return rom


def get_base_rom_bytes(file_name: str = "") -> bytes:
    base_rom_bytes = getattr(get_base_rom_bytes, "base_rom_bytes", None)
    if not base_rom_bytes:
        file_name = get_base_rom_path(file_name)
        base_rom_bytes = read_headerless_nes_rom(bytes(open(file_name, "rb").read()))

        basemd5 = hashlib.md5()
        basemd5.update(base_rom_bytes)
        rom_hash = basemd5.hexdigest
        if basemd5.hexdigest() != md5:
            print(basemd5.hexdigest())
            raise Exception('Supplied Base Rom does not match known MD5 for US(1.0) release. '
                            'Get the correct game and version, then dump it')
        headered_rom = bytearray(base_rom_bytes)
        headered_rom[0:0] = header
        setattr(get_base_rom_bytes, "base_rom_bytes", bytes(headered_rom))
        return bytes(headered_rom)
    return base_rom_bytes


def get_base_rom_path(file_name: str = "") -> str:
    options: Utils.OptionsType = Utils.get_options()
    if not file_name:
        file_name = options["zelda2_options"]["rom_file"]
    if not os.path.exists(file_name):
        file_name = Utils.user_path(file_name)
    return file_name


# Fix hint text, I have a special idea where I can give it info on a random region
