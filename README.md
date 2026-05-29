# KanMind - Kanban Board RESTful API

KanMind is a robust, production-ready RESTful API built with Django and Django REST Framework (DRF). It serves as a powerful backend for a Kanban project management application (similar to Trello or Jira). The project handles user authentication (via Token), automatic profile management, workspace organization using boards, task assignments, prioritizations, and cross-user task commenting.

---

## Key Features & Architectural Highlights

- **Custom Email Authentication:** Users can log in directly using their `email` and `password`. The API dynamically handles username lookups under the hood.
- **Dynamic Profile Creation:** A `UserProfile` is automatically spawned upon a successful registration hook.
- **Dynamic Fields (`@property` & Serializer Fields):** Full names are parsed from incoming registration payloads into Django's standard `first_name` and `last_name` architectures, ensuring zero database redundancy while presenting a unified `fullname` field via `SerializerMethodField`.
- **Granular Permissions:** Custom object-level authorization blocks unauthorized users from modifying profiles or tasks they don't own or participate in.
- **Global Error Architecture:** Integrated a custom exception handler ensuring all unhandled runtime errors return clean, standardized `500: Internal Server Error` JSON frames instead of raw Python traces.
- **Production-Ready Configuration:** Segregated configurations utilizing environment variables (`.env`) for critical parameters like `SECRET_KEY`.

---

## 📁 Project Structure

The project strictly follows a scalable, decoupled architecture where each application wraps its internal structural definitions (`serializers.py`, `views.py`, `urls.py`) inside an isolated `api/` directory layer.

```text
KanMind/
├── frontend/ # Decoupled Frontend Application
└── backend/ # Django Backend Project Root
 ├── .env # Local Environment Variables (Git-ignored)
 ├── .env.template # Public blueprint configuration for deployment Setup
 ├── manage.py # Django execution orchestrator
 ├── db.sqlite3 # Database state
 ├── core/ # Core System Configuration Application
 │ ├── settings.py
 │ └── urls.py
 ├── auth_app/ # Custom User Administration & Profiles App
 │ ├── models.py
 │ └── api/
 │ ├── serializers.py
 │ ├── views.py
 │ └── urls.py
 └── kanban_app/ # Core Kanban Logic App (Boards, Tasks, Comments)
 ├── models.py
 └── api/
 ├── serializers.py
 ├── views.py
 └── urls.py


 
```



## Data Models Relationship

The system builds its workspace graphs around the core native Django `User` model, extended through operational entity tables.

### 1. UserProfile Model (`auth_app`)

Extends the database user structure with custom regional meta-information.

- **user:** `OneToOneField` linking strictly to the native Django Auth User.
- **bio:** `TextField` for profile summaries (optional).
- **location:** `CharField` for regional location settings (optional).
- **fullname (Property):** Dynamically calculated string interpolation linking user first/last names.

### 2. Board Model (`kanban_app`)

Represents specific workspaces.

- **title:** `CharField` storing workspace naming configurations.
- **owner:** `ForeignKey` linking the workspace manager (cascades to `SET_NULL`).
- **member:** `ManyToManyField` tracking authorized participants allowed to access board instances.

### 3. Task Model (`kanban_app`)

Operational working entities mapped into Kanban status pipelines.

- **title / description:** Text variables mapping task core metrics.
- **status:** `CharField` utilizing state machines via `TaskStatus.choices` (`to-do`, `in-progress`, `review`, `done`).
- **priority:** `CharField` mapping operational urgency via `TaskPriority.choices` (`low`, `medium`, `high`).
- **due_date:** `DateField` handling milestone deadlines.
- **assignee / reviewer / creator:** Independent relational fields pointing explicitly to distinct `User` records.

### 4. Comment Model (`kanban_app`)

- **task:** `ForeignKey` linking to the parent task record.
- **author:** `ForeignKey` tracking comment writers.
- **content:** `TextField` keeping conversational thread tracking logs.



## API Endpoint Specifications

All data inputs and outputs use `application/json` payloads.

### Authentication Endpoints

- **`POST /api/registration/`** - Registers a new user account, auto-generates their `UserProfile`, and returns an immediate authorization token block.
- **`POST /api/login/`** - Accepts payload data with an `email` and `password` key-set. Resolves identities and delivers security tokens.

### Profile Endpoints

- **`GET /api/profiles/`** - Lists all system user profiles (Requires authentication).
- **`GET/PUT/PATCH/DELETE /api/profiles/<int:pk>/`** - Profile detail manipulation endpoint protected strictly by object-level permission configurations (Only the profile owner or system staff can mutate data).

### Kanban Operations

- **`GET/POST /api/boards/`** - Creates or lists workspaces the current context user owns or is registered to as a workspace participant.
- **`GET/PUT/PATCH/DELETE /api/tasks/`** - Task engine interface. Restricts operational modifications to authorized project members.
- **`POST /api/tasks/<int:pk>/comments/`** - Conversation streaming endpoint attached to specific task lines.

## Setup & Local Installation

Follow these steps to run this project locally:

1. **Clone the repository:**

   Bash

   ```
   cd KanMind # Ordner vom Hauptproekt
   git clone https://github.com/alex202-sys/KanMind.git .
   cd backend
   ```

2. **Initialize the Python Virtual Environment:**

   Bash

   ```
   python -m venv .venv
   # Activate on Windows:
   .venv\Scripts\activate
   ```

3. **Install dependencies:**

   Bash

   ```
   pip install -r requirements.txt
   ```

4. **Environment Variables Configuration:** Copy the public configuration template and configure your local settings:

   Bash

   ```
   cp .env.template .env
   ```

   Open your newly created `.env` file and define your development variables cleanly without quotes or extra spacing:

   Plaintext

   ```
   SECRET_KEY=your-super-secure-local-django-secret-key
   ```

5. **Execute database structural migrations & start the development engine:**

   Bash

   ```
   python manage.py migrate
   python manage.py runserver
   ```
   The local service endpoint will spawn cleanly on http://127.0.0.1:8000/api/

