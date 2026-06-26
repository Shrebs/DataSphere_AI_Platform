from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import pandas as pd
import io

# Import our automated ETL service layer
from services.etl import run_automated_etl

# Import our database tools
from database import init_db, get_db, DatasetMetadata

app = FastAPI(title="DataSphere AI Analytics Platform API")

# Initialize database tables on startup
@app.on_event("startup")
def on_startup():
    init_db()

# Configure Cross-Origin Resource Sharing (CORS) for frontend connection
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
    # 1. Validate file extension
    if not (filename.endswith('.csv') or filename.endswith('.xlsx')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only CSV or Excel files are allowed.")
    
    try:
        # 2. Read file contents into memory
        contents = await file.read()
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
            
        # 3. Calculate initial metadata dimensions
        total_rows = int(df.shape[0])
        total_columns = int(df.shape[1])
        duplicate_rows = int(df.duplicated().sum())

        # 4. Run the data through our automated ETL pipeline (Impute, Encode, Scale)
        etl_processed_df = run_automated_etl(df)
        
        # NOTE: For now, we are processing this data inline. In the next stage, 
        # we will hand this off to our Machine Learning modules!

        # 5. --- DATABASE LOGIC: Save metadata to SQL ---
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
        
        # 6. Build the structural response dictionary for Swagger / Frontend
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
            "message": "File uploaded, validated, and processed through ETL successfully!",
            "data_summary": summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

# API endpoint to see all datasets stored in SQL history
@app.get("/history")
def get_upload_history(db: Session = Depends(get_db)):
    datasets = db.query(DatasetMetadata).all()
    return datasets