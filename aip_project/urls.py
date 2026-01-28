from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView
from ninja import NinjaAPI
from django.http import HttpResponse

from auth_app.api import auth_router
from processing_app.api import processing_router

api = NinjaAPI(
    title="AIP- API's",
    version="1.0.0",
    description="AI Processing Backend",
    openapi_url="/openapi.json"
)

api.add_router("/auth/", auth_router)
api.add_router("/processing/", processing_router)

swagger_html = """
<!DOCTYPE html>
<html>
<head>
    <title>AIP Swagger</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist/swagger-ui.css"/>
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

def swagger_view(request):
    return HttpResponse(swagger_html)

urlpatterns = [
    path("", RedirectView.as_view(url="/api/swagger/", permanent=False)),
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("api/swagger/", swagger_view),
]
