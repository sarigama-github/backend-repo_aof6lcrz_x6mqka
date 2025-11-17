import os
from typing import List, Optional, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Product as ProductSchema, Order as OrderSchema

app = FastAPI(title="Clothing Store API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def serialize_id(value: Any):
    try:
        if isinstance(value, ObjectId):
            return str(value)
    except Exception:
        pass
    return value


def serialize_doc(doc: dict) -> dict:
    if not doc:
        return doc
    out = {}
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            out[k] = str(v)
        elif isinstance(v, list):
            out[k] = [serialize_id(i) for i in v]
        elif isinstance(v, dict):
            out[k] = {kk: serialize_id(vv) for kk, vv in v.items()}
        else:
            out[k] = v
    return out


@app.get("/")
def read_root():
    return {"message": "Clothing Store API running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set",
        "database_name": "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": [],
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["connection_status"] = "Connected"
            try:
                response["collections"] = db.list_collection_names()[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:80]}"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


@app.get("/api/products", response_model=List[ProductSchema])
def list_products():
    try:
        products = get_documents("product")
        # If no products, auto-seed a few featured ones
        if not products:
            seed_products()
            products = get_documents("product")
        return [ProductSchema(**{k: v for k, v in serialize_doc(p).items() if k != "_id"}) for p in products]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/featured", response_model=List[ProductSchema])
def list_featured():
    try:
        featured = get_documents("product", {"featured": True})
        if not featured:
            # ensure seed exists
            seed_products()
            featured = get_documents("product", {"featured": True})
        return [ProductSchema(**{k: v for k, v in serialize_doc(p).items() if k != "_id"}) for p in featured]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class OrderCreate(OrderSchema):
    pass


@app.post("/api/orders")
def create_order(order: OrderCreate):
    try:
        order_id = create_document("order", order)
        return {"order_id": order_id, "status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/schema")
def get_schema():
    """Expose schemas for tooling/viewers."""
    return {
        "product": ProductSchema.model_json_schema(),
        "order": OrderSchema.model_json_schema(),
    }


# --- Utilities ---

def seed_products():
    """Insert a small catalog if empty."""
    try:
        if db is None:
            return
        count = db["product"].count_documents({})
        if count > 0:
            return
        sample = [
            {
                "title": "AeroFlex Hoodie",
                "description": "Lightweight performance hoodie with breathable fabric and ergonomic fit.",
                "price": 69.0,
                "category": "Hoodies",
                "sizes": ["S", "M", "L", "XL"],
                "colors": ["black", "heather gray", "navy"],
                "images": [
                    "https://images.unsplash.com/photo-1503341455253-b2e723bb3dbb?q=80&w=1600&auto=format&fit=crop",
                ],
                "in_stock": True,
                "rating": 4.7,
                "featured": True,
                "spline_scene": "https://prod.spline.design/ZK9m7m7H6cD6JX6R/scene.splinecode",
            },
            {
                "title": "CloudNine Tee",
                "description": "Ultra-soft cotton tee with a relaxed, modern silhouette.",
                "price": 29.0,
                "category": "T-Shirts",
                "sizes": ["XS", "S", "M", "L", "XL"],
                "colors": ["white", "black", "sage"],
                "images": [
                    "https://images.unsplash.com/photo-1516826957135-700dedea698c?q=80&w=1600&auto=format&fit=crop",
                ],
                "in_stock": True,
                "rating": 4.6,
                "featured": True,
                "spline_scene": None,
            },
            {
                "title": "MotionLite Joggers",
                "description": "Tapered joggers with 4-way stretch and zip pockets.",
                "price": 59.0,
                "category": "Bottoms",
                "sizes": ["S", "M", "L", "XL"],
                "colors": ["charcoal", "olive"],
                "images": [
                    "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?q=80&w=1600&auto=format&fit=crop",
                ],
                "in_stock": True,
                "rating": 4.5,
                "featured": False,
                "spline_scene": None,
            },
            {
                "title": "Luxe Layer Jacket",
                "description": "Water-resistant shell with minimalist lines and premium finish.",
                "price": 119.0,
                "category": "Outerwear",
                "sizes": ["S", "M", "L"],
                "colors": ["stone", "black"],
                "images": [
                    "https://images.unsplash.com/photo-1539533113208-f6df8cc8b543?q=80&w=1600&auto=format&fit=crop",
                ],
                "in_stock": True,
                "rating": 4.8,
                "featured": False,
                "spline_scene": None,
            },
        ]
        for p in sample:
            db["product"].insert_one(p)
    except Exception:
        # best-effort seed; ignore errors
        pass


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
