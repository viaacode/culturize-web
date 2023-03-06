from django.urls import path
from api import views

urlpatterns = [
    path('api/info', views.ServiceInfo.as_view()),
    path('api/record', views.RecordList.as_view()),
    path('api/record/<int:rid>', views.RecordDetail.as_view()),
    path('api/logs', views.LogList.as_view()),
    path('api/logexport', views.LogCSVExportView.as_view()),
    path('api/logs/<int:rid>', views.RecordLogDetail.as_view()),
    path('api/login', views.Login.as_view()),
    path('<path:persistent_path>', views.redirect_view),
]
