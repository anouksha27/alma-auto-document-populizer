"""Pydantic model for passport data."""

from typing import Optional
from datetime import date
from pydantic import BaseModel, Field

class PassportData(BaseModel):
    """Passport data model with all fields optional."""
    
    surname: Optional[str] = Field(None, description="Last name / Surname")
    given_names: Optional[str] = Field(None, description="First name(s)")
    middle_names: Optional[str] = Field(None, description="Middle name(s)")
    passport_number: Optional[str] = Field(None, description="Passport number")
    country_of_issue: Optional[str] = Field(None, description="Country that issued the passport")
    nationality: Optional[str] = Field(None, description="Nationality")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    place_of_birth: Optional[str] = Field(None, description="Place of birth")
    sex: Optional[str] = Field(None, description="Sex (M/F/X)")
    issue_date: Optional[date] = Field(None, description="Date of issue")
    expiry_date: Optional[date] = Field(None, description="Date of expiration")
    
    class Config:
        """Pydantic config."""
        json_encoders = {
            date: lambda v: v.isoformat() if v else None
        }

