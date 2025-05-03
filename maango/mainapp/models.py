from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    avatar = models.ImageField(
        upload_to="avatars/",
        default="avatars/default.jpg",  # Make sure this path is correct
        blank=True
    )
    total_points = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    rank = models.IntegerField(default=0)
    streak = models.IntegerField(default=0)
    last_active_date = models.DateField(auto_now=True)
    problems_solved = models.ManyToManyField('Problem', through='UserSolution')

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def update_rank(self):
        # Update user's rank based on total_points
        profiles = UserProfile.objects.order_by('-total_points')
        for index, profile in enumerate(profiles, start=1):
            profile.rank = index
            profile.save(update_fields=['rank'])



class Problem(models.Model):
    DIFFICULTY_CHOICES = [
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    points = models.IntegerField(default=10)
    sample_input = models.TextField(blank=True, null=True)
    sample_output = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    tags = models.ManyToManyField('Tag', blank=True)
    time_limit = models.IntegerField(default=2)  # Time limit in seconds
    memory_limit = models.IntegerField(default=256)  # Memory limit in MB

    def __str__(self):
        return self.title

class TestCase(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    input = models.TextField()
    expected_output = models.TextField()
    is_hidden = models.BooleanField(default=False)  # For hidden test cases
class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class UserSolution(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    solved = models.BooleanField(default=False)
    solved_at = models.DateTimeField(auto_now_add=True)
    code = models.TextField(blank=True, null=True)
    language = models.CharField(max_length=20, default='python')
    execution_time = models.FloatField(null=True, blank=True)  # In milliseconds
    memory_used = models.FloatField(null=True, blank=True)  # In MB

    class Meta:
        unique_together = ('user', 'problem')  # Each user can have only one solution per problem

    def save(self, *args, **kwargs):
        if self.solved and not self.pk:  # Only on first successful solve
            self.user.total_points += self.problem.points
            self.user.save()
            self.user.update_rank()

            # Update streak
            today = timezone.now().date()
            if self.user.last_active_date == today - timedelta(days=1):
                self.user.streak += 1
            elif self.user.last_active_date != today:
                self.user.streak = 1
            self.user.last_active_date = today
            self.user.save()

        super().save(*args, **kwargs)



class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    modules = models.TextField(help_text="Comma-separated list of modules")

    def __str__(self):
        return self.title


class Module(models.Model):
    course = models.ForeignKey(Course, related_name="modules_list", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField(help_text="Detailed explanation about the topic.")

    def __str__(self):
        return self.title




class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    topic = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author} - {self.content[:20]}"

class Comment(models.Model):
    post = models.ForeignKey(Post, related_name="comments", on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author} on {self.post.content[:20]}"



