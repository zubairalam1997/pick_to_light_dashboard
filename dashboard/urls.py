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
    path('complete_asn/', views.kitting_config, name='kitting_config'),
    path('asn_input/', views.asn_input, name='asn_input'),
    path('vc_list/', views.vc_list, name='vc_list'),
    path('fetch-existing-vc-entries/', views.fetch_existing_vc_entries, name='fetch_existing_vc_entries'),
    path('update-vc/', views.update_vc, name='update_vc'),
     path('edit_vc/<int:id>/', views.edit_vc, name='edit_vc'),
    path('delete_vc/<str:part_no>/', views.delete_vc, name='delete_vc'),
     path('upload-excel/', views.upload_excel, name='upload_excel'),
     path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.user_register, name='register'),
]