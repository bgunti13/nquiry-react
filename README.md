# Nquiry - Intelligent Query Processing System

An AI-powered query processing system that automatically routes user queries to appropriate knowledge sources (JIRA, Confluence, MindTouch), performs semantic search, and provides intelligent responses using AWS Bedrock LLM.

**🚧 Migration Status**: This project is transitioning from a Streamlit-based application to a modern React + FastAPI architecture for better performance, scalability, and user experience.

## 🏗️ Project Architecture

### **Current Implementation (Python)**
- **Core Engine**: Python-based intelligent query processor
- **AI Integration**: AWS Bedrock LLM for classification and response formatting
- **Knowledge Sources**: JIRA, Confluence, MindTouch integration
- **Search**: Semantic search with sentence transformers and vector storage
- **Workflow**: LangGraph orchestration

### **Future Implementation (React + FastAPI)**
- **Frontend**: React 18 with Vite and Tailwind CSS
- **Backend**: FastAPI with modern async architecture
- **API**: RESTful design for better client-server separation
- **Deployment**: Scalable microservices architecture

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
- **Voice Input/Output**: Speech-to-text and text-to-speech capabilities
- **Chat History**: Persistent conversation management

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+ (for React frontend)
- AWS Bedrock access with Claude model permissions
- MCP Atlassian server setup (for JIRA/Confluence)
- MindTouch API access (optional)

## 🛠️ Installation & Setup

### Current Python Application

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

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   copy .env.example .env
   ```
   Edit `.env` with your actual credentials.

5. **Configure MCP Atlassian server** (for JIRA/Confluence integration):
   Follow the MCP Atlassian server setup instructions.

6. **Run the application**:
   ```bash
   python main.py
   ```

### Future React + FastAPI Migration

The system is being migrated to a modern React + FastAPI architecture:

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

## 🚀 Future Development (React + FastAPI Migration)

### Planned Architecture
- **Frontend**: React 18 with Vite and Tailwind CSS
- **Backend**: FastAPI with async architecture
- **API Design**: RESTful endpoints for scalability
- **Database**: MongoDB integration for persistent storage
- **Authentication**: JWT-based user authentication
- **Deployment**: Docker containerization and microservices

### Migration Benefits
- 🔧 **Better Performance**: Faster loading and optimized API calls
- 🎨 **Enhanced UX**: Modern responsive design with smooth animations
- 📈 **Scalability**: Separate frontend/backend deployment capability
- 🛠️ **Developer Experience**: Hot module replacement and better debugging tools
- 🏭 **Production Ready**: Proper API documentation and error handling

## 🛠️ Development Roadmap

### Phase 1: Core Migration
- [ ] FastAPI backend setup with core endpoints
- [ ] React frontend with chat interface
- [ ] WebSocket integration for real-time chat
- [ ] Voice input/output implementation

### Phase 2: Advanced Features
- [ ] User authentication and authorization
- [ ] Database integration (MongoDB)
- [ ] Advanced semantic search with vector databases
- [ ] Real-time collaboration features

### Phase 3: Production & Scaling
- [ ] Docker containerization
- [ ] CI/CD pipeline setup
- [ ] Monitoring and logging integration
- [ ] Performance optimization and caching

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
- MCP Atlassian for enterprise integration
- The open-source community for amazing tools and libraries

---

**Built with ❤️ using LangGraph, AWS Bedrock, and Sentence Transformers**

*Ready for the future with React + FastAPI migration*
