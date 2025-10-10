# Intelligent Query Processing System

An AI-powered query processing system that automatically routes user queries to appropriate knowledge sources (JIRA, Confluence, MindTouch), performs semantic search, and provides intelligent responses using AWS Bedrock LLM.

## 🚀 Features

- **Intelligent Query Classification**: Uses AWS Bedrock LLM to classify queries and route them to appropriate knowledge sources
- **Multi-Source Integration**: 
  - JIRA (via MCP Atlassian server)
  - Confluence (via MCP Atlassian server) 
  - MindTouch (via REST API)
- **Semantic Search**: Uses sentence transformers and cosine similarity for accurate content matching
- **Vector Storage**: Stores embeddings in local vector database for fast similarity search
- **Smart Response Formatting**: LLM-powered response formatting for user-friendly output
- **Automatic Ticket Creation**: Creates support tickets when no relevant information is found
- **LangGraph Workflow**: Orchestrates the entire process using LangGraph state management

## 📋 Prerequisites

- Python 3.8+
- AWS Bedrock access with Claude model permissions
- MCP Atlassian server setup (for JIRA/Confluence)
- MindTouch API access (optional)

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   # nQuiry - React + FastAPI Migration

This project contains the migrated version of the Streamlit nQuiry chatbot, now built with React frontend and FastAPI backend.

## 🏗️ Architecture Overview

### **Frontend (React)**
- **Framework**: React 18 with Vite
- **Styling**: Tailwind CSS
- **Components**: Modular chat interface, sidebar, forms
- **Features**: Voice input, chat history, ticket creation
- **Port**: `http://localhost:3000`

### **Backend (FastAPI)**
- **Framework**: FastAPI with uvicorn
- **API**: RESTful endpoints for chat, users, tickets
- **Storage**: In-memory (demo) - easily extensible to MongoDB
- **Features**: Chat processing, user management, ticket creation
- **Port**: `http://localhost:8000`

## 🚀 Quick Start

### 1. Setup Backend (FastAPI)

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
copy .env.example .env
# Edit .env file with your configuration

# Run the backend server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Setup Frontend (React)

```bash
# Open new terminal and navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🔌 How React and FastAPI Connect

### **Proxy Configuration**
The React development server is configured to proxy API requests to the FastAPI backend:

```javascript
// vite.config.js
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
```

### **API Service**
The React app uses axios to communicate with the backend:

```javascript
// src/services/api.js
const API_BASE_URL = 'http://localhost:8000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' }
})
```

### **CORS Configuration**
FastAPI is configured to accept requests from the React development server:

```python
# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📡 API Endpoints

### **Chat Endpoints**
- `POST /api/chat` - Send message to chatbot
- `GET /api/chat/history/{user_id}` - Get chat history
- `POST /api/chat/initialize` - Initialize processor
- `DELETE /api/chat/history/{user_id}` - Clear history

### **User Endpoints**
- `GET /api/users` - Get all organizations
- `GET /api/users/{user_id}` - Get specific user

### **Ticket Endpoints**
- `POST /api/tickets/create` - Create support ticket
- `GET /api/tickets/{ticket_id}` - Get ticket details
- `GET /api/tickets` - List tickets

## 🧩 Component Structure

### **React Components**
```
src/
├── components/
│   ├── chat/
│   │   ├── ChatContainer.jsx     # Main chat display
│   │   ├── ChatMessage.jsx       # Individual message
│   │   └── ChatInput.jsx         # Input form with voice
│   ├── sidebar/
│   │   └── Sidebar.jsx           # User selection & history
│   └── forms/
│       └── TicketForm.jsx        # Support ticket creation
├── hooks/
│   ├── useChat.js                # Chat state management
│   └── useVoice.js               # Voice input/output
├── services/
│   ├── api.js                    # Axios configuration
│   └── chatService.js            # Chat API calls
└── pages/
    └── ChatPage.jsx              # Main application page
```

## 🎨 Features Migrated from Streamlit

✅ **Chat Interface**
- Real-time messaging
- User/bot message styling
- Typing indicators
- Message timestamps

✅ **Voice Input**
- Speech-to-text (Web Speech API)
- Text-to-speech
- Recording indicators

✅ **User Management**
- Organization selection
- User context preservation
- Session management

✅ **Chat History**
- Conversation persistence
- History navigation
- Conversation threads

✅ **Ticket Creation**
- Support ticket forms
- Priority/category selection
- Escalation options

✅ **Responsive Design**
- Modern Tailwind CSS styling
- Mobile-friendly layout
- Smooth animations

## 🔧 Development Tips

### **Running Both Servers**
You need both servers running simultaneously:

1. **Terminal 1** (Backend):
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

2. **Terminal 2** (Frontend):
```bash
cd frontend
npm run dev
```

### **Making Changes**
- **Frontend changes**: Auto-reload with Vite
- **Backend changes**: Auto-reload with uvicorn `--reload` flag
- **API changes**: Check http://localhost:8000/docs for updated documentation

### **Debugging**
- **Frontend**: Browser DevTools + React DevTools
- **Backend**: FastAPI automatic interactive docs at `/docs`
- **Network**: Check Network tab for API request/response

## 🚀 Production Deployment

### **Frontend (React)**
```bash
cd frontend
npm run build
# Deploy dist/ folder to your hosting service
```

### **Backend (FastAPI)**
```bash
cd backend
# Use gunicorn for production
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### **Environment Variables**
Update `.env` for production:
- Set proper `SECRET_KEY`
- Configure database connections
- Update CORS origins
- Add authentication if needed

## 🔄 Migration Benefits

### **From Streamlit to React + FastAPI:**

✅ **Better Performance**
- Faster loading and interactions
- Optimized API calls
- Better state management

✅ **Enhanced UX**
- Modern, responsive design
- Smooth animations
- Better mobile experience

✅ **Scalability**
- Separate frontend/backend deployment
- API can serve multiple clients
- Better caching strategies

✅ **Development Experience**
- Hot module replacement
- Better debugging tools
- Component-based architecture

✅ **Production Ready**
- Proper API documentation
- Better error handling
- Scalable architecture

## 🛠️ Next Steps

1. **Database Integration**: Replace in-memory storage with MongoDB
2. **Authentication**: Add user authentication and authorization
3. **Real AI Integration**: Connect to OpenAI or other AI services
4. **Testing**: Add unit and integration tests
5. **Monitoring**: Add logging and performance monitoring
6. **Deployment**: Set up CI/CD pipelines

## 🆘 Troubleshooting

### **Common Issues:**

**CORS Errors:**
- Ensure FastAPI CORS is configured correctly
- Check React proxy configuration

**API Connection Failed:**
- Verify both servers are running
- Check ports 3000 (React) and 8000 (FastAPI)
- Ensure no firewall blocking

**Module Import Errors:**
- Ensure virtual environment is activated (backend)
- Run `npm install` (frontend)
- Check Python/Node versions

**Voice Input Not Working:**
- Requires HTTPS in production
- Check browser speech recognition support
- Ensure microphone permissions
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   copy .env.example .env
   ```
   Edit `.env` with your actual credentials.

4. **Configure MCP Atlassian server** (for JIRA/Confluence integration):
   Follow the MCP Atlassian server setup instructions.

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# AWS Credentials for Bedrock
aws_access_key_id=your-aws-access-key-id
aws_secret_access_key=your-aws-secret-access-key
aws_session_token=your-aws-session-token

# JIRA Configuration
JIRA_URL=https://yourcompany.atlassian.net
JIRA_API_TOKEN=your-jira-api-token
JIRA_USER=your-email@company.com

# Confluence Configuration
CONFLUENCE_URL=https://yourcompany.atlassian.net/wiki

# MindTouch Configuration
MINDTOUCH_BASE_URL=https://your-mindtouch-site.com/api
MINDTOUCH_API_KEY=your-mindtouch-api-key
```

### Configuration File

The `config.py` file contains system-wide settings:

- AWS region and Bedrock model selection
- Vector store configuration
- Similarity threshold settings
- LLM classification prompts

## 🚀 Usage

### Command Line Interface

Run the main application:

```bash
python main.py
```

The system will:
1. Show system status for all components
2. Prompt for user queries
3. Process queries through the complete workflow
4. Display intelligent responses or create tickets

### Programmatic Usage

```python
from main import IntelligentQueryProcessor

# Initialize the processor
processor = IntelligentQueryProcessor()

# Process a query
result = processor.process_query("How do I reset my password?")

print(result['response'])
```

## 🔄 Workflow

The system follows this LangGraph workflow:

1. **Query Classification** (`classify_query_node`)
   - Uses AWS Bedrock LLM to classify the query
   - Determines appropriate source: JIRA, Confluence, or MindTouch

2. **Data Fetching** (`fetch_from_source_node`)
   - Fetches relevant documents from the classified source
   - Stores documents in vector database

3. **Semantic Search** (`semantic_search_node`)
   - Performs cosine similarity search against stored embeddings
   - Returns top matching documents with similarity scores

4. **Response Decision** (`should_create_ticket`)
   - If relevant results found → Format response
   - If no relevant results → Create support ticket

5. **Response Formatting** (`format_response_node`)
   - Uses AWS Bedrock LLM to create user-friendly responses
   - Organizes information with proper formatting

6. **Ticket Creation** (`create_ticket_node`)
   - Collects ticket information from user
   - Creates JIRA support ticket

## 📁 Project Structure

```
nquiry/
├── main.py                 # Main LangGraph application
├── config.py              # Configuration settings
├── llm_classifier.py      # LLM-based query classification
├── semantic_search.py     # Semantic search with embeddings
├── response_formatter.py  # LLM-powered response formatting
├── ticket_creator.py      # Support ticket creation
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── vector_store/         # Local vector database storage
└── tools/
    ├── jira_tool.py      # JIRA integration wrapper
    ├── confluence_tool.py # Confluence integration wrapper
    └── mindtouch_tool.py  # MindTouch API integration
```

## 🔌 Integration Details

### JIRA & Confluence (MCP Atlassian)

The system uses placeholder implementations for JIRA and Confluence that can be easily replaced with actual MCP Atlassian server calls:

```python
# Example of real MCP integration (replace placeholder code)
from mcp_client import MCPClient

# In jira_tool.py
result = mcp_client.call("mcp_mcp-atlassian_jira_search", {
    "jql": f'text ~ "{query}"',
    "limit": limit
})
```

### MindTouch

Direct REST API integration for MindTouch knowledge base:

```python
# Automatically searches and retrieves page content
documents = mindtouch_tool.search_pages(query, limit=20)
```

## 🧠 Semantic Search

The system uses:
- **Sentence Transformers** (`all-MiniLM-L6-v2` model) for text embeddings
- **Cosine Similarity** for document matching
- **FAISS** for efficient vector operations
- **Local Storage** for persistent vector database

## 🎫 Ticket Creation

When no relevant information is found:
1. System prompts user for ticket details
2. Collects required fields (summary, priority, project key, etc.)
3. Creates JIRA ticket with structured information
4. Returns ticket key and confirmation

## 🔧 Customization

### Adding New Knowledge Sources

1. Create a new tool in `tools/` directory
2. Implement search and content retrieval methods
3. Update `config.py` classification prompt
4. Add to `main.py` workflow

### Modifying LLM Behavior

- **Classification**: Edit `CLASSIFICATION_PROMPT` in `config.py`
- **Response Formatting**: Modify prompts in `response_formatter.py`
- **Model Selection**: Change `BEDROCK_MODEL` in `config.py`

### Adjusting Similarity Threshold

Modify `SIMILARITY_THRESHOLD` in `config.py` (default: 0.75):
- Higher values = more strict matching
- Lower values = more permissive matching

## 🚨 Troubleshooting

### Common Issues

1. **AWS Bedrock Access Denied**
   - Verify AWS credentials in `.env`
   - Check Bedrock model permissions
   - Ensure correct region configuration

2. **MCP Connection Failed**
   - Verify MCP Atlassian server is running
   - Check JIRA/Confluence credentials
   - Test connection manually

3. **MindTouch API Errors**
   - Verify API key and base URL
   - Check network connectivity
   - Review API rate limits

4. **No Search Results**
   - Check if documents are stored in vector database
   - Verify similarity threshold setting
   - Try rephrasing the query

### System Status Check

Run the application and check the system status display for component health.

## 📈 Performance Considerations

- **Vector Storage**: Documents are stored locally for fast retrieval
- **Batch Processing**: Large document sets are processed in chunks
- **Caching**: Embeddings are cached to avoid recomputation
- **Rate Limiting**: Respects API rate limits for external services

## 🔒 Security

- **Environment Variables**: All sensitive credentials stored in `.env`
- **API Keys**: Secured through environment variable access
- **Local Storage**: Vector database stored locally (no cloud dependencies)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

[Add your license information here]

## 🆘 Support

For support and questions:
1. Check the troubleshooting section
2. Review system status for component health
3. Create a support ticket through the system
4. Contact the development team

---

Built with ❤️ using LangGraph, AWS Bedrock, and Sentence Transformers
