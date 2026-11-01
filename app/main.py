from fastapi import FastAPI

from app.routers import bonuses

app = FastAPI(title="Bonuses API")
app.include_router(bonuses.router)
