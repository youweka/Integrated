from fastapi import FastAPI
from api import routes

app = FastAPI(
    title="DN Diagnostics and Analysis Platform API",
    description="API for processing and analyzing Diebold Nixdorf (DN) log files, transaction journals, and registry data.",
    version="1.0.0"
)

# Include routers
app.include_router(routes.router, prefix="/api/v1", tags=["analysis-engine"])

@app.get("/")
async def root():
    return {"message": "ZIP File Processor API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}