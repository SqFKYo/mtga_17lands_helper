# -*- coding: utf-8 -*-

from collections import defaultdict, namedtuple
import json
from operator import attrgetter
from time import sleep

import requests

# AKR ChordOCalls
DATA_SOURCE = r'https://www.17lands.com/card_tiers/data/638b3c8483804afa878db3b7edc638f8'
PLAYER_LOG = r'C:\Users\sqfky\AppData\LocalLow\Wizards Of The Coast\MTGA\Player.log'
VALUE_MAP = {
    'A+': 10,
    'A': 10,
    'A-': 10,
    'B+': 9,
    'B': 8,
    'B-': 7,
    'C+': 6,
    'C': 5,
    'C-': 4,
    'D+': 3,
    'D': 2,
    'D-': 1,
    'F': 0,
    'SB': 0,
    'TBD': 0,
}


DraftCard = namedtuple("DraftCard", "name rarity color tier cmc")


class DraftHelper:
    def __init__(self):
        self.tiers = defaultdict(lambda: DraftCard("Unknown", "", "", -1, ""))

    def get_draft_choices(self, line):
        """Gets the most recent list of card_ids available in a draft"""
        if "Draft.Notify" not in line:
            return
        card_ids = json.loads(line.split("Draft.Notify")[1])["PackCards"]
        cards = [self.tiers[int(card_id)] for card_id in card_ids.split(',')]
        pick_order = sorted(cards, key=attrgetter('tier'), reverse=True)
        print("*"*36)
        for card in pick_order:
            print(f"{card.name}, {card.tier}, {card.rarity}")

    def parse_tiers(self, to_parse):
        """Parses raw json data into dict where card_id pulls the other data"""
        for card in to_parse:
            self.tiers[card["card_id"]] = DraftCard(card["name"],
                                                    card["rarity"],
                                                    card["color"],
                                                    VALUE_MAP[card["tier"]],
                                                    card["cmc"])


if __name__ == '__main__':
    helper = DraftHelper()

    response = requests.get(DATA_SOURCE)
    helper.parse_tiers(response.json())

    with open(PLAYER_LOG, 'rb') as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if line:
                helper.get_draft_choices(line)
            sleep(0.5)