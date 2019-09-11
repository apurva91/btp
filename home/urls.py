from django.urls import path

from . import views

app_name = 'home'
urlpatterns = [
    path('', views.index, name='index'),
    path('result/', views.post, name='result'),
    path('mesh/<int:json_no>/', views.othermeshquery, name='meshresult'),
    path('mesh/<int:json_no>/<int:abs_index>/' , views.paginate, name='paginate'),
    path('paperdetail/<int:json_no>/<int:currindex><int:offset>/' , views.paperdetail, name='paperdetail'),
    path('seesimilar/<int:json_no>/<int:currindex><int:offset>/' , views.seesimilar, name='seesimilar'),
    path('genecloud/<int:json_no>/', views.genecloud, name='genecloud'),
    path('genefile/<int:json_no>/', views.genefile, name='genefile'),
    path('meshcloud/<int:json_no>/', views.meshcloud, name='meshcloud'),
    path('entityrelation/<int:json_no>/<int:option>/', views.entityrelation, name='entityrelation'),
    path('entities/<int:json_no>/<int:eoption>/', views.entities, name='entities'),
    path('user-feedback/', views.feedback, name='feedback'),
    path('rerank/', views.rerank, name='rerank'),
    path('entity-feedback/', views.entity_feedback, name='entity-feedback'),

]