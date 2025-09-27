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
        # Check if record is a dictionary or object and access accordingly
        if isinstance(record, dict):
            # Handle dictionary format
            full_name = record.get('full_name', 'Unknown')
            timestamp = record.get('last_seen') or record.get('timestamp')
        else:
            # Handle object format
            full_name = getattr(record, 'full_name', 'Unknown')
            timestamp = getattr(record, 'last_seen', None) or getattr(record, 'timestamp', None)
        
        # Format the timestamp
        if timestamp and hasattr(timestamp, 'strftime'):
            # It's a datetime object
            timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        else:
            # It might already be a string or None
            timestamp_str = str(timestamp) if timestamp else 'N/A'
        
        writer.writerow([full_name, timestamp_str])

    # Get the CSV data as a string
    csv_data = output.getvalue()
    return csv_data