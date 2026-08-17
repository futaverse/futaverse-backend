from django.urls import path

from core.models import User


def queryset_by_role(
    user,
    model_class,
    *,
    alumnus_filter,
    student_filter,
    select_related=(),
    order_by=None,
):
    if user.role == User.Role.ALUMNI:
        filter_kwargs = alumnus_filter() if callable(alumnus_filter) else alumnus_filter
        qs = model_class.objects.filter(**filter_kwargs)
    elif user.role == User.Role.STUDENT:
        filter_kwargs = student_filter() if callable(student_filter) else student_filter
        qs = model_class.objects.filter(**filter_kwargs)
    else:
        return model_class.objects.none()

    if select_related:
        qs = qs.select_related(*select_related)
    if order_by:
        qs = qs.order_by(order_by)
    return qs


def generate_engagement_urls(
    *,
    prefix,
    entity_views,
    application_views,
    offer_views,
    engagement_views,
    extra=None,
):
    patterns = []

    patterns.append(
        path(
            "/application",
            application_views["create"].as_view(),
            name=f"create-{prefix}-application",
        )
    )
    patterns.append(
        path(
            "/applications",
            application_views["list"].as_view(),
            name=f"list-{prefix}-applications",
        )
    )
    patterns.append(
        path(
            "/applications/<slug:sqid>",
            application_views["retrieve"].as_view(),
            name=f"retrieve-{prefix}-application",
        )
    )
    patterns.append(
        path(
            "/applications/<slug:application_id>/accept",
            application_views["accept"].as_view(),
            name=f"accept-{prefix}-application",
        )
    )
    patterns.append(
        path(
            "/applications/<slug:application_id>/reject",
            application_views["reject"].as_view(),
            name=f"reject-{prefix}-application",
        )
    )
    patterns.append(
        path(
            "/applications/<slug:application_id>/withdraw",
            application_views["withdraw"].as_view(),
            name=f"withdraw-{prefix}-application",
        )
    )

    patterns.append(
        path(
            "/offer",
            offer_views["create"].as_view(),
            name=f"create-{prefix}-offer",
        )
    )
    patterns.append(
        path(
            "/offers",
            offer_views["list"].as_view(),
            name=f"list-{prefix}-offers",
        )
    )
    patterns.append(
        path(
            "/offers/<slug:sqid>",
            offer_views["retrieve"].as_view(),
            name=f"retrieve-{prefix}-offer",
        )
    )
    patterns.append(
        path(
            "/offers/<slug:offer_id>/accept",
            offer_views["accept"].as_view(),
            name=f"accept-{prefix}-offer",
        )
    )
    patterns.append(
        path(
            "/offers/<slug:offer_id>/reject",
            offer_views["reject"].as_view(),
            name=f"reject-{prefix}-offer",
        )
    )
    patterns.append(
        path(
            "/offers/<slug:offer_id>/withdraw",
            offer_views["withdraw"].as_view(),
            name=f"withdraw-{prefix}-offer",
        )
    )

    patterns.append(
        path(
            "/engagements",
            engagement_views["list"].as_view(),
            name=f"list-{prefix}-engagements",
        )
    )
    patterns.append(
        path(
            "/engagements/<slug:sqid>",
            engagement_views["retrieve"].as_view(),
            name=f"retrieve-{prefix}-engagement",
        )
    )
    patterns.append(
        path(
            "/engagements/<slug:sqid>/completed",
            engagement_views["completed"].as_view(),
            name=f"mark-{prefix}-completed",
        )
    )
    patterns.append(
        path(
            "/engagements/<slug:sqid>/acknowledged",
            engagement_views["acknowledged"].as_view(),
            name=f"mark-{prefix}-acknowledged",
        )
    )

    if extra:
        patterns.extend(extra)

    patterns.append(
        path(
            "",
            entity_views["list_create"].as_view(),
            name=f"list-create-{prefix}s",
        )
    )
    patterns.append(
        path(
            "/<slug:sqid>",
            entity_views["rud"].as_view(),
            name=f"rud-{prefix}",
        )
    )
    patterns.append(
        path(
            "/<slug:sqid>/toggle-active",
            entity_views["toggle_active"].as_view(),
            name=f"toggle-{prefix}-active",
        )
    )

    return patterns
