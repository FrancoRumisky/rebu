"""
Authentication Router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.security import (
    get_password_hash, verify_password,
    create_access_token, create_refresh_token,decode_token
)
from app.schemas.auth import (
    UserRegister, DriverRegister, LoginRequest,
    TokenResponse, FCMTokenUpdate, RefreshTokenRequest
)
from app.repositories import UserRepository, DriverRepository
from app.core.security import get_current_user

import httpx
from app.core.config import settings
from app.schemas.auth import GoogleLoginRequest
from app.core.security import get_current_user

router = APIRouter()


@router.post("/register/user", response_model=TokenResponse)
async def register_user(
    data: UserRegister,
    db: Session = Depends(get_db)
):
    """Register new user (client)"""
    user_repo = UserRepository(db)
    
    # Check if email exists
    if user_repo.get_by_email(data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if phone exists
    if user_repo.get_by_phone(data.phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone already registered"
        )
    
    # Create user
    password_hash = get_password_hash(data.password)
    user = user_repo.create(
        email=data.email,
        phone=data.phone,
        password_hash=password_hash,
        full_name=data.full_name
    )
    
    # Generate tokens
    access_token = create_access_token({"sub": str(user.id), "role": "USER"})
    refresh_token = create_refresh_token({"sub": str(user.id), "role": "USER"})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/register/driver", response_model=TokenResponse)
async def register_driver(
    data: DriverRegister,
    db: Session = Depends(get_db)
):
    """Register new driver"""
    driver_repo = DriverRepository(db)
    
    # Check if email exists
    if driver_repo.get_by_email(data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create driver
    password_hash = get_password_hash(data.password)
    license_expiry = datetime.fromisoformat(data.license_expiry_date)
    
    driver = driver_repo.create(
        email=data.email,
        phone=data.phone,
        password_hash=password_hash,
        full_name=data.full_name,
        license_number=data.license_number,
        license_expiry_date=license_expiry
    )
    
    # Generate tokens
    access_token = create_access_token({"sub": str(driver.id), "role": "DRIVER"})
    refresh_token = create_refresh_token({"sub": str(driver.id), "role": "DRIVER"})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login for both users and drivers"""
    user_repo = UserRepository(db)
    driver_repo = DriverRepository(db)
    
    # Try user first
    user = user_repo.get_by_email(data.email)
    if user and verify_password(data.password, user.password_hash):
        access_token = create_access_token({"sub": str(user.id), "role": "USER"})
        refresh_token = create_refresh_token({"sub": str(user.id), "role": "USER"})
        
        user.last_login_at = datetime.utcnow()
        db.commit()
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )
    
    # Try driver
    driver = driver_repo.get_by_email(data.email)
    if driver and verify_password(data.password, driver.password_hash):
        access_token = create_access_token({"sub":str(driver.id), "role": "DRIVER"})
        refresh_token = create_refresh_token({"sub": str(driver.id), "role": "DRIVER"})
        
        driver.last_login_at = datetime.utcnow()
        db.commit()
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials"
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshTokenRequest):
    """
    Refresh access token using a refresh token.
    Returns a new access token and (optionally) a new refresh token.
    """
    payload = decode_token(data.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    user_id = payload.get("sub")
    role = payload.get("role")

    if user_id is None or role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    # Generar tokens nuevos
    access_token = create_access_token({"sub": user_id, "role": role})

    # ✅ Recomendado: rotar refresh token (más seguro) y mantener compatibilidad con tu Flutter actual
    refresh_token = create_refresh_token({"sub": user_id, "role": role})

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/fcm-token")
async def update_fcm_token(
    data: FCMTokenUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update FCM token for push notifications"""
    entity = current_user["entity"]
    entity.fcm_token = data.fcm_token
    db.commit()
    
    return {"message": "FCM token updated"}


@router.post("/google", response_model=TokenResponse)
async def google_login(
    data: GoogleLoginRequest,
    db: Session = Depends(get_db),
):
    """
    Login/Signup with Google ID Token.
    Verifica el id_token contra Google tokeninfo, y devuelve JWT (access/refresh) propios.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GOOGLE_CLIENT_ID not configured"
        )

    # 1) Verificar token con Google
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": data.id_token},
            )
        if r.status_code != 200:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token")

        info = r.json()
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Google verification failed")

    # 2) Validaciones mínimas
    aud = info.get("aud")
    if aud != settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google token audience mismatch")

    email = info.get("email")
    email_verified = info.get("email_verified")
    sub = info.get("sub")  # Google user id
    name = info.get("name") or "Usuario"
    picture = info.get("picture")

    if not email or not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token payload")

    if str(email_verified).lower() not in ("true", "1"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not verified")

    user_repo = UserRepository(db)

    # 3) Buscar usuario existente por email
    user = user_repo.get_by_email(email)

    if user:
        # Si existe, lo marcamos como google si corresponde
        if not user.google_sub:
            user.google_sub = sub
        user.auth_provider = "google"
        if picture and not user.profile_image_url:
            user.profile_image_url = picture

        user.last_login_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
    else:
        # 4) Crear usuario nuevo (phone/password quedan null hasta completar perfil)
        user = user_repo.create(
            email=email,
            phone=None,
            password_hash=None,
            full_name=name,
        )
        user.auth_provider = "google"
        user.google_sub = sub
        user.profile_image_url = picture
        user.is_verified = True
        user.last_login_at = datetime.utcnow()
        db.commit()
        db.refresh(user)

    # 5) Devolver tus JWT (igual que login normal)
    access_token = create_access_token({"sub": str(user.id), "role": "USER"})
    refresh_token = create_refresh_token({"sub": str(user.id), "role": "USER"})

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)



