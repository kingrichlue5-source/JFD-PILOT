from django.urls import path
from . import views

app_name = 'users_auth'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('users/<uuid:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('roles/', views.RoleListView.as_view(), name='role-list'),
    path('roles/<uuid:pk>/', views.RoleDetailView.as_view(), name='role-detail'),
    path('departments/', views.DepartmentListView.as_view(), name='department-list'),
    path('departments/<uuid:pk>/', views.DepartmentDetailView.as_view(), name='department-detail'),
    path('check-permission/', views.RolePermissionCheckView.as_view(), name='check-permission'),
    path('task-counts/', views.task_counts, name='task-counts'),
]
