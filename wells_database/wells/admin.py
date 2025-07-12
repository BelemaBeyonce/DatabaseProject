from django.contrib import admin
from .models import Area, Wells, Curve, CurveValue, UploadLAS #registering the models to the admin site

admin.site.register(Area)
admin.site.register(Wells)
admin.site.register(Curve)
admin.site.register(CurveValue)
admin.site.register(UploadLAS)
# Register your models here.
