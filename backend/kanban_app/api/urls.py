from django.urls import path
from kanban_app.api.views import BoardListView, TasksView, EmailCheckView
from django.urls import include
from rest_framework import routers

router = routers.SimpleRouter()
router.register(r'boards', BoardListView)
router.register(r'tasks', TasksView, basename='tasks')
router.register(r'email-check', EmailCheckView, basename='email-check')

urlpatterns = [path('', include(router.urls))]