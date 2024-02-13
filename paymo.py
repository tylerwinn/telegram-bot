import requests
import os
import sys
from pprint import pprint
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from pprint import pprint

load_dotenv()
api_key = os.getenv('PAYMO_API_KEY')
base_url = 'https://app.paymoapp.com'

headers = {
    'Accept': 'application/json'
}

def get_my_id():
    URL = f'{base_url}/api/me'
    response = requests.get(URL, auth=(api_key, ''))
    data = response.json()
    myPaymoId = data['users'][0]['id']
    return myPaymoId

# Define time zones with offsets manually
EST = timezone(timedelta(hours=-5)) 
CST = timezone(timedelta(hours=-6))  

def get_last_saturday(time_zone):
    today = datetime.now().astimezone(time_zone)
    days_to_last_saturday = (today.weekday() - 5) % 7
    last_saturday = today - timedelta(days=days_to_last_saturday)
    last_saturday_start = last_saturday.replace(hour=0, minute=0, second=0, microsecond=0)
    return last_saturday_start

def get_next_friday(last_saturday):
    next_friday = last_saturday + timedelta(days=6)
    next_friday_end = next_friday.replace(hour=23, minute=59, second=59, microsecond=999999)
    return next_friday_end

def get_time_entries(previous_period=False, use_est=False):
    # Choose the timezone based on the flag
    time_zone = EST if use_est else CST
    
    # Determine the correct last Saturday based on the timezone
    last_saturday = get_last_saturday(time_zone)
    
    # If fetching for the previous period, adjust the last Saturday to the one before the current
    if previous_period:
        last_saturday = last_saturday - timedelta(days=7)
    
    # Calculate the next Friday from the adjusted last Saturday
    end_time = get_next_friday(last_saturday)
    
    # Format start and end time in ISO format with timezone
    start_time_iso = last_saturday.isoformat()
    end_time_iso = end_time.isoformat()
    
    # Format the URL with the start and end times
    URL = f'{base_url}/api/entries?where=time_interval in ("{start_time_iso}","{end_time_iso}")'
    response = requests.get(URL, auth=(api_key, ''))
    data = response.json()
    return data

previous_period = sys.argv[1] if len(sys.argv) > 1 else False
use_est = sys.argv[2] if len(sys.argv) > 2 else False


time_entries = get_time_entries(previous_period=previous_period, use_est=use_est)

my_paymo_id = get_my_id()

# Sum only the durations for entries matching 'my_paymo_id'
total_duration_seconds = sum(entry['duration'] for entry in time_entries['entries'] if entry['user_id'] == my_paymo_id)

# Convert total duration from seconds to hours, minutes, and seconds
hours = total_duration_seconds // 3600
minutes = (total_duration_seconds % 3600) // 60
seconds = total_duration_seconds % 60

# Format the result as HH:MM:SS
formatted_duration = f"{hours:02}:{minutes:02}:{seconds:02}"

# Calculate overtime: seconds beyond 40 hours (14400 seconds)
overtime_seconds = max(total_duration_seconds - (40 * 3600), 0)
overtime_hours = overtime_seconds / 3600

base_weekly_pay = float(os.getenv('BASE_WEEKLY_PAY'))
overtime_rate = float(os.getenv('OVERTIME_RATE'))
tax_rate = float(os.getenv('TAX_RATE'))

# Continue with the overtime hours calculation as before
gross_overtime_pay = overtime_hours * overtime_rate

# Calculate total gross pay (base weekly pay + gross overtime pay)
total_gross_pay = base_weekly_pay + gross_overtime_pay

# Calculate the tax deduction for total gross pay
total_tax_deduction = total_gross_pay * tax_rate

# Calculate net pay (total gross pay - total tax deduction)
net_pay = total_gross_pay - total_tax_deduction

print("Base Weekly Pay (Gross):", f"${base_weekly_pay:.2f}")
print("Total Duration:", formatted_duration)
print(f"Overtime Hours: {overtime_hours:.2f} hours")
print(f"Gross Overtime Pay: ${gross_overtime_pay:.2f}")
print(f"Total Gross Pay (Base + Overtime): ${total_gross_pay:.2f}")
print(f"Total Tax Deduction (@ {tax_rate*100}% for Base + Overtime): ${total_tax_deduction:.2f}")
print(f"Estimated Net Pay (After Tax): ${net_pay:.2f}")