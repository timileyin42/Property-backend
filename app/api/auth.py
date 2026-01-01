from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token
from app.core.permissions import get_current_user
from app.models.user import User, UserRole
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse, UserResponse, ForgotPasswordRequest, ResetPasswordRequest
from app.utils.hashing import hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """
    User signup endpoint - creates new user account with email verification
    
    New users start with USER role and is_verified=False.
    OTP is sent to email for verification.
    """
    from app.services.email_service import send_verification_otp, generate_otp
    from datetime import datetime, timedelta
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Generate OTP
    otp_code = generate_otp()
    otp_expires = datetime.utcnow() + timedelta(minutes=15)  # 15 minutes expiry
    
    # Create new user (unverified)
    new_user = User(
        email=request.email,
        password_hash=hash_password(request.password),
        full_name=request.full_name,
        phone=request.phone,
        role=UserRole.USER,
        is_verified=False,
        verification_token=otp_code,
        verification_token_expires=otp_expires
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Send OTP email
    try:
        send_verification_otp(
            email=new_user.email,
            name=new_user.full_name,
            otp_code=otp_code
        )
    except Exception as e:
        # Log error but don't fail signup
        print(f"Failed to send verification email: {e}")
    
    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        phone=new_user.phone,
        role=new_user.role,
        is_verified=new_user.is_verified,
        created_at=new_user.created_at
    )


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login endpoint - authenticates user and returns JWT tokens
    OAuth2 compatible - use email as username
    
    Requires email verification for non-admin users.
    """
    # Find user by email (username field in OAuth2 form)
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Verify password
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Check email verification (skip for admin)
    if user.role != UserRole.ADMIN and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your email for verification code."
        )
    
    # Generate tokens
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            role=user.role,
            is_verified=user.is_verified,
            created_at=user.created_at
        )
    )


@router.post("/verify-email", response_model=dict)
def verify_email(
    email: str = Body(...),
    otp_code: str = Body(...),
    db: Session = Depends(get_db)
):
    """
    Verify email with OTP code
    
    Args:
        email: User's email
        otp_code: 6-digit OTP code
    
    Returns:
        Success message
    """
    from datetime import datetime
    
    # Find user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if already verified
    if user.is_verified:
        return {"message": "Email already verified", "verified": True}
    
    # Check OTP
    if not user.verification_token or user.verification_token != otp_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    # Check expiry
    if user.verification_token_expires and user.verification_token_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code expired. Please request a new one."
        )
    
    # Mark as verified
    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    
    db.commit()
    
    return {
        "message": "Email verified successfully! You can now log in.",
        "verified": True
    }


@router.post("/resend-otp", response_model=dict)
def resend_otp(
    email: str = Body(...),
    db: Session = Depends(get_db)
):
    """
    Resend OTP verification code
    
    Args:
        email: User's email
    
    Returns:
        Success message
    """
    from app.services.email_service import send_verification_otp, generate_otp
    from datetime import datetime, timedelta
    
    # Find user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if already verified
    if user.is_verified:
        return {"message": "Email already verified"}
    
    # Generate new OTP
    otp_code = generate_otp()
    otp_expires = datetime.utcnow() + timedelta(minutes=15)
    
    # Update user
    user.verification_token = otp_code
    user.verification_token_expires = otp_expires
    
    db.commit()
    
    # Send OTP email
    try:
        send_verification_otp(
            email=user.email,
            name=user.full_name,
            otp_code=otp_code
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )
    
    return {
        "message": "Verification code sent to your email",
        "email": user.email
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information
    """
    return current_user


@router.post("/logout")
def logout():
    """
    Logout endpoint (client-side token removal)
    
    In a JWT-based system, logout is typically handled client-side
    by removing the token. This endpoint is here for completeness.
    """
    return {"message": "Successfully logged out"}


@router.post("/forgot-password", response_model=dict)
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset - sends reset code to user's email
    
    Args:
        request: Contains user's email
    
    Returns:
        Success message (always returns success for security)
    """
    from app.services.email_service import send_password_reset, generate_otp
    from datetime import datetime, timedelta
    
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    
    # Always return success message (don't reveal if email exists)
    # This prevents email enumeration attacks
    if not user:
        return {
            "message": "If an account with that email exists, a password reset code has been sent.",
            "email": request.email
        }
    
    # Generate reset code
    reset_code = generate_otp()
    reset_expires = datetime.utcnow() + timedelta(minutes=15)  # 15 minutes expiry
    
    # Update user with reset token
    user.password_reset_token = reset_code
    user.password_reset_token_expires = reset_expires
    
    db.commit()
    
    # Send reset email
    try:
        send_password_reset(
            email=user.email,
            name=user.full_name,
            reset_code=reset_code
        )
    except Exception as e:
        # Log error but don't reveal to user
        print(f"Failed to send password reset email: {e}")
    
    return {
        "message": "If an account with that email exists, a password reset code has been sent.",
        "email": request.email
    }


@router.post("/reset-password", response_model=dict)
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password using reset code
    
    Args:
        request: Contains email, reset code, and new password
    
    Returns:
        Success message
    """
    from datetime import datetime
    
    # Find user
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset code or email"
        )
    
    # Check if reset token exists
    if not user.password_reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No password reset requested for this account"
        )
    
    # Verify reset code
    if user.password_reset_token != request.reset_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset code"
        )
    
    # Check expiry
    if user.password_reset_token_expires and user.password_reset_token_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset code has expired. Please request a new one."
        )
    
    # Update password
    user.password_hash = hash_password(request.new_password)
    user.password_reset_token = None
    user.password_reset_token_expires = None
    
    db.commit()
    
    return {
        "message": "Password reset successfully! You can now log in with your new password.",
        "success": True
    }
