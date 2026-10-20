from dataclasses import FrozenInstanceError
import unittest
from wow_oreacle.mined_ore import MinedOre, OreQuality, OreType


class TestMinedOre(unittest.TestCase):
    def test_mined_ore_initialization(self):
        item = MinedOre(OreType.COPPER, OreQuality.SILVER, 25)
        self.assertIsInstance(item, MinedOre)
        self.assertEqual(item.ore, OreType.COPPER)
        self.assertEqual(item.quality, OreQuality.SILVER)
        self.assertEqual(item.amount, 25)

    def test_mined_ore_invalid_ore_type(self):
        with self.assertRaises(TypeError):
            MinedOre(ore="COPPER", quality=OreQuality.BRONZE, amount=15)

    def test_mined_ore_invalid_ore_quality(self):
        with self.assertRaises(TypeError):
            MinedOre(ore=OreType.COPPER, quality="good", amount=15)

    def test_mined_ore_invalid_amount_type(self):
        with self.assertRaises(TypeError):
            MinedOre(ore=OreType.COPPER, quality=OreQuality.BRONZE, amount="15")
        with self.assertRaises(TypeError):
            MinedOre(ore=OreType.COPPER, quality=OreQuality.BRONZE, amount=12.5)
        with self.assertRaises(TypeError):
            MinedOre(ore=OreType.COPPER, quality=OreQuality.BRONZE, amount=True)

    def test_mined_ore_invalid_amount(self):
        with self.assertRaises(ValueError):
            MinedOre(ore=OreType.COPPER, quality=OreQuality.GOLD, amount=-15)

    def test_mined_ore_valid_amount_zero(self):
        item = MinedOre(ore=OreType.COPPER, quality=OreQuality.GOLD, amount=0)
        self.assertEqual(item.amount, 0)

    def test_mined_ore_immutable(self):
        item = MinedOre(ore=OreType.SILVER, quality=OreQuality.SILVER, amount=200)
        with self.assertRaises(FrozenInstanceError):
            item.amount = 20
