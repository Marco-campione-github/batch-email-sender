import re
from auth import get_sheets_service


def extract_spreadsheet_id(sheet_input):
    """
    Extract spreadsheet ID from either a Google Sheets URL or direct ID.
    
    Supports formats:
    - https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
    - SPREADSHEET_ID
    """
    # Pattern to match Google Sheets URL
    url_pattern = r'docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)'
    match = re.search(url_pattern, sheet_input)
    
    if match:
        return match.group(1)
    
    # Assume it's already a spreadsheet ID
    return sheet_input.strip()


def get_sheet_columns(sheet_input):
    """
    Get the first row of the sheet to determine available columns.
    Returns a list of column headers.
    """
    spreadsheet_id = extract_spreadsheet_id(sheet_input)
    
    try:
        sheets_service = get_sheets_service()
        
        # Get the first row to determine headers
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range='A1:ZZ1'  # Get first row up to column ZZ
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            return []
        
        # Return the headers from the first row
        return values[0] if values else []
        
    except Exception as e:
        raise Exception(f"Failed to read sheet columns: {str(e)}")


def read_column_from_sheet(sheet_input, column_letter):
    """
    Read all values from a specific column in a Google Sheet.
    
    Args:
        sheet_input: Google Sheets URL or spreadsheet ID
        column_letter: Column letter (A, B, C, etc.)
    
    Returns:
        List of email addresses (non-empty values from the column, excluding header)
    """
    spreadsheet_id = extract_spreadsheet_id(sheet_input)
    
    try:
        sheets_service = get_sheets_service()
        
        # Read the entire column (skip first row which is the header)
        range_name = f'{column_letter}2:{column_letter}'
        
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            return []
        
        # Flatten the list and filter out empty values
        emails = [row[0].strip() for row in values if row and row[0].strip()]
        
        return emails
        
    except Exception as e:
        raise Exception(f"Failed to read column from sheet: {str(e)}")


def column_number_to_letter(col_num):
    """
    Convert column number (0-indexed) to column letter.
    Example: 0 -> A, 1 -> B, 25 -> Z, 26 -> AA
    """
    result = ""
    col_num += 1  # Convert to 1-indexed
    
    while col_num > 0:
        col_num -= 1
        result = chr(col_num % 26 + ord('A')) + result
        col_num //= 26
    
    return result


def column_letter_to_number(col_letter):
    """
    Convert column letter to number (0-indexed).
    Example: A -> 0, B -> 1, Z -> 25, AA -> 26
    """
    result = 0
    for char in col_letter.upper():
        result = result * 26 + (ord(char) - ord('A') + 1)
    return result - 1
