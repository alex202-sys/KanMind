from rest_framework import serializers
from kanban_app.models import Board, Task,  TaskStatus, TaskPriority

class BoardsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = '__all__'

class TaskSerializer(serializers.ModelSerializer):
    # oder fields = '__all__' oder hier andere definieren 
    #status = serializers.ChoiceField(choices=TaskStatus.choices,  default=TaskStatus.IN_PROGRESS)
    #priority = serializers.ChoiceField(choices=TaskPriority.choices,  default=TaskPriority.MEDIUM)
    class Meta:
        model = Task
        fields = '__all__'
        #fields = ['id', 'title', 'status', 'priority']