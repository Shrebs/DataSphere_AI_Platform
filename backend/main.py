from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import pandas as pd
import io

# Import our database tools
from database import init_db, get_db, DatasetMetadata

app = FastAPI(title="DataSphere AI Analytics Platform API")

# Initialize database tables on startup
@app.on_event("startup")
def on_startup():
    init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Welcome to the DataSphere AI Analytics Platform API!"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    filename = file.filename
    if not (filename.endswith('.csv') or filename.endswith('.xlsx')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only CSV or Excel files are allowed.")
    
    try:
        contents = await file.read()
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
            
        total_rows = int(df.shape[0])
        total_columns = int(df.shape[1])
        duplicate_rows = int(df.duplicated().sum())

        # --- DATABASE LOGIC: Save metadata to SQL ---
        db_dataset = DatasetMetadata(
            filename=filename,
            total_rows=total_rows,
            total_columns=total_columns,
            duplicate_rows=duplicate_rows
        )
        db.add(db_dataset)
        db.commit()
        db.refresh(db_dataset) # Grab the newly generated database ID
        # ---------------------------------------------
        
        summary = {
            "dataset_id": db_dataset.id,
            "filename": filename,
            "total_rows": total_rows,
            "total_columns": total_columns,
            "duplicate_rows": duplicate_rows,
            "columns": list(df.columns),
            "missing_values": {k: int(v) for k, v in df.isnull().sum().to_dict().items()},
            "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()}
        }
        
        return {
            "message": "File uploaded, validated, and saved to database successfully!",
            "data_summary": summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

# New API endpoint to see all datasets stored in SQL
@app.get("/history")
def get_upload_history(db: Session = Depends(get_db)):
    datasets = db.query(DatasetMetadata).all()
    return datasets