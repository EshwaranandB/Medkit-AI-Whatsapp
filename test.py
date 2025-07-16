import requests
import os
from dotenv import load_dotenv

load_dotenv()

headers = {
    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://your-app.com",
    "X-Title": "Your App"
}

data = {
    "model": "deepseek/deepseek-chat-v3-0324:free",
    "messages": [
        {"role": "system", "content": "You are a helpful health assistant."},
        {"role": "user", "content": "Who is eshwar anand badugu"}
    ]
}

res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)

print(res.status_code)
print(res.text)
