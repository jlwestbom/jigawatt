#!/usr/bin/python3
# Copyright 2017 Nate Bogdanowicz, Julia Westbom

from enum import Enum
from attr import attrs, attrib


class Style(Enum):
    Built = 0
    Stirred = 1
    Shaken = 2


@attrs
class Liquid:
    name = attrib()
    abv = attrib()
    sugar = attrib()
    acid = attrib()


@attrs
class Pour:
    liquid = attrib()
    ounces = attrib()


class Drink:
    def __init__(self, name, pours, style):
        self.name = name
        self.pours = [mk_pour(*args) for args in pours]

        tot_alc = sum((p.ounces*p.liquid.abv for p in self.pours))
        tot_sug = sum((p.ounces*p.liquid.sugar for p in self.pours))
        tot_acd = sum((p.ounces*p.liquid.acid for p in self.pours))

        self.start_ounces = sum((pour.ounces for pour in self.pours))
        self.start_abv = tot_alc / self.start_ounces
        self.start_sugar = tot_sug / self.start_ounces
        self.start_acid = tot_acd / self.start_ounces

        if style == Style.Stirred:
            dilution_ratio = -1.21 * self.start_abv**2 + 1.246 * self.start_abv + 0.145
        elif style == Style.Shaken:
            dilution_ratio = 1.567 * self.start_abv**2 + 1.742 * self.start_abv + 0.203
        else:
            raise NotImplementedError

        water_ounces = self.start_ounces * dilution_ratio

        self.ounces = self.start_ounces + water_ounces
        self.abv = tot_alc / self.ounces
        self.sugar = tot_sug / self.ounces
        self.acid = tot_acd / self.ounces


tups = [
    ('Lairds Applejack', .50, .00, .00),
    ('Cointreau', .40, .25, .00),
    ('Lemon Juice', .00, .016, .06),
    ('Simple Syrup', .00, .615, .00),
]

liquids = {tup[0]:Liquid(*tup) for tup in tups}


def mk_pour(name, ounces):
    liquid = liquids[name]
    return Pour(liquid, ounces)


drink = Drink('Jack Rose',
              [('Lairds Applejack', 2.00),
               ('Simple Syrup', 0.75),
               ('Lemon Juice', 0.75)],
              Style.Shaken)
