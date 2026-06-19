from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('property/<int:pk>/', views.property_detail, name='property_detail'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('post/', views.post_property, name='post_property'),
    path('favorite/<int:pk>/', views.toggle_favorite, name='toggle_favorite'),
    path('rate/<int:pk>/', views.rate_property, name='rate_property'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('contact/<int:pk>/', views.contact_owner, name='contact_owner'),
    path('search/', views.search, name='search'),
    path('about/', views.about, name='about'),
    path('contact-page/', views.contact_page, name='contact_page'),
    path('privacy/', views.privacy, name='privacy'),
    path('send-message/<int:pk>/', views.send_message, name='send_message'),
    path('inbox/', views.inbox, name='inbox'),
    path('message/<int:pk>/', views.message_detail, name='message_detail'),
    path('reply/<int:pk>/', views.reply_message, name='reply_message'),
    path('complete-deal/<int:pk>/', views.complete_deal, name='complete_deal'),
    path('transaction/<int:transaction_id>/', views.transaction_detail, name='transaction_detail'),
]