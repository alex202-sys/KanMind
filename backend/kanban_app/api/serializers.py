from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError
from django.contrib.auth import get_user_model
from django.http import Http404
from kanban_app.models import Board, Task, TaskStatus, TaskPriority, Comment

User = get_user_model()


class BoardsSerializer(serializers.ModelSerializer):
    """Serializer for Board model."""

    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()
    owner_id = serializers.SerializerMethodField()
    members = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        source="member",
        write_only=True,
        error_messages={
            "does_not_exist": "400: Invalid request data. Some user email addresses may be invalid."
        },
    )

    class Meta:
        model = Board
        fields = [
            "id",
            "title",
            "members",
            "member_count",
            "ticket_count",
            "tasks_to_do_count",
            "tasks_high_prio_count",
            "owner_id",
        ]
        # As a result, DRF reads the field during a POST request
        # but does not output it by default during a GET request.

    def to_internal_value(self, data):
        """Optimize Duplicate Members"""
        if "members" in data and isinstance(data["members"], list):
            data = data.copy()
            data["members"] = list(set(data["members"]))

        return super().to_internal_value(data)

    def get_member_count(self, obj):
        return obj.member.count()

    def get_ticket_count(self, obj):
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
        """
        Dynamically create responders based on the GET,
        RETRIEVE, and PATCH methods.
        """
        ret = super().to_representation(instance)
        request = self.context.get("request")
        view = self.context.get("view")

        # for non-superusers, show members details and owner details only in detail view
        if request and view and request.method == "GET" and view.action == "retrieve":
            # ret["owner_id"] = instance.owner.id
            members_liste = [
                {
                    "id": m.id,
                    "email": getattr(m, "email", ""),
                    "fullname": m.get_full_name() or m.username,
                }
                for m in instance.member.all()
            ]

            tasks_liste = [
                {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "status": t.status,
                    "priority": t.priority,
                    "assignee": (
                        {
                            "id": t.assignee.id,
                            "email": getattr(t.assignee, "email", ""),
                            "fullname": t.assignee.get_full_name()
                            or t.assignee.username,
                        }
                        if t.assignee
                        else None
                    ),
                    "reviewer": (
                        {
                            "id": t.reviewer.id,
                            "email": getattr(t.reviewer, "email", ""),
                            "fullname": t.reviewer.get_full_name()
                            or t.reviewer.username,
                        }
                        if t.reviewer
                        else None
                    ),
                    "due_date": str(t.due_date) if t.due_date else None,
                    "comments_count": (
                        t.comments.count()
                        if hasattr(t, "comments")
                        else t.comment_set.count()
                    ),
                }
                for t in instance.tasks.all()
            ]

            ret = {
                "id": ret.get("id"),
                "title": ret.get("title"),
                "owner_id": instance.owner.id if instance.owner else None,
                "members": members_liste,
                "tasks": tasks_liste,
            }

        # for non-superusers, show members details and owner details only
        # in PATCH partial_update view
        if (
            request
            and view
            and request.method == "PATCH"
            and view.action == "partial_update"
        ):
            if instance.owner:
                ret["owner_data"] = {
                    "id": instance.owner.id,
                    "email": instance.owner.email,
                    "fullname": instance.owner.get_full_name()
                    or instance.owner.username,
                }

            ret["members_data"] = [
                {
                    "id": m.id,
                    "email": getattr(m, "email", ""),
                    "fullname": m.get_full_name() or m.username,
                }
                for m in instance.member.all()
            ]
            ret.pop("members", None)
            ret.pop("member_count", None)
            ret.pop("ticket_count", None)
            ret.pop("tasks_to_do_count", None)
            ret.pop("tasks_high_prio_count", None)
            ret.pop("owner_id", None)

        return ret


class UserNestedSerializer(serializers.ModelSerializer):
    """_fullname_ is a read-only field that concatenates
    the first and last name of the user."""

    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "fullname"]

    def get_fullname(self, obj):
        full_name = f"{obj.first_name} {obj.last_name}".strip()
        return full_name if full_name else obj.username


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for Task model, with custom validation and representation logic.
    It includes fields for assignee and reviewer, which are represented as nested
    serializers for read operations and as primary key related fields for write operations.
    The serializer also includes custom validation to ensure that the assignee and
    reviewer are members of the board associated with the task, and that only superusers
    can set the creator field. The to_representation method is overridden to conditionally
    include or exclude certain fields based on the user's permissions and the request method.
    """

    comments_count = serializers.SerializerMethodField()
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="assignee",
        write_only=True,
        required=False,
        allow_null=True,
        error_messages={
            "does_not_exist": "400: Invalid request data. Required fields may be missing or contain invalid values."
        },
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="reviewer",
        write_only=True,
        required=False,
        allow_null=True,
        error_messages={
            "does_not_exist": "400: Invalid request data. Required fields may be missing or contain invalid values."
        },
    )
    assignee = UserNestedSerializer(read_only=True, allow_null=True)
    reviewer = UserNestedSerializer(read_only=True, allow_null=True)
    creator = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False
    )

    board = serializers.PrimaryKeyRelatedField(
        queryset=Board.objects.all(),
        error_messages={
            "does_not_exist": "404: Board not found. The specified Board ID does not exist."
        },
    )

    class Meta:
        model = Task
        fields = [
            "id",
            "board",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "assignee_id",
            "reviewer",
            "reviewer_id",
            "due_date",
            "comments_count",
            "creator",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["creator", "created_at", "updated_at"]

    def update(self, instance, validated_data):
        """Custom update method to handle the logic for updating a Task instance.
        It checks for the presence of 'assignee' and 'reviewer' in the validated
        data and updates them accordingly. It also checks if the 'creator' field
        is being updated and if the user making the request is a superuser before
        allowing the update. Finally, it updates any other fields that are present
        in the validated data and saves the instance.
        """
        if "assignee" in validated_data:
            instance.assignee = validated_data.get("assignee")

        if "reviewer" in validated_data:
            instance.reviewer = validated_data.get("reviewer")

        for attr, value in validated_data.items():
            if attr not in ["assignee", "reviewer"]:
                setattr(instance, attr, value)

        instance.save()
        return instance

    def to_internal_value(self, data):
        """Override to_internal_value to catch the case where the
        provided board ID does not exist, and raise a NotFound
        exception with a custom message instead of the default
        ValidationError.
        """
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError as exc:
            if "board" in exc.detail:
                raise NotFound(
                    "404: Board not found. The specified Board ID does not exist."
                )
            raise exc

    def get_reviewer_id(self, obj):
        if obj.reviewer:
            return obj.reviewer.id
        return None

    def get_assignee_id(self, obj):
        if obj.assignee:
            return obj.assignee.id
        return None

    def get_comments_count(self, obj):
        if hasattr(obj, "comments"):
            return obj.comments.count()
        return obj.comment_set.count()

    def validate(self, attrs):
        """Custom validation to ensure that the user making the request
        is a member of the board associated with the task, and that the
        assignee and reviewer (if provided) are also members of the board.
        """
        request = self.context.get("request")
        if not request or not request.user:
            raise serializers.ValidationError({"detail": "User not logged in."})

        if self.instance and "board" in attrs:
            if attrs["board"] != self.instance.board:
                raise PermissionDenied(
                    "403: Forbidden. Changing the existing Board ID is not allowed!"
                )

        board = attrs.get("board")
        if not board and self.instance:
            board = self.instance.board

        if not board:
            raise Http404(
                "404: Board not found. The specified Board ID does not exist."
            )

        current_user = request.user
        allowed_users = set(board.member.all())
        if current_user not in allowed_users and not current_user.is_superuser:
            action_text = "bearbeiten" if self.instance else "erstellen"
            if action_text == "bearbeiten":
                raise PermissionDenied(
                    "403: Forbidden. The user must be a member of the board to which the task belongs."
                )
            else:
                raise PermissionDenied(
                    "403: Forbidden. The user must be a member of the board to create a task."
                )

        new_assignee = attrs.get("assignee")
        if new_assignee and new_assignee not in allowed_users:
            raise serializers.ValidationError(
                {
                    "assignee_id": "400: Invalid request data. Required fields may be missing or contain invalid values."
                }
            )

        new_reviewer = attrs.get("reviewer")
        if new_reviewer and new_reviewer not in allowed_users:
            raise serializers.ValidationError(
                {
                    "reviewer_id": "400: Invalid request data. Required fields may be missing or contain invalid values."
                }
            )

        if "creator" in attrs:
            new_creator = attrs.get("creator")

            if request and request.user and not request.user.is_superuser:
                raise PermissionDenied(
                    "403: Forbidden. Only admins may change the creator."
                )

            if board:
                allowed_users = set(board.member.all())
                if board.owner:
                    allowed_users.add(board.owner)

                if new_creator not in allowed_users:
                    raise ValidationError(
                        {
                            "creator": "400: Invalid request data. The new creator must be a member or owner of the board."
                        }
                    )

        return attrs

    def to_representation(self, instance):
        """Override to_representation to conditionally include or exclude
        certain fields based on the user's permissions and the request method.
        For non-superusers, if the request method is PATCH, the 'board' and
        'comments_count' fields are removed from the response. Additionally,
        for non-superusers, the 'creator', 'created_at', and 'updated_at'
        fields are always removed from the response regardless of the request method.
        This allows for a more tailored response based on the user's permissions
        and the context of the request."""

        ret = super().to_representation(instance)
        request = self.context.get("request")

        if request and request.user:
            if not request.user.is_superuser and request.method == "PATCH":
                ret.pop("board", None)
                ret.pop("comments_count", None)

            if not request.user.is_superuser:
                ret.pop("creator", None)
                ret.pop("created_at", None)
                ret.pop("updated_at", None)

        return ret


class TaskCommentSerializer(serializers.ModelSerializer):
    """Serializer for Comment model, with a custom method field
    to represent the author's full name."""

    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ["id", "created_at", "author", "content"]

    def get_author(self, obj):
        if obj.author:
            return obj.author.get_full_name() or obj.author.username
        return "Unbekannter Autor"
