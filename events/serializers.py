from django.utils import timezone

from rest_framework import serializers

from .models import Event, Ticket, TicketPurchase, VirtualMeeting

class VirtualMeetingSerializer(serializers.ModelSerializer):
    class Meta:
        model = VirtualMeeting
        fields = ['sqid', 'platform', 'join_url', 'room_name']
        read_only_fields = ['sqid', 'created_at']
        
# class VirtualMeetingDetailsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = VirtualMeeting
#         exclude = ['is_deleted', 'deleted_at', 'id']
#         read_only_fields = ['sqid', 'created_at', 'updated_at']

class CreateTicketSerializer(serializers.ModelSerializer):
    event = serializers.SlugRelatedField(queryset=Event.objects.all(), slug_field='sqid')
    sales_price = serializers.ReadOnlyField()
    
    class Meta:
        model = Ticket
        exclude = ['is_deleted', 'deleted_at']
        read_only_fields = ['sqid', 'created_at', 'updated_at', 'quantity_sold', 'sales_price']
        
class TicketSerializer(serializers.ModelSerializer):
    sales_price = serializers.ReadOnlyField()
    event = serializers.SlugRelatedField(read_only=True, slug_field='sqid')
    
    class Meta:
        model = Ticket
        exclude = ['is_deleted', 'deleted_at', 'id']
        read_only_fields = ['sqid', 'created_at', 'updated_at', 'quantity_sold', 'sales_price']

class EventSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, required=False)
    platform = serializers.ChoiceField(choices=VirtualMeeting.Platform, required=False, write_only=True)
    redirect_after_auth = serializers.URLField(required=False, write_only=True)
    
    virtual_meeting = VirtualMeetingSerializer(required=False, read_only=True)
    
    class Meta:
        model = Event
        exclude = ['is_deleted', 'deleted_at', 'id']
        read_only_fields = ['sqid', 'created_at', 'updated_at', 'google_event_id', 'google_meet_link', 'is_cancelled', 'creator']
        
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        
        mode = validated_data.get("mode")
        platform = validated_data.get("platform")
        
        if (mode == Event.Mode.PHYSICAL or mode == Event.Mode.HYBRID) and not platform:
            raise serializers.ValidationError({"platform": "Platform is required for events with virtual or hybrid modes"})
        
        return validated_data
        
    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets", None)
        event = super().create(validated_data)
        
        if not tickets_data:
            Ticket.objects.create(event=event, name="Free", description="Standard", price=0, type=Ticket.Type.DEFAULT)
          
        if tickets_data:    
            for ticket_data in tickets_data:
                Ticket.objects.create(event=event, **ticket_data)
        
        return event
    
class TicketPurchaseSerializer(serializers.ModelSerializer):
    ticket = serializers.SlugRelatedField(queryset=Ticket.objects.all(), slug_field='sqid')
    email = serializers.EmailField(write_only=True, required=False)
    
    class Meta:
        model = TicketPurchase
        fields = ['ticket', 'email']
        read_only_fields = ['sqid', 'created_at', 'updated_at']
        
    def validate_ticket(self, value: Ticket):
        if value.is_active == False:
            raise serializers.ValidationError({"ticket": "Ticket is not active"})
        
        if value.sales_start > timezone.now():
            raise serializers.ValidationError({"ticket": "Ticket sales have not started yet"})
        
        if value.sales_end and value.sales_end < timezone.now():
            raise serializers.ValidationError({"ticket": "Ticket sales have ended"})
        
        if  value.quantity is not None and value.quantity_sold >= value.quantity:
            raise serializers.ValidationError({"ticket": "Ticket is sold out"})
        
        return value
    
class UpdateEventSerializer(serializers.ModelSerializer):
    redirect_after_auth = serializers.URLField(required=False, write_only=True)
    
    class Meta:
        model = Event
        fields = ['title', 'description', 'date', 'start_time', 'duration_mins', 'venue', 'max_capacity', 'allow_sponsorship', 'allow_donations', 'is_published', 'is_cancelled', 'redirect_after_auth']
        read_only_fields = ['sqid']
        
    def validate_max_capacity(self, value):
        total_sold = sum(ticket.quantity_sold for ticket in self.instance.tickets.all())
        if value and value < total_sold:
            raise serializers.ValidationError(f"Capacity cannot be lower than already sold tickets ({total_sold}).")
        return value

    def validate_date(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("Event date cannot be in the past.")
        return value
        
class ListEventSerializer(serializers.ModelSerializer):
    # tickets = TicketSerializer(many=True, read_only=True)
    virtual_meeting = VirtualMeetingSerializer(read_only=True)
    starting_price = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Event
        exclude = ['is_deleted', 'deleted_at', 'id', 'creator']
        
    def get_starting_price(self, obj):
        lowest = obj.tickets.order_by('price').first()
        return lowest.price if lowest else 0
    
class UpdateEventModeSerializer(serializers.ModelSerializer):
    mode = serializers.ChoiceField(choices=Event.Mode, required=True)
    venue = serializers.CharField(required=False)
    platform = serializers.ChoiceField(choices=VirtualMeeting.Platform, required=False)
    
    class Meta:
        model = Event
        fields = ['mode', 'venue', 'platform']
        read_only_fields = ['sqid']
        
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        
        mode = validated_data.get('mode', self.instance.mode if self.instance else None)
        venue = validated_data.get('venue', self.instance.venue if self.instance else None)
        
        platform = validated_data.get('platform')
        if hasattr(self.instance, 'virtual_meeting'):
            platform = validated_data.get('platform', self.instance.virtual_meeting.platform if self.instance else None)

        if mode in [Event.Mode.PHYSICAL, Event.Mode.HYBRID] and not venue:
            raise serializers.ValidationError({"venue": "Venue is required for Physical or Hybrid events."})
        
        if mode in [Event.Mode.VIRTUAL, Event.Mode.HYBRID] and not platform:
            raise serializers.ValidationError({"platform": "Platform is required for Virtual or Hybrid events."})
            
        return attrs

class ListTicketPurchaseSerializer(serializers.ModelSerializer):
    ticket = TicketSerializer(read_only=True)
    
    class Meta:
        model = TicketPurchase
        fields = ['email', 'ticket', 'ticket_uid', 'is_paid', 'checked_in', 'checked_in_at']
        read_only_fields = ['sqid', 'created_at', 'updated_at']