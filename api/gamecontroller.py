from main import app

from .gamelist import GAMES, GameResponse, find_game

from fastapi import Request
from pydantic.main import BaseModel

from models.game import Game, GameBase, GameState
from models.player import Player, PlayerBase
from models.card import Card, CardBase, CardType, Color
from utils.exceptions import (
    NotFoundException404,
    ForbiddenException403,
    BadRequestException400,
)

from typing import List, Optional


@app.post(
    "/GameController/{game_id}/start",
    response_model=GameResponse,
    responses={
        400: BadRequestException400.model("Game is already active."),
        403: ForbiddenException403.model("Only the host can start the game."),
        404: NotFoundException404.model("Game not found."),
    },
    tags=["game"],
)
async def start_game(request: Request, game_id: str):
    game = find_game(game_id)

    if game.host != request.session["player"]:
        raise ForbiddenException403.new("Only the host can start the game.")
    if game.state == GameState.ACTIVE:
        raise BadRequestException400.new("Game is already active.")

    game.start()
    return GameResponse(game=GameBase(**game.raw()))


class GameAdvance(BaseModel):
    card: Optional[CardBase] = None


@app.post(
    "/GameController/{game_id}/advance",
    response_model=GameResponse,
    responses={
        400: BadRequestException400.model("Game is not active. `|` Select a color."),
        403: ForbiddenException403.model("It is not your turn. `|` Wrong color."),
        404: NotFoundException404.model("Game not found."),
    },
    tags=["game"],
)
async def advance_game(request: Request, game_id: str, advance: GameAdvance):
    game = find_game(game_id)
    game_clone = None

    if game.turn != request.session["player"]["id"]:
        raise ForbiddenException403.new("It is not your turn.")
    if game.state != GameState.ACTIVE:
        raise BadRequestException400.new("Game is not active.")

    player: PlayerBase = request.session["player"]
    next_player = game.get_next_player()
    last_card = game.discard[-1]

    is_joker = (
        advance.card
        and advance.card.type
        and (advance.card.type == CardType.DRAW4 or advance.card.type == CardType.WILD)
    )

    if advance.card:
        if (
            game.override_color
            and advance.card.color != game.override_color
            and not is_joker
        ) or (advance.card.color != last_card.color and not is_joker):
            if (
                advance.card.type == CardType.NUMBER
                and advance.card.value == last_card.value
            ) or advance.card.color == last_card.color:
                pass
            else:
                raise ForbiddenException403.new("Wrong color.")

        if is_joker:
            if advance.card.color == Color.JOKER:
                raise BadRequestException400.new("Select a color.")

            game.override_color = advance.card.color
            advance.card.color = Color.JOKER
        elif advance.card.type == CardType.REVERSE:
            game.reverse = not game.reverse

        if advance.card.type == CardType.DRAW2:
            game.deck, game.players[next_player] = Card.draw_n(
                game.deck, hand=game.players[next_player], n=2
            )
        elif advance.card.type == CardType.DRAW4:
            game.deck, game.players[next_player] = Card.draw_n(
                game.deck, hand=game.players[next_player], n=4
            )

        game.discard, game.players[player["id"]] = Card.discard(
            game.discard, game.players[player["id"]], advance.card
        )
        if game.override_color != None:
            game.discard[-1].color = game.override_color
            game.override_color = None
        game.drawed = False

        if len(game.players[player["id"]]) == 0:
            game.state = GameState.FINISHED
            game_clone = game
        else:
            game.advance_turn(skip=advance.card.type == CardType.SKIP)

    else:
        if not game.drawed:
            card, game.deck = Card.draw(game.deck)
            game.players[player["id"]].append(card)
            game.drawed = True
        else:
            game.drawed = False
            game.advance_turn()

    if game.state == GameState.FINISHED:
        GAMES.remove(game)
        return GameResponse(game=GameBase(**game_clone.raw()))

    return GameResponse(game=GameBase(**game.raw()))
