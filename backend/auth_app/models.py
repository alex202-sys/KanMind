from django.db import models
from django.contrib.auth.models import User
from django.db import models

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    #telefonnummer = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        return self.user.username
    
    @property
    def fullname(self):
        # Holt sich die Daten dynamisch vom User-Model
        return f"{self.user.first_name} {self.user.last_name}".strip()





