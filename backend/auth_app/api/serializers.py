#api/serializer.py
from rest_framework import serializers
from auth_app.models import UserProfile
from django.contrib.auth.models import User


class UserProfileSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['id','user', 'fullname', 'bio', 'location']

    def get_fullname(self, obj):
        first = obj.user.first_name
        last = obj.user.last_name
        name = f"{first} {last}".strip()
        return name if name else obj.user.username


class RegistrationSerializer(serializers.ModelSerializer):
    #password=serializers.CharField(write_only=True)
    repeated_password=serializers.CharField(write_only=True)
    fullname = serializers.CharField(write_only=True) # Hilfsfeld für den Namen
    #fullname = serializers.SerializerMethodField()
    #telefonnummer = serializers.CharField()

    class Meta:
        model = User
        fields=['email','fullname' ,'first_name','last_name','password' , 'repeated_password' ]
        extra_kwargs={
            'password': {'write_only':True}
        }

    def get_fullname(self, obj):
        first = obj.user.first_name
        last = obj.user.last_name
        return f"{first} {last}".strip() or obj.user.username

    def validate_email(self, value):
        """ Prüft, ob die Email schon existiert -> HTTP 400 """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('User with the same email already exists')
        return value
    
    def validate_username(self, value):
        """ Prüft, ob der Username schon existiert -> HTTP 400 """
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("The User is already exists")
        return value
    
    def validate(self, data):
        """ Prüft, ob Passwörter übereinstimmen -> HTTP 400 """
        # print("def validate: password:", data.get('password') , "   repeat_password:", data.get('repeated_password'))
        if data.get('password') != data.get('repeated_password'):
          print("def validate:  data:", data)
          #raise serializers.ValidationError({"error":"Passwords do not match."})  
          # Hier geben wir ein Dictionary zurück, damit das Frontend weiß, welches Feld falsch ist
          raise serializers.ValidationError({"password": "Passwords do not match"})
        return data

    def save(self, **kwargs):
        try:
            fullname = self.validated_data.pop('fullname', '')
            parts = fullname.split(' ', 1) # Teilt beim ersten Leerzeichen
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""
            #username = first_name
            username = first_name or self.validated_data.get('username')
            # fullname = ""
            # first_name = self.validated_data.pop('first_name', '')
            # last_name = self.validated_data.pop('last_name', '')

            #account= User(email = self.validated_data['email'], username = self.validated_data['username'])
            account= User(email = self.validated_data['email'], username = username, first_name=first_name, last_name=last_name )
            account.set_password(self.validated_data['password'])
            account.save()

            # 3. UserProfile automatisch erstellen
            UserProfile.objects.create(user=account)
            
            return account    
        except Exception as e:
            raise serializers.ValidationError({"server_error": f"Fatal error: {str(e)}"})
