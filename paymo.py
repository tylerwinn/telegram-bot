import requests
import os
import sys
from pprint import pprint
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone, date
import time

load_dotenv()
api_key = os.getenv('PAYMO_API_KEY')
base_url = 'https://app.paymoapp.com'

# Define time zones with offsets manually
EST = timezone(timedelta(hours=-5)) 
CST = timezone(timedelta(hours=-6))  

headers = {
    'Accept': 'application/json'
}

def get_my_id():
    URL = f'{base_url}/api/me'
    response = requests.get(URL, auth=(api_key, ''))
    data = response.json()
    myPaymoId = data['users'][0]['id']
    return myPaymoId

def get_last_saturday(time_zone, today=datetime.now()):
    today = today.astimezone(time_zone)
    days_to_last_saturday = (today.weekday() - 5) % 7
    last_saturday = today - timedelta(days=days_to_last_saturday)
    last_saturday_start = last_saturday.replace(hour=0, minute=0, second=0, microsecond=0)
    return last_saturday_start

def get_next_friday(last_saturday):
    next_friday = last_saturday + timedelta(days=6)
    next_friday_end = next_friday.replace(hour=23, minute=59, second=59, microsecond=999999)
    return next_friday_end

def get_pay_period(use_est=False):
    time_zone = EST if use_est else CST
    last_saturday = get_last_saturday(time_zone)
    next_friday = get_next_friday(last_saturday)
    return (last_saturday, next_friday)

def get_pay_periods_for_year(year=datetime.now().year, use_est=False):
    time_zone = EST if use_est else CST
    pay_periods = []

    # Determine the starting point: the last Saturday of the current or specified year
    if year == datetime.now().year:
        pay_period_start = get_last_saturday(time_zone)
    else:
        # For past years, start with the last Saturday of that year
        pay_period_start = get_last_saturday(time_zone, today=datetime(year, 12, 31))

    # Loop to find all pay periods within the year
    while pay_period_start.year == year:
        pay_period_end = get_next_friday(pay_period_start)

        # Check if the pay period is within the same year
        if pay_period_end.year == year:
            pay_periods.append((pay_period_start, pay_period_end))

        # Move to the previous pay period
        pay_period_start = pay_period_start - timedelta(days=7)

    return pay_periods

def calculate_average_hours_per_pay_period(year=datetime.now().year, use_est=False):
    # Get the time zone based on the EST flag
    time_zone = EST if use_est else CST

    # Get all pay periods for the year
    pay_periods = get_pay_periods_for_year(year, use_est=use_est)

    # Get time entries for the entire year
    start_of_year = datetime(year, 1, 1, tzinfo=time_zone)
    end_of_year = datetime(year, 12, 31, 23, 59, 59, tzinfo=time_zone)
    all_time_entries = get_time_entries_for_period(start_of_year, end_of_year, use_est=use_est)

    # Initialize a dictionary to hold total hours for each pay period
    period_hours = {period: 0 for period in pay_periods}

    # Iterate through time entries and allocate them to the correct pay period
    my_paymo_id = get_my_id()
    for entry in all_time_entries['entries']:
        if entry['user_id'] == my_paymo_id:
            entry_date = datetime.fromisoformat(entry['start_time']).replace(tzinfo=time_zone)
            for start, end in pay_periods:
                if start <= entry_date <= end:
                    period_hours[(start, end)] += entry['duration'] / 3600
                    break

    # Calculate the average hours, excluding periods with 0 hours
    total_hours = sum(hours for hours in period_hours.values() if hours > 0)
    num_non_zero_periods = sum(1 for hours in period_hours.values() if hours > 0)

    # Avoid division by zero if there are no periods with non-zero hours
    if num_non_zero_periods == 0:
        return 0
    
    output = f"Average hours worked per pay period in {year}: {round(total_hours / num_non_zero_periods, 2)} hours"

    return output

def get_time_entries(previous_period=False, use_est=False):

    # Choose the timezone based on the flag
    time_zone = EST if use_est else CST
    
    # Determine the correct last Saturday based on the timezone
    start_time = get_last_saturday(time_zone)
    
    # If fetching for the previous period, adjust the last Saturday to the one before the current
    if previous_period:
        start_time = start_time - timedelta(days=7)
    
    # Calculate the next Friday from the adjusted last Saturday
    end_time = get_next_friday(start_time)

    start_time_iso = start_time.isoformat()
    end_time_iso = end_time.isoformat()
    
    # Format the URL with the start and end times
    URL = f'{base_url}/api/entries?where=time_interval in ("{start_time_iso}","{end_time_iso}")'
    response = requests.get(URL, auth=(api_key, ''))
    data = response.json()
    return data

def calculate_pay(previous_period=False, use_est=False):
    output = ""
    time_entries = get_time_entries(previous_period=previous_period, use_est=use_est)
    my_paymo_id = get_my_id()

    total_duration_seconds = sum(entry['duration'] for entry in time_entries['entries'] if entry['user_id'] == my_paymo_id)
    hours = total_duration_seconds // 3600
    minutes = (total_duration_seconds % 3600) // 60
    seconds = total_duration_seconds % 60

    formatted_duration = f"{hours:02}:{minutes:02}:{seconds:02}"

    overtime_seconds = max(total_duration_seconds - (40 * 3600), 0)
    overtime_hours = overtime_seconds / 3600

    base_weekly_pay = float(os.getenv('BASE_WEEKLY_PAY'))
    overtime_rate = float(os.getenv('OVERTIME_RATE'))
    tax_rate = float(os.getenv('TAX_RATE'))

    gross_overtime_pay = overtime_hours * overtime_rate
    total_gross_pay = base_weekly_pay + gross_overtime_pay
    total_tax_deduction = total_gross_pay * tax_rate
    net_pay = total_gross_pay - total_tax_deduction

    # Append information to the output string
    output += f"Base Weekly Pay (Gross): ${base_weekly_pay:.2f}\n"
    output += f"Total Duration: {formatted_duration}\n"
    output += f"Overtime Hours: {overtime_hours:.2f} hours\n"
    output += f"Gross Overtime Pay: ${gross_overtime_pay:.2f}\n"
    output += f"Total Gross Pay (Base + Overtime): ${total_gross_pay:.2f}\n"
    output += f"Total Tax Deduction (@ {tax_rate*100}% for Base + Overtime): ${total_tax_deduction:.2f}\n"
    output += f"Estimated Net Pay (After Tax): ${net_pay:.2f}"

    return output

def get_time_entries_for_period(start_time, end_time, use_est = False):
    time_zone = EST if use_est else CST
    start_time_iso = start_time.astimezone(time_zone).isoformat()
    end_time_iso = end_time.astimezone(time_zone).isoformat()
    URL = f'{base_url}/api/entries?where=time_interval in ("{start_time_iso}","{end_time_iso}")'
    response = requests.get(URL, auth=(api_key, ''))
    data = response.json()
    return data