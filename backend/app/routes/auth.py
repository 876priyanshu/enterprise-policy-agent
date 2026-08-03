from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext

# Adjust these imports to match your specific schemas and models
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse # Assuming you have schemas for registration
from app.services.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Setup the password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


#REGISTER ENDPOINT
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user. Accepts standard JSON.
    """
    # Check if the user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Hash the password and save the new user
    hashed_pwd = get_password_hash(user.password)
    new_user = User(email=user.email, hashed_password=hashed_pwd)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user



# LOGIN ENDPOINT
@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    print("\n--- DEBUG LOGIN PROCESS ---")
    print(f"1. Login attempt for email: '{form_data.username}'")
    
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if user is None:
        print("2. RESULT: User NOT found in the database!")
    else:
        print(f"2. RESULT: User found! Database ID: {user.id}")
        print(f"3. DB Hash stored: {user.hashed_password}")
        
        # Test the cryptographic comparison manually
        is_valid = verify_password(form_data.password, user.hashed_password)
        print(f"4. Cryptographic match result: {is_valid}")
    print("---------------------------\n")

    # Original logic continues...
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(data={"sub": str(user.email)})
    return {"access_token": access_token, "token_type": "bearer"}