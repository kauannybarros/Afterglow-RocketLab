from fastapi import APIRouter

from app.movie_lists.router import router as movie_lists_router
from app.movies.router import router as movies_router

api_router = APIRouter()
api_router.include_router(movies_router)
api_router.include_router(movie_lists_router)
