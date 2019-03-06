from django.urls import path

from . import views

app_name = 'home'
urlpatterns = [
    path('', views.index, name='index'),
    path('result/', views.post, name='result'),
    path('mesh/<int:json_no>/', views.get, name='meshresult'),
    path('mesh/<int:json_no>/<int:abs_index>/' , views.paginate, name='paginate'),
    path('paperdetail/<int:json_no>/<int:currindex><int:offset>/' , views.paperdetail, name='paperdetail'),
    path('genecloud/<int:json_no>/', views.genecloud, name='genecloud'),
    path('meshcloud/<int:json_no>/', views.meshcloud, name='meshcloud'),
    path('generelation/<int:json_no>/', views.generelation, name='generelation'),
    path('user-feedback/', views.feedback, name='feedback'),
]