from django.db import models

# Create your models here.
class AreaCode(models.Model):
    name = models.CharField(max_length=30, primary_key=True)
    code = models.IntegerField(unique=True)

    def __str__(self):
        return self.name

class AreaData(models.Model):
    areaname = models.ForeignKey(AreaCode, on_delete=models.CASCADE, related_name="area_data")
    title = models.CharField(max_length=200)
    addr = models.CharField(max_length=300)
    image = models.CharField(max_length=500)
    mapy = models.CharField(max_length=200)
    mapx = models.CharField(max_length=200)

    class Meta:
        ordering = ['areaname']