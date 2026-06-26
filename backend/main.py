from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io

app = FastAPI(title="DataSphere AI Analytics Platform API")

# Allow your frontend to talk to your backend seamlessly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # We will restrict this later in deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Welcome to the DataSphere AI Analytics Platform API!"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # 1. Validate file extension
    filename = file.filename
    if not (filename.endswith('.csv') or filename.endswith('.xlsx')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only CSV or Excel files are allowed.")
    
    try:
        # 2. Read file contents into memory
        contents = await file.read()
        
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
            
        # 3. Generate a quick metadata summary for data validation
        summary = {
            "filename": filename,
            
            "total_rows": int(df.shape[0]),
            "total_columns": int(df.shape[1]),
            "columns": list(df.columns),
            "missing_values": df.isnull().sum().to_dict(),
            "duplicate_rows": int(df.duplicated().sum()),
            "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()}
        }
        
        # Change numerical keys/values to standard python ints to ensure JSON serialization works
        summary["missing_values"] = {k: int(v) for k, v in summary["missing_values"].items()}
        
        return {
            "message": "File uploaded and validated successfully!",
            "data_summary": summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")