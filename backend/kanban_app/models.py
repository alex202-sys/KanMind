from django.contrib.auth.models import User
from django.db import models


class Board(models.Model):
    """Board hat a owner (user) und list of member (user)"""

    title = models.CharField(max_length=155)
    owner = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL, related_name="owners"
    )
    member = models.ManyToManyField(User, blank=True, related_name="members")

    def __str__(self):
        return self.title


class TaskStatus(models.TextChoices):
    """Status of tasks, a selection field in a task."""

    IN_PROGRESS = "in-progress", "In Progress"
    TODO = "to-do", "To-Do"
    DONE = "done", "Done"
    REVIEW = "review", "Review"


class TaskPriority(models.TextChoices):
    """Status of priority, a selection field in a task."""

    HIGH = "high", "High"
    MEDIUM = "medium", "Medium"
    LOW = "low", "Low"


class Task(models.Model):
    """Each "Task" model belongs to a "Board" model; it has "Status" and "Priority"
    choice fields, as well as "Assignee" and "Reviewer" fields linked to users."""

    title = models.CharField(max_length=255)
    board = models.ForeignKey(
        Board, on_delete=models.CASCADE, blank=True, null=True, related_name="tasks"
    )
    description = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20, choices=TaskStatus.choices, default=TaskStatus.IN_PROGRESS
    )
    priority = models.CharField(
        max_length=20, choices=TaskPriority.choices, default=TaskPriority.MEDIUM
    )
    due_date = models.DateField()
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="assigned_tasks",
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="reviewed_tasks",
    )
    creator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="created_by_tasks",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class Comment(models.Model):
    """Each comment has an author and is linked to a task belonging to a board;
    it can be created or edited by a board member, but deleted only by its author.
    """

    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, blank=True, null=True, related_name="comments"
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
