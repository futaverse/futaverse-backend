from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import CharField, Q, Value
from django.db.models.functions import Concat
from django_filters import rest_framework as filters

from .models import User


class UserSearchFilter(filters.FilterSet):
    name = filters.CharFilter(method="filter_by_name")

    class Meta:
        model = User
        fields = ["name"]

    def filter_by_name(self, queryset, name, value):
        role = self.data.get("role")

        if role == User.Role.ALUMNI:
            profile_prefix = "alumni_profile"
        else:
            profile_prefix = "student_profile"

        return (
            queryset.annotate(
                search_full_name=Concat(
                    f"{profile_prefix}__firstname",
                    Value(" "),
                    f"{profile_prefix}__middlename",
                    Value(" "),
                    f"{profile_prefix}__lastname",
                    output_field=CharField(),
                )
            )
            .annotate(similarity=TrigramSimilarity("search_full_name", value))
            .filter(Q(similarity__gt=0.15))
            .order_by("-similarity")
        )
