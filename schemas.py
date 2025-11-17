"""
Database Schemas for the Clothing Store

Each Pydantic model represents a collection in your MongoDB database.
The collection name is the lowercase of the class name (e.g., Product -> "product").
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List


class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product"
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in USD")
    category: str = Field(..., description="Product category")
    sizes: List[str] = Field(default_factory=lambda: ["S", "M", "L"], description="Available sizes")
    colors: List[str] = Field(default_factory=lambda: ["black", "white"], description="Available colors")
    images: List[str] = Field(default_factory=list, description="Image URLs")
    in_stock: bool = Field(True, description="Whether product is in stock")
    rating: float = Field(4.5, ge=0, le=5, description="Average rating")
    featured: bool = Field(False, description="Featured on the homepage")
    spline_scene: Optional[str] = Field(None, description="Optional Spline 3D scene URL")


class OrderItem(BaseModel):
    product_id: str = Field(..., description="Product ObjectId as string")
    title: str = Field(...)
    size: Optional[str] = Field(None)
    color: Optional[str] = Field(None)
    qty: int = Field(1, ge=1)
    price: float = Field(..., ge=0)


class Customer(BaseModel):
    name: str
    email: EmailStr
    address: Optional[str] = None


class Order(BaseModel):
    """
    Orders collection schema
    Collection name: "order"
    """
    items: List[OrderItem]
    subtotal: float = Field(..., ge=0)
    shipping: float = Field(0, ge=0)
    total: float = Field(..., ge=0)
    customer: Customer
    status: str = Field("placed", description="placed | paid | shipped | delivered | cancelled")
