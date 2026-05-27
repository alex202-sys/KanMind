from django.urls import path
from django.urls import include
from rest_framework import routers
from kanban_app.api.views import BoardListView, TasksView, EmailCheckView

router = routers.SimpleRouter()
router.register(r'boards', BoardListView)
router.register(r'tasks', TasksView, basename='tasks')
router.register(r'email-check', EmailCheckView, basename='email-check')

urlpatterns = [path('', include(router.urls))]