from django.contrib.auth import get_user_model
from django.db import models


class Label(models.Model):
    name = models.CharField(max_length=255, null=False)
    color = models.CharField(max_length=50, null=True, blank=True)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)

    def __str__(self):
        return self.name