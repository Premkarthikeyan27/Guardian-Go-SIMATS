from fastapi import APIRouter, HTTPException
from datetime import datetime
from backend.services.verification_service import get_guardians_list
from backend.services.booking_service import list_bookings
from backend.database import get_db_connection
from backend.models import dicts_from_rows, dict_from_row
from backend.schemas import DependentCreate, DependentUpdate

router = APIRouter(prefix="/api/v1/parent", tags=["parent"])

@router.get("/guardians")
def list_parent_guardians():
    return get_guardians_list()

@router.get("/bookings")
def list_parent_user_bookings(parent_id: int = 1):
    return list_bookings(role="parent", user_id=parent_id)

@router.get("/dependents")
def list_parent_dependents(parent_id: int = 1):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dependents WHERE parent_id = ?", (parent_id,))
    rows = cursor.fetchall()
    conn.close()
    return dicts_from_rows(rows)

@router.post("/dependents")
def add_parent_dependent(req: DependentCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO dependents (parent_id, name, age, special_needs, allergies, instructions, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (req.parent_id or 1, req.name, req.age, req.special_needs or "None", req.allergies or "None", req.instructions or "", now_str, now_str))
    dep_id = cursor.lastrowid
    conn.commit()
    
    cursor.execute("SELECT * FROM dependents WHERE id = ?", (dep_id,))
    row = cursor.fetchone()
    conn.close()
    return dict_from_row(row)

@router.put("/dependents/{id}")
def update_parent_dependent(id: int, req: DependentUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("SELECT * FROM dependents WHERE id = ?", (id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Dependent profile not found")
    
    ex_dict = dict(existing)
    name = req.name if req.name is not None else ex_dict["name"]
    age = req.age if req.age is not None else ex_dict["age"]
    special_needs = req.special_needs if req.special_needs is not None else ex_dict["special_needs"]
    allergies = req.allergies if req.allergies is not None else ex_dict["allergies"]
    instructions = req.instructions if req.instructions is not None else ex_dict["instructions"]
    
    cursor.execute("""
        UPDATE dependents
        SET name = ?, age = ?, special_needs = ?, allergies = ?, instructions = ?, updated_at = ?
        WHERE id = ?
    """, (name, age, special_needs, allergies, instructions, now_str, id))
    conn.commit()
    
    cursor.execute("SELECT * FROM dependents WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()
    return dict_from_row(row)

@router.delete("/dependents/{id}")
def delete_parent_dependent(id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM dependents WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"Dependent #{id} removed"}
