from django.contrib import admin
from .models import EslPart, VcDatabase, VcMaster, WorkTable ,AsnSchedule ,VcAndAsn , vc_n_asn ,trolley_data
# Register your models here.
admin.site.register(EslPart)
admin.site.register(VcDatabase)
admin.site.register(VcMaster)
admin.site.register(WorkTable)
admin.site.register(AsnSchedule)
admin.site.register(VcAndAsn)
admin.site.register(vc_n_asn)
admin.site.register(trolley_data)