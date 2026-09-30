from fastapi import APIRouter, HTTPException, status, Depends
from app.auth.models import UserRegister, UserLogin, UserResponse, Token
from app.auth.service import register_user, authenticate_user, create_access_token
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


def success_response(data):
    return {"success": True, "data": data}


def error_response(message: str, status_code: int = 400):
    raise HTTPException(
        status_code=status_code,
        detail={"success": False, "error": {"message": message}}
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_in: UserRegister):
    """
    Register a new user with email and password.
    Returns access token and user information.
    """
    try:
        user = await register_user(
            email=user_in.email,
            password=user_in.password,
            full_name=user_in.full_name
        )
    except ValueError as exc:
        error_response(str(exc), status_code=400)

    access_token = create_access_token(data={"sub": user["id"], "email": user["email"]})
    
    return success_response({
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    })


@router.post("/login")
async def login(user_in: UserLogin):
    """
    Authenticate user and return JWT access token.
    """
    user = await authenticate_user(email=user_in.email, password=user_in.password)
    if not user:
        error_response("Invalid email or password", status_code=401)

    access_token = create_access_token(data={"sub": user["id"], "email": user["email"]})

    return success_response({
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    })


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current logged in user profile.
    """
    return success_response(current_user)
