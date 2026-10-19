from django.db import models

# Create your models here.

class FuelStation(models.Model):
    opis_ID=models.IntegerField(unique=True)
    name= models.CharField(max_length=255)
    address= models.CharField(max_length=255)
    city= models.CharField(max_length=255)
    state= models.CharField(max_length=2)
    rack_id=models.IntegerField(null=True,blank=True)
    price= models.DecimalField(max_digits=10,decimal_places=3)
    lat=models.DecimalField(max_digits=8, decimal_places=3,null=True,blank=True)
    lon= models.DecimalField(max_digits=8,decimal_places=3,null=True,blank=True)

    def __str__(self):
        return f"{self.name} ({self.city}, {self.state})"