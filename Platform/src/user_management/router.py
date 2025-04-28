from odmantic import AIOEngine

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from Platform.src.user_management.schemas import UserCreate, UserLogin, UserOut
from Platform.src.user_management.services import create_user, authenticate_user
from Platform.src.core.dependencies import engine_dep

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register", response_model=UserOut)
async def register(user: UserCreate, engine=Depends(engine_dep)):
    new_user = await create_user(user, engine)
    user_dict = new_user.model_dump() if hasattr(new_user, "model_dump") else new_user.__dict__
    user_dict["_id"] = str(new_user.id)
    return user_dict

@router.post("/login")
async def login(user: UserLogin, engine=Depends(engine_dep)):
    token = await authenticate_user(user, engine)
    return token