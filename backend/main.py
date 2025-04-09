from fastapi import FastAPI
from database.db import init_db
from routers import user, chat

app = FastAPI()
init_db()

# Register routers
app.include_router(user.router, prefix="/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
