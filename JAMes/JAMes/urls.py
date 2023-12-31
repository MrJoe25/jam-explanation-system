"""JAMes URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from usermanagement import views as user_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('featureselection/', include('feature_selection.urls')),
    path('', include('users.urls')),
    path('usermanagement/', include('usermanagement.urls')),
    path('sampling_optimization_techniques/', include('sampling_optimization_techniques.urls')),
    path('process_documentation/', include('process_documentation.urls')),
    path('group_representation/', include('group_representation.urls')),
    path('group_preprocessing/', include('group_preprocessing.urls')),
    path('data_overview/', include('data_overview.urls')),
    path('ai_selection/', include('ai_selection.urls')),
    path('ai_explainability/', include('ai_explainability.urls')),
    path('bankrupt_company_search/', include(('bankrupt_company_search.urls', 'bankrupt_company_search'), namespace='bankrupt_company_search')),
    path('personal_dashboard/', user_views.personal_dashboard,  name="personal_dashboard"),
    path('personal_upload/', user_views.personal_upload,  name="personal_upload"),
    path('login/', auth_views.LoginView.as_view(template_name="usermanagement/login.html"), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name="usermanagement/logout.html"), name='logout'),
    #path('upload/', upload_views.views, name='upload'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)