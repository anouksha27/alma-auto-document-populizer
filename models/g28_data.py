"""Pydantic models for G-28 form data."""

from typing import Optional
from pydantic import BaseModel, Field

class AttorneyInfo(BaseModel):
    """Attorney information from G-28 form."""
    
    first_name: Optional[str] = Field(None, description="Attorney first name")
    middle_name: Optional[str] = Field(None, description="Attorney middle name")
    last_name: Optional[str] = Field(None, description="Attorney last name")
    street: Optional[str] = Field(None, description="Street address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State")
    zip: Optional[str] = Field(None, description="ZIP code")
    country: Optional[str] = Field(None, description="Country")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    fax: Optional[str] = Field(None, description="Fax number")
    online_account: Optional[str] = Field(None, description="Online account number")

class EligibilityInfo(BaseModel):
    """Eligibility information from G-28 form."""
    
    licensing_authority: Optional[str] = Field(None, description="Licensing authority")
    bar_number: Optional[str] = Field(None, description="Bar number")
    law_firm: Optional[str] = Field(None, description="Law firm name")
    is_not_subject_to_orders: Optional[bool] = Field(None, description="Not subject to orders checkbox")

class ClientInfo(BaseModel):
    """Client information from G-28 form."""
    
    first_name: Optional[str] = Field(None, description="Client first name")
    middle_name: Optional[str] = Field(None, description="Client middle name")
    last_name: Optional[str] = Field(None, description="Client last name")
    street: Optional[str] = Field(None, description="Street address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State")
    zip: Optional[str] = Field(None, description="ZIP code")
    country: Optional[str] = Field(None, description="Country")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    a_number: Optional[str] = Field(None, description="A-number (Alien number)")

class G28Data(BaseModel):
    """G-28 form data model."""
    
    attorney: Optional[AttorneyInfo] = Field(None, description="Attorney information")
    eligibility: Optional[EligibilityInfo] = Field(None, description="Eligibility information")
    client: Optional[ClientInfo] = Field(None, description="Client information")

