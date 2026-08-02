import os
import time
from typing import Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI()

# Get connection string from environment variable set in docker-compose.yml
DATABASE_URL = os.getenv("DATABASE_URL", "postgres://app_user:app_password@db:5432/app_db")

def get_db():
    # Retry connection in case Postgres is still starting up
    retries = 5
    while retries > 0:
        try:
            conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
            return conn
        except psycopg2.OperationalError as e:
            retries -= 1
            if retries == 0:
                raise e
            time.sleep(1)

# ==========================================
# STAGE 0: Create & Initialize Database
# ==========================================
def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Create tasks table in Postgres
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT FALSE
        )
    """)
    conn.commit()

    # Seed initial tasks if empty
    cursor.execute("SELECT COUNT(*) as count FROM tasks;")
    result = cursor.fetchone()
    if result["count"] == 0:
        cursor.executemany(
            "INSERT INTO tasks (title, done) VALUES (%s, %s);",
            [
                ("Buy milk", False),
                ("Complete Python assignment", False),
                ("Review SQL queries", True)
            ]
        )
        conn.commit()
    
    cursor.close()
    conn.close()

# Initialize table structure on app startup
@app.on_event("startup")
def startup_event():
    init_db()

# Pydantic models for validation
class TaskCreate(BaseModel):
    title: str

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

# Helper to format row
def format_task(row):
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}

# ==========================================
# STAGE 1: Read Endpoints (GET)
# ==========================================
@app.get("/tasks")
def get_tasks():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks ORDER BY id ASC;")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [format_task(r) for r in rows]

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = %s;", (task_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    return format_task(row)

# ==========================================
# STAGE 2: Create Endpoint (POST)
# ==========================================
@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate):
    if not task.title or task.title.strip() == "":
        raise HTTPException(status_code=400, detail="Title is required")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING *;", 
        (task.title, False)
    )
    new_row = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    return format_task(new_row)

# ==========================================
# STAGE 3: Update & Delete Endpoints (PUT & DELETE)
# ==========================================
@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: TaskUpdate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = %s;", (task_id,))
    existing = cursor.fetchone()
    
    if not existing:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")

    new_title = task.title if task.title is not None else existing["title"]
    new_done = task.done if task.done is not None else existing["done"]

    cursor.execute(
        "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING *;",
        (new_title, new_done, task_id)
    )
    updated_row = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    return format_task(updated_row)

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = %s;", (task_id,))
    conn.commit()
    
    if cursor.rowcount == 0:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")
        
    cursor.close()
    conn.close()
    return None