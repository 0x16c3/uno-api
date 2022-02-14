import shortuuid

from models.card import Card, CardBase

from pydantic.main import BaseModel

from typing import Dict, List, Callable


class PlayerBase(BaseModel):
    id: str


class Player:
    def __init__(self, ip: str) -> None:
        shortuuid.set_alphabet("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        self.id = str(shortuuid.uuid())

    def raw(self) -> Dict:
        return self.__dict__

    def __repr__(self) -> Callable:
        return self.__str__()

    def __str__(self) -> str:
        return str(self.raw())
