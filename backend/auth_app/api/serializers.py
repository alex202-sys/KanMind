from django.contrib.auth.models import User
from rest_framework import serializers
from auth_app.models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_

    Returns:
        _type_: _description_
    """

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
    """_summary_

    Args:
        serializers (_type_): _description_

    Raises:
        serializers.ValidationError: _description_
        serializers.ValidationError: _description_
        serializers.ValidationError: _description_
        serializers.ValidationError: _description_

    Returns:
        _type_: _description_
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
        print("validate_email  value", value)
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with the same email already exists")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("The User is already exists")
        return value

    def validate(self, data):
        print(
            "def validate: password:",
            data.get("password"),
            "   repeat_password:",
            data.get("repeated_password"),
        )
        if data.get("password") != data.get("repeated_password"):
            print("passwor is no valid.  data:", data)
            raise serializers.ValidationError({"password": "Passwords do not match"})
        return data

    def save(self, **kwargs):
        try:
            fullname = self.validated_data.pop("fullname", "")
            # Splits at the first space. If there's no space, the entire fullname is treated as the first name.
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
