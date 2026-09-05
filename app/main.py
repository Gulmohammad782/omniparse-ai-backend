from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Form, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import Optional

from app.services.extraction_service import extract_document_from_bytes
from app.db.session import engine, get_db
from app.models.database_model import (
    Base, InvoiceDBModel, BOEDbModel, AadhaarDbModel, PanDbModel, BillsDbModel, ChallanDbModel, UserDBModel
)
import json

Base.metadata.create_all(bind=engine)

app = FastAPI(title="OmniParse AI Enterprise Backend", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "https://omniparse-ai-backend.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

class UserCreateSchema(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = ""
    mobile_number: Optional[str] = ""
    photo_url: Optional[str] = ""
    is_admin: Optional[bool] = False

class UserUpdateSchema(BaseModel):
    full_name: Optional[str] = None
    mobile_number: Optional[str] = None
    photo_url: Optional[str] = None
    is_admin: Optional[bool] = None
    can_access_invoices: Optional[bool] = None
    can_access_boe: Optional[bool] = None
    can_access_ids: Optional[bool] = None
    can_access_bills: Optional[bool] = None
    can_access_challans: Optional[bool] = None
    allow_password_change: Optional[bool] = None
    new_password: Optional[str] = None

class PasswordChangeSchema(BaseModel):
    old_password: str
    new_password: str

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        user_id = token.split("-")[-1]
        user = db.query(UserDBModel).filter(UserDBModel.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

@app.on_event("startup")
def seed_default_admin():
    db = next(get_db())
    try:
        admin_user = db.query(UserDBModel).filter(UserDBModel.username == "admin").first()
        if not admin_user:
            default_user = UserDBModel(
                username="admin",
                hashed_password=get_password_hash("OmniParse@2026"),
                full_name="System Administrator",
                is_admin=True,
                allow_password_change=True,
                can_access_invoices=True,
                can_access_boe=True,
                can_access_ids=True,
                can_access_bills=True,
                can_access_challans=True
            )
            db.add(default_user)
            db.commit()
            print("Default admin user seeded successfully.")
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"status": "online", "service": "OmniParse AI Backend Enterprise"}

@app.post("/api/v1/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(UserDBModel).filter(UserDBModel.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {
        "access_token": f"omniparse-secure-token-{user.id}", 
        "token_type": "bearer",
        "username": user.username,
        "full_name": user.full_name or user.username,
        "mobile_number": user.mobile_number,
        "photo_url": user.photo_url,
        "is_admin": user.is_admin,
        "allow_password_change": user.allow_password_change,
        "permissions": {
            "invoices": user.can_access_invoices,
            "boe": user.can_access_boe,
            "ids": user.can_access_ids,
            "bills": user.can_access_bills,
            "challans": user.can_access_challans
        }
    }

@app.get("/api/v1/users/profile")
async def get_profile(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user_id = token.split("-")[-1]
    user = db.query(UserDBModel).filter(UserDBModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "mobile_number": user.mobile_number,
        "photo_url": user.photo_url,
        "is_admin": user.is_admin,
        "allow_password_change": user.allow_password_change,
        "permissions": {
            "invoices": user.can_access_invoices,
            "boe": user.can_access_boe,
            "ids": user.can_access_ids,
            "bills": user.can_access_bills,
            "challans": user.can_access_challans
        }
    }

@app.get("/api/v1/users")
async def list_users(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    users = db.query(UserDBModel).all()
    return [{
        "id": u.id, 
        "username": u.username, 
        "full_name": u.full_name,
        "mobile_number": u.mobile_number,
        "photo_url": u.photo_url,
        "is_admin": u.is_admin,
        "allow_password_change": u.allow_password_change,
        "permissions": {
            "invoices": u.can_access_invoices,
            "boe": u.can_access_boe,
            "ids": u.can_access_ids,
            "bills": u.can_access_bills,
            "challans": u.can_access_challans
        },
        "created_at": u.created_at
    } for u in users]

@app.post("/api/v1/users")
async def create_user(user_data: UserCreateSchema, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    admin_id = token.split("-")[-1]
    admin = db.query(UserDBModel).filter(UserDBModel.id == admin_id, UserDBModel.is_admin == True).first()
    if not admin:
        raise HTTPException(status_code=403, detail="Admin privileges required to create users.")

    existing = db.query(UserDBModel).filter(UserDBModel.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists.")
    
    new_user = UserDBModel(
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        mobile_number=user_data.mobile_number,
        photo_url=user_data.photo_url,
        is_admin=user_data.is_admin,
        allow_password_change=True,
        can_access_invoices=True,
        can_access_boe=True,
        can_access_ids=True,
        can_access_bills=True,
        can_access_challans=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"status": "success", "message": f"User '{user_data.username}' created successfully.", "id": new_user.id}

@app.put("/api/v1/users/{user_id}/permissions")
async def update_user_permissions(user_id: int, data: UserUpdateSchema, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    admin_id = token.split("-")[-1]
    admin = db.query(UserDBModel).filter(UserDBModel.id == admin_id, UserDBModel.is_admin == True).first()
    if not admin:
        raise HTTPException(status_code=403, detail="Admin privileges required.")
    
    target_user = db.query(UserDBModel).filter(UserDBModel.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    if data.full_name is not None: target_user.full_name = data.full_name
    if data.mobile_number is not None: target_user.mobile_number = data.mobile_number
    if data.photo_url is not None: target_user.photo_url = data.photo_url
    if data.is_admin is not None: target_user.is_admin = data.is_admin
    if data.can_access_invoices is not None: target_user.can_access_invoices = data.can_access_invoices
    if data.can_access_boe is not None: target_user.can_access_boe = data.can_access_boe
    if data.can_access_ids is not None: target_user.can_access_ids = data.can_access_ids
    if data.can_access_bills is not None: target_user.can_access_bills = data.can_access_bills
    if data.can_access_challans is not None: target_user.can_access_challans = data.can_access_challans
    if data.allow_password_change is not None: target_user.allow_password_change = data.allow_password_change
    if data.new_password:
        target_user.hashed_password = get_password_hash(data.new_password)
        
    db.commit()
    return {"status": "success", "message": f"Updated settings and profile for user ID {user_id}."}

@app.delete("/api/v1/users/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db), current_user: UserDBModel = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required.")
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own active administrative account.")
    
    user = db.query(UserDBModel).filter(UserDBModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    db.delete(user)
    db.commit()
    return {"status": "success", "message": f"User ID {user_id} deleted successfully."}

@app.post("/api/v1/auth/change-password")
async def change_password(data: PasswordChangeSchema, db: Session = Depends(get_db), current_user: UserDBModel = Depends(get_current_user)):
    if not current_user.is_admin and not current_user.allow_password_change:
        raise HTTPException(status_code=403, detail="Password change has been disabled for your account by the administrator.")
    
    if not verify_password(data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect existing password.")
    
    current_user.hashed_password = get_password_hash(data.new_password)
    db.commit()
    return {"status": "success", "message": "Password updated successfully."}

@app.post("/api/v1/extract-document")
async def extract_document(file: UploadFile = File(...), doc_type: str = Form("invoice"), current_user: UserDBModel = Depends(get_current_user), token: str = Depends(oauth2_scheme)):
    perms = {
        "invoice": current_user.can_access_invoices,
        "bills": current_user.can_access_bills,
        "boe": current_user.can_access_boe,
        "aadhaar": current_user.can_access_ids,
        "pan": current_user.can_access_ids,
        "challan": current_user.can_access_challans
    }
    if not current_user.is_admin and not perms.get(doc_type, True):
        raise HTTPException(status_code=403, detail=f"Access to pipeline '{doc_type}' is restricted by your administrator.")

    if not file.filename.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg', '.webp')):
        raise HTTPException(status_code=400, detail="Unsupported file format.")
    
    file_bytes = await file.read()
    try:
        structured_data = extract_document_from_bytes(file_bytes, file.filename, doc_type)
        return {
            "status": "success",
            "filename": file.filename,
            "doc_type": doc_type,
            "data": structured_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/save-document")
@app.post("/api/v1/save-invoice")
async def save_document(
    payload_json: str = Form(...),
    filename: str = Form("document.pdf"),
    doc_type: str = Form("invoice"),
    file: UploadFile = File(None), 
    db: Session = Depends(get_db),
    current_user: UserDBModel = Depends(get_current_user),
    token: str = Depends(oauth2_scheme)
):
    perms = {
        "invoice": current_user.can_access_invoices,
        "bills": current_user.can_access_bills,
        "boe": current_user.can_access_boe,
        "aadhaar": current_user.can_access_ids,
        "pan": current_user.can_access_ids,
        "challan": current_user.can_access_challans
    }
    if not current_user.is_admin and not perms.get(doc_type, True):
        raise HTTPException(status_code=403, detail=f"Access to save pipeline '{doc_type}' is restricted.")

    try:
        payload = json.loads(payload_json)
        file_bytes = await file.read() if file else None

        if doc_type == "invoice":
            db_record = InvoiceDBModel(
                filename=filename, pdf_data=file_bytes, raw_json=json.dumps(payload),
                vendor_name=payload.get("vendor_name"), gstin=payload.get("gstin"),
                invoice_number=payload.get("invoice_number"), invoice_date=payload.get("invoice_date"),
                po_number=payload.get("po_number"), total_taxable_amount=payload.get("total_taxable_amount"),
                total_gst_amount=payload.get("total_gst_amount"), total_due=payload.get("total_due")
            )
        elif doc_type == "boe":
            db_record = BOEDbModel(
                filename=filename, pdf_data=file_bytes, raw_json=json.dumps(payload),
                be_number=payload.get("be_number"), be_date=payload.get("be_date"),
                port_code=payload.get("port_code"), importer_name=payload.get("importer_name"),
                iec_code=payload.get("iec_code"), total_assessed_value=payload.get("total_assessed_value"),
                total_duty_amount=payload.get("total_duty_amount")
            )
        elif doc_type == "aadhaar":
            db_record = AadhaarDbModel(
                filename=filename, pdf_data=file_bytes, raw_json=json.dumps(payload),
                masked_aadhaar_number=payload.get("masked_aadhaar_number"), holder_name=payload.get("holder_name"),
                dob_or_yob=payload.get("dob_or_yob"), gender=payload.get("gender"), address=payload.get("address")
            )
        elif doc_type == "pan":
            db_record = PanDbModel(
                filename=filename, pdf_data=file_bytes, raw_json=json.dumps(payload),
                pan_number=payload.get("pan_number"), holder_name=payload.get("holder_name"),
                father_name=payload.get("father_name"), date_of_birth=payload.get("date_of_birth")
            )
        elif doc_type == "bills":
            db_record = BillsDbModel(
                filename=filename, pdf_data=file_bytes, raw_json=json.dumps(payload),
                biller_name=payload.get("biller_name"), consumer_id=payload.get("consumer_id"),
                bill_number=payload.get("bill_number"), bill_date=payload.get("bill_date"),
                due_date=payload.get("due_date"), total_amount_due=payload.get("total_amount_due")
            )
        elif doc_type == "challan":
            db_record = ChallanDbModel(
                filename=filename, pdf_data=file_bytes, raw_json=json.dumps(payload),
                challan_type=payload.get("challan_type"), challan_number=payload.get("challan_number"),
                challan_date=payload.get("challan_date"), issuer_or_bank=payload.get("issuer_or_bank"),
                total_amount=payload.get("total_amount")
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid document type pipeline.")

        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        return {"status": "success", "message": f"Successfully committed {doc_type} to MySQL!", "id": db_record.id}
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))