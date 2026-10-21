from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas, auth

router = APIRouter()


@router.post("/register/", response_model=schemas.RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(request: schemas.RegisterRequest, db: Session = Depends(get_db)):
    # Check if username already exists
    if db.query(models.User).filter(models.User.username == request.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    # Check if email already exists
    if db.query(models.User).filter(models.User.email == request.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    # Create user
    user = models.User(
        username=request.username,
        email=request.email,
        first_name=request.first_name,
        last_name=request.last_name,
        hashed_password=auth.hash_password(request.password),
    )
    db.add(user)
    db.flush()

    # Create profile
    profile = models.Profile(user_id=user.id)
    db.add(profile)
    db.commit()
    db.refresh(user)

    # Generate tokens
    access = auth.create_access_token(user.id, user.role, user.username, user.email)
    refresh = auth.create_refresh_token(user.id, user.role, user.username, user.email)

    return schemas.RegisterResponse(
        user=schemas.UserResponse.model_validate(user),
        tokens={"access": access, "refresh": refresh},
    )


@router.post("/login/", response_model=schemas.TokenResponse)
def login(request: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == request.username).first()
    if not user or not auth.verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="User account is disabled")

    access = auth.create_access_token(user.id, user.role, user.username, user.email)
    refresh = auth.create_refresh_token(user.id, user.role, user.username, user.email)

    return schemas.TokenResponse(
        access=access,
        refresh=refresh,
        user=schemas.UserResponse.model_validate(user),
    )


@router.post("/logout/")
def logout(
    request: schemas.LogoutRequest,
    current_user: models.User = Depends(auth.get_current_user),
):
    # In a stateless JWT setup, logout is handled client-side by discarding tokens.
    # For a real implementation, you'd blacklist the refresh token.
    return {"message": "Successfully logged out"}


@router.post("/token/refresh/", response_model=schemas.TokenRefreshResponse)
def refresh_token(request: schemas.TokenRefreshRequest):
    payload = auth.decode_token(request.refresh)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = int(payload.get("sub"))
    access = auth.create_access_token(user_id, payload["role"], payload["username"], payload["email"])

    return schemas.TokenRefreshResponse(access=access)


@router.get("/check/", response_model=schemas.CheckAuthResponse)
def check_auth(current_user: models.User = Depends(auth.get_current_user)):
    return schemas.CheckAuthResponse(
        authenticated=True,
        user=schemas.UserResponse.model_validate(current_user),
    )


@router.get("/profile/", response_model=schemas.UserResponse)
def get_profile(current_user: models.User = Depends(auth.get_current_user)):
    return schemas.UserResponse.model_validate(current_user)
