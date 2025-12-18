# Nquiry - Intelligent Query Processing System

An AI-powered query processing system that automatically routes user queries to appropriate knowledge sources (JIRA, Confluence, MindTouch), performs semantic search, and provides intelligent responses using AWS Bedrock LLM.

**✅ Current Implementation**: Modern React + FastAPI architecture providing optimal performance, scalability, and user experience.

## 🏗️ Project Architecture

### **Frontend (React)**
- **Framework**: React 18 with Vite for fast development
- **Styling**: Tailwind CSS for modern responsive design
- **UI Components**: Headless UI for accessible components
- **Icons**: Lucide React for consistent iconography
- **HTTP Client**: Axios for API communication

### **Backend (FastAPI)**
- **Framework**: FastAPI with modern async architecture
- **Core Engine**: Python-based intelligent query processor
- **AI Integration**: AWS Bedrock LLM for classification and response formatting
- **Knowledge Sources**: JIRA, Confluence, MindTouch integration
- **Search**: Semantic search with sentence transformers and vector storage
- **Workflow**: LangGraph orchestration
- **API**: RESTful design with automatic OpenAPI documentation

## 🚀 Features

- **Intelligent Query Classification**: Uses AWS Bedrock LLM to classify queries and route them to appropriate knowledge sources
- **Multi-Source Integration**: 
  - JIRA (via REST API)
  - Confluence (via REST API) 
  - MindTouch (via REST API)
- **Semantic Search**: Uses sentence transformers and cosine similarity for accurate content matching
- **Vector Storage**: Stores embeddings in local vector database for fast similarity search
- **Smart Response Formatting**: LLM-powered response formatting for user-friendly output
- **Automatic Ticket Creation**: Creates support tickets when no relevant information is found
- **LangGraph Workflow**: Orchestrates the entire process using LangGraph state management
- **Voice Input/Output**: Speech-to-text and text-to-speech capabilities
- **Chat History**: Persistent conversation management

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+ (for React frontend)
- AWS Bedrock access with Claude model permissions
- JIRA instance with API access (for JIRA integration)
- Confluence instance with API access (for Confluence integration)
- MindTouch API access (optional)

## 🛠️ Installation & Setup

### Backend Setup (FastAPI)

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd nquiry-react
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   
   # Activate virtual environment
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   copy .env.example .env
   ```
   Edit `.env` with your actual credentials.

5. **Run the FastAPI server**:
   ```bash
   python fastapi_server.py
   ```

### Frontend Setup (React)

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies**:
   ```bash
   npm install
   ```

3. **Start the development server**:
   ```bash
   npm run dev
   ```

4. **Access the application**:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# AWS Credentials for Bedrock
aws_access_key_id=your-aws-access-key-id
aws_secret_access_key=your-aws-secret-access-key
aws_session_token=your-aws-session-token

# JIRA Configuration (REST API)
JIRA_URL=https://yourcompany.atlassian.net
JIRA_API_TOKEN=your-jira-api-token
JIRA_USERNAME=your-email@company.com

# Confluence Configuration (REST API)
CONFLUENCE_URL=https://yourcompany.atlassian.net/wiki
CONFLUENCE_USERNAME=your-email@company.com
CONFLUENCE_API_TOKEN=your-confluence-api-token

# MindTouch Configuration (REST API)
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

### Web Application

1. **Start both servers**:
   ```bash
   # Terminal 1: Start FastAPI backend
   python fastapi_server.py
   
   # Terminal 2: Start React frontend
   cd frontend
   npm run dev
   ```

2. **Access the application**:
   - Open your browser to http://localhost:5173
   - Use the chat interface to ask questions
   - The system will intelligently route queries and provide responses

### API Usage

The FastAPI backend provides REST endpoints:

```python
import requests

# Send a query to the API
response = requests.post("http://localhost:8000/query", 
                        json={"query": "How do I reset my password?"})

result = response.json()
print(result['response'])
```

### Command Line Interface (Legacy)

You can still run the core system directly:

```bash
python main.py
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
nquiry-react/
├── main.py                    # Core LangGraph application
├── fastapi_server.py          # FastAPI backend server
├── config.py                  # Configuration settings
├── semantic_search.py         # Semantic search with embeddings
├── response_formatter.py      # LLM-powered response formatting
├── ticket_creator.py          # Support ticket creation
├── chat_history_manager.py    # Chat history management
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── vector_store/             # Local vector database storage
├── frontend/                 # React frontend application
│   ├── src/
│   │   ├── App.jsx          # Main React component
│   │   ├── components/      # UI components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API service layer
│   │   └── hooks/          # Custom React hooks
│   ├── package.json        # Node.js dependencies
│   └── vite.config.js      # Vite build configuration
└── tools/
    ├── jira_tool.py          # JIRA integration wrapper
    ├── confluence_tool.py    # Confluence integration wrapper
    └── mindtouch_tool.py     # MindTouch API integration
```

## 🔌 Integration Details

### JIRA & Confluence (REST API)

The system uses direct REST API integration for JIRA and Confluence:

```python
# JIRA integration example
from tools.jira_tool import JiraTool

jira_tool = JiraTool()
issues = jira_tool.search_issues(query, limit=20)

# Confluence integration example  
from tools.confluence_tool import ConfluenceTool

confluence_tool = ConfluenceTool()
pages = confluence_tool.search_pages(query, limit=20)
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

2. **JIRA/Confluence API Connection Failed**
   - Verify JIRA/Confluence credentials in `.env`
   - Check API token permissions
   - Test connection manually with curl or Postman
   - Ensure correct base URLs are configured

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

## ✨ Current Features

### Frontend (React)
- 🎨 **Modern UI**: Clean, responsive design with Tailwind CSS
- 💬 **Real-time Chat**: Interactive chat interface for natural conversations
- 📱 **Mobile Responsive**: Optimized for all device sizes
- ⚡ **Fast Performance**: Vite-powered development with hot module replacement
- 🔧 **Component Library**: Reusable UI components with Headless UI
- 🎯 **Accessibility**: Built with accessibility best practices

### Backend (FastAPI)
- 🚀 **High Performance**: Async FastAPI server with automatic API documentation
- 🔄 **RESTful API**: Well-structured endpoints for all functionality
- 📊 **Real-time Processing**: Streaming responses for better user experience
- 🔒 **CORS Support**: Properly configured for frontend-backend communication
- 📝 **Auto Documentation**: Swagger UI available at `/docs`
- 🏗️ **Modular Architecture**: Clean separation of concerns

## 🛠️ Development Roadmap

### Phase 1: Enhanced Features
- [ ] User authentication and authorization
- [ ] WebSocket integration for real-time chat
- [ ] Voice input/output implementation
- [ ] Advanced filtering and search options

### Phase 2: Enterprise Features
- [ ] Database integration (MongoDB/PostgreSQL)
- [ ] Multi-tenant organization support
- [ ] Advanced analytics and reporting
- [ ] Custom knowledge base management

### Phase 3: Production & Scaling
- [ ] Docker containerization
- [ ] CI/CD pipeline setup
- [ ] Monitoring and logging integration
- [ ] Performance optimization and caching
- [ ] Load balancing and high availability

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:

1. **Documentation**: Check the troubleshooting section above
2. **System Status**: Review system status for component health
3. **Issues**: Create a GitHub issue for bug reports or feature requests
4. **Discussions**: Use GitHub Discussions for questions and community support

## 🙏 Acknowledgments

- AWS Bedrock for advanced AI capabilities
- LangGraph for workflow orchestration
- Sentence Transformers for semantic search
- Atlassian REST APIs for enterprise integration
- The open-source community for amazing tools and libraries

---



*Modern architecture for intelligent query processing*
