from django.urls import path
from . import views
urlpatterns=[
    
    path('' , views.picking_plan, name='picking_plan'),
    path('get_combined_data/', views.get_combined_data, name='get_combined_data'),
    path('getPayloadData/', views.get_Payload_Data, name='get_payload_data'),
    path('open_modal', views.open_modal, name='open_modal'),
]