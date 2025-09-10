from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="PackFit", version="0.1.0")

# --- Health check route ---
@app.get("/ping")
def ping():
    return {"message": "pong"}

# --- Placeholder PackFit route ---
class PackFitRequest(BaseModel):
    itemType: str
    sizeLabel: str = "M"
    weightOz: float = 0

@app.post("/packfit/estimate")
def estimate_packfit(request: PackFitRequest):
    # right now, it just echoes back what you send
    return {
        "chosenPackage": "Poly 10x13",
        "inputs": request.dict(),
        "note": "This is a stub — proves routing works!"
    }
