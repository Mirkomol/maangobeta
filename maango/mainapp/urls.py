from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path("", views.index, name="index"),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path("problems", views.problems, name="problems"),
    path('problems/add/', views.add_problem, name='add_problem'),
    path('problems/add/test-cases/<int:problem_id>/', views.add_test_cases, name='add_test_cases'),
    path('problems/solve/<int:pk>/', views.solve_problem, name='solve_problem'),
    path('problems/runcode/<int:pk>/', views.runcode, name='runcode'),  # Updated to include pk for the problem
    path('problems/delete/<int:problem_id>/', views.delete_problem, name='delete_problem'),
    path("algorithms", views.algorithms, name="algorithms"),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('modules/<int:module_id>/', views.module_detail, name='module_detail'),
    path('create-course/', views.create_course, name='create_course'),
    path('create-module/', views.create_module, name='create_module'),
    path('discussion', views.discussion, name='discussion'),
    path('posts/<int:post_id>/add-comment/', views.add_comment, name='add_comment'),
    path("register", views.register, name="register"),
    path("login", views.login, name="login"),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('stats/<str:username>/', views.user_stats, name='user_stats'),
]

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
#
