from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
from src.db import Post, User, create_db_and_tables, get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from contextlib import asynccontextmanager
from imagekitio import APIStatusError
from src.media import imagekit_client

from src.users import auth_backend, current_active_user, fastapi_users
from src.schemas import UserCreate, UserRead, UserUpdate

import shutil
import os 
import uuid
import tempfile



@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app: FastAPI = FastAPI(lifespan=lifespan)

app.include_router(fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"])
app.include_router(fastapi_users.get_register_router(UserRead, UserCreate), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_reset_password_router(), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_verify_router(UserRead), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_users_router(UserRead, UserUpdate), prefix="/users", tags=["users"])



# API endpoints

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), caption: str = Form(""), user: User = Depends(current_active_user), session: AsyncSession = Depends(get_async_session)):
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
            user_id=user.id,
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


@app.get("/feed")
async def get_feed(session: AsyncSession = Depends(get_async_session), user: User = Depends(current_active_user)) -> dict[str, list]:
    result = await session.execute(select(Post).order_by(Post.created_at.desc()))
    posts = [row[0] for row in result.all()]

    posts_data = []
    for post in posts:
        posts_data.append(
            {
                "id" : str(post.id),
                "caption" : post.caption,
                "url" : post.url,
                "file_type" : post.file_type,
                "file_name" : post.file_name,
                "created_at" : post.created_at.isoformat(),
                "is_owner" : post.user_id == user.id
            }
        )

    return { "post" : posts_data }


@app.delete("/posts/{post_id}")
async def delete_post(post_id: str, session: AsyncSession = Depends(get_async_session), user: User = Depends(current_active_user)):
    try:
        post_uuid = uuid.UUID(post_id)
        result = await session.execute(select(Post).where(Post.id == post_uuid))
        post = result.scalars().first()

        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        if post.user_id != user.id:
            raise HTTPException(status_code=403, detail="You don't have permission to delete this post")
        
        await session.delete(post)
        await session.commit()

        return {
            "success" : True,
            "message" : "Post successfully deleted!"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# eosc