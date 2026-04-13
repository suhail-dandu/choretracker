from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
    path('accounts/', include('accounts.urls')),
    path('family/', include('family.urls')),
    path('chores/', include('chores.urls')),
    path('calendar/', include('calendar_tasks.urls')),
    path('dashboard/', include('dashboard.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "🌟 ChoreTracker Admin"
admin.site.site_title = "ChoreTracker"
admin.site.index_title = "Family Management Portal"
