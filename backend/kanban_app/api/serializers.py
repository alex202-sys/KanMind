from rest_framework import serializers
from django.contrib.auth import get_user_model
from kanban_app.models import Board, Task,  TaskStatus, TaskPriority, Comment


User = get_user_model()

class BoardsSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()
    tasks_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()
    #owner_id = serializers.IntegerField(source='owner.id', read_only=True, default=0)
    # owner_id = serializers.IntegerField(read_only=True, allow_null=True, default=0) #gem
    owner_id = serializers.SerializerMethodField()
    class Meta:
        model = Board
        
        if not User.is_superuser: 
            fields = [
                'id', 
                'title', 
                'member_count', 
                'tasks_count', 
                'tasks_to_do_count', 
                'tasks_high_prio_count', 
                'owner_id'
            ]
        else:
            #fields = '__all__'
            fields = [
                'id', 
                'title', 
                'tasks',
                'tasks_count', 
                'tasks_to_do_count', 
                'tasks_high_prio_count', 
                'owner_id',
                'owner',
                'member_count', 
                'member'
            ]

    # 1. Zählt die Mitglieder des Boards
    def get_member_count(self, obj):
        return obj.member.count()

    # 2. Zählt alle Tasks dieses Boards über deinen related_name 'tasks'
    def get_tasks_count(self, obj):
        return obj.tasks.count()

    # 3. Zählt alle Tasks im Status 'to-do'
    def get_tasks_to_do_count(self, obj):
        # Nutzt den echten Value aus deinen Choices ('to-do')
        return obj.tasks.filter(status=TaskStatus.TODO).count()

    # 4. Zählt alle Tasks mit der Priorität 'high'
    def get_tasks_high_prio_count(self, obj):
        # Nutzt den echten Value aus deinen Choices ('high')
        return obj.tasks.filter(priority=TaskPriority.HIGH).count()

    def get_owner_id(self, obj):
        # Wenn ein owner existiert, gib seine ID zurück, andernfalls die 0
        if obj.owner:
            return obj.owner.id
        return None 


class TaskSerializer(serializers.ModelSerializer):
    # oder fields = '__all__' oder hier andere definieren 
    #status = serializers.ChoiceField(choices=TaskStatus.choices,  default=TaskStatus.IN_PROGRESS)
    #priority = serializers.ChoiceField(choices=TaskPriority.choices,  default=TaskPriority.MEDIUM)
    comments_count = serializers.SerializerMethodField()
    assignee_id=serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='assignee',
        write_only=True,
        required=False,
        allow_null=True 
    )
    
    assignee = serializers.IntegerField(source='assignee.id', read_only=True, allow_null=True)
    class Meta:
        model = Task
        #fields = '__all__'
        #fields = ['id', 'title', 'status', 'priority']
        if not User.is_superuser: 
            fields = [
                'id',
                'board', 
                'title', 
                'description',
                'status', 
                'priority', 
                'assignee', 
                'assignee_id', 
                'reviewer',
                'due_date',
                'comments_count'
            ]
        else:
            fields = [
                'id',
                'board', 
                'title', 
                'description',
                'status', 
                'priority', 
                'assignee', 
                'assignee_id', 
                'reviewer',
                'due_date',
                'comments_count'
            ]

    def get_assignee_id(self, obj):
        # Wenn ein owner existiert, gib seine ID zurück, andernfalls die 0
        if obj.assignee:
            return obj.assignee.id
        return None 
    
    def get_reviewer_id(self, obj):
        # Wenn ein owner existiert, gib seine ID zurück, andernfalls die 0
        if obj.reviewer:
            return obj.reviewer.id
        return None 
    
    def get_comments_count(self,obj):
        return obj.comments.count()
        
class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'