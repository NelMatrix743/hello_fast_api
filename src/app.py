from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
from src.db import Post, create_db_and_tables, get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from imagekitio import APIStatusError
from src.media import imagekit_client

import shutil
import os 
import uuid
import tempfile



@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app: FastAPI = FastAPI(lifespan=lifespan)



# API endpoints

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), caption: str = Form(""), session: AsyncSession = Depends(get_async_session)):
    temporary_uploaded_file_path: str | None = None
    uploaded_file_extension: str = os.path.splitext(file.filename)[1]

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file_extension) as temporary_file:
            temporary_uploaded_file_path = temporary_file.name
            shutil.copyfileobj(file.file, temporary_file)

        file_upload_result = imagekit_client.files.upload(
            file=open(temporary_uploaded_file_path, "rb"),
            file_name=file.filename,
            use_unique_file_name=True,
            tags=["backend-upload"]
        )
  
        post: Post = Post(
            caption=caption,
            url=file_upload_result.url,
            file_type="video" if file.content_type.startswith("video/") else "image",
            file_name=file_upload_result.name
        )

        session.add(post)
        await session.commit()
        await session.refresh(post)
        return post

    except APIStatusError as error:
        # print("File upload to imagekit failed.")
        # print(error.status_code)
        # print(error.response)
        raise HTTPException(status_code=500, detail=str(error))

    finally:
        try:
            file.file.close()
        except Exception:
            pass

        if os.path.exists(temporary_uploaded_file_path):
            try:
                os.unlink(temporary_uploaded_file_path)
            except PermissionError:
                pass


# eosc