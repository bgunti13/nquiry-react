# 🚀 Complete nQuiry Setup Guide

## Quick Start - Run Both Frontend & Backend

### 🎯 Prerequisites
- **Node.js 16+** (for React frontend)
- **Python 3.8+** (for FastAPI backend)

### 🔥 One-Command Setup

#### Option 1: Two Terminals (Recommended)

**Terminal 1 - Backend:**
```bash
cd c:\Users\bgunti\Desktop\nquiry-react\backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd c:\Users\bgunti\Desktop\nquiry-react\frontend
npm install
npm run dev
```

#### Option 2: Command Prompt Batch Commands

**Setup Backend (run once):**
```cmd
cd c:\Users\bgunti\Desktop\nquiry-react\backend && python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt
```

**Run Backend:**
```cmd
cd c:\Users\bgunti\Desktop\nquiry-react\backend && venv\Scripts\activate && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Setup Frontend (run once):**
```cmd
cd c:\Users\bgunti\Desktop\nquiry-react\frontend && npm install
```

**Run Frontend:**
```cmd
cd c:\Users\bgunti\Desktop\nquiry-react\frontend && npm run dev
```

### ✅ Verify Everything is Working

1. **Backend Running**: http://127.0.0.1:8000 
   - Should show: `{"message": "nQuiry API is running"}`

2. **Frontend Running**: http://localhost:3000
   - Should show the nQuiry React app

3. **API Docs**: http://127.0.0.1:8000/docs
   - Interactive Swagger documentation

### 🎉 You're Ready!

- **React App**: http://localhost:3000
- **Backend API**: http://127.0.0.1:8000
- **API Documentation**: http://127.0.0.1:8000/docs

### 📱 How to Use the App

1. **Open** http://localhost:3000
2. **Enter** your email address (any email works for demo)
3. **Click** "Initialize nQuiry"
4. **Start chatting** - try asking:
   - "What's the latest version of your software?"
   - "How do I reset my password?"
   - "I need help with configuration"

### 🔧 Optional Configuration

**Backend Environment (.env):**
```bash
# Copy example file
cd backend
copy .env.example .env
# Edit .env with your settings
```

**Frontend API URL:**
- Default: http://127.0.0.1:8000
- Change in: `frontend/src/services/api.js`

### 🐛 Common Issues

**Port 8000 in use:**
```bash
# Use different port
uvicorn app.main:app --reload --port 8001
# Update frontend API_BASE_URL accordingly
```

**Virtual environment issues:**
```bash
# Windows
rmdir /s backend\venv
cd backend && python -m venv venv && venv\Scripts\activate
```

**Node modules issues:**
```bash
# Clean install
cd frontend
rmdir /s node_modules
npm install
```

## 🎯 Features Available

✅ Customer authentication
✅ Real-time chat interface  
✅ Voice input support
✅ Conversation history
✅ Support ticket creation
✅ System status monitoring
✅ Audio feedback toggle
✅ Mobile responsive design

## 📋 Next Steps

- **Production**: Set up proper database and authentication
- **Customization**: Modify styles in `frontend/src/styles/globals.css`
- **Integration**: Connect to real JIRA/MindTouch APIs
- **Deployment**: Deploy to cloud services

**Happy Coding! 🎉**