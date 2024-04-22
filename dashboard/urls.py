from django.urls import path
from . import views
urlpatterns=[
    
    path('' , views.picking_plan, name='picking_plan'),
    path('get_combined_data/', views.get_combined_data, name='get_combined_data'),
    path('getPayloadData/', views.get_Payload_Data, name='get_payload_data'),
    path('kitting_in_process/', views.kitting_in_process , name ='kitting_in_process'),
    path('open_modal/', views.open_modal, name='open_modal'),
    path('render_modal/', views.render_modal, name='render_modal'),
    path('enter-key', views.enter_key, name='enter_key'),
    path('completed_kittings/', views.completed_kittings, name='completed_kittings'),
]