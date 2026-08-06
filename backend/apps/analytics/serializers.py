from rest_framework import serializers
from .models import NavigationLog


class LogEventSerializer(serializers.Serializer):
    event_type = serializers.ChoiceField(choices=NavigationLog.EventType.choices)
    session_id = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    metadata = serializers.DictField(required=False, default=dict)
