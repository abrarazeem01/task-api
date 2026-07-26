# task-api
## W3-A1: SQLite Database Integration (Python FastAPI)

### Why SQLite?
SQLite was chosen because it is serverless, lightweight, and stores all data in a local file (`tasks.db`), ensuring tasks persist across server restarts.

### Database Location
The database is stored at the project root: `./tasks.db`

### How to Run
1. Activate venv: `.\venv\Scripts\activate`
2. Run server: `uvicorn main:app --reload`