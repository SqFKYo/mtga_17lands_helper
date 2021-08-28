# -*- coding: utf-8 -*-

from collections import Counter, defaultdict, namedtuple
import json
from operator import attrgetter
from time import sleep

from colorama import Back, Fore, Style
import requests

COLORS = True
if COLORS:
    COLOR_MAP = {
        'W': Fore.LIGHTWHITE_EX,
        'U': Fore.LIGHTCYAN_EX,
        'B': f"{Fore.BLACK}{Back.WHITE}",
        'R': Fore.LIGHTRED_EX,
        'G': Fore.GREEN,
        'L': Fore.MAGENTA,
        'C': Fore.MAGENTA,
        'M': Fore.LIGHTYELLOW_EX,
    }
    END_FORMAT = Style.RESET_ALL
else:
    COLOR_MAP = {
        'W': '',
        'U': '',
        'B': '',
        'R': '',
        'G': '',
        'L': '',
        'C': '',
        'M': '',
    }
    END_FORMAT = ''

# AFR ChordOCalls
# DATA_SOURCE = r'https://www.17lands.com/card_tiers/data/1d901171375f4cff9834c751667c4254'
# AKR ChordOCalls
# DATA_SOURCE = r'https://www.17lands.com/card_tiers/data/638b3c8483804afa878db3b7edc638f8'
# KLR ChordOCalls
# DATA_SOURCE = r'https://www.17lands.com/card_tiers/data/c63f7ddf532a44fe9ef142acc1df650b'
# KHM ChordOCalls
# DATA_SOURCE = r'https://www.17lands.com/card_tiers/data/69638dc98022443a9716300958e5fe9f'
# IKO ChordOCalls
DATA_SOURCE = r'https://www.17lands.com/card_tiers/data/db593297907e41af93eedd994e26da28'
PLAYER_LOG = r'C:\Users\sqfky\AppData\LocalLow\Wizards Of The Coast\MTGA\Player.log'
SHOW_PICKS = True
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
        if b"Draft.Notify" in line:
            card_ids = json.loads(line.split(b"Draft.Notify")[1])["PackCards"]
            cards = [self.tiers[int(card_id)] for card_id in card_ids.split(',')]
        elif b"Draft.DraftStatus" in line and b"payload" in line:
            _, tail = line.split(b'Draft.DraftStatus')
            jsonified = json.loads(tail)
            card_ids = jsonified["payload"]["DraftPack"]
            cards = [self.tiers[int(card_id)] for card_id in card_ids]
        elif b"DraftStatus" in line and b"PickNext" in line:
            try:
                line = line.replace(b'\\', b"")
                line = line.replace(b'\"{', b"{")
                line = line.replace(b'\"}', b"}")
                jsonfied = json.loads(line)
            except json.decoder.JSONDecodeError:
                # WotC stupid new format workaround
                card_ids = line.split(b'DraftPack')[1].split(b'PickedCards')[0].split(b'[')[1].split(b']')[0].split(b',')
                cards = [self.tiers[int(card_id.strip(b'\"'))] for card_id in card_ids]
            else:
                card_ids = jsonfied['Payload']['DraftPack']
                cards = [self.tiers[int(card_id)] for card_id in card_ids]
        elif b"CourseId" in line and b"CardPool" in line:
            self.print_pool(line)
            return
        else:
            return

        pick_order = sorted(cards, key=attrgetter('tier'), reverse=True)
        print("*"*36)
        for card in pick_order:
            try:
                print(f"{COLOR_MAP[card.color]}{card.name}, {card.tier}, {card.rarity}{END_FORMAT}")
            except KeyError:
                print(f"{card.name}, {card.tier}, {card.rarity}")

    def get_pick(self, line):
        if b'BotDraft_DraftPick' in line and b'CardId' in line:
            card_id = int(line.split(b'CardId')[1].split(b',')[0].split(b'\"')[2].replace(b"\\", b""))
        elif b'Event_PlayerDraftMakePick' in line and b'GrpId' in line:
            card_id = int(line.split(b'GrpId')[1].split(b',')[0].split(b':')[1])
        else:
            return
        card = self.tiers[card_id]
        print(f"You picked: {COLOR_MAP[card.color]}{card.name}, {card.tier}, {card.rarity}{END_FORMAT}")

    def parse_tiers(self, to_parse):
        """Parses raw json data into dict where card_id pulls the other data"""
        for card in to_parse:
            self.tiers[card["card_id"]] = DraftCard(card["name"],
                                                    card["rarity"],
                                                    card["color"],
                                                    VALUE_MAP[card["tier"]],
                                                    card["cmc"])

    def print_pool(self, line):
        jsonfied = json.loads(line)
        try:
            jsonfied = jsonfied['Courses']
        except KeyError:
            # Already in Courses structure
            pass
        try:
            card_ids = jsonfied[2]['CardPool']
        except TypeError:
            # Non-draft event?
            print('Actually hit the Non-draft event? clause. Weird.')
            return
        card_pool = Counter(card_ids)
        if not card_pool:
            return
        card_pool = {self.tiers[key]: value for key, value in card_pool.items()}
        build_order = sorted(card_pool.items(), key=lambda x: x[0][3], reverse=True)
        print('\nStarting draft tiers:')
        for card, amount in build_order:
            print(f"{COLOR_MAP[card.color]}{amount:>2} {card.name}, {card.tier}{END_FORMAT}")
        print('Ending draft tiers\n')


if __name__ == '__main__':
    helper = DraftHelper()

    response = requests.get(DATA_SOURCE)
    helper.parse_tiers(response.json())

    # with open(PLAYER_LOG, 'rb') as f:
    #     f.seek(0, 2)
    #     print("Helper online, waiting for draft data.")
    #     while True:
    #         line = f.readline()
    #         if line:
    #             helper.get_draft_choices(line)
    #             if SHOW_PICKS:
    #                 helper.get_pick(line)
    #         sleep(0.1)

    TEST_LOG = r'c:\users\sqfky\desktop\premium_draft_iko.log'
    with open(TEST_LOG, 'rb') as f:
        for line in f:
            helper.get_draft_choices(line)
            if SHOW_PICKS:
                helper.get_pick(line)