"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Student Result Management System Schemas

class Student(BaseModel):
    """
    Students collection schema
    Collection name: "student"
    """
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    roll_number: str = Field(..., description="Unique roll / registration number")
    class_name: str = Field(..., description="Class/Grade e.g. 10th, 12th, BSc-1")
    year: int = Field(..., ge=1900, le=2100, description="Academic year")
    email: Optional[str] = Field(None, description="Contact email")

class Course(BaseModel):
    """
    Courses collection schema
    Collection name: "course"
    """
    code: str = Field(..., description="Course code e.g. MATH101")
    title: str = Field(..., description="Course title")
    credits: float = Field(..., ge=0, description="Credit hours")

class Result(BaseModel):
    """
    Results collection schema
    Collection name: "result"
    """
    student_id: str = Field(..., description="Reference to student _id (string)")
    course_id: str = Field(..., description="Reference to course _id (string)")
    marks: float = Field(..., ge=0, le=100, description="Marks obtained out of 100")
    grade: Optional[str] = Field(None, description="Calculated letter grade")
    grade_point: Optional[float] = Field(None, description="Calculated grade point (0-10 or 0-4 scale)")

# Add your own schemas here:
# --------------------------------------------------

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
