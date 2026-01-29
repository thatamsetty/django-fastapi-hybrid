from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView
from django.http import HttpResponse
from ninja import NinjaAPI

from auth_app.api import auth_router
from processing_app.api import processing_router


# ======================================================
# NINJA API CONFIG
# ======================================================
api = NinjaAPI(
    title="AIP APIs",
    version="1.0.0",
    description="AI Processing Backend",
)


# ======================================================
# ROUTERS
# ======================================================
api.add_router("/auth/", auth_router)
api.add_router("/processing/", processing_router)


# ======================================================
# SIMPLE SWAGGER PAGE (OPTIONAL)
# ======================================================
def swagger_view(request):
    return HttpResponse(
        """
        <!DOCTYPE html>
        <html>
        <head>
            <title>AIP Swagger</title>
            <link rel="stylesheet"
             href="https://unpkg.com/swagger-ui-dist/swagger-ui.css"/>
        </head>
        <body>
            <div id="swagger-ui"></div>
            <script src="https://unpkg.com/swagger-ui-dist/swagger-ui-bundle.js"></script>
            <script>
            SwaggerUIBundle({
                url: '/api/openapi.json',
                dom_id: '#swagger-ui'
            });
            </script>
        </body>
        </html>
        """
    )


# ======================================================
# URL PATTERNS
# ======================================================
urlpatterns = [
    path("", RedirectView.as_view(url="/api/swagger/", permanent=False)),
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("api/swagger/", swagger_view),
]
