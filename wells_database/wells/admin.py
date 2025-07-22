from django.contrib import admin
from .models import Area, Wells, Curve, CurveValue, UploadLAS 
from .models import  DeviationSurvey, Checkshot, WellHeader
#registering the models to the admin site

admin.site.register(Area)
admin.site.register(Wells)
admin.site.register(Curve)
admin.site.register(CurveValue)
admin.site.register(UploadLAS)
admin.site.register(DeviationSurvey)
admin.site.register(Checkshot)
admin.site.register(WellHeader)
# Register your models here.
