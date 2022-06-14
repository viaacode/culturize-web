from django.urls import path
from api import views

urlpatterns = [
    path('api/record', views.RecordList.as_view()),
    path('api/logs', views.LogList.as_view()),
    #path('api/record/<str:uid>', views.ItemDetail.as_view()),
    path('<str:persistent_path>', views.redirect_view),
]
