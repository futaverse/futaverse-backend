from rest_framework import serializers


class StudentRatesAlumnusMetricsSerializer(serializers.Serializer):
    communication = serializers.IntegerField(min_value=1, max_value=5)
    availability = serializers.IntegerField(min_value=1, max_value=5)
    guidance_quality = serializers.IntegerField(min_value=1, max_value=5)
    industry_knowledge = serializers.IntegerField(min_value=1, max_value=5)
    supportiveness = serializers.IntegerField(min_value=1, max_value=5)
    
class AlumnusRatesStudentMetricsSerializer(serializers.Serializer):
    communication = serializers.IntegerField(min_value=1, max_value=5)
    technical_competence = serializers.IntegerField(min_value=1, max_value=5)
    initiative = serializers.IntegerField(min_value=1, max_value=5)
    reliability = serializers.IntegerField(min_value=1, max_value=5)
    professionalism = serializers.IntegerField(min_value=1, max_value=5)