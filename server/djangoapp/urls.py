from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from . import views

app_name = 'djangoapp'
urlpatterns = [
    
    # name the URL
    path(route='', view=views.get_dealerships, name='index'),
    # path for about view
    path(route='about', view=views.about, name="about"),
    # path for contact us view
    path(route='contact', view=views.contact, name='contact'),
    # path for registration
    path('signup/', views.signup_view, name='signup'),
    
    # path for login
    path('login/', views.login_view, name='login'),
    # path for logout
    path('signout/', views.signout_view, name='signout'),

    # path for dealer reviews view
    path(route='dealer/<int:dealer_id>/', view=views.get_dealer_details, name='dealer_details'),
    # path for add a review view
    path(route='dealer/<int:dealer_id>/add-review/', view=views.add_review, name="add_review"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)