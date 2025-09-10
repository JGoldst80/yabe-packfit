from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Literal, Optional
import math

app = FastAPI(title="PackFit", version="0.1.0")

class PackFitRequest(BaseModel):
    itemType: Literal["tshirt","jeans","hoodie","sweater","shoes","small_electronics","book","board_game","poster_tube","misc_soft","misc_boxable"]
    sizeLabel: Optional[str] = "M"
    weightOz: float = 0
    compressibility: Literal["soft","normal","rigid"] = "normal"
    longSideIn: float = 0
    preferPoly: bool = True

class PackFitResponse(BaseModel):
    chosenPackage: str
    outerDimsIn: List[float]
    cubicInches: float
    uspsDimWeightLb: Optional[int]
    upsFedexDimWeightLb: int
    notes: List[str]
    serviceHints: List[str]

POLY   = [("Poly 9x12",12,9,1.0), ("Poly 10x13",13,10,1.5), ("Poly 12x15.5",15.5,12,2.0)]
BUBBLE = [("Bubble 6x9",9,6,1.0), ("Bubble 8.5x12",12,8.5,1.5)]
BOXES  = [("Box 6x4x4",6,4,4), ("Box 8x6x4",8,6,4), ("Box 9x6x4",9,6,4),
         ("Box 10x8x6",10,8,6), ("Box 12x9x4",12,9,4), ("Box 12x10x4",12,10,4),
         ("Box 14x8x5 (shoe)",14,8,5), ("Box 14x10x6",14,10,6), ("Box 16x12x6",16,12,6),
         ("Box 10x10x10",10,10,10), ("Box 12x12x8",12,12,8)]
TUBES  = [("Tube 3x18",18,3,3), ("Tube 4x24",24,4,4), ("Tri 38x6x6",38,6,6)]

def base_fold(itemType, oz):
    return {
        "tshirt": (10,8,max(0.6,min(1.2,(oz or 10)/10))),
        "jeans": (12,9,2.0), "hoodie": (12,10,3.0), "sweater": (12,9,2.5),
        "shoes": (8,13.5,5.0), "small_electronics": (6,8,4.0), "book": (6,9,1.5),
        "board_game": (9,12,3.0), "poster_tube": (4,24,4.0),
        "misc_soft": (10,8,2.0), "misc_boxable": (8,10,2.0),
    }[itemType]

def size_bump(label):
    m = {"XS":-0.5,"S":-0.25,"M":0,"L":0.5,"XL":1.0,"XXL":1.5,"2XL":1.5,"3XL":2.0}
    return m.get((label or "M").upper(), 0)

def compress(v, mode): return v*(0.75 if mode=="soft" else 1.15 if mode=="rigid" else 1.0)

def choose_pkg(L,W,T, preferPoly=True, longSide=0):
    pools = [POLY,BUBBLE,BOXES,TUBES] if preferPoly else [BOXES,POLY,BUBBLE,TUBES]
    for pool in pools:
        for name,pL,pW,pH in pool:
            fits = (L<=pL and W<=pW and T<=pH) or (longSide and longSide<=pL and max(W,T)<=pW)
            if fits: return (name,pL,pW,pH)
    return BOXES[-1]

def usps_dim(L,W,H):
    cubic = L*W*H
    return None if cubic<=1728 else math.ceil(cubic/166)

def ups_dim(L,W,H): return math.ceil((L*W*H)/139)

@app.post("/packfit/estimate", response_model=PackFitResponse)
def estimate(r: PackFitRequest):
    W,L,T = base_fold(r.itemType, r.weightOz)
    bump = size_bump(r.sizeLabel)
    L2 = compress(L + bump, r.compressibility)
    W2 = compress(W + bump, r.compressibility)
    T2 = compress(T + bump*0.6, r.compressibility)
    name,Lo,Wo,Ho = choose_pkg(L2,W2,T2, r.preferPoly, r.longSideIn)
    cubic = Lo*Wo*Ho
    notes,hints = [],[]
    if name.startswith("Poly"): hints.append("Softpack; Ground Advantage ≤1 lb often cheapest.")
    if cubic > 1728:          hints.append("DIM applies (>1 cu ft). Compare UPS/FedEx 139 vs USPS 166.")
    if "(shoe)" in name:      notes.append("USPS Priority Shoe Box must ship via Priority.")
    return PackFitResponse(name,[round(Lo,2),round(Wo,2),round(Ho,2)],
                           round(cubic,2), usps_dim(Lo,Wo,Ho), ups_dim(Lo,Wo,Ho),
                           notes, hints)
