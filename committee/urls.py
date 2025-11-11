from django.urls import path
from . import views

app_name = "committee"

urlpatterns = [
    path("", views.offense_list, name="offense_list"),
    path("analytics/", views.analytics_dashboard, name="analytics_dashboard"),
    path("create/", views.offense_create, name="offense_create"),
    path("<int:offense_id>/", views.offense_detail, name="offense_detail"),
    path("<int:offense_id>/update/", views.offense_update, name="offense_update"),
    path("<int:offense_id>/delete/", views.offense_delete, name="offense_delete"),
    path("<int:offense_id>/pdf/", views.render_pdf_view, name="offense_pdf"),
]
