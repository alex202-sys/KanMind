from django.contrib.auth.models import User
from rest_framework import serializers
from auth_app.models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for the UserProfile model. It includes a method field
    `fullname` that combines the first and last name of the associated User model.
    The serializer allows for serialization and deserialization of UserProfile
    instances, including the related User information. The `fullname` field is
    read-only and is generated based on the first and last name of the user."""

    fullname = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ["id", "user", "fullname", "bio", "location"]

    def get_fullname(self, obj):
        first = obj.user.first_name
        last = obj.user.last_name
        name = f"{first} {last}".strip()
        return name if name else obj.user.username


class RegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration. It includes fields for email, fullname, and password confirmation.
    The serializer validates that the email is unique and that the password and repeated password match.
    """

    repeated_password = serializers.CharField(write_only=True)
    fullname = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "email",
            "fullname",
            "first_name",
            "last_name",
            "password",
            "repeated_password",
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def get_fullname(self, obj):
        first = obj.user.first_name
        last = obj.user.last_name
        return f"{first} {last}".strip() or obj.user.username

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with the same email already exists")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("The User is already exists")
        return value

    def validate(self, data):

        if data.get("password") != data.get("repeated_password"):
            raise serializers.ValidationError({"password": "Passwords do not match"})
        return data

    def save(self, **kwargs):
        try:
            fullname = self.validated_data.pop("fullname", "")
            parts = fullname.split(" ", 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""
            username = first_name or self.validated_data.get("username")

            account = User(
                email=self.validated_data["email"],
                username=username,
                first_name=first_name,
                last_name=last_name,
            )
            account.set_password(self.validated_data["password"])
            account.save()

            UserProfile.objects.create(user=account)
            return account
        except Exception as e:
            raise serializers.ValidationError(
                {"server_error": f"Fatal error: {str(e)}"}
            )
