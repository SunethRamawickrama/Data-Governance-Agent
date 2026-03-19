from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from datetime import datetime
from services.db_service import crud, schemas

import traceback

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://192.168.0.134:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/add_source")
def add_new_source(source: schemas.DataSourceCreate):
    try:

        data = source.model_dump()
        if data.get("metadata") is None:
            data["metadata"] = {}

        data["status"] = "active"
        data["last_ping"] = None
        data["created_at"] = datetime.now()

        result = crud.create_record(
        db_name="data_registry_data",
        table="data_sources",
        data=data
        )

        return {
            "message": "Source added successfully",
            "data": result.rows
        }
    
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            content={"message": f"Error: {str(e)}"},
            status_code=500
        )
    
@app.get("/api/sources")
def get_sources():
    try:
        result = crud.execute_query(
            db_name="data_registry_data",
            sql="SELECT * FROM data_sources ORDER BY created_at DESC;"
        )

        return {
            "data": result.rows
        }

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            content={"message": f"Error: {str(e)}"},
            status_code=500
        )