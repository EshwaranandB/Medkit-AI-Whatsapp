# WhatsApp Health Chatbot - MVP Backend

This is a minimal FastAPI backend for a WhatsApp health chatbot MVP. It integrates with Twilio WhatsApp API and OpenRouter AI API to provide health-related Q&A.

## Features

- Receives WhatsApp messages via Twilio webhook
- Sends user messages to AI models (DeepSeek, GPT-3.5, Mistral) via OpenRouter
- Responds back to WhatsApp users with AI-generated health answers
- Stores conversation history in MongoDB
- Handles long responses by splitting messages
- Includes fallback AI models for reliability

## Setup Instructions

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up MongoDB:**
   - Install MongoDB locally or use MongoDB Atlas
   - The app will automatically create the database and collections

3. **Create Environment Variables:**
   - Copy `env_template.txt` to `.env`
   - Fill in your actual API keys and credentials:
     ```bash
     # Twilio Configuration
     TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
     TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
     TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
     
     # AI API Configuration
     OPENROUTER_API_KEY=your_openrouter_api_key_here
     
     # MongoDB Configuration
     MONGODB_URI=mongodb://localhost:27017
     ```

4. **Set up Twilio WhatsApp Sandbox:**
   - Follow Twilio's guide: https://www.twilio.com/docs/whatsapp/sandbox
   - Note your Sandbox WhatsApp number and credentials

5. **Get OpenRouter API Key:**
   - Sign up at https://openrouter.ai/
   - Get your API key from the dashboard

6. **Run the FastAPI server:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

7. **Configure Twilio Webhook:**
   - Set your Twilio WhatsApp Sandbox webhook URL to:
   ```
   http://your-server-ip-or-domain:8000/webhook
   ```

8. **Test the API:**
   - Visit `http://localhost:8000/` to see the status
   - Use the test endpoint: `POST /test-api` with JSON body `{"message": "Hello"}`

## API Endpoints

- `GET /` - Health check and status
- `POST /webhook` - Twilio WhatsApp webhook
- `POST /test-api` - Test endpoint for API testing

## Architecture

- **FastAPI** - Web framework with async support
- **Twilio** - WhatsApp API integration
- **OpenRouter** - AI model access (DeepSeek, GPT-3.5, Mistral)
- **MongoDB** - Conversation history storage
- **Motor** - Async MongoDB driver

## Next Steps

- Add OCR and lab report analysis
- Add image-based symptom and meal analysis
- Implement user profiles and personalization
- Deploy backend to cloud hosting
- Add authentication and user management

## Disclaimer

This chatbot provides informational responses and is not a substitute for professional medical advice.

## Docker Deployment

To make deployment easier and consistent across environments, you can use Docker to containerize the application.

### Build Docker Image

From the root of the project (where `whatsapp-health-bot` folder is located), create a Docker image:

```bash
docker build -t whatsapp-health-bot -f whatsapp-health-bot/Dockerfile .
```

### Run Docker Container

Run the container exposing port 8000:

```bash
docker run -d -p 8000:8000 --env-file whatsapp-health-bot/.env whatsapp-health-bot
```

### Notes

- Ensure your `.env` file contains all required environment variables.
- The app will be accessible at `http://localhost:8000/`.
- You can deploy this container to any cloud provider supporting Docker containers.

## GitHub Repository Readiness

- `.gitignore` is configured to exclude environment files, logs, and other unnecessary files.
- `README.md` provides setup and usage instructions.
- `requirements.txt` lists all dependencies.
- Environment variables are managed via `.env` and `env_template.txt`.
- Consider adding a LICENSE file to clarify usage rights.
- Optionally, add CI workflows for automated testing on GitHub.

---
