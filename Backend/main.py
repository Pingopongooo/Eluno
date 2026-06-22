from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import models
import crud
import scheduler
from ai_agent import handle_qc_failure

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start_scheduler()
    yield
    scheduler.stop_scheduler()

app = FastAPI(title="AI OMS API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "AI OMS Backend is running."}

@app.get("/api/lens-types")
def get_lens_types():
    try:
        return crud.get_lens_types()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/inventory")
def get_inventory():
    try:
        return crud.get_inventory()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orders")
def get_orders():
    try:
        return crud.get_all_active_orders()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/orders")
def create_order(order: models.OrderCreate):
    try:
        return crud.create_order(order)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/orders/{order_id}/status")
def update_order_status(order_id: int, status_update: models.StatusUpdate):
    """
    General status update endpoint used for all stage transitions
    EXCEPT QC Failed, which has its own endpoint below.
    Staff reason is optional. If empty, a neutral note is logged.
    """
    try:
        return crud.update_status(order_id, status_update)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/orders/{order_id}/qc-fail")
def mark_qc_failed(order_id: int, status_update: models.StatusUpdate, background_tasks: BackgroundTasks):
    """
    Dedicated QC Fail endpoint.
    
    Step 1 (immediate): Updates status to 'QC Failed' in the database.
                        Returns response to frontend instantly. Staff sees update immediately.
    
    Step 2 (background): Triggers Gemini AI to recalculate predicted delivery date
                         and generate escalation message. Sends email alert.
                         Happens asynchronously — frontend does not wait for this.
    """
    try:
        # Force the status to QC Failed regardless of what was sent
        status_update.status = "QC Failed"
        result = crud.update_status(order_id, status_update)
        
        # Fire AI task in background — does not block the response
        background_tasks.add_task(handle_qc_failure, order_id)
        
        return {**result, "ai_assessment": "QC failure escalation triggered in background."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orders/{order_id}/history")
def get_order_history(order_id: int):
    """Returns the full status history timeline for a specific order."""
    try:
        return crud.get_order_status_history(order_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts")
def get_alerts():
    try:
        return crud.get_alerts()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/orders/{order_id}")
def delete_order(order_id: int):
    try:
        return crud.delete_order(order_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
