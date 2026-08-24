from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.audio import router as audio_router
from app.api.auth import router as auth_router
from app.api.aliases import router as aliases_router
from app.api.checkins import router as checkins_router
from app.api.communication import router as communication_router
from app.api.consents import router as consents_router
from app.api.documents import router as documents_router
from app.api.media import router as media_router
from app.api.preferences import router as preferences_router
from app.api.privacy import router as privacy_router
from app.api.profile import router as profile_router
from app.api.stt import router as stt_router
from app.api.tasks import router as tasks_router
from app.api.tutor import router as tutor_router
from app.api.viva import router as viva_router
from app.api.reader import router as reader_router
from app.core.config import settings
from app.db import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings.docs_dir.mkdir(parents=True, exist_ok=True)
    settings.audio_dir.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="NEUROLEARN API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth_router, profile_router, consents_router, documents_router, media_router, audio_router, tutor_router, tasks_router, viva_router, checkins_router, stt_router, preferences_router, reader_router, communication_router, privacy_router, aliases_router):
    app.include_router(r, prefix="/api")
