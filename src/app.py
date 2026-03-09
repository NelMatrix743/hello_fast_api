from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
from src.db import Post, create_db_and_tables, get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app: FastAPI = FastAPI(lifespan=lifespan)



# API endpoints

@app.post("/upload")
async def upload_files(file: UploadFile = File(...),
                       caption: str = Form(""),
                       session: AsyncSession = Depends(get_async_session)):
    pass 