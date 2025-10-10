from fastapi import APIRouter, HTTPException
from typing import List
from app.models.user import User, UserResponse

router = APIRouter()

# Mock users data (in production, this would come from a database)
MOCK_USERS = [
    User(name="AMD", email="support@amd.com", role="Customer", organization="AMD"),
    User(name="Viatris", email="support@viatris.com", role="Customer", organization="Viatris"),
    User(name="Novartis", email="support@novartis.com", role="Customer", organization="Novartis"),
    User(name="Wdc", email="support@wdc.com", role="Customer", organization="Wdc"),
]

@router.get("/", response_model=UserResponse)
async def get_users():
    """Get all available users/organizations"""
    try:
        return UserResponse(users=MOCK_USERS)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving users: {str(e)}")

@router.get("/{user_id}", response_model=User)
async def get_user(user_id: str):
    """Get a specific user by ID (email)"""
    try:
        for user in MOCK_USERS:
            if user.email == user_id:
                return user
        raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving user: {str(e)}")