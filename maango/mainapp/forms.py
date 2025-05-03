from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django import forms
from django.forms.widgets import PasswordInput, TextInput
from .models import Course, Module, TestCase
from .models import Post, Comment
from .models import Problem
from .models import UserProfile


# - Create/Register a user (Model Form)

class CreateUserForm(UserCreationForm):

    class Meta:

        model = User
        fields = ['username', 'email', 'password1', 'password2']


# - Authenticate a user (Model Form)

class LoginForm(AuthenticationForm):

    username = forms.CharField(widget=TextInput())
    password = forms.CharField(widget=PasswordInput())




class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'modules']  # Fields to include in the form

class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['course', 'title', 'content']  # Fields to include in the form



class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content', 'topic']
        widgets = {
            'content': forms.Textarea(attrs={'placeholder': 'What’s happening?', 'rows': 3}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'placeholder': 'Write a comment...', 'rows': 2}),
        }


class ProblemForm(forms.ModelForm):
    class Meta:
        model = Problem
        fields = ['title', 'description', 'difficulty', 'sample_input',
                 'sample_output', 'time_limit', 'memory_limit']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Detailed problem description...'}),
            'sample_input': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Example input that users will see'
            }),
            'sample_output': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Expected output for the sample input'
            }),
            'time_limit': forms.NumberInput(attrs={'min': 1, 'max': 10}),
            'memory_limit': forms.NumberInput(attrs={'min': 64, 'max': 1024}),
        }
        help_texts = {
            'time_limit': 'Time limit in seconds (1-10)',
            'memory_limit': 'Memory limit in MB (64-1024)',
        }

    def clean_time_limit(self):
        time_limit = self.cleaned_data['time_limit']
        if time_limit < 1 or time_limit > 10:
            raise forms.ValidationError("Time limit must be between 1 and 10 seconds")
        return time_limit

    def clean_memory_limit(self):
        memory_limit = self.cleaned_data['memory_limit']
        if memory_limit < 64 or memory_limit > 1024:
            raise forms.ValidationError("Memory limit must be between 64 and 1024 MB")
        return memory_limit


class TestCaseForm(forms.ModelForm):
    class Meta:
        model = TestCase
        fields = ['input', 'expected_output', 'is_hidden']
        widgets = {
            'input': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Test case input data',
                'class': 'test-case-input'
            }),
            'expected_output': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Expected output for this input',
                'class': 'test-case-output'
            }),
        }
        help_texts = {
            'is_hidden': 'Check to hide this test case from users (for secret test cases)'
        }

    def clean_input(self):
        input_data = self.cleaned_data['input']
        if not input_data.strip():
            raise forms.ValidationError("Test case input cannot be empty")
        return input_data

    def clean_expected_output(self):
        expected_output = self.cleaned_data['expected_output']
        if not expected_output.strip():
            raise forms.ValidationError("Expected output cannot be empty")
        return expected_output



class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'avatar']
