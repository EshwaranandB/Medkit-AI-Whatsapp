# db.py
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from datetime import datetime
from models import UserProfile

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")

try:
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client["medkitdatabase"]
    conversations_collection = db["conversations"]
    print("✅ Connected to MongoDB")
except Exception as e:
    print(f"❌ MongoDB connection error: {e}")

# --- Profile Helpers ---
async def get_or_create_profile(sender: str) -> dict:
    doc = await conversations_collection.find_one({"sender": sender})
    now = datetime.utcnow()
    if doc and "profile" in doc:
        # Ensure all fields exist
        profile = UserProfile(**doc["profile"])
        # Fill missing timestamps
        if not profile.created_at:
            profile.created_at = now
        if not profile.last_updated:
            profile.last_updated = now
        # Update in DB if needed
        await conversations_collection.update_one(
            {"sender": sender},
            {"$set": {"profile": profile.dict()}}
        )
        return profile.dict()
    else:
        # Create new profile
        profile = UserProfile(created_at=now, last_updated=now)
        await conversations_collection.update_one(
            {"sender": sender},
            {"$setOnInsert": {"profile": profile.dict(), "sender": sender, "history": []}},
            upsert=True
        )
        return profile.dict()

async def update_profile_field(sender: str, key: str, value):
    now = datetime.utcnow()
    # Only allow valid fields
    if key not in UserProfile.__fields__:
        return False
    update = {f"profile.{key}": value, "profile.last_updated": now}
    await conversations_collection.update_one(
        {"sender": sender},
        {"$set": update}
    )
    return True

async def get_profile_summary(sender: str) -> str:
    doc = await conversations_collection.find_one({"sender": sender})
    if not doc or "profile" not in doc:
        return "No profile found."
    profile = UserProfile(**doc["profile"])
    summary = []
    if profile.name:
        summary.append(f"Name: {profile.name}")
    if profile.age:
        summary.append(f"Age: {profile.age}")
    if profile.gender:
        summary.append(f"Gender: {profile.gender}")
    if profile.location:
        summary.append(f"Location: {profile.location}")
    if profile.profession:
        summary.append(f"Profession: {profile.profession}")
    if profile.medical_history:
        summary.append(f"Medical History: {', '.join(profile.medical_history)}")
    return " | ".join(summary) if summary else "Profile is empty."
