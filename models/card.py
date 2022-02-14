from __future__ import annotations

from enum import Enum

from pydantic.main import BaseModel

from typing import List, Dict, Callable, Optional, Tuple


class Color(int, Enum):
    RED = 0
    YELLOW = 1
    BLUE = 2
    GREEN = 3
    JOKER = 4


class CardType(int, Enum):
    NUMBER = 0
    DRAW2 = 1
    REVERSE = 2
    SKIP = 3
    WILD = 4
    DRAW4 = 5


class CardBase(BaseModel):
    color: Color
    type: CardType
    value: Optional[int]


class Card:
    def __init__(self, color: Color, type: CardType, value: int | None = None) -> None:
        self.color = color
        self.type = type
        self.value = value

    @staticmethod
    def create_deck() -> List[Card]:
        colors = [Color.RED, Color.YELLOW, Color.BLUE, Color.GREEN]

        deck = []

        for color in colors:
            for i in range(0, 10):
                deck.append(Card(color, CardType.NUMBER, i))

                # Cards bigger than 0 have 2 of them
                if i > 0:
                    deck.append(Card(color, CardType.NUMBER, i))

            for i in range(0, 2):
                deck.append(Card(color, CardType.SKIP))
                deck.append(Card(color, CardType.REVERSE))
                deck.append(Card(color, CardType.DRAW2))

            deck.append(Card(Color.JOKER, CardType.WILD))
            deck.append(Card(Color.JOKER, CardType.DRAW4))

        return deck

    @staticmethod
    def create_hand(deck: List[Card]) -> Tuple[List[Card], List[Card]]:
        hand = []

        for i in range(0, 7):
            hand.append(deck.pop())

        hand.append(Card(Color.JOKER, CardType.WILD))

        return hand, deck

    @staticmethod
    def draw(deck: List[Card]) -> Tuple[Card, List[Card]]:
        card = deck.pop()
        return card, deck

    @staticmethod
    def draw_n(
        deck: List[Card], hand: List[Card], n: int
    ) -> Tuple[List[Card], List[Card]]:
        for i in range(0, n):
            hand.append(deck.pop())

        return deck, hand

    @staticmethod
    def discard(
        discard: List[Card], hand: List[Card], card: Card
    ) -> Tuple[List[Card], List[Card]]:
        discard.append(card)
        hand.remove(card)
        return discard, hand

    def base(self) -> CardBase:
        return CardBase(color=self.color, type=self.type, value=self.value)

    def raw(self) -> Dict:
        return self.__dict__

    def __repr__(self) -> Callable:
        return self.raw()

    def __str__(self) -> str:
        return str(self.raw())
