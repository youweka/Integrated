from fastapi import FastAPI
from app.api import routes

app = FastAPI(
    title="ZIP File Processor",
    description="Extract and categorize ZIP file contents",
    version="1.0.0"
)

# Include routers
app.include_router(routes.router, prefix="/api/v1", tags=["zip-processing"])

@app.get("/")
async def root():
    return {"message": "ZIP File Processor API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}