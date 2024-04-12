import os
import sys
import schedule
import time

# Add the directory containing your Django project to the Python path
sys.path.append('C:\\Users\\asus\\Desktop\\pick_to_l\\kitting_dash')

# Set the DJANGO_SETTINGS_MODULE environment variable
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kitting_dash.settings')

# Initialize Django
import django
django.setup()

# Then import the necessary module
from dashboard.views import picking_plan

def run_task():
    picking_plan(None)  # Pass None for the request parameter since it's not used in the task

# Schedule the task to run every 3 seconds
schedule.every(3).seconds.do(run_task)

while True:
    schedule.run_pending()
    time.sleep(1)
