from django.urls import path
from kanban_app.api.views import BoardListView, TasksView
#, BoardDetailView, EmailCheckView, TaskListView  # Importiere deine Views
from django.urls import include
from rest_framework import routers

router = routers.SimpleRouter()
router.register(r'boards', BoardListView)
router.register(r'tasks', TasksView)

urlpatterns = [
    #path('boards/', BoardListView.as_view(), name='board-list'),
    path('', include(router.urls)),
    #path('boards/<int:board_id>/', BoardDetailView.as_view(), name='board-detail'),
    #path('email-check/', EmailCheckView.as_view(), name='email-check'),
    #path('tasks/', TaskListView.as_view(), name='task-list'),
]