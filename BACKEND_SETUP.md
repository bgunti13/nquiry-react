# 🚀 nQuiry Backend Setup Guide

Complete step-by-step instructions to run the FastAPI backend for nQuiry.

## 📋 Prerequisites

- **Python 3.8+** (Python 3.9+ recommended)
- **pip** (Python package manager)
- **Git** (for cloning the repository)

## 🛠️ Quick Start

### 1. Navigate to Project Root Directory
```bash
cd c:\Users\bgunti\Desktop\nquiry-react
```

### 2. Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
```bash
# Copy the example environment file
copy .env.example .env

# Edit .env file with your settings (optional for basic demo)
```

### 5. Run the Backend Server
```bash
# Method 1: Using uvicorn directly (RECOMMENDED)
uvicorn fastapi_server:app --reload --host 127.0.0.1 --port 8000

# Method 2: Using Python module
py -m uvicorn fastapi_server:app --reload --host 127.0.0.1 --port 8000

# Method 3: Run with Python directly
python fastapi_server.py
```

## ✅ Verify Backend is Running

1. **API Root**: Visit http://127.0.0.1:8000
   - Should show: `{"message": "nQuiry API is running", "version": "1.0.0"}`

2. **Health Check**: Visit http://127.0.0.1:8000/health
   - Should show: `{"status": "healthy", "service": "nquiry-api"}`

3. **API Documentation**: Visit http://127.0.0.1:8000/docs
   - Interactive Swagger UI documentation

## 🔧 Configuration Options

### Environment Variables (.env file)
```bash
# Required for production
SECRET_KEY=your-secret-key-here-change-in-production

# Database (optional - uses in-memory storage by default)
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=nquiry

# CORS Origins (already configured for React dev server)
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]

# Optional: JIRA Integration
JIRA_SERVER=https://your-company.atlassian.net
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token

# Optional: AI Service Integration
OPENAI_API_KEY=your-openai-api-key
```

### Port Configuration
- **Default**: Backend runs on port 8000
- **React Frontend**: Expects backend at http://127.0.0.1:8000
- **Change Port**: Add `--port XXXX` to uvicorn command

## 📡 API Endpoints

### Chat Endpoints
- `POST /api/chat/initialize` - Initialize query processor
- `POST /api/chat` - Send message to chatbot  
- `GET /api/chat/history/{user_id}` - Get chat history
- `DELETE /api/chat/history/{user_id}` - Clear chat history

### User Endpoints  
- `GET /api/users` - Get all organizations
- `GET /api/users/{user_id}` - Get specific user info

### Ticket Endpoints
- `POST /api/tickets/create` - Create support ticket
- `GET /api/tickets/{ticket_id}` - Get ticket details
- `GET /api/tickets` - List all tickets

### System Endpoints
- `GET /` - Root endpoint (API status)
- `GET /health` - Health check

## 🐛 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Error: [Errno 10048] Only one usage of each socket address
   # Solution: Use different port
   uvicorn app.main:app --reload --port 8001
   ```

2. **Module Not Found**
   ```bash
   # Error: ModuleNotFoundError: No module named 'fastapi_server'
   # Solution: Make sure you're in the project root directory
   cd c:\Users\bgunti\Desktop\nquiry-react
   ```

3. **Virtual Environment Issues**
   ```bash
   # Deactivate and recreate
   deactivate
   rmdir /s venv
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **CORS Issues**
   ```bash
   # If React frontend can't connect, check CORS settings in fastapi_server.py
   # Make sure React dev server URL is in allow_origins
   ```

### Logs and Debugging

- **Verbose Logging**: Add `--log-level debug` to uvicorn command
- **Auto-reload**: `--reload` flag automatically restarts on code changes
- **Console Output**: All API requests and responses logged to console

## 🔄 Running with React Frontend

### Terminal 1 (Backend):
```bash
cd c:\Users\bgunti\Desktop\nquiry-react
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn fastapi_server:app --reload --host 127.0.0.1 --port 8000
```

### Terminal 2 (Frontend):
```bash
cd c:\Users\bgunti\Desktop\nquiry-react\frontend  
npm install
npm run dev
```

### Access Points:
- **React App**: http://localhost:3000
- **Backend API**: http://127.0.0.1:8000
- **API Docs**: http://127.0.0.1:8000/docs

## 🚀 Production Deployment

For production deployment:

1. **Set SECRET_KEY** in .env
2. **Configure database** (MongoDB)
3. **Set proper CORS origins**
4. **Use production ASGI server**:
   ```bash
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

## 📁 Backend Structure

```
backend/
├── app/
│   ├── api/           # API routes
│   ├── core/          # Configuration
│   ├── models/        # Data models
│   ├── services/      # Business logic
│   └── main.py        # FastAPI app
├── requirements.txt   # Dependencies
├── .env.example      # Environment template
└── README.md         # This file
```

## 💡 Development Tips

- **Hot Reload**: Use `--reload` flag for development
- **API Testing**: Use `/docs` endpoint for interactive testing
- **Database**: Currently uses in-memory storage (great for demo)
- **Logging**: Check console for request/response logs
- **CORS**: Already configured for React development server

The backend is now ready to serve your React frontend! 🎉