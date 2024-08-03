from django.shortcuts import render ,  redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import vc_n_asn, VcMaster, VcDatabase, EslPart, AsnSchedule, WorkTable, trolley_data
import requests
from django.contrib import messages
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Exists, OuterRef, Q
import json
from itertools import cycle
from django.template.loader import render_to_string
from django.http import HttpResponseBadRequest
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from collections import defaultdict
import openpyxl
from django.core.files.storage import FileSystemStorage
from django.views.decorators.http import require_http_methods
from django.db import transaction
import os

# Initialize an in-memory queue
pending_data_queue = defaultdict(list)



# Assuming your trolley model is `Trolley`

# Define a list of queue colors
seven_queue = ["ff00", "ffff00", "ff", "ff0000", "ff00ff", "ffffff", "00ffff"]

# Function to display the color code
def display_color():
    # Get the first color code from the list
    color_code = seven_queue.pop(0)

    # Add the color code back to the end of the list
    seven_queue.append(color_code)

    # Return the color code
    return color_code


global vc_number
posted_vc = None

from django.contrib.messages import get_messages


@csrf_exempt
def get_messages_view(request):
    storage = get_messages(request)
    messages = [{'level': message.level, 'message': message.message} for message in storage]
    return JsonResponse({'messages': messages})

@csrf_exempt
def get_combined_data(request):
    qr_data = request.POST.get('qr_data')
    vc_n_asn_data = vc_n_asn.objects.all()
    combined_data = []
    print('combined Data:', qr_data)
    for entry in vc_n_asn_data:
        vc_number = entry.vcn
        asn_number = entry.asnn
        matching_models = VcMaster.objects.filter(vcnumber=vc_number)

        if matching_models.exists():
            model_info = matching_models.first().model
        else:
            model_info = 'No matching model found'

        data_entry = {
            'vc_number': vc_number,
            'asn_number': asn_number,
            'model': model_info,
            'trolley_qr': qr_data,
        }
        combined_data.append(data_entry)
        kitting_in_process_data = [entry for entry in combined_data if entry['vc_number'] == posted_vc]
        print('psted_vc', posted_vc)
    return JsonResponse({'combined_data': combined_data, 'kitting_in_process_data': kitting_in_process_data})


@csrf_exempt
def picking_plan(request):
    global posted_vc
    # vc_n_asn.objects.filter(vcn = posted_vc).delete()
    vc_n_asn_data = vc_n_asn.objects.all()

    # Define a list to store the combined data

    combined_data = []

    # Iterate over each entry in vc_n_asn_data
    for entry in vc_n_asn_data:
        vc_number = entry.vcn
        asn_number = entry.asnn
        date_time = entry.schedule_date_time

        # Query VcMaster to find matching model for the VC number
        matching_models = VcMaster.objects.filter(vcnumber=vc_number)

        # Check if matching_models is not empty
        if matching_models.exists():
            # Retrieve the first matching model
            model_info = matching_models.first().model

            # Create a dictionary to store VC, ASN, and model information
            data_entry = {
                'vc_number': vc_number,
                'asn_number': asn_number,
                'model': model_info,
                'plan_date': date_time.date(),
                'schedule_time': date_time.time(),
            }

            # Add the dictionary to the combined_data list
            combined_data.append(data_entry)
            combined_data = [entry for entry in combined_data if entry['vc_number'] != posted_vc]

            # add code to delete the combined data entry if match posted vc
        else:
            # If no matching model found, append a message to the combined_data list
            combined_data.append({
                'vc_number': vc_number,
                'asn_number': asn_number,
                'model': 'No matching model found',
                'plan_date': date_time.date(),
                'schedule_time': date_time.time(),
            })

             # Create a Paginator object with 10 items per page
    paginator = Paginator(combined_data, 10)

    # Get the current page number from the request, defaulting to 1
    page_number = request.GET.get('page', 1)

    try:
        # Get the requested page
        page = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        page = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results
        page = paginator.page(paginator.num_pages)

    # Pass the paginated data to the template
    return render(request, 'pick_plan.html', {'page': page})

    return render(request, 'pick_plan.html', {'combined_data': combined_data})


@csrf_exempt
@transaction.atomic
def get_Payload_Data(request):
    global posted_vc
    global vc_number

    if request.method == 'POST':
        qr_data = request.POST.get('qr_data')
        if qr_data is None:
            vc_number = request.POST.get('vc_number')

        try:
            if trolley_data.objects.filter(trolley_picking_status="pending").count() >= 7:
                return JsonResponse({'error': 'All trolleys are currently engaged'}, status=400)
            matching_trolley = trolley_data.objects.filter(trolley_code=qr_data).first()

            if matching_trolley and matching_trolley.trolley_picking_status == "pending":
                messages.warning(request , 'This trolley is already engaged!')
                return JsonResponse({'error': 'This trolley is already engaged'}, status=400)
            
            if matching_trolley and matching_trolley.trolley_picking_status == "completed":
                vc_data_list = VcDatabase.objects.filter(vc_no=vc_number)
                data_list = []
                vc_color_mapping = {}
                vc_color = vc_color_mapping.get(vc_number)
                if not vc_color:
                    vc_color = display_color()
                    vc_color_mapping[vc_number] = vc_color

                for vc_data in vc_data_list:
                    part_number = vc_data.part_no
                    try:
                        esl_data = EslPart.objects.get(partno=part_number)
                        data_list.append({
                            "Part No.": part_number,
                            "DESC": vc_data.part_desc,
                            "QTY": vc_data.quantity,
                            "mac": esl_data.tagid,
                            "ledstate": "0",
                            "ledrgb": vc_color,
                            "outtime": "0",
                            "styleid": "50",
                            "qrcode": "2001",# change this with matching trolley
                            "mappingtype": "79"
                        })
                    except EslPart.DoesNotExist:
                        pass

                if data_list and qr_data :
                    if not WorkTable.objects.exists():
                        # No entries in WorkTable, post data directly
                        response = requests.post('http://192.168.1.100/wms/associate/updateScreen', json=data_list)
                        response.raise_for_status()
                        if response.ok:
                            messages.success(request, 'Plan set to Kitting in Process.')
                            posted_vc = vc_number
                            try:
                                vc_n_asn_entry = vc_n_asn.objects.get(vcn=posted_vc)
                                asn_number = vc_n_asn_entry.asnn
                            except vc_n_asn.DoesNotExist:
                                return JsonResponse({'error': 'VC number not found in vc_n_asn'}, status=404)
                            try:
                                vc_master_entry = VcMaster.objects.get(vcnumber=posted_vc)
                                model_info = vc_master_entry.model
                            except VcMaster.DoesNotExist:
                                return JsonResponse({'error': 'VC number not found in VcMaster'}, status=404)

                            asn_schedule_created = AsnSchedule.objects.create(vc_no=posted_vc, asn_no=asn_number,
                                                                            model=model_info, start_time=timezone.now(), trqr=qr_data,
                                                                            color=vc_color)

                            if asn_schedule_created:
                                matching_trolley = trolley_data.objects.filter(trolley_code=qr_data).first()
                                if matching_trolley:
                                    trolley_mac = matching_trolley.mac
                                    matching_trolley.trolley_picking_status = "pending"
                                    matching_trolley.asn_num = asn_number
                                    matching_trolley.color = vc_color
                                    matching_trolley.save()
                                    trolley_payload = [{
                                        "mac": trolley_mac, "mappingtype": 135, "styleid": 54, "qrcode": asn_schedule_created.trqr,
                                        "Status": "PENDING", "MODEL": asn_schedule_created.model,
                                        "VC": asn_schedule_created.vc_no, "ASN": asn_schedule_created.asn_no,
                                        "ledrgb": vc_color, "ledstate": "0", "outtime": "0"}]

                                    response = requests.post('http://192.168.1.100/wms/associate/updateScreen', json=trolley_payload)
                                    response.raise_for_status()
                                    print("initial trolley payload" ,trolley_payload )
                                else:
                                    return JsonResponse({'error': 'No matching trolley found'}, status=404)
                            else:
                                return JsonResponse({'error': 'ASN Schedule not created'}, status=500)

                            for item in data_list:
                                WorkTable.objects.create(
                                    tagid=item['mac'],
                                    tagcode=item['qrcode'],
                                    tagname=item['mac'],
                                    stdatetime=timezone.now(),
                                    partno=item['Part No.'],
                                    partdesc=item['DESC'],
                                    qty=item['QTY'],
                                    asn=asn_number,
                                    color= vc_color,
                                )

                            return JsonResponse({'success': 'Data posted successfully'})
                        else:
                            return JsonResponse({'error': 'Failed to post data'}, status=500)
                    else:
                        pending_items = []
                        completed_items = []
                        processed_macs = set()

                        # Loop through each item in the data_list
                        for item in data_list:
                                mac = item['mac']
                                print("mac",mac ,  type(mac))
                                print("datalst is herwe",data_list)

                                # Query the WorkTable for entries with the current MAC address
                                worktable_entries = WorkTable.objects.filter(tagid=mac).order_by('-stdatetime')
                                print("worktable_entries", worktable_entries)

                                if worktable_entries.exists():
                                    for entry in worktable_entries:
                                        if entry.tagid in [mac for mac in processed_macs]:
                                            continue
                                        eslid = str(entry.tagid) 
                                        esl_id=str(eslid)
                                        print('entry.tagid ',eslid )
                                        print('eslid type ',type(eslid) )
                                        
                                        if entry.status == 'pending':
                                            pending_items.append(item)
                                            pending_data_queue[item['mac']].append(item)
                                            processed_macs.add(entry.tagid)
                                            posted_vc = vc_number
                                            try:
                                                vc_n_asn_entry = vc_n_asn.objects.get(vcn=posted_vc)
                                                asn_number = vc_n_asn_entry.asnn
                                                WorkTable.objects.create(
                                                    tagid=item['mac'],
                                                    tagcode=item['qrcode'],
                                                    tagname=item['mac'],
                                                    stdatetime=timezone.now(),
                                                    partno=item['Part No.'],
                                                    partdesc=item['DESC'],
                                                    qty=item['QTY'],
                                                    asn=asn_number,
                                                    color=vc_color,
                                                )
                                            except vc_n_asn.DoesNotExist:
                                                return JsonResponse({'error': 'VC number not found in vc_n_asn'}, status=404)

                                        elif entry.status == 'completed':
                                            if entry.tagid in processed_macs:
                                                continue
                                            completed_items.append(item)
                                            processed_macs.add(entry.tagid)
                                        print({"pending_data_queue":pending_data_queue,"pending_data_queue[item[mac]]":pending_data_queue[item['mac']],"processed_macs":processed_macs})        
                                            # Exit the loop since we have categorized the item
                                            
                                else:
                                    # If no worktable entry is found, consider it as completed
                                    # if mac  not in processed_macs:
                                    completed_items.append(item)
                                    print("all completed iterms", completed_items)
                        # Check if all items in data_list have status 'pending'
                        if len(pending_items) == len(data_list):
                            for tagid, items in pending_data_queue.items():
                                vc_num = vc_number
                                try:
                                    vc_n_asn_entry = vc_n_asn.objects.get(vcn=vc_num)
                                    asn_number = vc_n_asn_entry.asnn

                                    related_worktables = WorkTable.objects.filter(asn=asn_number).distinct()
                                    if all(worktable.status == 'pending' for worktable in related_worktables):
                                        try:
                                            vc_master_entry = VcMaster.objects.get(vcnumber=posted_vc)
                                            model_info = vc_master_entry.model
                                        except VcMaster.DoesNotExist:
                                            return JsonResponse({'error': 'VC number not found in VcMaster'}, status=404)

                                        asn_schedule_created = AsnSchedule.objects.create(vc_no=posted_vc, asn_no=asn_number,
                                                                                        model=model_info, start_time=timezone.now(), trqr=qr_data,
                                                                                        color=vc_color)
                                        print(f"asn_schedule created for ASN {asn_number}")
                                        if asn_schedule_created:
                                            matching_trolley = trolley_data.objects.filter(trolley_code=qr_data).first()
                                            if matching_trolley:
                                                trolley_mac = matching_trolley.mac
                                                matching_trolley.trolley_picking_status = "pending"
                                                matching_trolley.asn_num = asn_number
                                                pick_status = matching_trolley.trolley_picking_status
                                                matching_trolley.color = vc_color
                                                matching_trolley.save()
                                                trolley_payload = [{
                                                    "mac": trolley_mac, "mappingtype": 135, "styleid": 54, "qrcode": asn_schedule_created.trqr,
                                                    "Status": "Pending..", "MODEL": asn_schedule_created.model,
                                                    "VC": asn_schedule_created.vc_no, "ASN": asn_schedule_created.asn_no,
                                                    "ledrgb": vc_color, "ledstate": "0", "outtime": "0"
                                                }]

                                                response = requests.post('http://192.168.1.100/wms/associate/updateScreen', json=trolley_payload)
                                                response.raise_for_status()
                                                print("initial trolley payload", trolley_payload)
                                                return JsonResponse({'error': 'if all items lie in pending_data_queue, trolley posted successfully'})
                                            else:
                                                return JsonResponse({'error': 'No matching trolley found'}, status=404)
                                except vc_n_asn.DoesNotExist:
                                    return JsonResponse({'error': 'VC number not found in vc_n_asn'}, status=404)

                            # Check if there are any completed items to process
                        if completed_items:
                                response = requests.post('http://192.168.1.100/wms/associate/updateScreen', json=completed_items)
                                response.raise_for_status()
                                # completed_items.clear()
                                posted_vc = vc_number
                                try:
                                    vc_n_asn_entry = vc_n_asn.objects.get(vcn=posted_vc)
                                    asn_number = vc_n_asn_entry.asnn
                                except vc_n_asn.DoesNotExist:
                                    return JsonResponse({'error': 'VC number not found in vc_n_asn'}, status=404)
                                try:
                                    vc_master_entry = VcMaster.objects.get(vcnumber=posted_vc)
                                    model_info = vc_master_entry.model
                                except VcMaster.DoesNotExist:
                                    return JsonResponse({'error': 'VC number not found in VcMaster'}, status=404)

                                asn_schedule_created = AsnSchedule.objects.create(vc_no=posted_vc, asn_no=asn_number,
                                                                                model=model_info, start_time=timezone.now(), trqr=qr_data,
                                                                                color=vc_color)

                                if asn_schedule_created:
                                    matching_trolley = trolley_data.objects.filter(trolley_code=qr_data).first()
                                    if matching_trolley:
                                        trolley_mac = matching_trolley.mac
                                        matching_trolley.trolley_picking_status = "pending"
                                        matching_trolley.asn_num = asn_number
                                        pick_status =matching_trolley.trolley_picking_status
                                        matching_trolley.color = vc_color
                                        matching_trolley.save()
                                        trolley_payload = [{
                                            "mac": trolley_mac, "mappingtype": 135, "styleid": 54, "qrcode": asn_schedule_created.trqr,
                                            "Status": "Pending..", "MODEL": asn_schedule_created.model,
                                            "VC": asn_schedule_created.vc_no, "ASN": asn_schedule_created.asn_no,
                                            "ledrgb": vc_color, "ledstate": "0", "outtime": "0"}]

                                        response = requests.post('http://192.168.1.100/wms/associate/updateScreen', json=trolley_payload)
                                        response.raise_for_status()
                                        print("initial trolley payload" ,trolley_payload )
                                    else:
                                        return JsonResponse({'error': 'No matching trolley found'}, status=404)
                                else:
                                    return JsonResponse({'error': 'ASN Schedule not created'}, status=500)

                                for item in completed_items:
                                    WorkTable.objects.create(
                                        tagid=item['mac'],
                                        tagcode=item['qrcode'],
                                        tagname=item['mac'],
                                        stdatetime=timezone.now(),
                                        partno=item['Part No.'],
                                        partdesc=item['DESC'],
                                        qty=item['QTY'],
                                        asn=asn_number,
                                        color=vc_color,
                                    )

                                return JsonResponse({'success': 'Data posted s successfully'})
                        else:
                                return JsonResponse({'error': 'Failed to post data'}, status=500)

                        # if pending_items:
                        #     for item in pending_items:
                        #         pending_data_queue[item['mac']].append(item)
                        #         print("pending_data_queue items", pending_data_queue)
                                
                else:
                    return JsonResponse({'error': 'No matching part numbers found in ESL model'}, status=404)      #     return JsonResponse({'success': 'Pending items added to the queue'})

            else:
                return JsonResponse({'error':'Invalid QR data or Trolley code  '},status = 404)           # return JsonResponse(data_list, safe=False)
                
        except VcDatabase.DoesNotExist:
            return JsonResponse({'error': 'VC number not found'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)


def kitting_in_process(request):
    try:
        # Subquery to check if there are any entries with pending status for the same ASN number
        pending_subquery = WorkTable.objects.filter(
            asn=OuterRef('asn'), status='pending'
        )

        # Annotate each ASN number with a flag indicating if any entry has a pending status
        completed_work_table = WorkTable.objects.annotate(
            any_pending=Exists(pending_subquery)
        )

        # Filter to get only those ASN numbers where all entries are completed and none has a pending status
        filtered_work_table = completed_work_table.values('asn').annotate(
            completed_count=Count('id', filter=Q(status='completed')),
        ).filter(
            completed_count=Count('id'),
            any_pending=False,
        )

        # Get the distinct ASN numbers from the filtered queryset
        completed_asn_values = [item['asn'] for item in filtered_work_table]

        # Filter AsnSchedule objects based on the completed ASN numbers
        kitting_in_process_data = AsnSchedule.objects.exclude(asn_no__in=completed_asn_values).distinct('asn_no')

        return render(request, 'kitting_in_process.html', {'kitting_in_process_data': kitting_in_process_data})

    except AsnSchedule.DoesNotExist:
        return render(request, 'kitting_in_process.html', {'kitting_in_process_data': None})


@csrf_exempt
def open_modal(request):
    if request.method == 'POST':
        clicked_asn = request.POST.get('asn_number')

        # Retrieve the relevant data from the database
        open_modal_data = list(WorkTable.objects.filter(asn=clicked_asn).values('partno', 'partdesc', 'qty', 'status','asn'))

        # Return the data as JSON response
        return JsonResponse(open_modal_data, safe=False)

    # Return a JsonResponse even for GET requests with an empty list
    return JsonResponse([], safe=False)


@csrf_exempt
def render_modal(request):
    if request.method == 'POST':
        data = json.loads(request.POST.get('open_modal_data', '[]'))
        rendered_html = render_to_string('modal.html', {'open_modal_data': data})
        return HttpResponse(rendered_html)
    else:
        return HttpResponseBadRequest('Invalid request method')


@require_POST
@csrf_exempt
@transaction.atomic
def enter_key(request):
 try:
        data = json.loads(request.body)
        mac_address = data.get('mac')
        print(f'Received MAC address: {mac_address}')

        # Update WorkTable entry
        worktable_entry = WorkTable.objects.filter(tagid=mac_address, status='pending').order_by('stdatetime').first()
        if worktable_entry:
            worktable_entry.status = 'completed'
            worktable_entry.eddatetime = timezone.now()
            worktable_entry.save()
            print(f'Updated WorkTable entry for MAC address: {mac_address}')

        # Handle pending data queue
        if mac_address in pending_data_queue:
            if pending_data_queue[mac_address]:
                esl_payload = [pending_data_queue[mac_address].pop(0)]
                response = requests.post('http://192.168.1.100/wms/associate/updateScreen', json=esl_payload)
                if response.status_code == 200:
                    print(f'Data posted successfully for MAC address: {mac_address}')
                else:
                    print(f'Failed to post data for MAC address: {mac_address}, Status Code: {response.status_code}, Response: {response.text}')
            else:
                print(f'No data in pending_data_queue for MAC address: {mac_address}')
        else:
            print(f'No data found for MAC address: {mac_address}')

        
        # Orders the filtered results by eddatetime in descending orderand Retrieves the first entry from the ordered results, which will be the most recent one based on eddatetime 
        latest_completed_worktable =  WorkTable.objects.filter(tagid=mac_address, status='completed').order_by('-eddatetime').first()
        # Check the ASN of the updated worktable entry
        asn = latest_completed_worktable.asn

        # Check all WorkTable entries related to the ASN
        related_worktables = WorkTable.objects.filter(asn=asn)
        all_completed = all(entry.status == 'completed' for entry in related_worktables)

        if all_completed:
            # Update the AsnSchedule status to 'completed'
            asn_schedule = AsnSchedule.objects.filter(asn_no=asn).first()
            if asn_schedule:
                asn_schedule.selection_status = 'completed'
                asn_schedule.end_time = timezone.now()
                asn_schedule.save()
                print(f'ASN Schedule {asn} updated to completed')

            # Update the trolley status to 'completed' if matched with the ASN
            matching_trolleys = trolley_data.objects.filter(asn_num=asn )
            for trolley in matching_trolleys:
                trolley.trolley_picking_status = 'completed'
                trolley.save()
                print(f'Trolley {trolley.mac} updated to completed')

                # Form the payload and post it
                trolley_payload = [{
                    "mac": trolley.mac,
                    "Status": trolley.trolley_picking_status,
                    "mappingtype": 135,
                    "styleid": 54,
                    "qrcode": asn_schedule.trqr,
                    "MODEL": asn_schedule.model,
                    "VC": asn_schedule.vc_no,
                    "ASN": asn_schedule.asn_no+".",
                    "ledrgb": trolley.color,
                    "ledstate": "1",
                    "outtime": "3"
                }]
                if trolley.trolley_picking_status == 'completed':


                    response = requests.post('http://192.168.1.100/wms/associate/updateScreen', json=trolley_payload)
                    response.raise_for_status()
                    print(f'Trolley data updated successfully, Response: {response.text}',trolley_payload)
                    trolley.asn_num= None
                    trolley.save()

 except (WorkTable.DoesNotExist, AsnSchedule.DoesNotExist, trolley_data.DoesNotExist) as e:
        print(f'Exception occurred: {e}',"hello me")
        return JsonResponse({'message': 'Request processed for trolley successfully'})
 except requests.exceptions.RequestException as e:
        print(f'Request to external service failed: {e}',"hellotwo")
        return JsonResponse({'message': 'Failed to update trolley data', 'error': str(e)}, status=500)

 return JsonResponse({'message': 'Request processed successfully'})
def completed_kittings(request):
    try:
        # Subquery to check if there are any entries with pending status for the same ASN number
        pending_subquery = WorkTable.objects.filter(
            asn=OuterRef('asn'), status='pending'
        )

        # Annotate each ASN number with a flag indicating if any entry has a pending status
        completed_work_table = WorkTable.objects.annotate(
            any_pending=Exists(pending_subquery)
        )

        # Filter to get only those ASN numbers where all entries are completed and none has a pending status
        filtered_work_table = completed_work_table.values('asn').annotate(
            completed_count=Count('id', filter=Q(status='completed')),
        ).filter(
            completed_count=Count('id'),
            any_pending=False,
        )

        # Get the distinct ASN numbers from the filtered queryset
        completed_asn_values = [item['asn'] for item in filtered_work_table]

        # Filter AsnSchedule objects based on the completed ASN numbers
        completed_picks = AsnSchedule.objects.filter(asn_no__in=completed_asn_values).distinct('asn_no')

        return render(request, 'completed_kittings.html', {'completed_picks': completed_picks})

    except AsnSchedule.DoesNotExist:
        # Handle the case where no AsnSchedule objects are found
        return render(request, 'completed_kittings.html', {'completed_picks': None})


@require_POST
@csrf_exempt
def kitting_config(request):
    try:
        data = json.loads(request.body)
        asn_number = data.get('asn_number')
        print(f'Received ASN number: {asn_number}')

        # Update ASN schedule
        asn_schedule = AsnSchedule.objects.filter(asn_no=asn_number).first()
        if asn_schedule:
            asn_schedule.selection_status = 'completed'
            asn_schedule.end_time = timezone.now()
            asn_schedule.save()
            print(f'ASN Schedule {asn_number} updated to completed')

            # Update trolley data
            matching_trolleys = trolley_data.objects.filter(asn_num=asn_number)
            for trolley in matching_trolleys:
                trolley.trolley_picking_status = 'completed'
                trolley.save()
                print(f'Trolley {trolley.mac} updated to completed')

                # Form the payload and post it
                trolley_payload = [{
                    "mac": trolley.mac,
                    "mappingtype": 135,
                    "styleid": 54,
                    "qrcode": asn_schedule.trqr,
                    "Status": "Completed",
                    "MODEL": asn_schedule.model,
                    "VC": asn_schedule.vc_no,
                    "ASN": asn_schedule.asn_no + ".",
                    "ledrgb": trolley.color,
                    "ledstate": "1",
                    "outtime": "3"
                }]
                if trolley.trolley_picking_status == 'completed':
                    try:
                        response = requests.post('http://192.168.1.100/wms/associate/updateScreen', json=trolley_payload)
                        response.raise_for_status()
                        trolley.asn_num = None
                        trolley.save()
                        print(f'Trolley data updated successfully, Response: {response.text}')
                    except requests.exceptions.RequestException as e:
                        print(f'Request to update trolley failed: {e}')
                        return JsonResponse({'message': 'Failed to update trolley data', 'error': str(e)}, status=500)

        # Fetch and update WorkTable entries
        worktable_entries = WorkTable.objects.filter(asn=asn_number)
        worktable_entries.update(status='completed', eddatetime=timezone.now())
        print(f'Updated WorkTable entries for ASN number: {asn_number}')
        
        if worktable_entries:
            # Send payload to each ESL whose WorkTable entry comes under the given ASN
            for worktable_entry in worktable_entries:
                print('worktabletagid1',worktable_entry.tagid ,worktable_entry.status)
                # if worktable_entry.status == 'Pending':
                print('worktabletagid2',worktable_entry.tagid)
                esl_payload = [{
                    "mac": worktable_entry.tagid,
                    "mappingtype": 79,
                    "styleid": 50,
                    "qrcode": worktable_entry.tagcode,
                    "Part No.": worktable_entry.partno,
                    "DESC": worktable_entry.partdesc+".",
                    "QTY": worktable_entry.qty,
                    "ledrgb": worktable_entry.color,
                    "ledstate": "1",
                    "outtime": "1"
                },]
                print(f"Updating ESL for MAC: {worktable_entry.tagid , worktable_entry.color}")
                
                if worktable_entry.status== 'completed':
                    try:
                        response = requests.post('http://192.168.1.100/wms/associate/updateScreen', json=esl_payload)
                        response.raise_for_status()
                        print(f'ESL data updated successfully for MAC {worktable_entry.tagid}, Response: {response.text}')
                    except requests.exceptions.RequestException as e:
                        print(f'Request to update ESL failed: {e}')
                        return JsonResponse({'message': 'Failed to update ESL data', 'error': str(e)}, status=500)

            return JsonResponse({'message': 'ASN status and related data updated successfully'})
    except (WorkTable.DoesNotExist, AsnSchedule.DoesNotExist, trolley_data.DoesNotExist) as e:
        print(f'Exception occurred: {e}')
        return JsonResponse({'message': 'Error processing ASN', 'error': str(e)}, status=500)
    except json.JSONDecodeError as e:
        print(f'Invalid JSON received: {e}')
        return JsonResponse({'message': 'Invalid JSON received', 'error': str(e)}, status=400)
    except Exception as e:
        print(f'Unexpected error: {e}')
        return JsonResponse({'message': 'Unexpected error occurred', 'error': str(e)}, status=500)

def asn_input(request):
    return render(request, 'kitting_config.html')

def vc_list(request):
    vcs = EslPart.objects.all()
    vc_masters = VcMaster.objects.all()
    return render(request, 'model_matrix.html', {'vcs': vcs, 'vc_masters': vc_masters})

def Part_VC_Map_Data(request):
    vcs = EslPart.objects.all()
    vc_masters = VcMaster.objects.all()
    return render(request,  "model_matrix/vc_part_map.html", {'vcs': vcs, 'vc_masters': vc_masters})
    
def add_esl_part_template(request):
    return render(request, 'model_matrix/add_esl.html')   

def add_new_trolley_template(request):
    return render(request, 'model_matrix/add_new_trolley.html')  
def vc_model_mapping_template(request):
    vc_masters = VcMaster.objects.all()
    return render(request, 'model_matrix/vc_model_mapping.html' ,{'vc_masters':vc_masters}) 

def fetch_existing_vc_entries(request):
    part_no = request.GET.get('part_no')
    if part_no:
        existing_vc_entries = VcDatabase.objects.filter(part_no=part_no).values_list('vc_no', flat=True)
        return JsonResponse(list(existing_vc_entries), safe=False)
    
    return JsonResponse([], safe=False)


def update_vc(request):
    print(f"Request method: {request.method}")
    if request.method == 'POST':
        vc_id = request.POST.get('vc_id')
        part_number = request.POST.get('part_number')
        part_desc = request.POST.get('part_desc')
        quantity = request.POST.get('quantity')
        selected_vc_ids = request.POST.getlist('vc_master_id[]')  # Use getlist to fetch multiple selected IDs

        print("Selected VC IDs:", selected_vc_ids)

        try:
            existing_vc_entries = VcDatabase.objects.filter(part_no=part_number)
            existing_vc_ids = list(existing_vc_entries.values_list('vc_no', flat=True))

            selected_vc_numbers = list(VcMaster.objects.filter(id__in=selected_vc_ids).values_list('vcnumber', flat=True))

            # Create or update entries for checked items
            created_items = []
            for vc_id in selected_vc_ids:
                vc_master = VcMaster.objects.get(id=vc_id)
                print("Processing VC Master:", vc_master)

                if vc_master.vcnumber not in existing_vc_ids:
                    created_item = VcDatabase.objects.create(
                        vc_no=vc_master.vcnumber,
                        part_no=part_number,
                        part_desc=part_desc,
                        quantity=quantity
                    )
                    created_items.append(created_item)
                    print("Created items:", created_items)
                else:
                    vc_entry = VcDatabase.objects.get(vc_no=vc_master.vcnumber, part_no=part_number)
                    if vc_entry.quantity != int(quantity):
                        vc_entry.quantity = quantity
                        vc_entry.save()
                        print(f"Updated VC entry: {vc_entry.vc_no} with quantity: {vc_entry.quantity}")
                        # Update quantity in EslPart if the quantity has changed
                        try:
                            esl_part = EslPart.objects.get(part_no=part_number)
                            if esl_part.quantity != int(quantity):
                                esl_part.quantity = quantity
                                esl_part.save()
                                print(f"Updated ESL part: {esl_part.partno} with quantity: {esl_part.quantity}")
                        except EslPart.DoesNotExist:
                            EslPart.objects.create(partno=part_number, quantity=quantity)
                            print(f"Created new ESL part: {part_number} with quantity: {quantity}")

            # Delete entries for unchecked items
            for vc_entry in existing_vc_entries:
                if vc_entry.vc_no not in selected_vc_numbers:
                    vc_entry.delete()
                    print(f"Deleted VC entry: {vc_entry.vc_no}")

            # Show success message and redirect
            messages.success(request, 'VC entries updated successfully.')
            return JsonResponse({'status': 'success', 'message': 'VC entries updated successfully.'})

        except Exception as e:
            # Handle exceptions and show error message
            messages.error(request, f'Error updating VC entries: {str(e)}')
            return JsonResponse({'status': 'error', 'message': f'Error updating VC entries: {str(e)}'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})
def edit_vc(request, id):
    vc = get_object_or_404(VcDatabase, id=id)
    if request.method == "POST":
        form = VcDatabaseForm(request.POST, instance=vc)
        if form.is_valid():
            form.save()
            return redirect('vc_list')
    else:
        form = VcDatabaseForm(instance=vc)
    return render(request, 'edit_vc.html', {'form': form})

def delete_vc(request, part_no):
    try:
        esl_part = EslPart.objects.get(partno=part_no)
        if esl_part:
            esl_part.delete()
            return redirect('vc_list')
        return JsonResponse({'message': f'Part number {part_no} deleted from EslPart.'},status=204)
    except EslPart.DoesNotExist:
        return JsonResponse({'error': f'Part number {part_no} not found in EslPart.'}, status=404)
    
import logging
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import openpyxl
from .models import VcDatabase

logger = logging.getLogger(__name__)

@csrf_exempt
def add_esl_part(request):
    if request.method == 'POST':
        try:
            part_no = request.POST.get('part_no')
            tag_mac = request.POST.get('tagId')
            part_desc = request.POST.get('part_desc')
            quantity = request.POST.get('quantity')

            if not part_no or not part_desc or not quantity:
                return JsonResponse({'success': False, 'message': 'All fields are required.'})

            EslPart.objects.create(
                   # Adjust as needed
                partno=part_no,
                part_desc=part_desc,
                tagid = tag_mac,
                quantity=quantity
            )

            return JsonResponse({'success': True, 'message': 'ESL Part added successfully.'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error: {e}'})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from openpyxl import load_workbook

@csrf_exempt
def upload_esl_excel(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        try:
            wb = load_workbook(filename=excel_file, data_only=True)
            sheet = wb.active
            for row in sheet.iter_rows(min_row=2, values_only=True):  # Assuming the first row is the header
                partno = row[0]
                part_desc = row[1]
                tagid = row[2]
                quantity = row[3]
                
                if partno and part_desc and tagid and quantity is not None:  # Validate values
                    EslPart.objects.update_or_create(
                        partno=partno,
                        defaults={
                            'part_desc': part_desc,
                            'tagid': tagid,
                            'quantity': quantity
                        }
                    )
            return JsonResponse({'success': True, 'message': 'ESL Excel uploaded and data updated successfully.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error processing Excel file: {e}'})
    return JsonResponse({'success': False, 'message': 'No file uploaded or invalid request method.'})


@csrf_exempt
@require_http_methods(["POST"])
def upload_excel(request):
    if request.method == "POST" and request.FILES.get('excel_file'):
        try:
            excel_file = request.FILES['excel_file']
            fs = FileSystemStorage()
            filename = fs.save(excel_file.name, excel_file)
            file_path = fs.path(filename)

            wb = openpyxl.load_workbook(file_path)
            sheet = wb.active

            for row in sheet.iter_rows(min_row=2, values_only=True):  # Assuming the first row is the header
                try:
                    vc_no, side, master_id, part_no, part_desc, quantity = row
                    logger.info(f"Processing row: {row}")  # Log the row being processed

                    vc, created = VcDatabase.objects.update_or_create(
                        part_no=part_no,
                        defaults={
                            'vc_no': vc_no,
                            'side': side,
                            'part_desc': part_desc,
                            'quantity': quantity
                        }
                    )

                    if created:
                        logger.info(f"Created new entry for part_no: {part_no}")
                    else:
                        logger.info(f"Updated existing entry for part_no: {part_no}")

                except ValueError as e:
                    logger.error(f"ValueError processing row {row}: {e}")
                    continue  # Skip the row if there's a value error
                except Exception as e:
                    logger.error(f"Error processing row {row}: {e}")
                    continue  # Skip the row if there's any other error

            return JsonResponse({'success': True, 'message': 'Excel file processed successfully.'})

        except Exception as e:
            logger.error(f"Error processing the uploaded file: {e}")
            return JsonResponse({'success': False, 'message': f'There was an error processing the uploaded file: {e}'})

    return JsonResponse({'success': False, 'message': 'No file uploaded.'})


from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from .forms import SignUpForm, LoginForm

def user_register(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account has been created successfully.')
            return redirect('/')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SignUpForm()
    return render(request, 'user_register.html', {'form': form})
def user_login(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('/')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    
    return render(request, 'user_login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('')

def download_sample_excel(request):
    filepath = os.path.join(os.path.dirname(__file__), 'sample.xlsx')
    with open(filepath, 'rb') as file:
        response = HttpResponse(file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=sample.xlsx'
        return response

@require_http_methods(["DELETE"])
@csrf_exempt
def delete_vc_master(request, id):
    try:
        vc_master = VcMaster.objects.get(id=id)
        vc_num=vc_master.vcnumber
        # Delete related VC entries
        VcDatabase.objects.filter(vc_no=vc_num).delete()
        # Delete the VC master entry
        vc_master.delete()
        return JsonResponse({'success': True})
    except VcMaster.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'VC Master entry not found.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
def add_vc_master(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        vcnumber = data.get('vcnumber')
        model = data.get('model')
        if vcnumber and model:
            new_vc_master = VcMaster(vcnumber=vcnumber, model=model)
            new_vc_master.save()
            return JsonResponse({'success': True, 'id': new_vc_master.id})
        else:
            return JsonResponse({'success': False}, status=400)

def add_trolley_esl(request):
    if request.method == 'POST':
        mac = request.POST.get('mac')
        trolley_code = request.POST.get('trolley_code')
        asn_num = request.POST.get('asn_num')
        color = request.POST.get('color')
        trolley_picking_status = request.POST.get('trolley_picking_status')

        try:
            trolley_data.objects.create(
                mac=mac,
                trolley_code=trolley_code,
                asn_num=asn_num,
                color=color,
                trolley_picking_status=trolley_picking_status
            )
            return JsonResponse({'success': True, 'message': 'Trolley ESL added successfully.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error adding Trolley ESL: {e}'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})

def base_model_matrix(request):
    return render(request ,"model_matrix/base_model_matrix.html") 
