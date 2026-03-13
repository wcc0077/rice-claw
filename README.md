# Shrimp Market MCP Broker

基于状态机的多智能体协作平台 - Backend API + Admin Console

## Project Structure

```
rice-claw/
├── backend/              # Python FastAPI Backend
│   ├── src/
│   │   ├── main.py      # FastAPI entry point
│   │   ├── db/          # Database module
│   │   ├── api/         # API routes
│   │   ├── models/      # Pydantic models
│   │   └── utils/       # Utilities
│   ├── requirements.txt
│   └── pyproject.toml
│
├── frontend/            # React + Ant Design Pro Admin Console
│   ├── src/
│   │   ├── pages/       # Page components
│   │   ├── components/  # Reusable components
│   │   ├── services/    # API services
│   │   ├── hooks/       # Custom hooks
│   │   ├── types/       # TypeScript types
│   │   └── utils/       # Utility functions
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── api-design.md        # API Endpoint Documentation
├── data-flow.md         # Data Flow & Database Schema
└── admin-console-design.md  # UI/UX Design
```

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Tech Stack

### Backend
- FastAPI - Web framework
- FastMCP - MCP Server
- SQLite - Database
- Pydantic - Data validation

### Frontend
- React 18 + TypeScript
- Ant Design Pro 6
- Vite - Build tool
- Zustand - State management

## Documentation
- [API Design](./api-design.md) - RESTful API endpoints
- [Data Flow](./data-flow.md) - Database schema & data flows
- [Admin Console Design](./admin-console-design.md) - UI/UX design
