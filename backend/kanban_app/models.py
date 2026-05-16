from django.db import models
from django.contrib.auth.models import User
from django.db import models

# Create your models here.
class Boards(models.Model):
    title = models.CharField(max_length=155)
    owner_id = models.OneToOneField(User, on_delete=models.CASCADE)
    member = models.ManyToManyField(User, related_name='members')

    def __str__(self):
        return self.title

class TicketStatus(models.TextChoices):
    IN_PROGRESS = 'in-progress', 'In Progress'
    TODO = 'to-do', 'To-Do'
    DONE = 'done', 'Done' 
    REVIEW = 'review', 'Review' 
     

class TicketPriority(models.TextChoices):
    HIGH = 'high', 'High'
    MEDIUM = 'medium', 'Medium'
    LOW = 'low', 'Low' 
    # Holt alle Tickets, die fertig sind
    #finished_tickets = Ticket.objects.filter(status=Ticket.Status.ENDED)
    # ticket.status = Ticket.Status.IN_PROGRESS
    # ticket.save()


class Ticket(models.Model):
    title = models.CharField(max_length=255)
    boards = models.OneToOneField(Boards, on_delete=models.SET_NULL, null=True)
    description = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=TicketStatus.choices,  default=TicketStatus.IN_PROGRESS)
    priority = models.CharField(max_length=20, choices=TicketPriority.choices,  default=TicketPriority.MEDIUM)
    due_date = models.DateField()
    assignee = models.OneToOneField(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='assignees')
    reviewer = models.OneToOneField(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='reviewers')

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"