from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    # Client CRUD endpoints
    path('', views.ClientListView.as_view(), name='client_list'),
    path('create/', views.ClientCreateView.as_view(), name='client_create'),
    path('<int:id>/', views.ClientDetailView.as_view(), name='client_detail'),
    path('<int:id>/update/', views.ClientUpdateView.as_view(), name='client_update'),
    path('<int:id>/location/', views.ClientLocationView.as_view(), name='client_location'),
    
    # Search and utility endpoints
    path('search/', views.client_search, name='client_search'),
    path('nearby/', views.nearby_clients, name='nearby_clients'),
]
