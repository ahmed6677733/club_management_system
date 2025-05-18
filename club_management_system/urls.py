from django.shortcuts import redirect
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import messages

from club.models import Club


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('base_app.urls')),
    path('accounts/', include('accounts.urls')),
    path('club/', include('club.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('payment/', include('payment.urls')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)