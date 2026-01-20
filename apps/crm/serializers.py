from rest_framework import serializers
from .models import Lead, LeadNote

class LeadNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadNote
        fields = ['id', 'note', 'created_at']

class LeadSerializer(serializers.ModelSerializer):
    history_notes = LeadNoteSerializer(many=True, read_only=True)
    
    class Meta:
        model = Lead
        fields = [
            'id', 'name', 'mobile_number', 'email', 'status', 
            'notes', 'history_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class LeadUpdateStatusSerializer(serializers.ModelSerializer):
    new_note = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Lead
        fields = ['status', 'notes', 'new_note']

    def update(self, instance, validated_data):
        new_note_text = validated_data.pop('new_note', None)
        if new_note_text:
            LeadNote.objects.create(lead=instance, note=new_note_text)
            # Optionally update the main notes field too
            instance.notes = new_note_text 
        return super().update(instance, validated_data)
