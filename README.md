# CTLChat - AI-Powered Team Building & Planning Assistant

CTLChat is a RAG (Retrieval-Augmented Generation) chatbot application that helps you plan team building programs using AI and your organization's knowledge base.

## Features

- **AI-Powered Chat** - Get intelligent responses using Claude AI
- **RAG Mode** - Query your uploaded documents and knowledge base
- **General Knowledge Mode** - Ask questions using Claude's general knowledge
- **Web Search Mode** - Search the web for current information (coming soon)
- **Conversation History** - All conversations are saved and can be resumed
- **Document Upload** - Upload documents (PDF, DOCX, TXT, MD, CSV, XLSX) to your knowledge base
- **Multi-Organization** - Support for multiple organizations with shared and personal documents
- **User Roles** - Admin and user roles with different permissions

## Prerequisites

- Python 3.12+
- Node.js 18+
- npm or yarn

## Project Structure

```
CTLChat/
├── backend/           # Python FastAPI backend
│   ├── src/          # Source code
│   ├── data/         # Document storage
│   ├── scripts/      # Utility scripts
│   └── schema.sql    # Database schema
├── Frontend/         # React frontend
│   └── src/         # Source code
└── venv/            # Python virtual environment
```

## Quick Start

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (in parent directory)
cd ..
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Initialize database with sample data
../venv/bin/python scripts/init_database.py --sample-data

# Start the backend server
cd src
../../venv/bin/python api.py
```

Backend will run on `http://localhost:8000`

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
# Required
ANTHROPIC_API_KEY=your_api_key_here

# Optional (defaults shown)
MODEL_NAME=claude-haiku-4-5-20251001
MAX_TOKENS=4096
TEMPERATURE=0.7
DATABASE_PATH=./ctlchat.db
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

## Troubleshooting

### Backend Issues

**Error: "No module named 'loguru'"**
```bash
source ../venv/bin/activate
pip install -r requirements.txt
```

**Error: Database not found**
```bash
cd backend
../venv/bin/python scripts/init_database.py --sample-data
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

## Tech Stack

### Backend
- **Framework**: FastAPI
- **Database**: SQLite
- **Vector Store**: ChromaDB
- **LLM**: Anthropic Claude
- **Embeddings**: sentence-transformers

### Frontend
- **Framework**: React 18
- **Router**: React Router v7
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui
- **Markdown**: react-markdown

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

## License

MIT
