from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.rules import router as rules_router
from app.routes.migrations import router as migrations_router
from app.routes.reference import router as reference_router
from app.routes.policy import router as policy_router
from app.routes.reviews import router as reviews_router
from app.database import seed_database


@asynccontextmanager
async def lifespan(application: FastAPI):
    await seed_database()
    yield


app = FastAPI(lifespan=lifespan)

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(rules_router)
app.include_router(migrations_router)
app.include_router(reference_router)
app.include_router(policy_router)
app.include_router(reviews_router)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
