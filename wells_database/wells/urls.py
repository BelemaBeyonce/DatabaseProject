from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_las_file, name='upload_las_file'),
    path('upload-success/', views.upload_success, name='upload_success'),
    path('uploaded/', views.uploaded_files_table, name='uploaded_files_table'),
    path('delete/<int:file_id>/', views.delete_file, name='delete_file'),
]
