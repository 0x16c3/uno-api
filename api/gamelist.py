import asyncio
from main import app

from fastapi import Request
from pydantic.main import BaseModel

from models.game import Game, GameBase, GameState
from models.player import Player, PlayerBase
from utils import Status
from utils.exceptions import (
    NotFoundException404,
    ForbiddenException403,
    BadRequestException400,
)

from typing import List

GAMES: List[Game] = []


def find_game(game_id: str) -> Game:
    for game in GAMES:
        if game.id == game_id:
            return game
    raise NotFoundException404.new("Game not found.")


class UserIdResponse(BaseModel):
    id: str


class GameResponse(BaseModel):
    game: GameBase


class GameListResponse(BaseModel):
    games: List[GameBase]


@app.get(
    "/GameList",
    response_model=GameListResponse,
    tags=["sessions"],
)
async def get_game_list(request: Request):
    return GameListResponse(games=[GameBase(**game.raw()) for game in GAMES])


@app.get(
    "/GameList/me",
    response_model=UserIdResponse,
    tags=["sessions"],
)
async def get_current_use(request: Request):
    if not "player" in request.session:
        # Please note that player objects do not persist.
        request.session["player"] = Player(ip=str(request.client)).raw()

    return UserIdResponse(id=request.session["player"]["id"])


@app.post(
    "/GameList/create",
    response_model=GameResponse,
    responses={400: BadRequestException400.model("You already have a game.")},
    tags=["sessions"],
)
async def create_game(request: Request):
    if not "player" in request.session:
        # Please note that player objects do not persist.
        request.session["player"] = Player(ip=str(request.client)).raw()

    current_game = None
    for _game in GAMES:
        if _game.host["id"] == request.session["player"]["id"]:
            current_game = _game

    if current_game:
        raise BadRequestException400.new("You already have a game.")

    game = Game(host=request.session["player"])
    GAMES.append(game)
    return GameResponse(game=GameBase(**game.raw()))


@app.get(
    "/GameList/{game_id}",
    response_model=GameResponse,
    responses={404: NotFoundException404.model("Game not found.")},
    tags=["sessions"],
)
async def get_game(request: Request, game_id: str):
    return GameResponse(game=GameBase(**find_game(game_id).raw()))


@app.get(
    "/GameList/{game_id}/join",
    response_model=GameResponse,
    responses={
        400: ForbiddenException403.model("Game is already active. `|` Game is full."),
        404: NotFoundException404.model("Game not found."),
    },
    tags=["sessions"],
)
async def join_game(request: Request, game_id: str):
    game = find_game(game_id)

    if not "player" in request.session:
        request.session["player"] = Player(request).raw()

    if game.state == GameState.ACTIVE:
        raise BadRequestException400.new("Game is already active.")
    elif game.state == GameState.IDLE:
        if request.session["player"] == game.host:
            raise BadRequestException400.new("Game is already active.")
    if len(game.players) == game.players_max:
        raise BadRequestException400.new("Game is full.")

    game.players[request.session["player"]["id"]] = []

    return GameResponse(game=GameBase(**game.raw()))


@app.get(
    "/GameList/{game_id}/leave",
    response_model=GameResponse,
    responses={
        403: ForbiddenException403.model(
            "You are not in the game. `|` You can't leave your own game."
        ),
        404: NotFoundException404.model("Game not found."),
    },
    tags=["sessions"],
)
async def leave_game(request: Request, game_id: str):
    game = find_game(game_id)

    if not "player" in request.session:
        request.session["player"] = Player(request).raw()

    if request.session["player"] == game.host:
        return ForbiddenException403.new("You can't leave your own game.")
    if request.session["player"]["id"] not in game.players:
        return ForbiddenException403.new("You are not in the game.")

    del game.players[request.session["player"]["id"]]

    return GameResponse(game=GameBase(**game.raw()))


@app.post(
    "/GameList/{game_id}/end",
    response_model=Status,
    responses={
        403: ForbiddenException403.model(
            "You are not in the game. `|` You are not the host."
        ),
        404: NotFoundException404.model("Game not found."),
    },
    tags=["sessions"],
)
async def end_game(request: Request, game_id: str):
    game = find_game(game_id)

    if not "player" in request.session:
        request.session["player"] = Player(request).raw()

    if request.session["player"]["id"] not in game.players:
        return ForbiddenException403.new(error="You are not in the game.")
    if request.session["player"] != game.host:
        return ForbiddenException403.new(error="You are not the host.")

    GAMES.remove(game)

    return Status(status=True, message="Game ended.")


from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        if websocket not in self.active_connections:
            await websocket.accept()
            self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def _alive_task(self, websocket: WebSocket):
        try:
            await websocket.receive_text()
        except (WebSocketDisconnect):
            pass

    async def _send_task(self, websocket: WebSocket, game_id: int):
        game_idx = 0
        game_set = False
        game_lst = None

        while True:
            await asyncio.sleep(1)

            # data = await websocket.receive_text()

            if not game_set:
                for _game in GAMES:
                    if _game.id == game_id:
                        game_idx = GAMES.index(_game)
                        game_lst = _game.id
                        game_set = True

            if game_idx >= len(GAMES) or game_lst and game_lst != GAMES[game_idx].id:
                await self.broadcast(Status(status=False, message="Game ended.").json())
                self.disconnect(websocket)

            elif game_idx is not None and GAMES[game_idx]:
                await self.broadcast(
                    GameResponse(game=GameBase(**GAMES[game_idx].raw())).json()
                )

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.websocket("/GameList/{game_id}/ws")
async def game_websocket(websocket: WebSocket, game_id: str):
    await manager.connect(websocket)

    try:
        loop = asyncio.get_running_loop()
        alive_task = loop.create_task(
            manager._alive_task(websocket),
            name=f"WS alive check: {websocket.client}",
        )
        send_task: asyncio.Task = loop.create_task(
            manager._send_task(websocket, game_id),
            name=f"WS data sending: {websocket.client}",
        )

        def alive_close(result):
            send_task.cancel(result)
            manager.disconnect(websocket)

        def send_close(result):
            alive_task.cancel(result)
            manager.disconnect(websocket)

        alive_task.add_done_callback(alive_close)
        send_task.add_done_callback(send_close)

        await asyncio.wait({alive_task, send_task})

    except WebSocketDisconnect:
        manager.disconnect(websocket)
