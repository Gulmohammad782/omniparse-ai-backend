from pydantic import BaseModel, Field
from typing import List, Optional

class LineItem(BaseModel):
    sr_no: Optional[str] = Field(default="", description="Serial number or item index")
    description: str = Field(description="Description of goods or service")
    hsn_code: Optional[str] = Field(default="", description="HSN or SAC code")
    quantity: float = Field(default=0.0, description="Quantity billed")
    uom: Optional[str] = Field(default="", description="Unit of measurement like Nos, Sq.Ft")
    rate: float = Field(default=0.0, description="Unit rate or price")
    total: float = Field(default=0.0, description="Total line cost")
    taxable_value: float = Field(default=0.0, description="Taxable value for the line item")
    cgst_percent: float = Field(default=0.0, description="CGST percentage e.g. 6")
    cgst_amount: float = Field(default=0.0, description="CGST monetary amount")
    sgst_percent: float = Field(default=0.0, description="SGST percentage e.g. 6")
    sgst_amount: float = Field(default=0.0, description="SGST monetary amount")

class InvoiceSchema(BaseModel):
    vendor_name: str = Field(description="Name of the company/vendor issuing the invoice")
    vendor_address: Optional[str] = Field(default="", description="Vendor address")
    gstin: Optional[str] = Field(default="", description="GSTIN number of vendor")
    invoice_number: str = Field(description="Unique invoice identifier code")
    invoice_date: str = Field(description="Date of issuance")
    po_number: Optional[str] = Field(default="", description="Purchase Order number reference")
    buyer_name: Optional[str] = Field(default="", description="Name of the billing recipient / buyer")
    line_items: List[LineItem] = Field(default_factory=list, description="List of all detailed billable items and tax breakdowns")
    total_taxable_amount: float = Field(default=0.0, description="Sum of all taxable values")
    total_gst_amount: float = Field(default=0.0, description="Total CGST + SGST combined amount")
    total_due: float = Field(default=0.0, description="Absolute final balance/gross total due")
    confidence_score: float = Field(default=0.98, description="Model confidence score between 0.0 and 1.0")

class BOESchema(BaseModel):
    be_number: Optional[str] = Field(default="", description="Bill of Entry number")
    be_date: Optional[str] = Field(default="", description="Bill of Entry date")
    port_code: Optional[str] = Field(default="", description="Port code")
    importer_name: Optional[str] = Field(default="", description="Name of the importer")
    iec_code: Optional[str] = Field(default="", description="Importer Exporter Code (IEC)")
    total_assessed_value: float = Field(default=0.0, description="Total assessed value")
    total_duty_amount: float = Field(default=0.0, description="Total duty amount payable")
    confidence_score: float = Field(default=0.98, description="Model confidence score between 0.0 and 1.0")

class AadhaarSchema(BaseModel):
    masked_aadhaar_number: Optional[str] = Field(default="", description="Masked Aadhaar identification number")
    holder_name: Optional[str] = Field(default="", description="Name of the cardholder")
    dob_or_yob: Optional[str] = Field(default="", description="Date of birth or year of birth")
    gender: Optional[str] = Field(default="", description="Gender of the cardholder")
    address: Optional[str] = Field(default="", description="Residential address")
    confidence_score: float = Field(default=0.98, description="Model confidence score between 0.0 and 1.0")

class PanSchema(BaseModel):
    pan_number: Optional[str] = Field(default="", description="PAN card alphanumeric number")
    holder_name: Optional[str] = Field(default="", description="Name of the cardholder")
    father_name: Optional[str] = Field(default="", description="Father's name of the cardholder")
    date_of_birth: Optional[str] = Field(default="", description="Date of birth")
    confidence_score: float = Field(default=0.98, description="Model confidence score between 0.0 and 1.0")

class BillsSchema(BaseModel):
    biller_name: Optional[str] = Field(default="", description="Name of the utility biller or company")
    consumer_id: Optional[str] = Field(default="", description="Consumer ID or account number")
    bill_number: Optional[str] = Field(default="", description="Unique bill reference number")
    bill_date: Optional[str] = Field(default="", description="Date the bill was issued")
    due_date: Optional[str] = Field(default="", description="Payment due date")
    total_amount_due: float = Field(default=0.0, description="Total monetary amount due for payment")
    confidence_score: float = Field(default=0.98, description="Model confidence score between 0.0 and 1.0")

class ChallanSchema(BaseModel):
    challan_type: Optional[str] = Field(default="", description="Type of challan such as GST, traffic, gas, etc.")
    challan_number: Optional[str] = Field(default="", description="Challan or reference number")
    challan_date: Optional[str] = Field(default="", description="Date of challan issuance or payment")
    issuer_or_bank: Optional[str] = Field(default="", description="Issuing authority or collecting bank")
    total_amount: float = Field(default=0.0, description="Total amount paid or payable under the challan")
    confidence_score: float = Field(default=0.98, description="Model confidence score between 0.0 and 1.0")