from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional

app = FastAPI(
    title="Task API",
    version="1.0",
    description="W2 A1 CRUD API Assignment"
)

# --- STAGE 2: IN-MEMORY DATABASE ---
tasks_db = [
    {"id": 1, "title": "Buy groceries", "done": False},
    {"id": 2, "title": "Complete W2 Assignment", "done": True},
    {"id": 3, "title": "Read FastAPI Documentation", "done": False},
]

# Task Models
class TaskCreate(BaseModel):
    title: str

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

# --- STAGE 1: ROOT & HEALTH ENDPOINTS ---
@app.get("/")
def get_root():
    """API description endpoint"""
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }

@app.get("/health")
def get_health():
    """Healthcheck endpoint for monitoring server status"""
    return {"status": "ok"}

# --- STAGE 2: READ ENDPOINTS ---
@app.get("/tasks")
def get_all_tasks():
    """Returns the full list of tasks"""
    return tasks_db

@app.get("/tasks/{task_id}")
def get_single_task(task_id: int):
    """Returns a single task by ID or 404 error"""
    for task in tasks_db:
        if task["id"] == task_id:
            return task
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task {task_id} not found"
    )

# --- STAGE 3: CREATE ENDPOINT ---
@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate):
    """Creates a new task with validation"""
    if not task.title or task.title.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title cannot be empty"
        )
    
    # Calculate next free ID
    next_id = max([t["id"] for t in tasks_db], default=0) + 1
    new_task = {
        "id": next_id,
        "title": task.title,
        "done": False
    }
    tasks_db.append(new_task)
    return new_task

# --- STAGE 4: UPDATE & DELETE ENDPOINTS ---
@app.put("/tasks/{task_id}")
def update_task(task_id: int, task_update: TaskUpdate):
    """Updates a task's title and/or done status"""
    for task in tasks_db:
        if task["id"] == task_id:
            if task_update.title is not None:
                if task_update.title.strip() == "":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Title cannot be empty"
                    )
                task["title"] = task_update.title
            if task_update.done is not None:
                task["done"] = task_update.done
            return task

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task {task_id} not found"
    )

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    """Deletes a task by ID"""
    for index, task in enumerate(tasks_db):
        if task["id"] == task_id:
            tasks_db.pop(index)
            return
            
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task {task_id} not found"
    )
