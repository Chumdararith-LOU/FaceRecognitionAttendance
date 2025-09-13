import io
import csv

def generate_attendance_csv(records):
    """
    Generates a CSV file in memory from a list of attendance records.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Write the header row
    writer.writerow(['Student Name', 'Timestamp'])

    # Write the data rows
    for record in records:
        writer.writerow([record.full_name, record.last_seen.strftime("%Y-%m-%d %H:%M:%S")])

    # Get the CSV data as a string
    csv_data = output.getvalue()
    return csv_data