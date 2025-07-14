# Text-to-SQL AI System

A sophisticated AI-powered system that converts natural language queries into SQL statements with high accuracy and error handling capabilities. The system features a modern React frontend, FastAPI backend, and a comprehensive text-to-SQL engine with multiple generation strategies.

## Author
Michael Jonathan Halim
<br>13521124
<br>Institut Teknologi Bandung
<br>IF4092 Tugas Akhir

## Features

### Core Capabilities
- **Natural Language to SQL**: Convert English and Indonesian queries to SQL statements
- **Multi-Strategy Generation**: 5 different SQL generation strategies (baseline, v1-v5) with increasing sophistication
- **Error Handling**: Multi-stage error correction and query refinement
- **Context Awareness**: Retrieval-augmented generation with relevant examples
- **Schema Linking**: Intelligent database schema understanding and linking
- **Query Evaluation**: Comprehensive evaluation and scoring system

### User Interface
- **Modern React Frontend**: Clean, responsive UI built with React 19 and Tailwind CSS
- **Real-time Chat Interface**: Interactive chat experience for SQL generation
- **Chat History**: Persistent conversation history with user authentication
- **Feedback System**: User feedback collection for continuous improvement
- **Multi-language Support**: English and Indonesian language detection and processing

### Technical Features
- **AI Agent Workflow**: LangGraph-powered intelligent agent with multi-step reasoning
- **Database Integration**: PostgreSQL support with query execution capabilities
- **Authentication System**: JWT-based user authentication and authorization
- **Docker Support**: Containerized deployment for both frontend and backend
- **Incremental Query Building**: Step-by-step query construction with validation

## Architecture

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │  Text-to-SQL    │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   Engine        │
│                 │    │                 │    │                 │
│ • Chat UI       │    │ • Authentication│    │ • Query Gen     │
│ • History       │    │ • API Routes    │    │ • Components    │
│ • Feedback      │    │ • AI Agent      │    │ • Evaluator     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Database      │
                       │   (PostgreSQL)  │
                       │                 │
                       │ • User          │
                       │ • History       │
                       │ • Chat          │
                       │ • Feedback      │
                       └─────────────────┘
```

### Text-to-SQL Framework

The core engine implements a sophisticated multi-stage framework:

1. **Language Detection**: Automatically detects English/Indonesian queries
2. **Intent Recognition**: Classifies query intent and complexity
3. **Prompt Rewriting**: Enhances and clarifies user queries
4. **Schema Linking**: Maps natural language to database schema
5. **Context Retrieval**: Finds relevant examples from knowledge base
6. **SQL Generation**: Multiple strategies from baseline to advanced
7. **Error Handling**: Multi-stage validation and correction
8. **Evaluation**: Comprehensive scoring and quality assessment

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: Database ORM
- **PostgreSQL**: Primary database
- **LangGraph**: AI agent workflow management
- **Transformers**: Hugging Face models for NLP
- **Sentence Transformers**: Semantic similarity and embeddings
- **PyTorch**: Deep learning framework

### Frontend
- **React 19**: Modern React with latest features
- **Tailwind CSS**: Utility-first CSS framework
- **Vite**: Fast build tool and development server
- **React Router**: Client-side routing
- **React Hot Toast**: Notification system

### AI/ML
- **LangChain**: LLM application framework
- **Sentence Transformers**: Embedding models
- **Custom NLP Framework**: Multi-strategy text-to-SQL conversion
- **Error Correction**: Multi-stage validation and refinement

## Installation

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 12+
- Docker (optional)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials and API keys
```

5. Run the backend server:
```bash
uvicorn main:app
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

### Docker Deployment

Build individual containers:

```bash
# Backend
cd backend
docker build -t text-to-sql-backend .
docker run -p 8000:8000 text-to-sql-backend

# Frontend
cd frontend
docker build -t text-to-sql-frontend .
docker run -p 8080:8080 text-to-sql-frontend
```

## Usage

### Basic Usage

1. **Start the Application**: Launch both backend and frontend servers
2. **Create Account**: Register a new user account
3. **Ask Questions**: Type natural language queries about your database
4. **Get SQL**: Receive generated SQL with explanations
5. **Provide Feedback**: Rate results to improve the system

### API Endpoints

#### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login

#### Chat
- `POST /chat/query` - Generate SQL from natural language
- `GET /chat/histories` - Get user's chat history
- `GET /chat/history/{chat_id}` - Get specific chat
- `DELETE /chat/history/{chat_id}` - Delete chat history
- `POST /chat/feedback` - Submit feedback

### Configuration

The system supports extensive configuration through the `Config` class:

```python
from text_to_sql import (
    Config,
    LLMConfig,
    SLConfig,
    ContextConfig,
    QueryConfig,
)
import os

config = Config(
    max_retry_attempt=5,
    rewriter_config=LLMConfig(
        type="api",
        model=MODEL,
        provider=PROVIDER,
        api_key=os.getenv(f"API_KEY_{provider_key}"),
    ),
    query_generator_config=LLMConfig(
        type="api",
        model=MODEL,
        provider=PROVIDER,
        api_key=os.getenv(f"API_KEY_{provider_key}"),
    ),
    schema_linker_config=SLConfig(
        type="api",
        model=MODEL,
        provider=PROVIDER,
        api_key=os.getenv(f"API_KEY_{provider_key}"),
        schema_path=f"../files/schema/{DATABASE}.txt",
        metadata_path=f"../files/metadata/{DATABASE}.json",
    ),
    retrieve_context_config=ContextConfig(data_path=f"../files/dataset/dataset_{DATABASE}_example.csv"),
    query_executor_config = QueryConfig(
        host=os.getenv(f"DB_HOST_{db_key}"),
        database=os.getenv(f"DB_DATABASE_{db_key}"),
        user=os.getenv(f"DB_USER_{db_key}"),
        password=os.getenv(f"DB_PASSWORD_{db_key}"),
        port=os.getenv(f"DB_PORT_{db_key}"),
    ),
)
```

### SQL Generation Strategies

1. **Baseline**: Basic LLM generation
2. **V1**: Adds query rewriting and example retrieval
3. **V2**: Includes multi-stage error handling
4. **V3**: Implements schema linking
5. **V4**: Implements incremental query building without schema linking
6. **V5**: Implements incremental query building with schema linking

## Development

### Project Structure

```
text-to-sql/
├── backend/                # FastAPI backend
│   ├── ai_agent/           # LangGraph AI agent
│   ├── database/           # Database models and connection
│   ├── files/              # All necessary files
│   ├── models/             # Pydantic models
│   ├── routers/            # API route handlers
│   ├── text_to_sql/        # Text-to-SQL framework
│   ├── utils/              # Utility functions
│   └── main.py             # FastAPI application
├── frontend/               # React frontend
│   ├── src/
│   │   ├── pages/          # React pages
│   └── public/             # Static assets
├── text_to_sql/            # Core text-to-SQL engine
│   ├── common/             # Configuration and models
│   ├── core/               # Core processing modules
│   ├── experiment/         # Files for experiment
│   ├── files/              # All necessary files
│   ├── tools/              # Additional tools
│   └── text_to_sql.py      # Main engine class
└── README.md               # This file
```

## Acknowledgments

- Built with modern AI/ML frameworks and libraries
- Inspired by state-of-the-art text-to-SQL research
- Community contributions and feedback
