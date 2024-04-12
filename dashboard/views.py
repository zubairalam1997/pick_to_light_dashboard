from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import vc_n_asn ,VcMaster , VcDatabase ,EslPart
import requests


def get_combined_data(request):
    vc_n_asn_data = vc_n_asn.objects.all()
    combined_data = []

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
        }
        combined_data.append(data_entry)

    return JsonResponse({'combined_data': combined_data})

def picking_plan(request):
    vc_n_asn_data = vc_n_asn.objects.all()

    # Define a list to store the combined data
    combined_data = []

    # Iterate over each entry in dummy_data
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
        else:
            # If no matching model found, append a message to the combined_data list
            combined_data.append({
                'vc_number': vc_number,
                'asn_number': asn_number,
                'model': 'No matching model found',
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
            vc_data = VcDatabase.objects.get(vc_no=vc_number)
            part_number = vc_data.part_no

            # Match part number in ESL model
            try:
                esl_data = EslPart.objects.get(partno=part_number)
                tag_id = esl_data.tagid

                data = {
                    'part_number': part_number,
                    'part_description': vc_data.part_desc,
                    'quantity': vc_data.quantity,
                    'tag_id': tag_id,
                }
                print(data)
                return JsonResponse(data)
            except EslPart.DoesNotExist:
                return JsonResponse({'error': 'Part number not found in ESL model'}, status=404)

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

