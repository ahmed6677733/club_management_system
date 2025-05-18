from django.db import models


class Post(models.Model):
    user = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, null=True, blank=True)
    body = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Add created_at field

    class Meta:
        ordering = ['-created_at']  # Orders posts by created_at in descending order (latest first)

    def __str__(self):
        return self.title


class Comment(models.Model):
    user = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, null=True, blank=True, on_delete=models.CASCADE)
    message = models.CharField(max_length=200, null=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Add created_at field

    class Meta:
        ordering = ['-created_at']  # Orders comments by created_at in descending order (latest first)

    def __str__(self):
        return self.message

class React(models.Model):
    pass