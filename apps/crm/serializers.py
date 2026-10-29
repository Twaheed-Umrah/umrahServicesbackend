from rest_framework import serializers
from .models import Lead, LeadNote, Task

class LeadNoteSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = LeadNote
        fields = ['id', 'note', 'author_name', 'created_at']

    def get_author_name(self, obj):
        if obj.author:
            return f"{obj.author.first_name} {obj.author.last_name}".strip() or obj.author.username
        return "System"


class LeadSerializer(serializers.ModelSerializer):
    history_notes = LeadNoteSerializer(many=True, read_only=True)
    assigned_caller_name = serializers.SerializerMethodField()
    assigned_caller_details = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = [
            'id', 'user', 'name', 'mobile_number', 'email', 'city',
            'source', 'campaign_name', 'journey_type', 'pax_count', 'budget',
            'status', 'notes', 'next_followup_at', 'lost_reason', 'assigned_caller', 'assigned_caller_name',
            'assigned_caller_details', 'is_in_agency_pool', 'history_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

    def get_assigned_caller_name(self, obj):
        if obj.assigned_caller:
            full = f"{obj.assigned_caller.first_name} {obj.assigned_caller.last_name}".strip()
            return full or obj.assigned_caller.username
        return "Unassigned (Master Pool)"

    def get_assigned_caller_details(self, obj):
        if obj.assigned_caller:
            return {
                'id': obj.assigned_caller.id,
                'username': obj.assigned_caller.username,
                'email': obj.assigned_caller.email,
                'is_present': obj.assigned_caller.is_present,
                'caller_status': getattr(obj.assigned_caller, 'caller_status', 'available'),
            }
        return None


class LeadUpdateStatusSerializer(serializers.ModelSerializer):
    new_note = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Lead
        fields = ['status', 'notes', 'new_note', 'assigned_caller']

    def update(self, instance, validated_data):
        request = self.context.get('request')
        user = request.user if request else None

        new_note_text = validated_data.pop('new_note', None)
        old_status = instance.status
        old_caller = instance.assigned_caller

        lead = super().update(instance, validated_data)

        notes_to_create = []
        if new_note_text:
            notes_to_create.append(new_note_text)
            lead.notes = new_note_text
            lead.save(update_fields=['notes'])

        if old_status != lead.status:
            notes_to_create.append(f"Status changed from {old_status} to {lead.status}")

        if old_caller != lead.assigned_caller:
            new_c_name = lead.assigned_caller.username if lead.assigned_caller else "Master Pool"
            notes_to_create.append(f"Reassigned to {new_c_name}")

        for note_txt in notes_to_create:
            LeadNote.objects.create(lead=lead, note=note_txt, author=user)

        return lead


class TaskSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    task_type_display = serializers.CharField(source='get_task_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    lead_name = serializers.CharField(source='related_lead.name', read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'task_type', 'task_type_display',
            'priority', 'priority_display', 'status', 'due_date',
            'assigned_to', 'assigned_to_name', 'created_by', 'created_by_name',
            'related_lead', 'lead_name', 'description', 'resolution_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
