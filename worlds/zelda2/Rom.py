import hashlib
import os
import Utils
import typing
import struct
from worlds.Files import APProcedurePatch, APTokenMixin, APTokenTypes, APPatchExtension
from typing import TYPE_CHECKING, Optional
from logging import warning
from .game_data import world_version

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

def randomize_drop_table(world, rom):
    # TODO: Add configuration for this
    possible_drops = [
        0x90, #blue jar
        0x91, #red jar
        0x8a, #50 pbag
        0x8b, #100 pbag
        0x8c, #200 pbag
        0x8d, #500 pbag
        0x92, #1up
        0x88  #key
    ]

    for i in range(8):
        small_drop = world.random.randint(0, len(possible_drops) - 1)
        large_drop = world.random.randint(0, len(possible_drops) - 1)


        rom.write_bytes(0x1E880 + i, bytearray([possible_drops[small_drop]]))
        rom.write_bytes(0x1E888 + i, bytearray([possible_drops[large_drop]]))

#Shuffles pbag amounts to roughly + or - 66% of vanilla value
def randomize_pbag_amounts(world, rom):
    # TODO: shuffle pbag amounts option
    rom.write_bytes(0x1e800, bytearray([world.random.randint(5, 9)])) #20 - 100
    rom.write_bytes(0x1e801, bytearray([world.random.randint(7, 11)])) #50 - 300
    rom.write_bytes(0x1e802, bytearray([world.random.randint(9, 13)]))  #100 - 700
    rom.write_bytes(0x1e803, bytearray([world.random.randint(11, 15)]))  #200 - 1000

def randomize_enemy_health(world, rom):
    # TODO config value
    enemy_health_pool_bank1 = [
        0x03, 0x03, 0x03, 0x08, 0x03, 0x00, 0x00, 0x08,
        0x02, 0x02, 0x03, 0x04, 0x03, 0x03, 0x04, 0x04,
        0x00, 0x04, 0x0C, 0x12, 0x12, 0x18, 0x0C, 0x0E,
        0x12, 0x04, 0x03, 0x03, 0x04, 0x08, 0x00, 0x02
    ]

    enemy_health_pool_bank2 = [
        0x03, 0x04, 0x04, 0x30, 0x08, 0x00, 0x00, 0x08,
        0x02, 0x02, 0x0C, 0x0C, 0x08, 0x08, 0x0C, 0x0C,
        0x00, 0x18, 0x10, 0x10, 0x08, 0x30, 0x20, 0x30,
        0x20, 0x38, 0x01
    ]

    new_enemy_health_pool_bank1 = randomize_values(world, enemy_health_pool_bank1)
    rom.write_bytes(0x5434, bytearray(new_enemy_health_pool_bank1))

    new_enemy_health_pool_bank2 = randomize_values(world, enemy_health_pool_bank2)
    rom.write_bytes(0x9434, bytearray(new_enemy_health_pool_bank2))
    #randomize_enemy_health_internal(world, rom, 0x5434, 0x5453)
    #randomize_enemy_health_internal(world, rom, 0x9434, 0x944E)
    #randomize_enemy_health_internal(world, rom, 0x11435, 0x11435)
    #randomize_enemy_health_internal(world, rom, 0x11437, 0x11454)
    #randomize_enemy_health_internal(world, rom, 0x13C86, 0x13C87)
    #randomize_enemy_health_internal(world, rom, 0x15434, 0x15438)
    #randomize_enemy_health_internal(world, rom, 0x15440, 0x15443)
    #randomize_enemy_health_internal(world, rom, 0x15445, 0x1544B)
    #randomize_enemy_health_internal(world, rom, 0x1544E, 0x1544E)
    #randomize_enemy_health_internal(world, rom, 0x12935, 0x12935)
    #randomize_enemy_health_internal(world, rom, 0x12937, 0x12954)

def randomize_enemy_other_attributes(world, rom):
    # XX.. ....  Palette code
    # ..X. ....  Requires fire
    # ...X ....  Steals exp
    # .... XXXX  Experience code

    # bank1 is Western continent
    # bank2 is Eastern and Maze Island

    # All enemies here start without requiring fire and stealing exp
    # These will be randomized to different enemies
    enemy_attributes_bank1 = [
        0xC2, 0xC1, 0x81, 0x84, 0xC2, 0x80, 0x80, 0x84,
        0x00, 0x00, 0x81, 0xC2, 0x02, 0x82, 0x84, 0x84,
        0x40, 0x44, 0x85, 0xC5, 0x48, 0x89, 0x45, 0x85,
        0xC6, 0xC2, 0x00, 0x41, 0xC3, 0x83, 0x00, 0x41,
        0x02
    ]

    enemy_attributes_bank2 = [
        0xC3, 0xC1, 0x81, 0xD7, 0xC4, 0x80, 0x90, 0x84,
        0x10, 0x10, 0x83, 0xC4, 0x10, 0x93, 0xC5, 0xC5,
        0x40, 0xE7, 0x85, 0xC4, 0xC7, 0xE7, 0xCA, 0x89,
        0x4A, 0xCB, 0x87
    ]

    randomize_experience_stealing(world, enemy_attributes_bank1, 5)
    randomize_experience_stealing(world, enemy_attributes_bank2, 5)

    randomize_enemy_exp_in_bank(world, enemy_attributes_bank1)
    randomize_enemy_exp_in_bank(world, enemy_attributes_bank2)

    rom.write_bytes(0x54E8, bytearray(enemy_attributes_bank1))
    rom.write_bytes(0x94e8, bytearray(enemy_attributes_bank2))
    # 0x54E8; i < 0x54ED
    # 0x54EF; i < 0x54F8
    # 0x54F9; i < 0x5508

def randomize_experience_stealing(world, enemy_attribute_bank: [], max_number: int):
    print("New enemies that steal experience")
    # Randomize enemies that steal exp, dups are just less enemies getting this annoyance
    for i in range(max_number):
        new_enemy = world.random.randint(0, len(enemy_attribute_bank) - 1)
        print(new_enemy)
        if (new_enemy != 16):  # 16 is an elevator
            enemy_attribute_bank[new_enemy] = enemy_attribute_bank[new_enemy] | 0x10

    return enemy_attribute_bank

def randomize_enemy_exp_in_bank(world, enemy_attribute_bank: []):
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
        min_value = value - round(value * 0.5)
        max_value = value + round(value * 0.5)
        print(min_value, max_value);
        new_values.append(world.random.randint(min_value, max_value))

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
    print('randomizing attack')
    # address 0x1E67D with 8 bytes

    vanilla_values = [0x02, 0x03, 0x04, 0x06, 0x09, 0x0C, 0x12, 0x18]
    new_values = []
    previous = 0
    new_attack = 0

    for attack in vanilla_values:

        min_attack = attack - round(attack * 0.333)
        max_attack = attack + round(attack * 0.5)

        new_attack = world.random.randint(min_attack, max_attack)

        # Do not allow attack to go down upon leveling up
        if new_attack < previous:
            new_attack = previous

        previous = new_attack
        new_values.append(new_attack)

    print('vanilla attack effectiveness: ')
    print(bytearray(vanilla_values))
    print('Random attack effectiveness: ')
    print(bytearray(new_values))
    rom.write_bytes(0x1E67D, bytearray(new_values))

def randomize_life_spell_amount(world, rom):
    containers = world.random.randint(1, 5)
    hp = containers * 16
    print("Life spell effectiveness: ", hp)
    # TODO configure this
    rom.write_bytes(0xE7A, bytearray([hp]))

def patch_rom(world, rom, player: int):

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

        #for i in range(9):
         #   rom.copy_bytes(0x298F0 + (i * 0x2000), 0x40, 0x3B1C0 + (i * 0x40)) # Pillar head

       # for i in range(9):
        #    rom.copy_bytes(0x29A60 + (i * 0x2000), 0x20, 0x3B400 + (i * 0x20)) # Pillar Body

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

    # TODO: Add option for these
    randomize_pbag_amounts(world, rom)
    randomize_drop_table(world, rom)
    randomize_enemy_health(world, rom)
    randomize_enemy_other_attributes(world, rom)
    randomize_attack_effectiveness(world, rom)
    randomize_life_spell_amount(world, rom)
    
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
        multipliers = [2.5, 2, 1, 0.5, 0.3]
        encounter_rate = multipliers[int.from_bytes(rom.read_bytes(0x3A2E0, 1))]
        print(encounter_rate)
        enemy_timer_table = list(rom.read_bytes(0x250, 6))
        for timer in enemy_timer_table:
            print(hex(int(timer * encounter_rate)))

        #half encounter rate
        rom.write_bytes(0x250, bytearray([0x40]))
        rom.write_bytes(0x251, bytearray([0x30]))
        rom.write_bytes(0x252, bytearray([0x30]))
        rom.write_bytes(0x253, bytearray([0x40]))
        rom.write_bytes(0x254, bytearray([0x12]))
        rom.write_bytes(0x255, bytearray([0x06]))

        rom.write_bytes(0x88A, bytearray([0x10]))
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
