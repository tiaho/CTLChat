# CTLChat - AI-Powered Team Building & Planning Assistant

CTLChat is a RAG (Retrieval-Augmented Generation) chatbot application that helps you plan team building programs using AI and your organization's knowledge base.

## Features

### Frontend Features
- **AI-Powered Chat** - Get intelligent responses using Claude AI
- **RAG Mode** - Query your uploaded documents and knowledge base
- **General Knowledge Mode** - Ask questions using Claude's general knowledge
- **Web Search Mode** - Search the web for current information (coming soon)
- **Conversation History** - All conversations are saved and can be resumed
- **Document Upload** - Upload documents (PDF, DOCX, TXT, MD, CSV, XLSX) to your knowledge base
- **Multi-Organization** - Support for multiple organizations with shared and personal documents
- **User Roles** - Admin and user roles with different permissions

### Backend Features
- **Document Processing** - Supports TXT, PDF, DOCX, and Markdown files
- **Scanned PDF Support** - Automatic OCR using Claude's vision API for scanned documents
- **Vector Search** - Uses ChromaDB for efficient semantic search
- **Claude Integration** - Powered by Anthropic's Claude for response generation
- **REST API** - FastAPI server with streaming support
- **Configurable** - Environment-based configuration
- **Pre-built Vector Database** - ChromaDB with embeddings included in repository

## Prerequisites

- **Python** 3.11, 3.12, or 3.13 (not compatible with 3.14+)
- **Node.js** 18+
- **npm** or yarn
- **poppler** (for scanned PDF support)
  - macOS: `brew install poppler`
  - Linux: `sudo apt-get install poppler-utils`

## Project Structure

```
CTLChat/
├── backend/                  # Python FastAPI backend
│   ├── src/                 # Source code
│   │   ├── api.py          # Main API routes
│   │   ├── config.py       # Configuration management
│   │   ├── database.py     # Database operations
│   │   ├── rag_engine.py   # RAG implementation
│   │   ├── vector_store.py # ChromaDB operations
│   │   ├── document_loader.py  # Document processing
│   │   └── utils.py        # Utility functions
│   ├── data/               # Document storage
│   │   ├── curated_data/   # Markdown files (split by ## headers)
│   │   └── program_logs/   # Program logs (character-based chunking)
│   ├── chroma_db/          # Pre-built vector database (included in git)
│   ├── logs/               # Application logs (created on first run)
│   ├── venv/               # Virtual environment (created during setup)
│   ├── scripts/            # Utility scripts
│   │   ├── init_database.py    # Database initialization
│   │   └── ingest_documents.py # Document ingestion (optional)
│   ├── requirements.txt    # Python dependencies
│   ├── setup_venv.sh       # Automated virtual environment setup
│   ├── .env.example        # Environment template
│   └── schema.sql          # Database schema
├── Frontend/               # React frontend
│   └── src/               # Source code
└── README.md              # This file
```

## Quick Start

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Set up virtual environment (automated)
./setup_venv.sh

# Configure environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Initialize database with sample data
venv/bin/python scripts/init_database.py --sample-data

# Start the backend server
cd src
../venv/bin/python api.py
```

Backend will run on `http://localhost:8000`

**Note:** The vector database (`chroma_db/`) with pre-built embeddings is included in the repository, so you don't need to run document ingestion unless you add new documents.

### 2. Frontend Setup

```bash
# In a new terminal, navigate to frontend directory
cd Frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

Frontend will run on `http://localhost:5173`

## Platform-Specific Setup Guides

For detailed platform-specific instructions and troubleshooting:

- **[macOS Setup Guide](backend/README-macOS.md)** - Complete setup instructions for macOS
- **[Windows Setup Guide](backend/README-Windows.md)** - Complete setup instructions for Windows

## Using the Application

1. **Visit the Landing Page**: Open `http://localhost:5173` in your browser

2. **Login**:
   - Click "Get Started"
   - Select a demo user:
     - **John Doe** (user_sample_001) - Regular user
     - **Jane Doe** (user_sample_002) - Admin user
   - Click "Sign In"

3. **Start Chatting**:
   - Click "New Chat" to create a conversation
   - Type your question and press Enter
   - All conversations are automatically saved!

4. **Upload Documents**:
   - Click "Upload" in the sidebar
   - Choose "Personal" or "Organization" (admin only)
   - Select files: .txt, .md, .pdf, .docx, .csv, .xlsx

5. **Query Modes**:
   - Click ⚙️ Settings icon to choose mode:
     - **RAG Mode** - Uses your uploaded documents
     - **General Knowledge** - Uses Claude's built-in knowledge
     - **Web Search** - Coming soon

## Sample Users

After running the database initialization, you'll have:

- **Organization**: Sample Organization (org_sample_001)
- **Users**:
  - John Doe (john.doe@example.com) - User role
  - Jane Doe (jane.doe@example.com) - Admin role

## API Documentation

Once the backend is running, visit:
- **Interactive API Docs**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

## Environment Variables

Required in `backend/.env`:

```env
# Anthropic API Configuration (Required)
ANTHROPIC_API_KEY=your_api_key_here

# Model Configuration (Optional - defaults shown)
MODEL_NAME=claude-haiku-4-5-20251001
MAX_TOKENS=4096
TEMPERATURE=0.7

# ChromaDB Configuration
CHROMA_DB_PATH=./chroma_db
COLLECTION_NAME=ctl_chat_docs

# Document Processing Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RESULTS=5

# Embedding Model
EMBEDDING_MODEL=all-MiniLM-L6-v2

# API Server Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_LEVEL=INFO
LOG_DIR=./logs

# Database Configuration
DATABASE_PATH=./ctlchat.db
```

## Troubleshooting

### Backend Issues

**Error: "No module named 'loguru'"**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

**Error: Database not found**
```bash
cd backend
venv/bin/python scripts/init_database.py --sample-data
```

**Error: "Collection does not exist" or UUID mismatch**
This happens when the vector database collection was recreated while the server was running. Simply restart the API server:
```bash
# Stop the server (Ctrl+C), then restart
cd backend/src
../venv/bin/python api.py
```

**Error: "Unable to get page count. Is poppler installed?"**
Install poppler for scanned PDF support:
```bash
# macOS
brew install poppler

# Linux
sudo apt-get install poppler-utils
```

### Frontend Issues

**Port already in use**
```bash
# The dev server will prompt you to use a different port
# Just press 'y' to continue
```

**Failed to create conversation**
- Verify backend is running: `curl http://localhost:8000/health`
- Check browser console for errors
- Make sure you're logged in

## Tech Stack Documentation

### Programming Languages
- **Python** (3.11, 3.12, or 3.13 required - not compatible with 3.14+)
- **JavaScript/JSX** (ES6+)

### Backend Technologies

#### Core RAG Stack
- **anthropic** (≥0.39.0) - Anthropic Claude SDK
- **chromadb** (≥0.4.22) - Vector database for embeddings
- **sentence-transformers** (≥2.2.2) - Embedding model (all-MiniLM-L6-v2)

#### Web Framework
- **FastAPI** (≥0.109.0) - REST API framework
- **uvicorn** (≥0.27.0) - ASGI server with standard extras
- **python-multipart** (≥0.0.6) - Form data parsing

#### Document Processing
- **pypdf** (≥4.0.0) - PDF text extraction
- **python-docx** (≥1.1.0) - Word document processing
- **markdown** (≥3.5.0) - Markdown file processing
- **pdf2image** (≥1.16.0) - PDF to image conversion for OCR
- **Pillow** (≥10.0.0) - Image processing

#### Utilities
- **python-dotenv** (≥1.0.0) - Environment variable management
- **pydantic** (≥2.5.0) - Data validation
- **pydantic-settings** (≥2.1.0) - Settings management
- **loguru** (≥0.7.2) - Structured logging

#### System Dependencies
- **poppler** - PDF rendering library (required for scanned PDF support)
  - macOS: `brew install poppler`
  - Linux: `sudo apt-get install poppler-utils`

### Frontend Technologies
- **React** 18 - UI framework
- **React Router** v7 - Client-side routing
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - Re-usable component library
- **react-markdown** - Markdown rendering
- **Vite** - Build tool and dev server

### APIs
- **Anthropic Claude API**
  - Text generation (RAG responses and general knowledge)
    - Default model: `claude-haiku-4-5-20251001`
  - Vision API (OCR for scanned PDFs)
    - Uses: `claude-sonnet-4-5-20250929` (vision-capable model)

### Databases
- **ChromaDB** - Vector database for storing document embeddings
  - Collection name: `ctl_chat_docs`
  - Pre-built database included in repository
- **SQLite** - Relational database for application data
  - User management
  - Organization management
  - Conversation history
  - Document metadata
- **Embedding Model**: all-MiniLM-L6-v2 (via sentence-transformers)

### Deployment Platforms
- **Local Development** (runs on localhost:8000 for backend, localhost:5173 for frontend)
- **Compatible with**:
  - AWS (EC2, Lambda, ECS, Elastic Beanstalk)
  - Google Cloud Platform (Compute Engine, Cloud Run, App Engine)
  - Microsoft Azure (Virtual Machines, App Service, Container Instances)
  - Heroku
  - Digital Ocean
  - Vercel (frontend)
  - Railway
  - Render
  - Any platform supporting Python/FastAPI and React/Vite

### Development Tools
- **Node.js** 18+ - JavaScript runtime for frontend development
- **npm** or **yarn** - Package managers
- **Python venv** - Virtual environment management
- **Git** - Version control

## Project Files

### Backend Key Files
- `backend/src/api.py` - Main API routes
- `backend/src/database.py` - Database operations
- `backend/src/rag_engine.py` - RAG implementation
- `backend/src/config.py` - Configuration
- `backend/schema.sql` - Database schema

### Frontend Key Files
- `Frontend/src/App.jsx` - App with routing
- `Frontend/src/pages/ChatPage.jsx` - Main chat interface
- `Frontend/src/pages/LoginPage.jsx` - Login page
- `Frontend/src/pages/LandingPage.jsx` - Landing page
- `Frontend/src/api/client.js` - API client

## Future Plans

- **Refined complexity ratings:** A more nuanced difficulty assessment system to better match activities to group experience levels
- **Enhanced facilitation guides:** Detailed tips, common pitfalls, and troubleshooting advice for each activity
- **Expert insights integration:** Wisdom and best practices from CTLC's veteran facilitators
- **Broader accessibility:** Expanding the platform to serve organizations and communities beyond Cornell

## Challenges We Ran Into

- **Version control learning curve:** Half our team was new to Git, which slowed our initial workflow as we learned to collaborate effectively through version control.
- **Document digitization:** We wanted to include real program logs from past years as training examples, but these handwritten documents proved difficult for Claude's vision capabilities to parse accurately, requiring significant manual cleanup.
- **Development environment inconsistencies:** We encountered platform-specific issues—one team member faced storage limitations while another had to adapt our Mac-based codebase for Windows compatibility.

## License

MIT
