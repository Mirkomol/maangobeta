# mainapp/recommendation_utils.py
from .models import Problem, UserSolution, Tag
from django.contrib.auth.models import User
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from django.db.models import Q, Count
import re

def get_user_recommendations(user, num_recommendations=5):
    """
    Get recommended problems for a user based on their solved problems
    """
    try:
        # Get user's solved problems
        solved_problems = UserSolution.objects.filter(
            user=user.userprofile,
            solved=True
        ).select_related('problem').values_list('problem', flat=True)

        # If user hasn't solved any problems, return popular problems
        if not solved_problems:
            return Problem.objects.annotate(
                solved_count=Count('usersolution')
            ).order_by('-solved_count')[:num_recommendations]

        # Get all problems except solved ones
        candidate_problems = Problem.objects.exclude(
            id__in=solved_problems
        ).prefetch_related('tags')

        # If no candidate problems, return empty
        if not candidate_problems:
            return Problem.objects.none()

        # Create problem representations (title + tags)
        problem_texts = [
            f"{p.title} {' '.join(t.name for t in p.tags.all())}"
            for p in candidate_problems
        ]

        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(stop_words='english')
        problem_vectors = vectorizer.fit_transform(problem_texts)

        # Get user's solved problems text
        solved_texts = [
            f"{p.title} {' '.join(t.name for t in p.tags.all())}"
            for p in Problem.objects.filter(id__in=solved_problems)
        ]

        # Create average vector for user's solved problems
        solved_vectors = vectorizer.transform(solved_texts)
        user_vector = np.mean(solved_vectors.toarray(), axis=0).reshape(1, -1)

        # Calculate cosine similarity between user vector and all problems
        similarities = cosine_similarity(user_vector, problem_vectors).flatten()

        # Get indices of top N most similar problems
        top_indices = np.argsort(-similarities)[:num_recommendations]

        # Return recommended problems
        return [candidate_problems[i] for i in top_indices]

    except Exception as e:
        print(f"Error in recommendation: {e}")
        # Fallback to popular problems if error occurs
        return Problem.objects.annotate(
            solved_count=Count('usersolution')
        ).order_by('-solved_count')[:num_recommendations]