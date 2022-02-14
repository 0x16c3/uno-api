from fastapi import FastAPI

from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from utils.session import HatsuSessionMiddleware

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

tags_metadata = [
    {
        "name": "sessions",
        "description": "Manage sessions.",
    },
    {
        "name": "game",
        "description": "Manage games.",
    },
]

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
    "https://uno.vercel.app",
    "https://web.postman.co",
]

app = FastAPI(
    title="0x16c3 uno API",
    contact={
        "name": "0x16c3",
        "url": "https://0x16c3.com",
        "email": "0x16c3@gmail.com",
    },
    openapi_tags=tags_metadata,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    HatsuSessionMiddleware,
    session_cookie="uno-session",
    # we won't be storing valuable information in the session
    # so we can just define it directly
    secret_key="73D64A44613BC86E2746659BCE57F41C",
    https_only=True,
    same_site="none",
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

import api.gamelist
import api.gamecontroller
