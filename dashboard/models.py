from django.db import models

class AsnSchedule(models.Model):
    STATUS_CHOICES = (
        ('processing', 'Processing...'),
        ('completed', 'Completed'),
    )
    master_id = models.AutoField(primary_key=True)
    asn_no = models.CharField(max_length=50, blank=True, null=True)
    side = models.CharField(max_length=5, blank=True, null=True)
    model = models.CharField(max_length=50, blank=True, null=True)
    vc_no = models.CharField(max_length=50, blank=True, null=True)
    seq_no = models.CharField(max_length=50, blank=True, null=True)
    datetime = models.DateTimeField(blank=True, null=True)
    selection_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending...')
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    duration = models.IntegerField(blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    prod_date = models.DateTimeField(blank=True, null=True)
    trqr = models.CharField(max_length=50, blank=True, null=True)

    
class EslPart(models.Model):
    masterid = models.AutoField(primary_key=True)
    rack = models.CharField(max_length=5, blank=True, null=True)
    seq = models.IntegerField(blank=True, null=True)
    rw = models.IntegerField(blank=True, null=True)
    partno = models.CharField(max_length=58, blank=True, null=True)
    part_desc = models.CharField(max_length=58, blank=True, null=True)
    side = models.CharField(max_length=5, blank=True, null=True)
    tagid = models.CharField(max_length=50, blank=True, null=True)
    tagname = models.CharField(max_length=58, blank=True, null=True)
    tagcode = models.CharField(max_length=59, blank=True, null=True)
    min1 = models.IntegerField(blank=True, null=True)
    max1 = models.IntegerField(blank=True, null=True)

    
class VcDatabase(models.Model):
    vc_no = models.CharField(max_length=50, blank=True, null=True)
    side = models.CharField(max_length=5, blank=True, null=True)
    master_id = models.AutoField(primary_key=True)
    part_no = models.CharField(max_length=50, blank=True, null=True)
    part_desc = models.CharField(max_length=50, blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)

   
class VcMaster(models.Model):
    id = models.BigAutoField(primary_key=True)
    vcnumber = models.CharField(blank=True, null=True)
    model = models.CharField(blank=True, null=True)

    
class WorkTable(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    )
    id = models.BigAutoField(primary_key=True)
    tagid = models.CharField(max_length=50, blank=True, null=True)
    tagcode = models.CharField(max_length=50, blank=True, null=True)
    tagname = models.CharField(max_length=50, blank=True, null=True)
    stdatetime = models.DateTimeField(blank=True, null=True)
    eddatetime = models.DateTimeField(blank=True, null=True)
    asn = models.CharField(max_length=50, blank=True, null=True)
    side = models.CharField(max_length=5, blank=True, null=True)
    partno = models.CharField(max_length=50, blank=True, null=True)
    partdesc = models.CharField(max_length=50, blank=True, null=True)
    qty = models.IntegerField(blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    rack = models.CharField(max_length=50, blank=True, null=True)
    seq = models.IntegerField(blank=True, null=True)
    rw = models.IntegerField(blank=True, null=True)
    clan = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    tror = models.CharField(max_length=50, blank=True, null=True)
    mint = models.IntegerField(blank=True, null=True)
    maxi = models.IntegerField(blank=True, null=True)
    trigtime = models.DateTimeField(blank=True, null=True)

   
class VcAndAsn(models.Model):
    id = models.BigAutoField(primary_key=True)
    vc_number = models.CharField(max_length=50, blank=True, null=True)
    asn_number = models.CharField(max_length=100, blank=True, null=True)
    
    # Specify the database alias for this model
    # class Meta:
    #     using = 'vc_asn'
        # managed = False  # Optional, set to False if the table is managed externally

class vc_n_asn(models.Model):
    id = models.BigAutoField(primary_key=True)
    schedule_date_time   = models.DateTimeField(max_length=100 , blank=True ,null=True)
    vcn = models.CharField(max_length=50, blank=True, null=True)
    asnn = models.CharField(max_length=100, blank=True, null=True)

class trolley_data(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    )
    mac = models.CharField(max_length=50, blank=True, null=True)
    trolley_code = models.CharField( max_length=25,blank=True, null= True)
    asn_num = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    trolley_picking_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')