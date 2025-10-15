import requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

def format_date(date):
    """Format date object into year, month, day strings"""
    return {
        'year': date.strftime('%Y'),
        'month': date.strftime('%m'),
        'day': date.strftime('%d')
    }

def generate_url(template, year, month, day):
    """Generate URL from template and date parts"""
    return template.replace('{YYYY}', year).replace('{MM}', month).replace('{DD}', day)

def check_directory(url):
    """Check if directory exists by examining response text"""
    try:
        response = requests.get(url, timeout=10)
        text = response.text
        
        # Check if response contains "Not found" - means directory doesn't exist
        if 'Not found' in text:
            return False
        
        # Check if response contains "Not a file" - means directory exists!
        if 'Not a file' in text:
            return True
        
        # If status is 200, directory exists
        if response.status_code == 200:
            return True
            
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"Error checking {url}: {e}", file=sys.stderr)
        return False

def get_all_dates(start_date, end_date):
    """Generate all dates between start and end"""
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current)
        current += timedelta(days=1)
    return dates

def scan_directories(url_template, start_date, end_date, max_workers=10):
    """Scan all directories in date range"""
    dates = get_all_dates(start_date, end_date)
    total = len(dates)
    completed = 0
    found = 0
    valid_directories = []
    
    print(f"Scanning {total} dates from {start_date} to {end_date}...")
    print(f"URL template: {url_template}\n")
    
    # Use thread pool for concurrent requests
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_url = {}
        for date in dates:
            date_parts = format_date(date)
            url = generate_url(url_template, date_parts['year'], date_parts['month'], date_parts['day'])
            future = executor.submit(check_directory, url)
            future_to_url[future] = url
        
        # Process completed tasks
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            completed += 1
            
            try:
                is_valid = future.result()
                if is_valid:
                    found += 1
                    valid_directories.append(url)
                    print(f"✓ FOUND: {url}")
            except Exception as e:
                print(f"Error processing {url}: {e}", file=sys.stderr)
            
            # Progress update every 50 checks
            if completed % 50 == 0:
                print(f"Progress: {completed}/{total} ({found} found)")
    
    print(f"\n{'='*60}")
    print(f"Scan complete!")
    print(f"Checked: {total} URLs")
    print(f"Found: {found} valid directories")
    print(f"{'='*60}\n")
    
    return valid_directories

if __name__ == "__main__":
    # Configuration
    URL_TEMPLATE = "https://cdn.runescape.com/assets/img/external/oldschool/{YYYY}/newsposts/{YYYY}-{MM}-{DD}/"
    START_DATE = datetime(2000, 1, 1)
    END_DATE = datetime(2025, 12, 31)
    MAX_WORKERS = 20  # Number of concurrent requests
    
    # Run scan
    valid_dirs = scan_directories(URL_TEMPLATE, START_DATE, END_DATE, MAX_WORKERS)
    
    # Save results to file
    if valid_dirs:
        output_file = "valid_directories.txt"
        with open(output_file, 'w') as f:
            f.write('\n'.join(valid_dirs))
        print(f"Results saved to {output_file}")
        
        # Also print all results
        print("\nAll valid directories:")
        for directory in valid_dirs:
            print(directory)
    else:
        print("No valid directories found.")