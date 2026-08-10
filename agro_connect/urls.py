from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("products.urls")),
    path("accounts/", include("accounts.urls")),
    path("farmers/", include("farmers.urls")),
    path("farmer/", include("farmers.farmer_urls")),
    path("admin-panel/", include("admin_panel.urls")),
    path("cart/", include("cart.urls")),
    path("", include("orders.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
