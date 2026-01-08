"""File validation utilities."""

from fastapi import UploadFile

def validate_upload(file: UploadFile, max_size_mb: int) -> None:
    """Validate uploaded file.
    
    Args:
        file: Uploaded file
        max_size_mb: Maximum file size in MB
        
    Raises:
        ValueError: If validation fails with specific message
    """
    # Check if file exists and has content
    if not file or not file.filename:
        raise ValueError("No file uploaded")
    
    # Check file extension (case insensitive)
    valid_extensions = {'.pdf', '.jpg', '.jpeg', '.png'}
    file_ext = file.filename.lower().split('.')[-1]
    if f'.{file_ext}' not in valid_extensions:
        raise ValueError(
            f"Invalid file type: .{file_ext}. "
            f"Supported formats: PDF, JPEG, PNG"
        )
    
    # Check file size (if content_type indicates size)
    # Note: We'll do a more thorough check when reading the file
    # For now, just do basic validation
    
    # File is valid
    return

