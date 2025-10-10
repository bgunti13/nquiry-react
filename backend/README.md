# nQuiry FastAPI Backend

This is the backend API for the nQuiry Intelligent Query Assistant, built with FastAPI.

## Features

- RESTful API endpoints for chat functionality
- User/organization management
- Support ticket creation
- In-memory storage for demo (easily extensible to MongoDB)
- CORS enabled for React frontend
- Placeholder for AI service integration

## API Endpoints

### Chat
- `POST /api/chat` - Send a message to the chatbot
- `GET /api/chat/history/{user_id}` - Get chat history for a user
- `POST /api/chat/initialize` - Initialize the query processor
- `DELETE /api/chat/history/{user_id}` - Clear chat history

### Users
- `GET /api/users` - Get all available organizations
- `GET /api/users/{user_id}` - Get specific user information

### Tickets
- `POST /api/tickets/create` - Create a support ticket
- `GET /api/tickets/{ticket_id}` - Get ticket details
- `GET /api/tickets` - List tickets

## Installation

1. Create virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the server:
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
API documentation will be available at `http://localhost:8000/docs`

## Development

The backend uses:
- **FastAPI** for the web framework
- **Pydantic** for data validation
- **Motor** for async MongoDB operations (when enabled)
- **Uvicorn** as the ASGI server

## Production Notes

- Replace in-memory storage with proper database
- Set up proper authentication/authorization
- Configure environment variables for production
- Add logging and monitoring
- Set up proper CORS origins