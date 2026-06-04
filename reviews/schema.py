from drf_spectacular.utils import extend_schema, PolymorphicProxySerializer, OpenApiExample
from drf_spectacular.openapi import AutoSchema
from .metrics_serializers import StudentRatesAlumnusMetricsSerializer, AlumnusRatesStudentMetricsSerializer

CREATEREVIEWSCHEMA = {
    "description": "Create a review for an engagement. The metrics fields depend on the type of review being created (i.e. whether a student is reviewing an alumnus or vice versa). Check the examples for reference.",
    "request": {
        'application/json': PolymorphicProxySerializer(
            component_name='CreateReview',
            serializers=[
                StudentRatesAlumnusMetricsSerializer,
                AlumnusRatesStudentMetricsSerializer,
            ],
            resource_type_field_name='engagement_type',
        )
    },
    "examples": [
        OpenApiExample(
            name="Student rates Alumnus",
            value={
                "engagement_type": "internship_engagement",
                "engagement": "abc1234",
                "review_text": "Great mentor!",
                "metrics": {
                    "communication": 5,
                    "availability": 4,
                    "guidance_quality": 5,
                    "industry_knowledge": 4,
                    "supportiveness": 5,
                }
            },
            request_only=True,
        ),
        OpenApiExample(
            name="Alumnus rates Student",
            value={
                "engagement_type": "internship_engagement",
                "engagement": "abc1234",
                "review_text": "Hardworking student.",
                "metrics": {
                    "communication": 5,
                    "technical_competence": 4,
                    "initiative": 3,
                    "reliability": 5,
                    "professionalism": 4,
                }
            },
            request_only=True,
        ),
    ]
}