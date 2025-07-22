from django.db import models

#creating models for the well logs database
class Area(models.Model):  #defining the area model,  and inheriting the models. this groups wells into projects or fields.
    area_name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.area_name
    

class Wells(models.Model): #defining the wells model annd its inheriting the models.Model class. the class for the tables.
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    well_name = models.CharField(max_length=100)
    uwi = models.CharField("Unique Well Identifier", max_length=100, unique=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    depth_start = models.FloatField(blank=True, null=True)
    depth_stop = models.FloatField(blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    # Adding optional fields for latitude and longitude
    # These can be used to store the geographical coordinates of the well.
    # They are set to blank=True and null=True to allow for wells without these details.
    operator = models.CharField(max_length=100, blank=True, null=True)
    field = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    unit = models.CharField(max_length=50)

    def __str__(self):
        return self.well_name
    
class Curve(models.Model): #defining the curve model, which will hold the well log curves.
    well = models.ForeignKey(Wells, on_delete=models.CASCADE)
    mnemonic = models.CharField(max_length=50)
    unit = models.CharField(max_length=50, null= True, blank=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.mnemonic} - {self.well.well_name}"
    
class CurveValue(models.Model): #defining the curve value model, which will hold the values for each curve at different depths.
    curve = models.ForeignKey(Curve, on_delete=models.CASCADE)
    depth = models.FloatField()
    value = models.FloatField()

class UploadLAS (models.Model):  #defining the upload LAS model, which will hold the uploaded LAS files.
    files = models.FileField(upload_to='las_files/')
    well = models.ForeignKey(Wells, on_delete=models.CASCADE, null=True, blank=True)  # Optional: link to a well
    uploaded_at = models.DateTimeField(auto_now_add=True)

class DeviationSurvey(models.Model):
    well = models.ForeignKey(Wells, on_delete=models.CASCADE)
    md = models.FloatField()  # Measured Depth
    incl = models.FloatField()  # Inclination
    azim = models.FloatField()  # Azimuth

    def __str__(self):
        return f"{self.well.well_name} at {self.md}m"

class Checkshot(models.Model):
    well = models.ForeignKey(Wells, on_delete=models.CASCADE)
    depth = models.FloatField()
    time = models.FloatField()

    

class WellHeader(models.Model):
    well = models.ForeignKey(Wells, on_delete=models.CASCADE)
    content = models.TextField()  # Store header as text
    uploaded_at = models.DateTimeField(auto_now_add=True)


    

    



# Create your models here.
