from django.urls import path
from api import views

urlpatterns = [
    path('api/record', views.RecordList.as_view()),
    path('api/record/<int:pk>', views.RecordDetail.as_view()),
    path('api/logs', views.LogList.as_view()),
    path('api/logs/<int:pk>', views.RecordLogDetail.as_view()),
    path('api/login', views.Login.as_view()),
    path('<str:persistent_path>', views.redirect_view),
]
