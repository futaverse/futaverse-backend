from decimal import Decimal
from rest_framework.exceptions import ValidationError


class BaseReviewPlugin:
    """Base plugin for review validation and rating computation."""
    
    allowed_metrics = []
    
    def validate_metrics(self, metrics: dict) -> dict:
        """
        Validate metrics dict against allowed_metrics and value ranges.
        Raises ValidationError if keys are invalid or values are outside 1-5.
        Returns the validated metrics dict.
        """
        if not metrics:
            return metrics
        
        for key, value in metrics.items():
            if key not in self.allowed_metrics:
                raise ValidationError(f"Metric '{key}' is not allowed for this review type.")
            
            if not isinstance(value, (int, float, Decimal)):
                raise ValidationError(f"Metric '{key}' must be numeric.")
            
            value_decimal = Decimal(str(value))
            if value_decimal < 1 or value_decimal > 5:
                raise ValidationError(f"Metric '{key}' must be between 1 and 5.")
        
        return metrics
    
    def compute_overall(self, metrics: dict) -> Decimal:
        """
        Compute overall rating as the mean of all metric values.
        Returns Decimal rounded to 2 places.
        """
        if not metrics:
            return Decimal("0.00")
        
        values = [Decimal(str(v)) for v in metrics.values()]
        mean = sum(values) / len(values)
        return mean.quantize(Decimal("0.01"))


class AlumnusRatesStudentPlugin(BaseReviewPlugin):
    """Plugin for alumni rating students after internship engagement."""
    
    allowed_metrics = [
        "communication",
        "technical_competence",
        "initiative",
        "reliability",
        "professionalism"
    ]


class StudentRatesAlumnusPlugin(BaseReviewPlugin):
    """Plugin for students rating alumni mentors after mentorship engagement."""
    
    allowed_metrics = [
        "communication",
        "availability",
        "guidance_quality",
        "industry_knowledge",
        "supportiveness"
    ]


# Plugin registry: (source_content_type_id, reviewer_role) -> plugin instance
plugin_registry = {}


def register_plugin(source_content_type_id, reviewer_role, plugin_class):
    """
    Register a plugin in the registry.
    
    Args:
        source_content_type_id: ContentType ID of the source (e.g., InternshipEngagement)
        reviewer_role: String role of the reviewer (e.g., 'alumni', 'student')
        plugin_class: Plugin class (not instance) to instantiate
    """
    plugin_registry[(source_content_type_id, reviewer_role)] = plugin_class()


def get_plugin(source_content_type_id, reviewer_role):
    """
    Look up a plugin in the registry.
    Returns None if not found.
    
    Args:
        source_content_type_id: ContentType ID of the source
        reviewer_role: String role of the reviewer
    
    Returns:
        Plugin instance or None
    """
    return plugin_registry.get((source_content_type_id, reviewer_role))
