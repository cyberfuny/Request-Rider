"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path
from lab import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('api/history', views.history, name='history'),
    path('api/history/export', views.history_export, name='history-export'),
    path('api/history/import', views.history_import, name='history-import'),
    path('api/history/bulk', views.history_bulk, name='history-bulk'),
    path('api/history/<int:record_id>', views.history_detail, name='history-detail'),
    path('api/traffic', views.traffic, name='traffic'),
    path('api/traffic/stream', views.traffic_stream, name='traffic-stream'),
    path('api/traffic/save', views.save_traffic, name='traffic-save'),
    path('api/traffic/annotate', views.annotate_traffic, name='traffic-annotate'),
    path('api/traffic/sessions', views.traffic_sessions, name='traffic-sessions'),
    path('api/traffic/sessions/<int:session_id>', views.traffic_sessions, name='traffic-session-detail'),
    path('api/execute', views.execute, name='execute'),
    path('api/intruder', views.intruder, name='intruder'),
    path('api/intruder/saved', views.intruder_saved, name='intruder-saved'),
    path('api/intruder/saved/<int:attack_id>', views.intruder_saved, name='intruder-saved-detail'),
    path('api/intruder/saved/<int:attack_id>/run', views.intruder_saved, name='intruder-saved-run'),
    path('api/target-map', views.target_map, name='target-map'),
    path('api/osint', views.osint, name='osint'),
    path('api/scanner', views.scanner, name='scanner'),
    path('api/agent/chat', views.agent_chat, name='agent-chat'),
    path('api/route', views.route, name='route'),
    path('api/route/check', views.route_check, name='route-check'),
]
