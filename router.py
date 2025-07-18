from fastapi import APIRouter, Request, Form
from fastapi.responses import PlainTextResponse, JSONResponse
from utils import query_deepseek
from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
from twilio.rest import Client
from db import conversations_collection, get_or_create_profile, update_profile_field, get_profile_summary
import re
from typing import Optional
from models import UserProfile

router = APIRouter()
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

PROFILE_FIELDS = [
    ("name", "your name"),
    ("age", "your age"),
    ("gender", "your gender (male/female/other)"),
    ("location", "your location (city/country)"),
    ("profession", "your profession"),
    ("medical_history", "any relevant medical history (comma separated, or say 'none')")
]

def clean_message(text: str) -> str:
    text = text.replace("**", "")
    text = re.sub(r"[^\x20-\x7E\n]+", "", text)
    return text.strip()

def split_response(text: str, max_len: int = 1000, max_parts: int = 3) -> list:
    parts = []
    while len(text) > max_len and len(parts) < max_parts:
        idx = text.rfind("\n", 0, max_len)
        idx = idx if idx > 300 else max_len
        parts.append(text[:idx].strip())
        text = text[idx:].strip()
    if text and len(parts) < max_parts:
        parts.append(text.strip())
    return parts

async def get_history(sender_id: str):
    doc = await conversations_collection.find_one({"sender": sender_id})
    return doc["history"] if doc else []

async def save_message(sender_id: str, role: str, content: str):
    doc = await conversations_collection.find_one({"sender": sender_id})
    message = {"role": role, "content": content}
    
    if doc:
        new_history = doc["history"][-10:] + [message]  # Trim to last 10 for memory control
        await conversations_collection.update_one(
            {"sender": sender_id},
            {"$set": {"history": new_history}}
        )
    else:
        await conversations_collection.insert_one(
            {"sender": sender_id, "history": [message]}
        )

def parse_profile_update(user_msg: str):
    """Try to extract profile field and value from user message."""
    # Simple regex-based extraction for age, name, gender, location, profession, medical_history
    msg = user_msg.lower()
    # Age
    age_match = re.search(r"i(?:'m| am| am aged| am age)?\s*(\d{1,3})\b", msg)
    if age_match:
        age = int(age_match.group(1))
        return ("age", age)
    # Name
    name_match = re.search(r"my name is ([a-zA-Z ]{2,40})", user_msg, re.I)
    if name_match:
        name = name_match.group(1).strip()
        return ("name", name)
    # Gender
    gender_match = re.search(r"i(?:'m| am)? (male|female|other)\b", msg)
    if gender_match:
        gender = gender_match.group(1).capitalize()
        return ("gender", gender)
    # Location
    loc_match = re.search(r"i(?:'m| am)? from ([a-zA-Z ,]{2,40})", user_msg, re.I)
    if loc_match:
        location = loc_match.group(1).strip()
        return ("location", location)
    # Profession
    prof_match = re.search(r"i(?:'m| am)? a[n]? ([a-zA-Z ]{2,40})", user_msg, re.I)
    if prof_match:
        profession = prof_match.group(1).strip()
        return ("profession", profession)
    # Medical history
    if "medical history" in msg or "i have" in msg or "i had" in msg:
        med_hist = re.findall(r"(diabetes|hypertension|asthma|cancer|allergy|covid|flu|cold|fever|bp|blood pressure|cholesterol|thyroid|heart|stroke|none)", msg)
        if med_hist:
            med_hist = [m.capitalize() for m in med_hist if m != "none"]
            return ("medical_history", med_hist)
        elif "none" in msg:
            return ("medical_history", [])
    # Comma separated medical history
    if any(x in msg for x in ["asthma", "diabetes", "hypertension", "cancer", "allergy", "covid", "flu", "cold", "fever", "bp", "blood pressure", "cholesterol", "thyroid", "heart", "stroke"]):
        med_hist = re.findall(r"(asthma|diabetes|hypertension|cancer|allergy|covid|flu|cold|fever|bp|blood pressure|cholesterol|thyroid|heart|stroke)", msg)
        med_hist = [m.capitalize() for m in med_hist]
        return ("medical_history", med_hist)
    return (None, None)

async def get_missing_profile_fields(profile: dict):
    missing = []
    for key, desc in PROFILE_FIELDS:
        if key == "medical_history":
            val = profile.get(key)
            if not val or (isinstance(val, list) and len(val) == 0):
                missing.append((key, desc))
        else:
            if not profile.get(key):
                missing.append((key, desc))
    return missing

@router.post("/webhook")
async def whatsapp_webhook(
    Body: Optional[str] = Form(None),
    From: Optional[str] = Form(None)
):
    user_msg = Body or "Hello"
    sender = From or ""
    
    if not sender:
        return PlainTextResponse("Missing sender information", status_code=400)
    
    print(f"{sender} says: {user_msg}")

    await save_message(sender, "user", user_msg)
    history = await get_history(sender)
    context = history[-6:]  # Keep context short

    # --- Profile logic ---
    profile = await get_or_create_profile(sender)
    key, value = parse_profile_update(user_msg)
    if key and value is not None:
        if key == "medical_history" and value:
            existing = profile.get("medical_history", [])
            merged = list(set(existing + value))
            await update_profile_field(sender, key, merged)
        else:
            await update_profile_field(sender, key, value)
        profile = await get_or_create_profile(sender)

    # --- System prompt with privacy-first context ---
    profile_summary = []
    if profile.get("name"): profile_summary.append(f"Name: {profile['name']}")
    if profile.get("age"): profile_summary.append(f"Age: {profile['age']}")
    if profile.get("gender"): profile_summary.append(f"Gender: {profile['gender']}")
    if profile.get("location"): profile_summary.append(f"Location: {profile['location']}")
    if profile.get("profession"): profile_summary.append(f"Profession: {profile['profession']}")
    if profile.get("medical_history"): profile_summary.append(f"Medical History: {', '.join(profile['medical_history'])}")
    profile_context = " | ".join(profile_summary)

    system_prompt = {
        "role": "system",
        "content": (
            "You are a polite, helpful AI health assistant named Medkit. Respond in English.\n"
            "You may use the user's profile details like name, age, gender, profession, location, and medical history **only if they are available** to personalize the advice.\n"
            "Do not ask for personal information unless it is **relevant to the current health question**. Always prioritize user comfort and privacy.\n"
            "If the user shares new info like name or age voluntarily, remember and use it politely in future responses.\n"
            "Avoid interrogating the user for data.\n"
            f"User profile: {profile_context}"
        )
    }
    messages = [system_prompt] + context

    ai_response = await query_deepseek(messages)
    print(f"AI response: {ai_response}")

    await save_message(sender, "assistant", ai_response)
    cleaned = clean_message(ai_response)
    parts = split_response(cleaned)

    # Only send the AI response to the user, never 'OK'
    for part in parts:
        if part.strip() and part.strip().lower() != "ok":
            client.messages.create(
                from_=TWILIO_WHATSAPP_NUMBER,
                to=sender,
                body=part
            )

    return PlainTextResponse("")

@router.get("/")
async def home():
    return {"status": "Medkit AI backend running with MongoDB"}

@router.post("/test-api")
async def test_api(request: Request):
    data = await request.json()
    user_msg = data.get("message", "")
    sender = "test_user"

    await save_message(sender, "user", user_msg)
    history = await get_history(sender)
    profile = await get_or_create_profile(sender)
    key, value = parse_profile_update(user_msg)
    if key and value is not None:
        if key == "medical_history" and value:
            existing = profile.get("medical_history", [])
            merged = list(set(existing + value))
            await update_profile_field(sender, key, merged)
        else:
            await update_profile_field(sender, key, value)
        profile = await get_or_create_profile(sender)
    profile_summary = []
    if profile.get("name"): profile_summary.append(f"Name: {profile['name']}")
    if profile.get("age"): profile_summary.append(f"Age: {profile['age']}")
    if profile.get("gender"): profile_summary.append(f"Gender: {profile['gender']}")
    if profile.get("location"): profile_summary.append(f"Location: {profile['location']}")
    if profile.get("profession"): profile_summary.append(f"Profession: {profile['profession']}")
    if profile.get("medical_history"): profile_summary.append(f"Medical History: {', '.join(profile['medical_history'])}")
    profile_context = " | ".join(profile_summary)
    messages = [{"role": "system", "content": (
        "You are a polite, helpful AI health assistant named Medkit. Respond in English.\n"
        "You may use the user's profile details like name, age, gender, profession, location, and medical history **only if they are available** to personalize the advice.\n"
        "Do not ask for personal information unless it is **relevant to the current health question**. Always prioritize user comfort and privacy.\n"
        "If the user shares new info like name or age voluntarily, remember and use it politely in future responses.\n"
        "Avoid interrogating the user for data.\n"
        f"User profile: {profile_context}"
    )}] + history[-6:]
    ai_response = await query_deepseek(messages)
    await save_message(sender, "assistant", ai_response)
    return JSONResponse(content={"reply": ai_response})

@router.get("/profile-summary")
async def profile_summary(sender: str):
    summary = await get_profile_summary(sender)
    return {"sender": sender, "profile_summary": summary}
