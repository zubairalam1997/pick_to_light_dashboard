from .models import vc_n_asn, AsnSchedule
from datetime import timedelta

def avg_cycle_list(request):
    # Count the total number of plans
    no_of_plan = vc_n_asn.objects.count()

    # Count the number of kitting in process plans
    no_of_kitting_in_process = AsnSchedule.objects.filter(selection_status='Pending...').count()
    

    # Count the number of completed plans
    no_of_completed_plan = AsnSchedule.objects.filter(selection_status='completed').count()

    # Calculate the total cycle time for all completed items
    completed_plans = AsnSchedule.objects.filter(selection_status='completed')
    total_seconds = 0

    for plan in completed_plans:
        if plan.end_time and plan.start_time:
            total_seconds += (plan.end_time - plan.start_time).total_seconds()

    # Calculate the average cycle time
    if no_of_completed_plan > 0:
        avg_seconds = total_seconds / no_of_completed_plan
        avg_cycle_time = timedelta(seconds=avg_seconds)
    else:
        avg_cycle_time = None

    # Format the average cycle time to a human-readable format
    if avg_cycle_time:
        minutes, seconds = divmod(avg_cycle_time.total_seconds(), 60)
        formatted_avg_cycle_time = f"{int(minutes)} min {int(seconds)} sec"
    else:
        formatted_avg_cycle_time = None

    # Return the counts and formatted average cycle time in a dictionary
    return {
        'no_of_plan': no_of_plan,
        'no_of_kitting_in_process': no_of_kitting_in_process,
        'no_of_completed_plan': no_of_completed_plan,
        'avg_cycle_time': formatted_avg_cycle_time
    }
