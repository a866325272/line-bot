import gspread, os
GAC = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
def insert_cell_to_google_sheet(spreadsheet_id, worksheet_name, row, col, value):
    gc = gspread.service_account(GAC)

    # Open the Google Sheet
    sh = gc.open_by_key(spreadsheet_id)

    # Select the worksheet
    worksheet = sh.worksheet(worksheet_name)

    # Update the specific cell with the value
    worksheet.update_cell(row, col, value)

def create_and_insert_sheet(spreadsheet_id, worksheet_name, data):
    gc = gspread.service_account(GAC)

    # Create a new spreadsheet
    sh = gc.open_by_key(spreadsheet_id)

    # Add a worksheet
    worksheet = sh.add_worksheet(title=worksheet_name, rows=len(data)+1, cols=len(data[0]))

    # Insert headers
    headers = list(data[0].keys())
    worksheet.append_row(headers)

    # Insert values
    values =[]
    for item in data:
        values.append(list(item.values()))
    worksheet.append_rows(values)

    return worksheet.url    

