from django.db import models

# Create your models here.
class users(models.Model):
    department = models.CharField(max_length = 255, null=True, blank=True)
    code = models.CharField(max_length = 255, null=True, blank=True)
    email = models.EmailField(max_length = 255, unique=True)
    designation = models.CharField(max_length = 255)

class seminarHall(models.Model):
    capacity = models.IntegerField()
    name = models.CharField(max_length = 255)
    incharge = models.TextField()
    status = models.CharField(max_length = 255, default = "Active")

class event(models.Model):
    name = models.CharField(max_length = 255)
    agenda = models.TextField()
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status_HoD = models.CharField(max_length = 255)
    status_Admin = models.CharField(max_length = 255)
    audience = models.IntegerField()
    user_id = models.ForeignKey(users, on_delete=models.CASCADE)
    location_id = models.ForeignKey(seminarHall, on_delete=models.CASCADE)
    hod_id = models.ForeignKey(users, related_name= "HoD", on_delete=models.CASCADE)
    feedback_HoD = models.TextField(blank=True, null=True)
    feedback_Admin = models.TextField(blank=True, null=True)