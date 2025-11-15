# CTLChat RAG Backend

A Retrieval-Augmented Generation (RAG) chatbot backend built with FastAPI, ChromaDB, and Claude.

## Features

- **Document Processing**: Supports TXT, PDF, DOCX, and Markdown files
- **Vector Search**: Uses ChromaDB for efficient semantic search
- **Claude Integration**: Powered by Anthropic's Claude for response generation
- **REST API**: FastAPI server with streaming support
- **Configurable**: Environment-based configuration

## Project Structure

```
backend/
├── src/
│   ├── config.py           # Configuration management
│   ├── utils.py            # Utility functions
│   ├── document_loader.py  # Document processing
│   ├── vector_store.py     # ChromaDB operations
│   ├── rag_engine.py       # RAG core logic
│   └── api.py              # FastAPI server
├── scripts/
│   └── ingest_documents.py # Document ingestion script
├── data/
│   ├── curated_data/       # Place your documents here
│   └── program_logs/       # Application logs
├── chroma_db/              # Vector database storage
├── venv/                   # Virtual environment (not in git)
├── requirements.txt        # Python dependencies
├── setup_venv.sh           # Virtual environment setup script
├── .env                    # Environment variables (not in git)
└── .env.example            # Environment template
```

## Setup

### 1. Set Up Virtual Environment

It's recommended to use a Python virtual environment to isolate dependencies:

**Option A: Automated Setup (recommended)**

```bash
cd backend
./setup_venv.sh
```

This script will:
- Create a virtual environment in `backend/venv/`
- Upgrade pip
- Install all dependencies from `requirements.txt`

**Option B: Manual Setup**

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Activate the virtual environment:**
```bash
source venv/bin/activate
```

You'll know the virtual environment is active when you see `(venv)` in your terminal prompt.

**Deactivate when done:**
```bash
deactivate
```

> **Note:** Make sure to activate the virtual environment before running any Python scripts or starting the server.

### 2. Configure Environment Variables

Copy the example environment file and add your Anthropic API key:

```bash
cp .env.example .env
```

Then edit `.env` and add your actual API key:

```bash
ANTHROPIC_API_KEY=your_actual_api_key_here
```

Other settings can be adjusted as needed (see `.env.example` for all available options).

### 3. Add Documents

Place your documents in the `data/curated_data/` directory. Supported formats:
- `.txt` - Plain text files
- `.pdf` - PDF documents
- `.docx` - Word documents
- `.md` - Markdown files

### 4. Ingest Documents

Run the ingestion script to process and index your documents:

```bash
# Make sure virtual environment is activated first
source venv/bin/activate
python scripts/ingest_documents.py
```

This will:
- Load all documents from `data/curated_data/`
- Chunk them into manageable pieces
- Generate embeddings using sentence-transformers
- Store them in ChromaDB

### 5. Start the API Server

```bash
# Make sure virtual environment is activated first
source venv/bin/activate
cd src
python api.py
```

Or using uvicorn directly:

```bash
# Make sure virtual environment is activated first
source venv/bin/activate
cd src
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Health Check
```bash
GET /health
```

### Get Statistics
```bash
GET /stats
```

### Chat (Non-streaming)
```bash
POST /chat
Content-Type: application/json

{
  "query": "What is the main topic of the documents?",
  "top_k": 5,
  "conversation_history": [
    {"role": "user", "content": "Previous question"},
    {"role": "assistant", "content": "Previous answer"}
  ]
}
```

### Chat (Streaming)
```bash
POST /chat/stream
Content-Type: application/json

{
  "query": "Explain the key concepts",
  "top_k": 5
}
```

## Usage Examples

### Using curl

**Simple query:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the main topics?"}'
```

**Streaming query:**
```bash
curl -X POST "http://localhost:8000/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain the key concepts"}' \
  --no-buffer
```

### Using Python

```python
import requests

# Simple query
response = requests.post(
    "http://localhost:8000/chat",
    json={"query": "What are the main topics?"}
)
print(response.json())

# Streaming query
response = requests.post(
    "http://localhost:8000/chat/stream",
    json={"query": "Explain the key concepts"},
    stream=True
)
for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
    if chunk:
        print(chunk, end='', flush=True)
```

## Configuration

All configuration is managed through environment variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | Required |
| `MODEL_NAME` | Claude model to use | claude-3-5-sonnet-20241022 |
| `MAX_TOKENS` | Maximum response tokens | 4096 |
| `TEMPERATURE` | Response randomness (0-1) | 0.7 |
| `CHUNK_SIZE` | Document chunk size | 1000 |
| `CHUNK_OVERLAP` | Overlap between chunks | 200 |
| `TOP_K_RESULTS` | Number of results to retrieve | 5 |
| `EMBEDDING_MODEL` | Sentence transformer model | all-MiniLM-L6-v2 |
| `API_PORT` | API server port | 8000 |

## Development

### Adding New Document Types

To add support for new file formats, edit `document_loader.py`:

1. Add the extension to `supported_extensions`
2. Create a new `_load_<format>()` method
3. Update the `load_file()` method

### Customizing Retrieval

Edit `vector_store.py` to modify:
- Search parameters
- Metadata filtering
- Embedding models

### Customizing Generation

Edit `rag_engine.py` to modify:
- System prompts
- Response formatting
- Context construction

## Troubleshooting

**No documents loaded:**
- Check that documents are in `data/curated_data/`
- Verify file formats are supported
- Check logs in `data/program_logs/`

**API key errors:**
- Ensure `ANTHROPIC_API_KEY` is set in `.env`
- Verify the key is valid

**Empty responses:**
- Run ingestion script to populate vector database
- Check vector store has documents: `GET /stats`

## License

MIT
