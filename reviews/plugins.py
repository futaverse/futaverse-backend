from decimal import Decimal

from .metrics_serializers import StudentRatesAlumnusMetricsSerializer, AlumnusRatesStudentMetricsSerializer

class BaseReviewPlugin:
    metrics_serializer = None
    
    def compute_overall(self, metrics: dict) -> Decimal:
        if not metrics:
            return Decimal("0.00")

        values = [Decimal(str(v)) for v in metrics.values()]
        return (sum(values) / len(values)).quantize(Decimal("0.01"))

class AlumnusRatesStudentPlugin(BaseReviewPlugin):
    metrics_serializer = AlumnusRatesStudentMetricsSerializer

class StudentRatesAlumnusPlugin(BaseReviewPlugin):
    metrics_serializer = StudentRatesAlumnusMetricsSerializer

class ReviewType:
    STUDENT_RATES_ALUMNUS = "student_rates_alumnus"
    ALUMNUS_RATES_STUDENT = "alumnus_rates_student"

ENGAGEMENT_REVIEW_PLUGIN = {
    ReviewType.STUDENT_RATES_ALUMNUS: StudentRatesAlumnusPlugin(),
    ReviewType.ALUMNUS_RATES_STUDENT: AlumnusRatesStudentPlugin(),
}