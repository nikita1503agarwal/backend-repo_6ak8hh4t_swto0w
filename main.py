import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Student, Course, Result

app = FastAPI(title="Student Result Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Student Result Management API"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# Utility to convert str id to ObjectId

def to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id format")

# Grade calculation helpers

def calculate_grade(marks: float):
    if marks >= 90:
        return "A+", 10.0
    if marks >= 80:
        return "A", 9.0
    if marks >= 70:
        return "B", 8.0
    if marks >= 60:
        return "C", 7.0
    if marks >= 50:
        return "D", 6.0
    if marks >= 40:
        return "E", 5.0
    return "F", 0.0

# Request models

class StudentCreate(Student):
    pass

class CourseCreate(Course):
    pass

class ResultCreate(BaseModel):
    student_id: str
    course_id: str
    marks: float

# Endpoints for Students

@app.post("/api/students")
def create_student(student: StudentCreate):
    student_id = create_document("student", student)
    return {"id": student_id}

@app.get("/api/students")
def list_students():
    docs = get_documents("student")
    # Convert ObjectId to string
    for d in docs:
        d["_id"] = str(d["_id"])
    return docs

# Endpoints for Courses

@app.post("/api/courses")
def create_course(course: CourseCreate):
    course_id = create_document("course", course)
    return {"id": course_id}

@app.get("/api/courses")
def list_courses():
    docs = get_documents("course")
    for d in docs:
        d["_id"] = str(d["_id"])
    return docs

# Endpoints for Results

@app.post("/api/results")
def create_result(result: ResultCreate):
    # Validate referenced documents exist
    if db["student"].count_documents({"_id": to_object_id(result.student_id)}) == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    if db["course"].count_documents({"_id": to_object_id(result.course_id)}) == 0:
        raise HTTPException(status_code=404, detail="Course not found")

    grade, grade_point = calculate_grade(result.marks)
    payload = Result(
        student_id=result.student_id,
        course_id=result.course_id,
        marks=result.marks,
        grade=grade,
        grade_point=grade_point,
    )
    result_id = create_document("result", payload)
    return {"id": result_id, "grade": grade, "grade_point": grade_point}

@app.get("/api/results")
def list_results(student_id: Optional[str] = None):
    filt = {}
    if student_id:
        filt["student_id"] = student_id
    docs = get_documents("result", filt)
    for d in docs:
        d["_id"] = str(d["_id"])
    return docs

# Aggregate: Get transcript for a student

@app.get("/api/students/{student_id}/transcript")
def get_transcript(student_id: str):
    # Fetch student
    student = db["student"].find_one({"_id": to_object_id(student_id)})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Fetch results and join courses
    pipeline = [
        {"$match": {"student_id": student_id}},
        {"$addFields": {"courseObjId": {"$toObjectId": "$course_id"}}},
        {"$lookup": {
            "from": "course",
            "localField": "courseObjId",
            "foreignField": "_id",
            "as": "course"
        }},
        {"$unwind": "$course"}
    ]

    records = list(db["result"].aggregate(pipeline))

    total_points = 0.0
    total_credits = 0.0
    transcript_items = []
    for r in records:
        credits = r["course"].get("credits", 0)
        gp = r.get("grade_point", 0.0)
        total_points += gp * credits
        total_credits += credits
        transcript_items.append({
            "course_code": r["course"].get("code"),
            "course_title": r["course"].get("title"),
            "credits": credits,
            "marks": r.get("marks"),
            "grade": r.get("grade"),
            "grade_point": gp,
        })

    gpa = round(total_points / total_credits, 2) if total_credits > 0 else 0.0

    student["_id"] = str(student["_id"])

    return {
        "student": {
            "id": student["_id"],
            "first_name": student.get("first_name"),
            "last_name": student.get("last_name"),
            "roll_number": student.get("roll_number"),
            "class_name": student.get("class_name"),
            "year": student.get("year"),
        },
        "gpa": gpa,
        "results": transcript_items
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
