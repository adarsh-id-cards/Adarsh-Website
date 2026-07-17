from django.urls import path
from . import views

app_name = 'api_sharing'

urlpatterns = [
    path('web-share/portfolio/', views.shared_portfolio_list, name='shared_portfolio_list'),
    path('web-share/clients/', views.shared_client_list, name='shared_client_list'),
    path('web-share/contact/', views.shared_contact_submit, name='shared_contact_submit'),
]
