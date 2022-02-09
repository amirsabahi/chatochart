from django.urls import path
from . import views

app_name = 'social'
urlpatterns = [
       path('spaces/',
            views.SpaceListView.as_view(),
            name='space_list'),
       path('space/<pk>/',
            views.SpaceDetailView.as_view(),
            name='space_detail'),
]
