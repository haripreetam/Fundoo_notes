from rest_framework import serializers

from .models import Label


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ['id', 'name', 'color', 'user']
        extra_kwargs = {
            'user': {'write_only': True}  # Correct way to specify write-only fields
        }