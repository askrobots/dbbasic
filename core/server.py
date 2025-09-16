#!/usr/bin/env python3
"""
DBBasic Server - FastAPI wrapper around dbbasic_fast.py

Provides REST API for spreadsheet operations using Polars + DuckDB.
Each user gets their own isolated data directory.

Requirements:
    pip install fastapi uvicorn polars duckdb pyarrow python-multipart aiofiles

Run:
    uvicorn dbbasic_server:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
import polars as pl
import duckdb
import numpy as np
import time
import os
import json
import uuid
from pathlib import Path
import io
import aiofiles
from datetime import datetime

# Initialize FastAPI
app = FastAPI(
    title="DBBasic API",
    description="Spreadsheet operations at 285 million rows/second",
    version="1.0.0"
)

# Enable CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve the main HTML file
@app.get("/")
async def serve_main():
    """Serve the main DBBasic HTML interface"""
    return FileResponse("dbbasic_v1.html")

@app.get("/dbbasic_v1.html")
async def serve_dbbasic_v1():
    """Serve the DBBasic V1 HTML file"""
    return FileResponse("dbbasic_v1.html")

# User data directory
DATA_DIR = Path("user_data")
DATA_DIR.mkdir(exist_ok=True)

# Session storage (in production, use Redis)
sessions = {}

# Request/Response Models
class GenerateRequest(BaseModel):
    rows: int
    columns: Optional[List[str]] = None
    session_id: Optional[str] = None

class CalculateRequest(BaseModel):
    operation: str  # SUM, AVG, COUNT, GROUP BY, etc.
    column: Optional[str] = None
    group_by: Optional[str] = None
    session_id: str

class SQLRequest(BaseModel):
    query: str
    session_id: str

class CommandRequest(BaseModel):
    command: str
    session_id: str

class DataResponse(BaseModel):
    data: List[List[Any]]
    columns: List[Dict[str, Any]]
    rows: int
    execution_time: float
    rows_per_second: Optional[float] = None

class CalculationResponse(BaseModel):
    result: Any
    execution_time: float
    rows_processed: int
    rows_per_second: float

class SessionInfo(BaseModel):
    session_id: str
    created_at: str
    rows: int
    columns: int
    memory_mb: float

# Helper Functions
def get_user_dir(session_id: str) -> Path:
    """Get or create user-specific data directory"""
    user_dir = DATA_DIR / session_id
    user_dir.mkdir(exist_ok=True)
    return user_dir

def get_session_data(session_id: str) -> pl.DataFrame:
    """Load session data from disk or memory"""
    if session_id in sessions:
        return sessions[session_id]

    user_dir = get_user_dir(session_id)
    parquet_file = user_dir / "data.parquet"

    if parquet_file.exists():
        df = pl.read_parquet(parquet_file)
        sessions[session_id] = df
        return df

    return pl.DataFrame()

def save_session_data(session_id: str, df: pl.DataFrame):
    """Save session data to disk and memory"""
    sessions[session_id] = df
    user_dir = get_user_dir(session_id)
    parquet_file = user_dir / "data.parquet"
    df.write_parquet(parquet_file)

# API Endpoints
@app.get("/")
async def root():
    return {
        "name": "DBBasic API",
        "version": "1.0.0",
        "speed": "285 million rows/second",
        "engine": "Polars + DuckDB"
    }

@app.post("/update/cell")
async def update_cell(
    session_id: str = Form(...),
    row: int = Form(...),
    column: str = Form(...),
    value: str = Form(...)
):
    """Update a single cell value"""
    df = get_session_data(session_id)
    if df.is_empty():
        raise HTTPException(status_code=404, detail="No data in session")

    try:
        # Update the value in the DataFrame
        df = df.with_row_count()

        # Convert value to appropriate type based on column
        col_type = df[column].dtype
        if col_type in [pl.Float64, pl.Int64]:
            value = float(value) if '.' in str(value) else int(value)

        # Update the specific cell
        df = df.with_columns(
            pl.when(pl.col("row_nr") == row)
            .then(pl.lit(value))
            .otherwise(pl.col(column))
            .alias(column)
        )

        # Remove the row_nr column
        df = df.drop("row_nr")

        # Save updated data
        save_session_data(session_id, df)

        return {
            "success": True,
            "row": row,
            "column": column,
            "value": value
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/update/batch")
async def update_batch(
    session_id: str = Form(...),
    updates: str = Form(...)  # JSON string of updates
):
    """Update multiple cells at once"""
    import json

    df = get_session_data(session_id)
    if df.is_empty():
        raise HTTPException(status_code=404, detail="No data in session")

    try:
        updates_list = json.loads(updates)

        for update in updates_list:
            row = update['row']
            column = update['column']
            value = update['value']

            # Update each cell
            df = df.with_row_count()

            # Convert value to appropriate type
            col_type = df[column].dtype
            if col_type in [pl.Float64, pl.Int64]:
                value = float(value) if '.' in str(value) else int(value)

            df = df.with_columns(
                pl.when(pl.col("row_nr") == row)
                .then(pl.lit(value))
                .otherwise(pl.col(column))
                .alias(column)
            )

            df = df.drop("row_nr")

        # Save updated data
        save_session_data(session_id, df)

        return {
            "success": True,
            "updates": len(updates_list)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/add/row")
async def add_row(
    session_id: str = Form(...),
    data: Optional[str] = Form(None)  # JSON string of row data
):
    """Add a new row to the data"""
    import json

    df = get_session_data(session_id)

    try:
        if data:
            row_data = json.loads(data)
        else:
            # Create empty row with default values
            row_data = {col: None for col in df.columns}

        # Create new row as DataFrame
        new_row = pl.DataFrame([row_data])

        # Append to existing data
        df = pl.concat([df, new_row])

        # Save updated data
        save_session_data(session_id, df)

        return {
            "success": True,
            "rows": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/delete/row")
async def delete_row(
    session_id: str = Form(...),
    row: int = Form(...)
):
    """Delete a row from the data"""
    df = get_session_data(session_id)
    if df.is_empty():
        raise HTTPException(status_code=404, detail="No data in session")

    try:
        # Add row numbers and filter out the specified row
        df = df.with_row_count()
        df = df.filter(pl.col("row_nr") != row)
        df = df.drop("row_nr")

        # Save updated data
        save_session_data(session_id, df)

        return {
            "success": True,
            "rows": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/session/create")
async def create_session():
    """Create a new user session"""
    session_id = str(uuid.uuid4())
    sessions[session_id] = pl.DataFrame()

    return SessionInfo(
        session_id=session_id,
        created_at=datetime.now().isoformat(),
        rows=0,
        columns=0,
        memory_mb=0
    )

@app.get("/session/{session_id}/info")
async def get_session_info(session_id: str):
    """Get session information"""
    df = get_session_data(session_id)

    return SessionInfo(
        session_id=session_id,
        created_at=datetime.now().isoformat(),
        rows=len(df),
        columns=len(df.columns),
        memory_mb=df.estimated_size('mb') if len(df) > 0 else 0
    )

@app.get("/session/{session_id}/data")
async def get_session_data_endpoint(session_id: str):
    """Get the actual data from a session"""
    df = get_session_data(session_id)

    if df.is_empty():
        return {
            "data": [],
            "columns": [],
            "rows": 0
        }

    # Convert to list format for spreadsheet
    data_list = df.to_numpy().tolist()
    columns = [
        {"title": col, "width": 120, "type": "numeric" if df[col].dtype in [pl.Float64, pl.Int64] else "text"}
        for col in df.columns
    ]

    return {
        "data": data_list,
        "columns": columns,
        "rows": len(df)
    }

@app.post("/generate", response_model=DataResponse)
async def generate_data(request: GenerateRequest):
    """Generate test data with specified rows"""
    start_time = time.time()

    # Get or create session
    session_id = request.session_id or str(uuid.uuid4())
    n = request.rows

    # Generate data using Polars (FAST!)
    data = {
        'ID': range(1, n + 1),
        'Value': np.random.randn(n) * 100,
        'Category': np.random.choice(['A', 'B', 'C', 'D'], n),
        'Price': np.random.uniform(10, 1000, n),
        'Quantity': np.random.randint(1, 100, n),
    }

    df = pl.DataFrame(data)

    # Add calculated column
    df = df.with_columns(
        (pl.col('Price') * pl.col('Quantity')).alias('Total')
    )

    # Save to session
    save_session_data(session_id, df)

    # Convert to response format
    elapsed = time.time() - start_time

    # Convert to list format for JSON response
    data_list = df.to_numpy().tolist()
    columns = [
        {"title": col, "width": 120, "type": "numeric" if df[col].dtype in [pl.Float64, pl.Int64] else "text"}
        for col in df.columns
    ]

    return DataResponse(
        data=data_list[:100],  # Return first 100 rows for display
        columns=columns,
        rows=len(df),
        execution_time=elapsed,
        rows_per_second=n / elapsed
    )

@app.post("/calculate", response_model=CalculationResponse)
async def calculate(request: CalculateRequest):
    """Perform calculations on data"""
    start_time = time.time()

    df = get_session_data(request.session_id)
    if df.is_empty():
        raise HTTPException(status_code=404, detail="No data in session")

    result = None
    operation = request.operation.upper()

    if operation == "SUM":
        if request.column and request.column in df.columns:
            result = df[request.column].sum()
        else:
            result = df.select(pl.sum(pl.all())).to_numpy()[0].tolist()

    elif operation == "AVG" or operation == "MEAN":
        if request.column and request.column in df.columns:
            result = df[request.column].mean()
        else:
            result = df.select(pl.mean(pl.all())).to_numpy()[0].tolist()

    elif operation == "COUNT":
        result = len(df)

    elif operation == "MAX":
        if request.column and request.column in df.columns:
            result = df[request.column].max()

    elif operation == "MIN":
        if request.column and request.column in df.columns:
            result = df[request.column].min()

    elif operation == "GROUP" and request.group_by:
        if request.column:
            grouped = df.group_by(request.group_by).agg(pl.col(request.column).sum())
            result = grouped.to_dict(as_series=False)
        else:
            result = {"error": "Column required for GROUP BY"}

    elapsed = time.time() - start_time
    rows = len(df)

    return CalculationResponse(
        result=result,
        execution_time=elapsed,
        rows_processed=rows,
        rows_per_second=rows / elapsed if elapsed > 0 else 0
    )

@app.post("/sql")
async def execute_sql(request: SQLRequest):
    """Execute SQL query using DuckDB"""
    start_time = time.time()

    df = get_session_data(request.session_id)
    if df.is_empty():
        raise HTTPException(status_code=404, detail="No data in session")

    # Create DuckDB connection
    conn = duckdb.connect(':memory:')

    # Register DataFrame as table
    conn.register('sheet', df)

    try:
        # Execute query
        result = conn.execute(request.query).pl()

        elapsed = time.time() - start_time

        # Convert result to response format
        data_list = result.to_numpy().tolist() if not result.is_empty() else []
        columns = [
            {"title": col, "width": 120}
            for col in result.columns
        ]

        return DataResponse(
            data=data_list[:1000],  # Limit response size
            columns=columns,
            rows=len(result),
            execution_time=elapsed,
            rows_per_second=len(df) / elapsed if elapsed > 0 else 0
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SQL Error: {str(e)}")
    finally:
        conn.close()

@app.post("/command")
async def execute_command(request: CommandRequest):
    """Execute DBBasic command"""
    cmd = request.command.upper().strip()
    session_id = request.session_id

    if cmd.startswith("GENERATE"):
        # Parse: GENERATE 1000 rows
        import re
        match = re.match(r'GENERATE\s+(\d+)\s+ROWS?', cmd)
        if match:
            rows = int(match.group(1))
            gen_request = GenerateRequest(rows=rows, session_id=session_id)
            return await generate_data(gen_request)

    elif cmd.startswith("CALC"):
        # Parse: CALC SUM(column)
        import re
        match = re.match(r'CALC\s+(\w+)\(([\w\s]+)\)', cmd)
        if match:
            operation = match.group(1)
            column = match.group(2).strip()
            calc_request = CalculateRequest(
                operation=operation,
                column=column,
                session_id=session_id
            )
            return await calculate(calc_request)

    elif cmd.startswith("SQL"):
        # Parse: SQL SELECT * FROM sheet
        query = cmd[3:].strip()
        sql_request = SQLRequest(query=query, session_id=session_id)
        return await execute_sql(sql_request)

    else:
        raise HTTPException(status_code=400, detail=f"Unknown command: {cmd}")

@app.post("/upload/csv")
async def upload_csv(
    file: UploadFile = File(...),
    session_id: str = Form(...)
):
    """Upload CSV file"""
    start_time = time.time()

    # Read CSV into Polars
    contents = await file.read()
    df = pl.read_csv(io.BytesIO(contents))

    # Save to session
    save_session_data(session_id, df)

    elapsed = time.time() - start_time

    return {
        "filename": file.filename,
        "rows": len(df),
        "columns": len(df.columns),
        "execution_time": elapsed,
        "rows_per_second": len(df) / elapsed
    }

@app.get("/download/csv")
async def download_csv(session_id: str):
    """Download data as CSV"""
    df = get_session_data(session_id)
    if df.is_empty():
        raise HTTPException(status_code=404, detail="No data in session")

    # Convert to CSV
    csv_buffer = io.StringIO()
    df.write_csv(csv_buffer)
    csv_buffer.seek(0)

    return StreamingResponse(
        io.BytesIO(csv_buffer.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=dbbasic_{session_id}.csv"}
    )

@app.get("/download/parquet")
async def download_parquet(session_id: str):
    """Download data as Parquet (much faster and smaller)"""
    df = get_session_data(session_id)
    if df.is_empty():
        raise HTTPException(status_code=404, detail="No data in session")

    user_dir = get_user_dir(session_id)
    parquet_file = user_dir / "data.parquet"

    if parquet_file.exists():
        return FileResponse(
            parquet_file,
            media_type="application/octet-stream",
            filename=f"dbbasic_{session_id}.parquet"
        )
    else:
        raise HTTPException(status_code=404, detail="Parquet file not found")

@app.post("/benchmark")
async def run_benchmark(session_id: str = Form(...)):
    """Run performance benchmark"""
    results = []

    # Generate test data
    df = pl.DataFrame({
        'ID': range(1, 1000001),
        'Value': np.random.randn(1000000) * 100,
        'Category': np.random.choice(['A', 'B', 'C', 'D'], 1000000),
        'Price': np.random.uniform(10, 1000, 1000000),
        'Quantity': np.random.randint(1, 100, 1000000),
    })

    df = df.with_columns(
        (pl.col('Price') * pl.col('Quantity')).alias('Total')
    )

    save_session_data(session_id, df)
    rows = len(df)

    # Benchmark 1: SUM
    start = time.time()
    total = df['Total'].sum()
    sum_time = time.time() - start
    results.append({
        "operation": "SUM",
        "time": sum_time,
        "rows_per_second": rows / sum_time,
        "result": float(total)
    })

    # Benchmark 2: GROUP BY
    start = time.time()
    grouped = df.group_by('Category').agg(pl.col('Total').sum())
    group_time = time.time() - start
    results.append({
        "operation": "GROUP BY",
        "time": group_time,
        "rows_per_second": rows / group_time
    })

    # Benchmark 3: FILTER
    start = time.time()
    filtered = df.filter(pl.col('Price') > 500)
    filter_time = time.time() - start
    results.append({
        "operation": "FILTER",
        "time": filter_time,
        "rows_per_second": rows / filter_time,
        "matches": len(filtered)
    })

    # Benchmark 4: SORT
    start = time.time()
    sorted_df = df.sort('Total', descending=True)
    sort_time = time.time() - start
    results.append({
        "operation": "SORT",
        "time": sort_time,
        "rows_per_second": rows / sort_time
    })

    # Benchmark 5: Complex SQL
    conn = duckdb.connect(':memory:')
    conn.register('sheet', df)
    start = time.time()
    result = conn.execute("""
        SELECT Category,
               COUNT(*) as count,
               AVG(Price) as avg_price,
               SUM(Total) as total_revenue
        FROM sheet
        GROUP BY Category
        ORDER BY total_revenue DESC
    """).pl()
    sql_time = time.time() - start
    conn.close()

    results.append({
        "operation": "Complex SQL",
        "time": sql_time,
        "rows_per_second": rows / sql_time
    })

    # Calculate average
    total_ops = sum(r['rows_per_second'] for r in results)
    avg_speed = total_ops / len(results)

    return {
        "results": results,
        "average_speed": avg_speed,
        "rows_tested": rows,
        "summary": f"Average: {avg_speed:,.0f} operations/second"
    }

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete session and its data"""
    # Remove from memory
    if session_id in sessions:
        del sessions[session_id]

    # Remove from disk
    user_dir = get_user_dir(session_id)
    if user_dir.exists():
        import shutil
        shutil.rmtree(user_dir)

    return {"message": "Session deleted", "session_id": session_id}

if __name__ == "__main__":
    import uvicorn
    print("""
╔══════════════════════════════════════════════════╗
║  DBBasic Server - FastAPI + Polars + DuckDB     ║
║                                                  ║
║  Endpoints:                                      ║
║  POST /session/create    - Create new session   ║
║  POST /generate         - Generate test data    ║
║  POST /calculate        - Run calculations      ║
║  POST /sql             - Execute SQL queries    ║
║  POST /benchmark       - Run performance test   ║
║                                                  ║
║  Starting server on http://localhost:8000       ║
╚══════════════════════════════════════════════════╝
    """)

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)