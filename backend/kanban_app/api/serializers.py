from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError
from django.contrib.auth import get_user_model
from django.http import Http404
from kanban_app.models import Board, Task,  TaskStatus, TaskPriority, Comment

User = get_user_model()
class BoardsSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()
    tasks_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()
    owner_id = serializers.SerializerMethodField()
    class Meta:
        model = Board
        fields = [
            'id', 
            'title', 
            'member_count', 
            'tasks_count', 
            'tasks_to_do_count', 
            'tasks_high_prio_count', 
            'owner_id'
        ]

    def get_member_count(self, obj):
        return obj.member.count()

    def get_tasks_count(self, obj):
        return obj.tasks.count()

    def get_tasks_to_do_count(self, obj):
        return obj.tasks.filter(status=TaskStatus.TODO).count()

    def get_tasks_high_prio_count(self, obj):
        return obj.tasks.filter(priority=TaskPriority.HIGH).count()

    def get_owner_id(self, obj):
        if obj.owner:
            return obj.owner.id
        return None 
    
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        request = self.context.get('request')
        view = self.context.get('view')


        if not instance.owner:
            ret['owner_id'] = None 
        else:
            ret['owner_id'] = instance.owner.id

        if request and request.user and request.user.is_superuser:
            ret['member'] = [
                {
                    'id': m.id, 
                    'username': m.username, 
                    'fullname': m.get_full_name() or m.username
                } 
                for m in instance.member.all()
            ]

            if instance.owner:
                ret['owner_id'] = {
                        'id': instance.owner.id, 
                        'username': instance.owner.username,
                        'fullname': instance.owner.get_full_name() or instance.owner.username
                    } 
            
        if request and view and request.method == 'GET' and view.action == 'retrieve':
            ret['members'] = [
                {
                    'id': m.id,
                    'email': getattr(m, 'email', ''),
                    'fullname': m.get_full_name() or m.username
                }
                for m in instance.member.all()
            ]
            ret.pop('member', None) 
            ret.pop('member_count', None)
            ret.pop('tasks_count', None)
            ret.pop('tasks_to_do_count', None)
            ret.pop('tasks_high_prio_count', None)

            ret['tasks'] = [
                {
                    'id': t.id,
                    'title': t.title,
                    'description': t.description,
                    'status': t.status,
                    'priority': t.priority,
                    'assignee': {
                        'id': t.assignee.id,
                        'email': getattr(t.assignee, 'email', ''),
                        'fullname': t.assignee.get_full_name() or t.assignee.username
                    } if t.assignee else None,
                    'reviewer': {
                        'id': t.reviewer.id,
                        'email': getattr(t.reviewer, 'email', ''),
                        'fullname': t.reviewer.get_full_name() or t.reviewer.username
                    } if t.reviewer else None,
                    'due_date': str(t.due_date) if t.due_date else None,
                    'comments_count': t.comments.count() if hasattr(t, 'comments') else t.comment_set.count()
                }
                for t in instance.tasks.all() 
            ]    

        if request and view and request.method == 'PATCH' and view.action == 'partial_update':
            if instance.owner:
                ret['owner_data'] = {
                        'id': instance.owner.id, 
                        'email': instance.owner.email,
                        'fullname': instance.owner.get_full_name() or instance.owner.username
                    } 
            
            ret['members_data'] = [
                {
                    'id': m.id,
                    'email': getattr(m, 'email', ''),
                    'fullname': m.get_full_name() or m.username
                }
                for m in instance.member.all()
            ]
            ret.pop('member', None) 
            ret.pop('member_count', None)
            ret.pop('tasks_count', None)
            ret.pop('tasks_to_do_count', None)
            ret.pop('tasks_high_prio_count', None)
            ret.pop('owner_id', None)

        return ret

class UserNestedSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']

    def get_fullname(self, obj):
        full_name = f"{obj.first_name} {obj.last_name}".strip()
        return full_name if full_name else obj.username

class TaskSerializer(serializers.ModelSerializer):
    comments_count = serializers.SerializerMethodField()
    assignee_id=serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source='assignee', write_only=True, required=False, allow_null=True, error_messages={
            'does_not_exist': '400: Ungültige Anfragedaten. Möglicherweise fehlen erforderliche Felder oder enthalten ungültige Werte.'
        })
    reviewer_id=serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source='reviewer', write_only=True, required=False, allow_null=True, error_messages={
            'does_not_exist': '400: Ungültige Anfragedaten. Möglicherweise fehlen erforderliche Felder oder enthalten ungültige Werte.'
        })
    assignee = UserNestedSerializer(read_only=True, allow_null=True)
    reviewer = UserNestedSerializer(read_only=True, allow_null=True)
    creator = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)

    board = serializers.PrimaryKeyRelatedField(queryset=Board.objects.all(), error_messages={
            'does_not_exist': '404: Board nicht gefunden. Die angegebene Board-ID existiert nicht.'
        })
    
    class Meta:
        model = Task
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
            'reviewer_id',
            'due_date',
            'comments_count',
            'creator',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['creator', 'created_at', 'updated_at']

    def update(self, instance, validated_data):
        if 'assignee' in validated_data:
            instance.assignee = validated_data.get('assignee')
            
        if 'reviewer' in validated_data:
            instance.reviewer = validated_data.get('reviewer')
            
        print("Creator in validated_data:", validated_data.get('creator'))
        request=self.context.get('request')
        if 'creator' in validated_data:
            if request.user and request.user.is_superuser:
                instance.creator = validated_data.get('creator')


        # Alle anderen Standardfelder (title, description, status, etc.) aktualisieren
        for attr, value in validated_data.items():
            if attr not in ['assignee', 'reviewer']:
                setattr(instance, attr, value)

        # Änderungen in der Datenbank speichern
        instance.save()
        return instance


    def to_internal_value(self, data):
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError as exc:
            if 'board' in exc.detail:
                raise NotFound("404: Board nicht gefunden. Die angegebene Board-ID existiert nicht.")
            raise exc

    def get_reviewer_id(self, obj):
        if obj.reviewer:
            return obj.reviewer.id
        return None 
    
    def get_assignee_id(self, obj):
        if obj.assignee:
            return obj.assignee.id
        return None 

    def get_comments_count(self,obj):
        if hasattr(obj, 'comments'):
            return obj.comments.count()
        return obj.comment_set.count()
        
    def validate(self, attrs):
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError({"detail": "Benutzer nicht eingeloggt."})
        current_user = request.user

        if self.instance and 'board' in attrs:
            if attrs['board'] != self.instance.board:
                raise PermissionDenied(
                   "403: Verboten. Das Ändern der bestehenden Board-ID ist nicht erlaubt!" 
                )

        board = attrs.get('board')
        if not board and self.instance:
            board = self.instance.board

        if not board:
           raise Http404("404: Board nicht gefunden. Die angegebene Board-ID existiert nicht.")

        allowed_users = set(board.member.all())
        if current_user not in allowed_users and not current_user.is_superuser:
            action_text = "bearbeiten" if self.instance else "erstellen"
            if action_text == "bearbeiten":
                raise PermissionDenied(
                    "403: Verboten. Der Benutzer muss Mitglied des Boards sein, zu dem die Task gehört."
                ) 
            else:    
                raise PermissionDenied(
                    "403: Verboten. Der Benutzer muss Mitglied des Boards sein, um eine Task zu erstellen"
                )    

        new_assignee = attrs.get('assignee')
        if new_assignee and new_assignee not in allowed_users:
            raise serializers.ValidationError(
                {"assignee_id": "400: Ungültige Anfragedaten. Möglicherweise fehlen erforderliche Felder oder enthalten ungültige Werte."}
            )   
        
        new_reviewer = attrs.get('reviewer')
        if new_reviewer and new_reviewer not in allowed_users:
            raise serializers.ValidationError(
                {"reviewer_id": "400: Ungültige Anfragedaten. Möglicherweise fehlen erforderliche Felder oder enthalten ungültige Werte."}
            )  
        

        if 'creator' in attrs:
            new_creator = attrs.get('creator')

            if request and request.user and not request.user.is_superuser:
                raise PermissionDenied("403: Verboten. Nur Admins dürfen den Creator ändern.")

            if board:
                allowed_users = set(board.member.all())
                if board.owner:
                    allowed_users.add(board.owner)

                if new_creator not in allowed_users:
                    raise ValidationError(
                        {"creator": "400: Ungültige Anfragedaten. Der neue Creator muss ein Mitglied oder Besitzerdieses Boards sein."}
                    )

        return attrs  
    
    def to_representation(self, instance):
        print("Task instance",instance)
        ret = super().to_representation(instance)
        request = self.context.get('request')
        if request and request.user: 
            if not request.user.is_superuser and request.method=='PATCH':
                    ret.pop('board', None)
                    ret.pop('comments_count', None)

            if not request.user.is_superuser:
                    ret.pop('creator', None)
                    ret.pop('created_at', None)
                    ret.pop('updated_at', None)         
        
        return ret

class TaskCommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    class Meta:
        model = Comment
        fields = ['id', 'created_at', 'author', 'content']

    def get_author(self, obj):
        if obj.author:
            return obj.author.get_full_name() or obj.author.username
        return "Unbekannter Autor"

