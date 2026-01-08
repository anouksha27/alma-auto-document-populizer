"""Data mapping utilities to map extracted data to form field IDs."""

from typing import Dict
from models.passport_data import PassportData
from models.g28_data import G28Data

def map_to_form_fields(passport_data: PassportData, g28_data: G28Data) -> Dict[str, str]:
    """Map extracted data to form field IDs.
    
    Args:
        passport_data: Extracted passport data
        g28_data: Extracted G-28 data
        
    Returns:
        Dictionary mapping field IDs to values
    """
    fields = {}
    
    # Helper function to format dates
    def format_date(date_obj):
        """Format date as MM/DD/YYYY."""
        if date_obj:
            return date_obj.strftime("%m/%d/%Y")
        return ""
    
    # Helper function to get value or empty string
    def get_value(val):
        """Get value or empty string if None."""
        return val if val is not None else ""
    
    # Map passport fields (Part 3 - uses hyphenated IDs)
    fields["passport-surname"] = get_value(passport_data.surname)
    fields["passport-given-names"] = get_value(passport_data.given_names)
    fields["passport-middle-name"] = get_value(passport_data.middle_names)  # Virtual ID for second field
    fields["passport-number"] = get_value(passport_data.passport_number)
    fields["passport-country"] = get_value(passport_data.country_of_issue)
    fields["passport-nationality"] = get_value(passport_data.nationality)
    fields["passport-dob"] = str(passport_data.date_of_birth) if passport_data.date_of_birth else ""
    fields["passport-pob"] = get_value(passport_data.place_of_birth)
    fields["passport-sex"] = get_value(passport_data.sex)
    fields["passport-issue-date"] = str(passport_data.issue_date) if passport_data.issue_date else ""
    fields["passport-expiry-date"] = str(passport_data.expiry_date) if passport_data.expiry_date else ""
    
    # Map G-28 attorney fields (Part 1 - uses hyphenated IDs)
    if g28_data.attorney:
        fields["online-account"] = get_value(g28_data.attorney.online_account)
        fields["family-name"] = get_value(g28_data.attorney.last_name)
        fields["given-name"] = get_value(g28_data.attorney.first_name)
        fields["middle-name"] = get_value(g28_data.attorney.middle_name)
        fields["street-number"] = get_value(g28_data.attorney.street)
        fields["city"] = get_value(g28_data.attorney.city)
        fields["state"] = get_value(g28_data.attorney.state)
        fields["zip"] = get_value(g28_data.attorney.zip)
        fields["country"] = get_value(g28_data.attorney.country)
        fields["daytime-phone"] = get_value(g28_data.attorney.phone)
        fields["email"] = get_value(g28_data.attorney.email)
    
    # Map G-28 eligibility fields (Part 2 - uses hyphenated IDs)
    if g28_data.eligibility:
        fields["licensing-authority"] = get_value(g28_data.eligibility.licensing_authority)
        fields["bar-number"] = get_value(g28_data.eligibility.bar_number)
        fields["law-firm"] = get_value(g28_data.eligibility.law_firm)
    
    # Note: Form A-28 doesn't have client fields in Part 4
    # Client info from G-28 is not mapped to this form
    
    return fields

def get_checkbox_fields(g28_data: G28Data) -> Dict[str, bool]:
    """Get checkbox field values from G-28 data.
    
    Args:
        g28_data: Extracted G-28 data
        
    Returns:
        Dictionary mapping checkbox field IDs to boolean values
    """
    checkboxes = {}
    
    # Map checkbox fields (uses hyphenated IDs)
    if g28_data.eligibility:
        # "I am not subject to orders" checkbox
        if g28_data.eligibility.is_not_subject_to_orders is not None:
            checkboxes["not-subject"] = g28_data.eligibility.is_not_subject_to_orders
    
    return checkboxes

