"""
Authentication API Endpoints
Integrates with PDAM Kota Semarang authentication system
"""

from fastapi import APIRouter, HTTPException, Depends, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import httpx
import jwt
import hashlib
import secrets

from app.core.config import settings

router = APIRouter()
security = HTTPBearer(auto_error=False)


# === Pydantic Models ===

class LoginRequest(BaseModel):
    """Login request payload"""
    npp: str = Field(..., min_length=1, max_length=20, description="Nomor Pokok Pegawai")
    password: str = Field(..., min_length=1, description="Password")
    hwid: Optional[str] = Field(default="chatbot-web", description="Hardware ID")


class LoginResponse(BaseModel):
    """Login response"""
    success: bool
    message: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    user: Optional[Dict[str, Any]] = None
    expires_at: Optional[str] = None


class TokenValidateRequest(BaseModel):
    """Token validation request"""
    access_token: str


class TokenRefreshRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str


# === Helper Functions ===

def create_jwt_token(data: Dict[str, Any], expires_delta: timedelta = None) -> str:
    """Create JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


async def validate_pdam_token(access_token: str) -> Optional[Dict[str, Any]]:
    """Validate token with PDAM API"""
    try:
        async with httpx.AsyncClient(timeout=settings.PDAM_AUTH_TIMEOUT, verify=False) as client:
            response = await client.get(
                f"{settings.PDAM_AUTH_API_URL}/validate",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == 200:
                    return data.get("data")
            return None
    except Exception as e:
        print(f"PDAM token validation error: {e}")
        return None


# === Dependency Functions ===

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Get current authenticated user - REQUIRED"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = credentials.credentials
    
    # First try local JWT
    payload = decode_jwt_token(token)
    if payload:
        return payload
    
    # Then try PDAM token validation
    user_data = await validate_pdam_token(token)
    if user_data:
        return user_data
    
    raise HTTPException(status_code=401, detail="Invalid or expired token")


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[Dict[str, Any]]:
    """Get current user if authenticated - OPTIONAL"""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


async def require_admin(
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Require admin role"""
    roles = current_user.get("roles", [])
    if "admin" not in roles and "developer" not in roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# === API Endpoints ===

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Login with PDAM credentials
    
    - **npp**: Nomor Pokok Pegawai
    - **password**: Password pegawai
    - **hwid**: Hardware ID (optional)
    """
    
    try:
        async with httpx.AsyncClient(timeout=settings.PDAM_AUTH_TIMEOUT, verify=False) as client:
            response = await client.post(
                f"{settings.PDAM_AUTH_API_URL}/login",
                json={
                    "npp": request.npp,
                    "password": request.password,
                    "hwid": request.hwid or f"chatbot-{secrets.token_hex(8)}"
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )
            
            data = response.json()
            
            if data.get("status") == 200 and data.get("data"):
                auth_data = data["data"]
                user = auth_data.get("user", {})
                
                # Create local JWT with PDAM user data
                local_token = create_jwt_token({
                    "npp": user.get("npp"),
                    "name": user.get("name"),
                    "jabatan": user.get("rl_pegawai", {}).get("jabatan"),
                    "satker": user.get("rl_pegawai", {}).get("satker"),
                    "roles": ["user"],
                    "pdam_token": auth_data.get("access_token")
                })
                
                expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
                
                return LoginResponse(
                    success=True,
                    message="Login berhasil!",
                    access_token=local_token,
                    refresh_token=auth_data.get("refresh_token"),
                    user={
                        "npp": user.get("npp"),
                        "name": user.get("name"),
                        "jabatan": user.get("rl_pegawai", {}).get("jabatan"),
                        "satker": user.get("rl_pegawai", {}).get("satker")
                    },
                    expires_at=expires_at.isoformat()
                )
            else:
                return LoginResponse(
                    success=False,
                    message=data.get("message", "Login gagal. Periksa NPP dan password.")
                )
                
    except httpx.TimeoutException:
        return LoginResponse(
            success=False,
            message="Timeout menghubungi server PDAM. Silakan coba lagi."
        )
    except Exception as e:
        print(f"Login error: {e}")
        return LoginResponse(
            success=False,
            message=f"Error: {str(e)}"
        )


@router.post("/validate")
async def validate_token(request: TokenValidateRequest):
    """Validate an access token"""
    
    # Try local JWT first
    payload = decode_jwt_token(request.access_token)
    if payload:
        return {
            "valid": True,
            "source": "local",
            "user": {
                "npp": payload.get("npp"),
                "name": payload.get("name"),
                "roles": payload.get("roles", [])
            },
            "expires_at": datetime.fromtimestamp(payload.get("exp", 0)).isoformat()
        }
    
    # Try PDAM validation
    user_data = await validate_pdam_token(request.access_token)
    if user_data:
        return {
            "valid": True,
            "source": "pdam",
            "user": user_data
        }
    
    return {
        "valid": False,
        "message": "Token tidak valid atau sudah expired"
    }


@router.post("/refresh")
async def refresh_token(request: TokenRefreshRequest):
    """Refresh access token using refresh token"""
    
    try:
        async with httpx.AsyncClient(timeout=settings.PDAM_AUTH_TIMEOUT, verify=False) as client:
            response = await client.post(
                f"{settings.PDAM_AUTH_API_URL}/refresh",
                json={"refresh_token": request.refresh_token},
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )
            
            data = response.json()
            
            if data.get("status") == 200:
                return {
                    "success": True,
                    "access_token": data.get("data", {}).get("access_token"),
                    "refresh_token": data.get("data", {}).get("refresh_token")
                }
            else:
                return {
                    "success": False,
                    "message": data.get("message", "Refresh token gagal")
                }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


@router.post("/logout")
async def logout(current_user: Dict = Depends(get_current_user)):
    """Logout and invalidate token"""
    
    # In a real implementation, you would:
    # 1. Add token to blacklist (Redis)
    # 2. Call PDAM logout API
    
    return {
        "success": True,
        "message": "Logout berhasil"
    }


@router.get("/me")
async def get_current_user_info(current_user: Dict = Depends(get_current_user)):
    """Get current user information"""
    
    return {
        "user": {
            "npp": current_user.get("npp"),
            "name": current_user.get("name"),
            "jabatan": current_user.get("jabatan"),
            "satker": current_user.get("satker"),
            "roles": current_user.get("roles", [])
        }
    }


# === Guest/Public Access ===

@router.post("/guest-token")
async def get_guest_token():
    """
    Get a guest token for public chatbot access
    
    Guest tokens have limited functionality
    """
    
    guest_id = f"guest_{secrets.token_hex(8)}"
    
    token = create_jwt_token({
        "guest_id": guest_id,
        "roles": ["guest"],
        "is_guest": True
    }, expires_delta=timedelta(hours=24))
    
    return {
        "success": True,
        "access_token": token,
        "guest_id": guest_id,
        "expires_in": 86400,  # 24 hours in seconds
        "message": "Token guest berhasil dibuat"
    }
