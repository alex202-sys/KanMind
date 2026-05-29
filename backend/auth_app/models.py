from django.db import models
from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        return self.user.username

    @property
    def fullname(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        return f"{self.user.first_name} {self.user.last_name}".strip()
