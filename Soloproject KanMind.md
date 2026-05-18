# **Soloprojekt** KanMind

### Ziele

- Datenmodell mit Django abbilden

- Eigene RESTful API schreiben

- Anwendung von Django REST Framework

  ​	

#### Resourse

Git: https://github.com/alex202-sys/KanMind.git

Frondend Repo: https://github.com/Developer-Akademie-Backendkurs/project.KanMind.git

Checkliste Django/DRF-Projekte:  https://docs.google.com/document/d/1-gUz-skb24UTLAiY5Y-wYDB6GEYI4H9vnxATo-2QsOM/edit?tab=t.0#heading=h.oeodsmlvkdaa

kanmind API Endpoint Dokumentation:  https://cdn.developerakademie.com/courses/Backend/EndpointDoku/index.html?name=kanmind

HTTP_Status Codes  https://www.django-rest-framework.org/api-guide/status-codes/

https://hackmd.io/@mtUtNKDMTzWHLKW5U9RnOw/By0cNiZbWe  .env für den Django SECRET_KEY anlegen

https://www.drawio.com/  Diagrammen



```
	mkdir Market_AU_PM  #C:\Users\aleks\Desktop\DJANGO_PROJECT\KanMind\backend
	cd backend
	python -m venv .venv  # ".venv" kann auch "venv" oder "env" heißen
	.venv/Scripts/activate  # Windows
	python -m pip install Django
	pip install djangorestframework 
	python -m pip install django-cors-headers
    pip freeze  # Überprüfen, ob alles installiert wurde
    pip freeze > requirements.txt  # Abhängigkeiten speichern
	django-admin startproject core .
#.gitignore hinzufügen und Projekt pushen
#.gitignore aus anderen Projekten übernehmen (z. B. von GitHub oder #gitignore.io). https://github.com/github/gitignore/blob/main/Python.gitignore
#Erst nach dem Hinzufügen zur .gitignore das Projekt auf Git pushen!
	python manage.py startapp auth_app
	python manage.py startapp kanban_app
```





- Alle Apps erhalten ein sprechendes Präfix oder Suffix, z. B. **auth_app**,  **kanban_app**
- Jede App enthält zusätzlich einen api/-Ordner indem sich die **serializers.py, views.py, urls.py, permissions.py** usw. befinden.

- Die Admin Umgebung soll nutzbar sein.

```
_APPS = [    ...         
	'rest_framework',
    'kanban_app',
    'corsheaders',
    'user_auth_app',
]
MIDDLEWARE = [
  'corsheaders.middleware.CorsMiddleware', ...]
  
CORS_ALLOWED_ORIGINS = ["http://127.0.0.1:5500", "http://localhost:5500"]
  
#core  
    path('api/auth/', include('auth_app.api.urls')),
    path('api/', include('rest_framework.urls')),  # Optional: for DRF's login/logout views
```



Models.py, serializer.py erstellen

```
	py manage.py makemigrations
 	py manage.py migrate
    py manage.py runserver  
    #http://127.0.0.1:8000/
    #neue Terminal öffne. In /backend komme. (env) soll sein.
	python manage.py createsuperuser
	#	aleks   pw123@pw.com
	#	pw123
```



#### Enviroment für Token vorbereten    

```python
#settings.py
INSTALLED_APPS = [
    ...
    'rest_framework.authtoken',
]

#Am Ende der settings.py einfügen.
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
        #'rest_framework.permissions.AllowAny',
    ], 
    
    'DEFAULT_AUTHENTICATION_CLASSES': [
    'rest_framework.authentication.TokenAuthentication', # Für Angular
    'rest_framework.authentication.SessionAuthentication', # Für die Web-Ansicht (oben rechts)
]
}
```

Unbedingt ausführen:

```
py manage.py makemigrations
py manage.py migrate
```

http://127.0.0.1:8000/admin/auth/user/  zeigt AUTH TOKEN

- Token für aleks erstellt. OK

 http://127.0.0.1:8000/api/auth/profiles/ ÖK



#### POST /api/registration/  OK

fullname ist  "This field may not be blank." Gleichzeitig erstelle ich Userprofile mit leer Felde bio und location

```
{
  "fullname": "Example Username",
  "email": "example@mail.de",
  "password": "examplePassword",
  "repeated_password": "examplePassword"
}
{
  "token": "83bf098723b08f7b23429u0fv8274",
  "fullname": "Example Username",
  "email": "example@mail.de",
  "user_id": 123
}
```

Status Codes -  **201:** Der Benutzer wurde erfolgreich erstellt. **400:** Ungültige Anfragedaten. **500:** Interner Serverfehler. Rate Limits - No limit  OK

#### POST /api/login/



```python
# Request Body:
{
  "email": "example@mail.de",
  "password": "examplePassword"
}
# Success Response. Erfolgreiche Authentifizierung gibt ein Token sowie 
# Benutzerinformationen zurück.
{
  "token": "83bf098723b08f7b23429u0fv8274",
  "fullname": "Example Username",
  "email": "example@mail.de",
  "user_id": 123
}
```

















##### Lege im Stammverzeichnis deines Django-Projekts eine Datei namens .env an.

Das „Stammverzeichnis des Django-Projekts“ (oft auch *Project Root* genannt) ist der Ordner, in dem die Datei **`manage.py`** liegt. (/backend)

/KanMind/               <-- Das ist der Hauptordner deines Gesamtprojekts
├── /frontend/
└── /backend/           <-- HIERHER GEHÖRT DIE .env DATEI (Django-Stammverzeichnis)
    ├── .env            <-- [NEUE DATEI]
    ├── manage.py       
    └── /core/          <-- (Hier liegen settings.py und urls.py)

Pfad C:\Users\aleks\Desktop\DJANGO_PROJECT\KanMind\backend\  

Datei .env im /backend/ nimmt intern von settings.py oder 

```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

.env in .gitignore eintragen

```python
# python-dotenv installieren:
pip install python-dotenv
```

Secret Key in settings.py aus der .env laden

```python
# übertrage diese Zeile von settings.py 
SECRET_KEY = 'django-insecure-5g3qku*=r6#j#-t)4o8!v8qrzs0z$jx(9(c49j4+@t3tq_s6=o'
# in .env (ohne Anführungszeichen und keine Leerzeichen um das Gleichheitszeichen herum benutzen.)
SECRET_KEY=django-insecure-5g3qku*=r6#j#-t)4o8!v8qrzs0z$jx(9(c49j4+@t3tq_s6=o

# Eintrage in settings.py
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
load_dotenv()  # Lädt Variablen aus .env
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY is not set in the environment variables.")
```

















**UserProfileDetail** und permissions for owner Creater and Delete, nothing for no owner and no staff or admin

```python
    path('profiles/<int:pk>/', UserProfileDetail.as_view(), name='userprofile-detail'),

# serializer.py
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
#models.py
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    #telefonnummer = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        return self.user.username
    
    @property
    def fullname(self):
        # Holt sich die Daten dynamisch vom User-Model
        return f"{self.user.first_name} {self.user.last_name}".strip()    
# views.py
class UserProfileDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()] # oder IsAuthenticated(),AllowAny  falls eingeloggt Pflicht ist
        # 2. Für Änderungen (PATCH, PUT, DELETE): Nur Admins oder eingeloggte User
        return [permissions.IsAuthenticatedOrReadOnly()]  #IsAdminUser IsAuthenticated
    def check_object_permissions(self, request, obj):
        # Führt die Standard-Checks aus (z.B. für IsAdminUser)
        super().check_object_permissions(request, obj)
        # 3. Besitz-Prüfung für PATCH, PUT und DELETE
        #if request.method not in permissions.SAFE_METHODS:
            # Wenn der User kein Admin ist, MUSS er der Besitzer des Profils sein
        if not request.user.is_staff and obj.user != request.user:
            self.permission_denied(
                request, 
                message="Nur der Besitzer oder ein Admin darf dieses Profil ändern."
            )


```





#####  Was macht `rest_framework.urls` in  **path**('api/', **include**('rest_framework.urls'))  wirklich?

```python
path('api/', include('rest_framework.urls')), 
# Nur für Browser Oberfläche Standart ohne json in Response, nur Statuscode
```

Dieser Pfad stellt lediglich die **Standard-Login- und Logout-Ansichten** für die "Browsable API" (die Web-Oberfläche von Django REST) bereit.

**Response:** Nach dem Login leitet diese Ansicht dich einfach nur auf die Startseite der API weiter oder gibt ein einfaches Status-OK zurück. Sie ist für **Session-Authentifizierung** im Browser gedacht, nicht für die Token-Ausgabe an ein Frontend (wie Angular).  Die Standard-Views geben standardmäßig **keinen Token** im JSON-Body zurück.

```python
class UserLoginView(ObtainAuthToken):
        #permission_classes=[AllowAny]
        def post(self, request, *args, **kwargs):
             email = request.data.get('email')
             if email and not request.data.get('username'):
                try:
                  user_obj = User.objects.get(email=email)
                  request.data['username'] = user_obj.username
                except User.DoesNotExist:
                  return Response({"error","User with same email dosnt match"}, status=status.HTTP_400_BAD_REQUEST ) 
            
             serializer = self.serializer_class(data=request.data)
             if serializer.is_valid():
                user=serializer.validated_data['user']
                token, created = Token.objects.get_or_create(user=user)
                data = {'token': token.key,
                        #'username': username,
                        'fullname': f"{user.first_name} {user.last_name}".strip() or user.username,
                        'email': user.email,
                        'user_id': user.id,
                        }
                return Response(data, status=status.HTTP_200_OK)
             return Response(serializer.errors , status=status.HTTP_400_BAD_REQUEST)
```













#### Problem fullname einlösen.

Es ist besser, **kein** Feld `fullname` im Model zu speichern.

1. **Keine Redundanz:** Wenn du `first_name`, `last_name` UND `fullname` speicherst, hast du die gleichen Daten doppelt. Wenn sich der Vorname ändert, müsstest du zwei Felder aktualisieren.
2. **Django-Standard:** Django ist darauf ausgelegt, `first_name` und `last_name` zu nutzen. Viele interne Funktionen greifen darauf zu.

```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # ... andere Felder ...

    @property
    def fullname(self):
        # Holt sich die Daten dynamisch vom User-Model
        return f"{self.user.first_name} {self.user.last_name}".strip()
    
    
    class RegistrationSerializer(serializers.ModelSerializer):
    # Diese Felder existieren nur im Serializer (Eingabe), nicht in der DB
    fullname = serializers.CharField(write_only=True)
    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'repeated_password', 'fullname']

    def create(self, validated_data):
        # 1. Fullname extrahieren und aufteilen
        fullname = validated_data.pop('fullname', '')
        parts = fullname.split(' ', 1) # Teilt beim ersten Leerzeichen
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

        # 2. User mit den Standard-Feldern erstellen
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=first_name,
            last_name=last_name
        )

        # 3. Das leere Profil für den User anlegen
        UserProfile.objects.create(user=user)

        return user
```

##### Zusammenfassung für deine Aufgabe:

1. **POST-Eingabe:** Nutze den **Serializer**, um den String zu splitten und in `user.first_name` und `user.last_name` zu speichern.
2. **Speicherung:** Nur in den Standard-Django-Feldern.
3. **Anzeige (GET):** Nutze das `SerializerMethodField` oder die `@property` im Model, um den Namen wieder als `fullname` auszugeben.





#### Vorgaben der Klischee.



```python
#Models
class Customer(models.Model):
      first_name = models.CharField(max_length=30, error_messages={'blank': 'Oppa, Vorname darf nicht leer sein'}, help_text='max 30 letters dummy')
      last_name = models.CharField(max_length=30)
      email = models.EmailField(max_length=50, blank=True, default="")
      newsletter_abo = models.BooleanField(default=True)
      account = models.FloatField(blank=True, null=True, help_text='nur Ziffer erlaubt')
      pw_account = models.CharField(max_length=16, blank=True, default="")  
      slug = models.SlugField(blank=True, default="")
      
      class Meta:
        verbose_name="Customer" ##Darstellung an Begriff der Tabelle
        verbose_name_plural="Kunden" #Darstellung an linke Spalter
        ordering=['-first_name'] #Sortierung
      
      def __str__(self):
           return f"{self.first_name} {self.last_name}"
      
      def save(self, *args, **kwargs): # Füge *args und **kwargs hinzu
        #   self.account = 1634554 #Eintragung bei jeden save
            full_name = f"{self.first_name} {self.last_name}"
            self.slug=slugify(full_name)
            # Reiche diese Argumente hier ebenfalls an super().save() weiter
            return super().save(*args, **kwargs)
            # super().save(*args, **kwargs)
```



- **`email`**: Steht bereits im Standard-`User`. Du musst es im `UserProfile` **nicht** nochmal anlegen.
- **`fullname`**: Django hat `first_name` und **`last_name`.** Wenn du ein einziges Feld `fullname` willst, kannst du es in das `UserProfile` schreiben. Meistens lässt man es aber weg und setzt den Namen im Serializer oder Frontend aus Vor- und Nachname zusammen.

```python
# Methode 1
# Eine Property im Model (Bessere Architektur)
# Es ist oft besser, die Logik direkt im Model zu speichern. So kannst du fullname # überall in deinem Projekt nutzen, nicht nur im Serializer.
    # 1.1 models.py
    class UserProfile(models.Model):
        ...
        @property
        def fullname(self):
            return f"{self.user.first_name} {self.user.last_name}".strip()
    # 1.2 Jetzt kannst du fullname einfach wie ein normales Feld in die fields Liste         # aufnehmen. Dafür in deiner serializers.py:
    class UserProfileSerializer(serializers.ModelSerializer):
    	class Meta:
            model = UserProfile
            fields = ['user', 'fullname', 'bio'] # DRF erkennt die @property automatisch
   
    
# Methode 2
# Ein SerializerMethodField (Nur zum Lesen)
# Das ist der sauberste Weg, wenn du den Namen im Frontend anzeigen möchtest. Das Feld 
# wird "on the fly" berechnet.
# serializers.py

class UserProfileSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()
    class Meta:
        model = UserProfile
        fields = ['user', 'fullname', 'email','bio', 'location']
	
    def get_fullname(self, obj):
        # obj ist hier die Instanz von UserProfile
        # Wir greifen auf das verknüpfte User-Objekt zu
        first = obj.user.first_name
        last = obj.user.last_name
        return f"{first} {last}".strip() or obj.user.username
    	# .strip() or obj.user.username sorgt dafür, dass der Username angezeigt wird, 	         # falls Vor- und Nachname leer sind.
```



- **`password`**: Steht **immer** im `User`-Modell. Es wird niemals im Klartext in der Datenbank gespeichert!

*In models.py   KEIN Passwort oder Email, das ist schon im 'user' Objekt*

- **Basis-Daten (Email, Username, Passwort):** Bleiben im Django `User`.
- **Zusatz-Daten (Bio, Ort, etc.):** Kommen ins `UserProfile`.
- **Passwort-Check:** Passiert nur im `Serializer`, gespeichert wird nur das verschlüsselte Passwort im `User`.



#### Response füllen.

Verantwortlich für die Struktur der Antwort (Response) in deinem Fall ist die **`views.py`**, da du dort das Dictionary `data` manuell zusammenbaust. Damit du genau das gewünschte Format erhältst, musst du die `data`-Variable in deiner `RegistrationView` anpassen.

```python
# In deiner RegistrationView innerhalb der post-Methode:

if serializer.is_valid():
    saved_account = serializer.save()
    token, created = Token.objects.get_or_create(user=saved_account)
    
    # Hier baust du die Antwort genau nach deinen Wünschen:
    data = {
        "token": token.key,
        "fullname": f"{saved_account.first_name} {saved_account.last_name}".strip() or saved_account.username,
        "email": saved_account.email,
        "user_id": saved_account.pk  # .pk oder .id gibt die ID zurück
    }
    
    return Response(data, status=status.HTTP_201_CREATED)
```

1. **Die View kontrolliert den "Umschlag":** Der Serializer ist primär dafür da, die Daten zu validieren und in die Datenbank zu schreiben. Die `View` entscheidet am Ende, welche Teile dieser Daten (plus zusätzliche Dinge wie das `token`) in das JSON-Paket für das Frontend gepackt werden.
2. **Manuelle Daten-Zusammenstellung:** Da du in deiner View `data = {...}` geschrieben hast, überschreibst du die Standard-Antwort des Serializers komplett. Das ist völlig okay, bedeutet aber, dass jede Änderung an der gewünschten Antwort genau hier in diesem Dictionary passieren muss.

**`user_id`**: In Django kannst du `saved_account.pk` (Primary Key) oder `saved_account.id` verwenden.



```python
# Was ist besser nutzen?
username = first_name or self.validated_data['username'],   
# ODER
username = first_name or self.validated_data.pop('username', ''),   
```

**Die erste Variante ist deutlich besser und sicherer gegen Angriffe (Cybersecurity).**

Die Methode `.pop()` in Variante 2 **löscht** Daten aktiv aus dem Dictionary `validated_data`.

- Wenn nachfolgende Programmteile oder Logger später noch auf `fullname` zugreifen müssen, sind diese Daten unwiderruflich weg.
- Variante 1 (`['username']`) liest den Wert nur aus, ohne die Datenstruktur zu zerstören. Das hält den Zustand der Anwendung stabil und nachvollziehbar.



#### HTTP_201 , 400, 500



| **Wo?**            | **Zweck**                                                    | **Ergebnis**                        |
| ------------------ | ------------------------------------------------------------ | ----------------------------------- |
| **serializers.py** | Prüfen, ob Passwörter matchen, Email existiert, etc.         | **400 Bad Request** (Sauber gelöst) |
| **views.py**       | Abfangen von unerwarteten Fehlern beim Speichern oder Token-Erstellen. | **Verhindert den 500er Absturz**    |

```python
class RegistrationSerializer(serializers.ModelSerializer):
	# Jede def validate_email(), def validate_username() oder def validate() prüft, ob 		# email, username oder password übereinstimmen -> HTTP 400
    # ... 
    def save(self, **kwargs):
        try:
            pass #alle Code mit .save()
        except Exception as e:
            raise serializers.ValidationError({"server_error": f"Fatal error: {str(e)}"})
            
            
            
class RegistrationView(generics.CreateAPIView):     
    def post(self, request, *args, **kwargs):
             serializer = RegistrationSerializer(data=request.data)
             data={}
             if serializer.is_valid():
                try:
                    saved_account = serializer.save()
                    token, created = Token.objects.get_or_create(user=saved_account)
                    data = {'token': token.key,
                            #'username': saved_account.username,
                            'fullname': f"{saved_account.first_name} 												{saved_account.last_name}".strip() or saved_account.username,
                            'email': saved_account.email,
                            'user_id': saved_account.pk # .pk oder .id gibt die ID zurück
                            # 'message': "User and Profile created successfully.",
                            }
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                except Exception as e:
                    return Response({"error": str(e)}, 																				tatus=status.HTTP_500_INTERNAL_SERVER_ERROR)
             else:
                    return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)                    

```

