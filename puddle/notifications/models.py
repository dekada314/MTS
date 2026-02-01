# core/models.py
from django.db import models
from users.models import User

class NotificationLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('success', 'Success'), ('failed', 'Failed'), ('simulated', 'Simulated')])
     
 
class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_subscribed = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {'Subscribed' if self.is_subscribed else 'Unsubscribed'}"