from rest_framework import serializers
from django.contrib.auth import get_user_model
from kanban_app.models import Board, Task,  TaskStatus, TaskPriority, Comment
from django.http import Http404
from rest_framework.exceptions import PermissionDenied, NotFound

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
        fields = [
            'id', 
            'title', 
            'member_count', 
            'tasks_count', 
            'tasks_to_do_count', 
            'tasks_high_prio_count', 
            'owner_id'
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
    
    def to_representation(self, instance):
    # Basis-Daten generieren
        print("instance",instance)
        ret = super().to_representation(instance)
    
        # Zugriff auf den aktuellen User aus dem Request
        request = self.context.get('request')
        if request and request.user and request.user.is_superuser:
            # Wenn Superuser: Ersetze die ID-Liste mit detaillierten Objekten
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
        else:
                print("owner_id = None ")
                ret['owner_id'] = None  
        return ret

class UserNestedSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']

    def get_fullname(self, obj):
        # Kombiniert Vor- und Nachname. Falls leer, wird der Username genutzt.
        full_name = f"{obj.first_name} {obj.last_name}".strip()
        return full_name if full_name else obj.username

class TaskSerializer(serializers.ModelSerializer):
    # oder fields = '__all__' oder hier andere definieren 
    #status = serializers.ChoiceField(choices=TaskStatus.choices,  default=TaskStatus.IN_PROGRESS)
    #priority = serializers.ChoiceField(choices=TaskPriority.choices,  default=TaskPriority.MEDIUM)
    comments_count = serializers.SerializerMethodField()
    assignee_id=serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source='assignee', write_only=True, required=False, allow_null=True)
    reviewer_id=serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source='reviewer', write_only=True, required=False, allow_null=True)
    assignee = UserNestedSerializer(read_only=True, allow_null=True)
    reviewer = UserNestedSerializer(read_only=True, allow_null=True)
    creator = UserNestedSerializer(read_only=True, allow_null=True)
    board = serializers.PrimaryKeyRelatedField(queryset=Board.objects.all())
    # Hier überschreiben wir das Feld, um die Fehlermeldungen anzupassen:
    # board = serializers.PrimaryKeyRelatedField(
    #     queryset=Board.objects.all(),
    #     error_messages={
    #         'does_not_exist': '404: Board nicht gefunden. Die angegebene Board-ID existiert nicht.',
    #         'incorrect_type': 'Die Board-ID muss eine gültige Zahl sein.',
    #         'null': 'Ein Task muss einem Board zugewiesen sein.'
    #     }
    # )
    
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

    def to_internal_value(self, data):
        try:
            # Versucht die Standard-Validierung (prüft ob Board-ID existiert)
            return super().to_internal_value(data)
        except serializers.ValidationError as exc:
            # Wenn der Fehler vom 'board'-Feld kommt, werfe HTTP 404
            if 'board' in exc.detail:
                raise NotFound("404: Board nicht gefunden. Die angegebene Board-ID existiert nicht.")
            raise exc


    def get_reviewer_id(self, obj):
        # Wenn ein owner existiert, gib seine ID zurück, andernfalls die 0
        if obj.reviewer:
            return obj.reviewer.id
        return None 
    
    def get_assignee_id(self, obj):
        # Wenn ein owner existiert, gib seine ID zurück, andernfalls die 0
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
        print("def validate board: ",board)
        print("def self.instance: ",self.instance)
        if not board and self.instance:
            board = self.instance.board

        if not board:
            # raise serializers.ValidationError({"board": "404: Board nicht gefunden. Die angegebene Board-ID existiert nicht."})
           raise Http404("404: Board nicht gefunden. Die angegebene Board-ID existiert nicht.")

        allowed_users = set(board.member.all())
        # Permissions required: Der Benutzer muss Mitglied des Boards sein, um eine Task zu erstellen.
        # if board.owner:
        #     allowed_users.add(board.owner)
        #print("current_user: ",current_user, " allowed_users: ",allowed_users)
        if current_user not in allowed_users and not current_user.is_superuser:
            # raise serializers.ValidationError({
            #     "detail": "403: Verboten. Der Benutzer muss Mitglied des Boards sein, um eine Task zu erstellen"
            # })
            # Dynamischer Text je nachdem, ob es ein PATCH (Update) oder POST (Erstellung) ist
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
                {"assignee_id": "Der zugewiesene Benutzer (Assignee) muss ein Mitglied dieses Boards sein."}
            )   
        
        new_reviewer = attrs.get('reviewer')
        if new_reviewer and new_reviewer not in allowed_users:
            raise serializers.ValidationError(
                {"reviewer_id": "Der zugewiesene Benutzer (reviewer) muss ein Mitglied dieses Boards sein."}
            )  
        
        return attrs  
    
    def to_representation(self, instance):
    # Basis-Daten generieren
        print("Task instance",instance)
        ret = super().to_representation(instance)
        request = self.context.get('request')
        if request and request.user: 
            if not request.user.is_superuser and request.method=='PATCH':
                    # Wenn Superuser: Ersetze die ID-Liste mit detaillierten Objekten
                    ret.pop('board', None)
                    ret.pop('comments_count', None)

            if not request.user.is_superuser:
                    ret.pop('creator', None)
                    ret.pop('created_at', None)
                    ret.pop('updated_at', None)         
        
        return ret





class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'