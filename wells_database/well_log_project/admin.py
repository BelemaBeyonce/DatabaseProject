from django.contrib import admin
from well.models import Area, Wells, Curve, CurveValue #registering the models to the admin site

admin.site.register(Area)
admin.site.register(Wells)
admin.site.register(Curve)
admin.site.register(CurveValue)
# Register your models here.