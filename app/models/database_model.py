from sqlalchemy import Column, Integer, String, Float, Text, DateTime, LargeBinary, Boolean
from sqlalchemy.dialects.mysql import LONGTEXT
from datetime import datetime
from app.db.session import Base

class UserDBModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    
    # Profile & Role Management Fields
    full_name = Column(String(255), default="")
    mobile_number = Column(String(20), default="")
    photo_url = Column(LONGTEXT, default="")
    is_admin = Column(Boolean, default=False)
    
    # Admin-Controlled Pipeline & Security Permissions for Non-Admin Users
    can_access_invoices = Column(Boolean, default=True)
    can_access_boe = Column(Boolean, default=True)
    can_access_ids = Column(Boolean, default=True)  # Covers Aadhaar / PAN
    can_access_bills = Column(Boolean, default=True)
    can_access_challans = Column(Boolean, default=True)
    allow_password_change = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class BaseDocumentModel:
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(255))
    pdf_data = Column(LargeBinary(length=(2**32)-1))
    raw_json = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class InvoiceDBModel(Base, BaseDocumentModel):
    __tablename__ = "invoices"
    vendor_name = Column(String(255))
    gstin = Column(String(50))
    invoice_number = Column(String(100))
    invoice_date = Column(String(50))
    po_number = Column(String(100))
    total_taxable_amount = Column(Float)
    total_gst_amount = Column(Float)
    total_due = Column(Float)

class BOEDbModel(Base, BaseDocumentModel):
    __tablename__ = "boe_documents"
    be_number = Column(String(100))
    be_date = Column(String(50))
    port_code = Column(String(50))
    importer_name = Column(String(255))
    iec_code = Column(String(50))
    total_assessed_value = Column(Float)
    total_duty_amount = Column(Float)

class AadhaarDbModel(Base, BaseDocumentModel):
    __tablename__ = "aadhaar_documents"
    masked_aadhaar_number = Column(String(50))
    holder_name = Column(String(255))
    dob_or_yob = Column(String(50))
    gender = Column(String(20))
    address = Column(Text)

class PanDbModel(Base, BaseDocumentModel):
    __tablename__ = "pan_documents"
    pan_number = Column(String(50))
    holder_name = Column(String(255))
    father_name = Column(String(255))
    date_of_birth = Column(String(50))

class BillsDbModel(Base, BaseDocumentModel):
    __tablename__ = "bills_documents"
    biller_name = Column(String(255))
    consumer_id = Column(String(100))
    bill_number = Column(String(100))
    bill_date = Column(String(50))
    due_date = Column(String(50))
    total_amount_due = Column(Float)

class ChallanDbModel(Base, BaseDocumentModel):
    __tablename__ = "challans_documents"
    challan_type = Column(String(100)) # e.g., GST Challan, Gas Challan, Traffic, etc.
    challan_number = Column(String(100))
    challan_date = Column(String(50))
    issuer_or_bank = Column(String(255))
    total_amount = Column(Float)