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

def create_worksheet(spreadsheet_id, worksheet_name):
    gc = gspread.service_account(GAC)

    # Open a spreadsheet
    sh = gc.open_by_key(spreadsheet_id)

    # Add a worksheet
    worksheet = sh.add_worksheet(title=worksheet_name, rows=1, cols=10)

def delete_worksheet_if_exist(spreadsheet_id, worksheet_name):
    gc = gspread.service_account(GAC)

    # Open a spreadsheet
    sh = gc.open_by_key(spreadsheet_id)

    try:
        worksheet = sh.worksheet(worksheet_name)
    except:
        return "Worksheet is not exist."
    
    # Delete the worksheet
    sh.del_worksheet(worksheet)
    return "Worksheet deleted successfully."

def append_data(spreadsheet_id, worksheet_name, data):
    gc = gspread.service_account(GAC)

    # Open the Google Sheet
    sh = gc.open_by_key(spreadsheet_id)

    # Select the worksheet
    worksheet = sh.worksheet(worksheet_name)
    worksheet.append_rows(data)

    return worksheet.url

def update_table(spreadsheet_id, worksheet_name, table_data, starting_cell):
    gc = gspread.service_account(GAC)

    # Open the Google Sheet
    sh = gc.open_by_key(spreadsheet_id)

    # Select the worksheet
    worksheet = sh.worksheet(worksheet_name)

    worksheet.update(starting_cell, table_data, raw=False)

    return worksheet.url

def set_format_percent(spreadsheet_id, worksheet_name, cell_range):
    gc = gspread.service_account(GAC)

    # Open the Google Sheet
    sh = gc.open_by_key(spreadsheet_id)

    # Select the worksheet
    worksheet = sh.worksheet(worksheet_name)

    try:
        worksheet.format(cell_range,{"numberFormat": { "type": "PERCENT", "pattern": "0.00%"}})
        print(f"Cell range {cell_range} format set to: ")
    except:
        print("An error occurred:")
