from enum import Enum
import random, shortuuid
from time import time

from models.card import Card, CardBase, CardType, Color

from .player import Player, PlayerBase
from pydantic.main import BaseModel

from typing import Dict, List, Callable, Union


class GameState(int, Enum):
    IDLE = 0
    ACTIVE = 1
    FINISHED = 2


class GameBase(BaseModel):
    id: str
    state: GameState

    host: PlayerBase
    players: Dict[str, List[CardBase]]
    players_max: int

    turn: Union[str, None]
    reverse: bool
    override_color: Union[Color, None]
    drawed: bool

    deck: List[CardBase]
    discard: List[CardBase]


class Game:
    def __init__(self, host: Player) -> None:
        shortuuid.set_alphabet("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        self.id = shortuuid.random(length=5)
        self.state = GameState.IDLE

        self.host = host
        self.players = {host["id"]: []}
        self.players_max = 8

        self.turn = None
        self.reverse = False
        self.override_color = None
        self.drawed = False

        self.deck: List[Card] = []
        self.discard: List[Card] = []

    def start(self) -> bool:
        if self.state != GameState.ACTIVE:
            self.state = GameState.ACTIVE

            self.turn = random.choice(list(self.players.keys()))
            self.deck = Card.create_deck()

            for card in self.deck:
                if card.type == CardType.NUMBER:
                    self.discard.append(card)
                    self.deck.remove(card)
                    break

            random.seed(int(round(time() * 1000)))
            random.shuffle(self.deck)

            for i, pid in enumerate(self.players):
                self.players[pid], self.deck = Card.create_hand(self.deck)

            return True

        return False

    def join(self, player: Player) -> bool:
        if len(self.players) <= self.players_max:
            self.players[player.id] = []
            return True

        return False

    def leave(self, player: Player) -> bool:
        if player.id in self.players:
            del self.players[player.id]
            return True

        return False

    def advance_turn(self, skip: bool = False) -> None:
        amount = 2 if skip else 1
        if self.reverse:
            amount *= -1

        self.turn = list(self.players.keys())[
            (list(self.players.keys()).index(self.turn) + amount) % len(self.players)
        ]

    def get_next_player(self) -> PlayerBase:
        return list(self.players.keys())[
            (list(self.players.keys()).index(self.turn) + (-1 if self.reverse else 1))
            % len(self.players)
        ]

    def raw(self) -> Dict:
        d = self.__dict__.copy()

        for i, pid in enumerate(d["players"]):
            for i, card in enumerate(d["players"][pid]):
                if isinstance(card, Card):
                    d["players"][pid][i] = card.base()
        for i, card in enumerate(d["deck"]):
            if isinstance(card, Card):
                d["deck"][i] = card.base()
        for i, card in enumerate(d["discard"]):
            if isinstance(card, Card):
                d["discard"][i] = card.base()

        return d

    def __repr__(self) -> Callable:
        return self.__str__()

    def __str__(self) -> str:
        return str(self.raw())
