from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import vc_n_asn ,VcMaster , VcDatabase ,EslPart
import requests
import json

def get_combined_data(request):
    
    qr_data = request.POST.get('qr_data')
    vc_n_asn_data = vc_n_asn.objects.all()
    combined_data = []
    print(qr_data)
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

    return JsonResponse({'combined_data': combined_data})

@csrf_exempt
def picking_plan(request):
    qr_data = request.POST.get('qr_data')
    vc_n_asn_data = vc_n_asn.objects.all()

    # Define a list to store the combined data
    combined_data = []
    
    print(qr_data)

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
                'trolley_qr': qr_data,
                'plan_date': date_time.date(),
                'schedule_time': date_time.time(),
            }

            # Add the dictionary to the combined_data list
            combined_data.append(data_entry)
        else:
            # If no matching model found, append a message to the combined_data list
            combined_data.append({
                'vc_number': vc_number,
                'asn_number': asn_number,
                'model': 'No matching model found',
                'trolley_qr': 'no q_r data found',
                'plan_date': date_time.date(),
                'schedule_time':date_time.time(),
            })

    # Render the template with the combined data
        #return JsonResponse({'combined_data': combined_data})
    return render(request, 'pick_plan.html', {'combined_data': combined_data})

def open_modal(request):
    
    return render(request, 'scanner.html' )

@csrf_exempt
def get_Payload_Data(request):
    if request.method == 'POST':
        vc_number = request.POST.get('vc_number')

        try:
            # Get all VC data objects for the given VC number
            vc_data_list = VcDatabase.objects.filter(vc_no=vc_number)

            # Initialize an empty list to store the data for each part number
            data_list = []

            for vc_data in vc_data_list:
                part_number = vc_data.part_no

                try:
                    # Get the ESL data for the current part number
                    esl_data = EslPart.objects.get(partno=part_number)

                    # Append the data for the current part number to the list
                    data_list.append({
                        "Part No.": part_number,
                        "DESC": vc_data.part_desc,
                        "QTY": vc_data.quantity,
                        "mac": esl_data.tagid,
                        "ledstate": "0",  # Default value for ledstate
                        "ledrgb": "ff00",
                        "outtime": "60",
                        "styleid": "50",
                        "qrcode": "12345",
                        "mappingtype": "79"
                    })
                except EslPart.DoesNotExist:
                    # Handle if part number not found in ESL model
                    pass

            if data_list:
                #print('post_it:',data_list)
                # for tag_id in data_list[tag_id]:
                # response = requests.post('http://192.168.1.100/wms/associate/updateScreen', json=data_list)
                # response.raise_for_status()
                # # Check if the request was successful
                # if response.ok:
                #     return JsonResponse({'success': 'Data posted successfully'})
                # else:
                #     return JsonResponse({'error': 'Failed to post data'}, status=500)
            
                return JsonResponse(data_list, safe=False)
            else:
                return JsonResponse({'error': 'No matching part numbers found in ESL model'}, status=404)

        except VcDatabase.DoesNotExist:
            return JsonResponse({'error': 'VC number not found'}, status=404)

    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)

    #NOW EXTRACT PART NUMBER FROM THIS AND MATCH IT IN ESL AND POST DATA ON THAT MAC BEFORE THIS MAKE A POSTDATA FUNCTION 
def postData(mac, part_number, description, quantity):
    payload = [{"mac": mac,
                "Part No.": part_number,
                "DESC": description,
                "QTY": quantity,
                "ledstate": "0",  # Default value for ledstate
                "ledrgb": "ff00",
                "outtime": "60",
                "styleid": "50",
                "qrcode": "12345",
                "mappingtype": "79"}]

    try:
        r = requests.post('http://192.168.1.100/wms/associate/updateScreen', json=payload)
        r.raise_for_status()
        return JsonResponse({'message': 'Screen updated successfully'})
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': str(e)}, status=500)

