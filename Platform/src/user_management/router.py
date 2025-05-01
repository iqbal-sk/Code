from fastapi import APIRouter, Depends
from odmantic import AIOEngine, ObjectId
from Platform.src.user_management.schemas import UserCreate, UserLogin, UserOut, Token
from Platform.src.user_management.services import create_user, authenticate_user
from Platform.src.core.dependencies import engine_dep
from Platform.src.auth.dependencies import get_current_user, TokenData
from Platform.src.user_management.models import User

router = APIRouter(prefix="/api/v1/users", tags=["users"])

@router.post("/register", response_model=UserOut)
async def register(user: UserCreate, engine: AIOEngine = Depends(engine_dep)):
    new_user = await create_user(user, engine)
    user_dict = new_user.model_dump() if hasattr(new_user, "model_dump") else new_user.__dict__
    user_dict["_id"] = str(new_user.id)
    return user_dict

@router.post("/login", response_model=Token)
async def login(user: UserLogin, engine: AIOEngine = Depends(engine_dep)):
    return await authenticate_user(user, engine)

@router.get("/me", response_model=UserOut)
async def get_current_user(token_data: TokenData = Depends(get_current_user),
                           engine: AIOEngine = Depends(engine_dep)):
    current_user_id = ObjectId(token_data.id)
    current_user = await engine.find_one(User, User.id == current_user_id)

    user_dict = current_user.model_dump() if hasattr(current_user, "model_dump") else current_user.__dict__
    user_dict["_id"] = str(current_user.id)
    return user_dict
