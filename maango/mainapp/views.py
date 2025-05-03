from django.contrib.auth.decorators import login_required
import subprocess
from django.forms import formset_factory
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import render, get_object_or_404
from .forms import CourseForm, ModuleForm, ProblemForm, UserProfileForm, PostForm, CommentForm, TestCaseForm
from .models import *
from django.db.models import Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import tempfile
from .models import Course
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from django.db.models import Count, Sum
from datetime import timedelta
from django.utils import timezone
import os
import time
import resource
from .models import Problem, UserSolution
from django.shortcuts import render
from django.core.paginator import Paginator
from .models import Problem
import re
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required



@staff_member_required
def admin_dashboard(request):
    # User statistics
    total_users = User.objects.count()
    new_users_today = User.objects.filter(date_joined__date=timezone.now().date()).count()
    active_users = User.objects.filter(last_login__date=timezone.now().date()).count()

    # Problem statistics
    total_problems = Problem.objects.count()
    problems_by_difficulty = Problem.objects.values('difficulty').annotate(count=Count('id'))

    # Course statistics
    total_courses = Course.objects.count()
    total_modules = Module.objects.count()

    # Forum statistics
    total_posts = Post.objects.count()
    total_comments = Comment.objects.count()

    # Recent activity
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_solutions = UserSolution.objects.filter(solved=True).order_by('-solved_at')[:5]
    recent_posts = Post.objects.order_by('-created_at')[:5]

    context = {
        'total_users': total_users,
        'new_users_today': new_users_today,
        'active_users': active_users,
        'total_problems': total_problems,
        'problems_by_difficulty': problems_by_difficulty,
        'total_courses': total_courses,
        'total_modules': total_modules,
        'total_posts': total_posts,
        'total_comments': total_comments,
        'recent_users': recent_users,
        'recent_solutions': recent_solutions,
        'recent_posts': recent_posts,
    }
    return render(request, 'mainapp/admin_dashboard.html', context)


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Save the user
            # Create UserProfile only if it doesn't exist
            UserProfile.objects.get_or_create(user=user)
            messages.success(request, f'Welcome {user.username}')
            return redirect('login')  # Redirect to login after successful registration
    else:
        form = UserCreationForm()

    return render(request, 'mainapp/register.html', {'form': form})

# Login view
def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)  # Login the user
            return redirect('index')  # Redirect to a home page or dashboard
        else:
            messages.error(request, 'Invalid credentials, please try again.')

    return render(request, 'mainapp/login.html')


# Logout view
def logout(request):
    logout(request)
    return redirect('login')  # Redirect to login page after logout




#@login_required(login_url="login")
def index(request):
    return render(request,"mainapp/index.html")


#
#
# def problems(request):
#     search_query = request.GET.get('q', '').strip().lower()
#     all_problems = Problem.objects.all().order_by('id')
#
#     if search_query:
#         tokens = [token for token in re.split(r'\W+', search_query) if token]
#         query = Q()
#         for token in tokens:
#             query |= Q(title__icontains=token)
#         all_problems = all_problems.filter(query).distinct()
#
#     # Get solved problems for the current user
#     solved_problems = set()
#     solved_problems_count = 0  # initialize
#     if request.user.is_authenticated:
#         solved_problem_qs = UserSolution.objects.filter(
#             user=request.user.userprofile,
#             solved=True
#         )
#         solved_problems = set(solved_problem_qs.values_list('problem_id', flat=True))
#         solved_problems_count = solved_problem_qs.count()
#
#     # Get count of solvers for each problem
#     problems_with_solvers = all_problems.annotate(
#         solver_count=Count('usersolution', filter=Q(usersolution__solved=True))
#     )
#
#     easy_count = all_problems.filter(difficulty__iexact='easy').count()
#     medium_count = all_problems.filter(difficulty__iexact='medium').count()
#     hard_count = all_problems.filter(difficulty__iexact='hard').count()
#
#     paginator = Paginator(problems_with_solvers, 6)
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
#
#     context = {
#         'page_obj': page_obj,
#         'search_query': search_query,
#         'total_problems': all_problems.count(),
#         'easy_count': easy_count,
#         'medium_count': medium_count,
#         'hard_count': hard_count,
#         'solved_problems': solved_problems,
#         'solved_problems_count': solved_problems_count,  # ✅ added
#         'no_results': bool(search_query) and page_obj.paginator.count == 0
#     }
#
#     return render(request, "mainapp/problems.html", context)



from .recommendation_utils import get_user_recommendations

def problems(request):
    search_query = request.GET.get('q', '').strip().lower()
    all_problems = Problem.objects.all().order_by('id')

    if search_query:
        tokens = [token for token in re.split(r'\W+', search_query) if token]
        query = Q()
        for token in tokens:
            query |= Q(title__icontains=token)
        all_problems = all_problems.filter(query).distinct()

    # Get recommendations if user is authenticated
    recommended_problems = []
    if request.user.is_authenticated:
        recommended_problems = get_user_recommendations(request.user)

    easy_count = all_problems.filter(difficulty__iexact='easy').count()
    medium_count = all_problems.filter(difficulty__iexact='medium').count()
    hard_count = all_problems.filter(difficulty__iexact='hard').count()

    paginator = Paginator(all_problems, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_problems': all_problems.count(),
        'easy_count': easy_count,
        'medium_count': medium_count,
        'hard_count': hard_count,
        'no_results': bool(search_query) and page_obj.paginator.count == 0,
        'recommended_problems': recommended_problems,
    }

    return render(request, "mainapp/problems.html", context)



def add_problem(request):
    if request.method == "POST":
        form = ProblemForm(request.POST)
        if form.is_valid():
            problem = form.save()
            return redirect('add_test_cases', problem_id=problem.id)
    else:
        form = ProblemForm()
    return render(request, "mainapp/add_problem.html", {"form": form})


def delete_problem(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id)

    if not request.user.is_staff and not request.user.is_superuser:
        return HttpResponseForbidden("Permission denied")

    if request.method == 'POST':
        problem.delete()
        return redirect('problems')

    return render(request, 'mainapp/confirm_delete.html', {'problem': problem})

def add_test_cases(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id)
    TestCaseFormSet = formset_factory(TestCaseForm, extra=3)

    if request.method == "POST":
        formset = TestCaseFormSet(request.POST)
        if formset.is_valid():
            for form in formset:
                if form.cleaned_data.get('input'):
                    test_case = form.save(commit=False)
                    test_case.problem = problem
                    test_case.save()
            return redirect('problems')
    else:
        formset = TestCaseFormSet()

    return render(request, "mainapp/add_test_cases.html", {
        "formset": formset,
        "problem": problem
    })


def solve_problem(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    test_cases = problem.testcase_set.filter(is_hidden=False)

    # Check if user has already solved this problem
    is_solved = False
    if request.user.is_authenticated:
        is_solved = UserSolution.objects.filter(
            user=request.user.userprofile,
            problem=problem,
            solved=True
        ).exists()

    # Get user's previous solution if exists
    try:
        previous_solution = UserSolution.objects.get(
            user=request.user.userprofile,
            problem=problem
        )
        initial_code = previous_solution.code
        initial_language = previous_solution.language
    except UserSolution.DoesNotExist:
        initial_code = ""
        initial_language = "python"

    return render(request, 'mainapp/solve_problem.html', {
        "problem": problem,
        "test_cases": test_cases,
        "initial_code": initial_code,
        "initial_language": initial_language,
        "is_solved": is_solved
    })


def runcode(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    test_cases = problem.testcase_set.all()
    results = []
    passed_count = 0
    success = False
    execution_time = None
    memory_used = None
    code = request.POST.get("codearea", "") if request.method == "POST" else ""
    language = request.POST.get("language", "python") if request.method == "POST" else "python"

    if request.method == "POST":
        code = request.POST.get("codearea", "")
        language = request.POST.get("language", "python")

        if not code.strip():
            messages.error(request, "Please enter some code to execute")
            return redirect('solve_problem', pk=pk)

        for test_case in test_cases:
            result = {
                'input': test_case.input,
                'expected': test_case.expected_output,
                'output': '',
                'passed': False,
                'error': None,
                'hidden': test_case.is_hidden,
                'execution_time': 0,
                'memory_used': 0
            }

            try:
                # Create temp file with code
                with tempfile.NamedTemporaryFile(mode="w+", suffix=f".{language}", delete=False) as temp_file:
                    temp_file.write(code)
                    temp_file_path = temp_file.name

                # Prepare input
                input_data = test_case.input.replace('\r\n', '\n')

                # Select command based on language
                if language == "python":
                    cmd = ["python3", temp_file_path]
                elif language == "javascript":
                    cmd = ["node", temp_file_path]
                else:
                    raise ValueError("Unsupported language")

                # Run code with timeout
                start_time = time.time()

                try:
                    process = subprocess.Popen(
                        cmd,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )

                    try:
                        stdout, stderr = process.communicate(
                            input=input_data,
                            timeout=problem.time_limit + 1
                        )
                    except subprocess.TimeoutExpired:
                        process.kill()
                        result['error'] = "Time Limit Exceeded"
                        results.append(result)
                        continue

                    execution_time = (time.time() - start_time) * 1000  # ms

                    # Get memory usage (approximate)
                    memory_used = 0
                    if hasattr(resource, 'getrusage'):
                        try:
                            mem = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
                            if os.name == 'posix':  # Linux/Unix
                                memory_used = mem / 1024  # KB to MB
                            else:  # MacOS
                                memory_used = mem / (1024 * 1024)  # bytes to MB
                        except:
                            pass

                    # Clean output for comparison
                    user_output = stdout.strip().replace('\r\n', '\n')
                    expected_output = test_case.expected_output.strip().replace('\r\n', '\n')

                    # Check if output matches
                    passed = user_output == expected_output
                    if passed:
                        passed_count += 1

                    result.update({
                        'output': user_output,
                        'passed': passed,
                        'error': stderr if stderr else None,
                        'execution_time': execution_time,
                        'memory_used': memory_used
                    })

                except Exception as e:
                    result['error'] = str(e)

                finally:
                    if os.path.exists(temp_file_path):
                        try:
                            os.unlink(temp_file_path)
                        except:
                            pass

            except Exception as e:
                result['error'] = f"Execution Error: {str(e)}"

            results.append(result)

        # Check if all test cases passed
        success = passed_count == len(test_cases)

        if success:
            # Save successful solution
            UserSolution.objects.update_or_create(
                user=request.user.userprofile,
                problem=problem,
                defaults={
                    'solved': True,
                    'code': code,
                    'language': language,
                    'execution_time': execution_time,
                    'memory_used': memory_used,
                }
            )
            # messages.success(request, "Congratulations! You solved the problem!")
        else:
            # messages.warning(request, f"Passed {passed_count}/{len(test_cases)} test cases")
            pass

    return render(request, "mainapp/solve_problem.html", {
        "problem": problem,
        "code": code,
        "results": results,
        "success": success,
        "language": language,
        "execution_time": execution_time,
        "memory_used": memory_used,
    })



def algorithms(request):
    """
    Display a list of algorithm courses with enhanced search and pagination.
    Includes basic NLP capabilities using TF-IDF and cosine similarity.
    """
    search_query = request.GET.get('q', '').strip()
    courses = Course.objects.all().order_by('title')
    no_results = False

    try:
        if search_query:
            # Basic exact matching using available fields
            exact_matches = courses.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            ).distinct()

            if exact_matches.exists():
                courses = exact_matches
            else:
                # If no exact matches, try NLP-based similarity
                all_courses = list(courses)
                if all_courses:  # Only proceed if there are courses
                    course_texts = [
                        f"{course.title} {course.description}"
                        for course in all_courses
                    ]

                    # Create TF-IDF vectors
                    vectorizer = TfidfVectorizer(stop_words='english')
                    tfidf_matrix = vectorizer.fit_transform(course_texts)

                    # Vectorize the search query
                    query_vec = vectorizer.transform([search_query])

                    # Calculate cosine similarities
                    similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()

                    # Get indices of top matches (similarity > 0.2)
                    matched_indices = np.where(similarities > 0.2)[0]

                    if len(matched_indices) > 0:
                        # Sort by similarity score (descending)
                        sorted_indices = matched_indices[np.argsort(-similarities[matched_indices])]
                        matched_courses = [all_courses[i] for i in sorted_indices]
                        courses = Course.objects.filter(id__in=[c.id for c in matched_courses])
                    else:
                        no_results = True
                        courses = Course.objects.none()
                else:
                    no_results = True
                    courses = Course.objects.none()

        # Set up pagination: 6 courses per page
        paginator = Paginator(courses, 6)
        page = request.GET.get('page', 1)

        try:
            courses_page = paginator.page(page)
        except PageNotAnInteger:
            courses_page = paginator.page(1)
        except EmptyPage:
            courses_page = paginator.page(paginator.num_pages)

        context = {
            'courses': courses_page,
            'search_query': search_query,
            'no_results': no_results,
        }

        return render(request, "mainapp/algorithms.html", context)

    except Exception as e:
        # Fallback to simple search if NLP processing fails
        print(f"Error in search processing: {str(e)}")
        courses = Course.objects.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        ).distinct()

        paginator = Paginator(courses, 6)
        page = request.GET.get('page', 1)

        try:
            courses_page = paginator.page(page)
        except PageNotAnInteger:
            courses_page = paginator.page(1)
        except EmptyPage:
            courses_page = paginator.page(paginator.num_pages)

        context = {
            'courses': courses_page,
            'search_query': search_query,
            'no_results': not courses.exists(),
        }
        return render(request, "mainapp/algorithms.html", context)


def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)  # Fetch the course by ID
    modules = course.modules.split(",")  # Split the modules string into a list
    return render(request, "mainapp/course_detail.html", {'course': course, 'modules': modules})




def module_detail(request, module_id):
    module = get_object_or_404(Module, id=module_id)  # Fetch the module by ID
    return render(request, "mainapp/module_detail.html", {'module': module})



def create_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()  # Save the new course to the database
            return redirect('algorithms')  # Redirect to the course list page
    else:
        form = CourseForm()
    return render(request, 'mainapp/create_course.html', {'form': form})

def create_module(request):
    if request.method == 'POST':
        form = ModuleForm(request.POST)
        if form.is_valid():
            form.save()  # Save the new module to the database
            return redirect('algorithms')  # Redirect to the course list page
    else:
        form = ModuleForm()
    return render(request, 'mainapp/create_module.html', {'form': form})



# Discussion view

def discussion(request):
    posts = Post.objects.all().order_by('-created_at')
    search_query = request.GET.get('q', '')

    if search_query:
        posts = posts.filter(
            Q(content__icontains=search_query) | Q(topic__icontains=search_query)
        )

    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('discussion')
    else:
        form = PostForm()

    return render(request, 'mainapp/discussion.html', {'posts': posts, 'form': form, 'search_query': search_query})




def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            return redirect('discussion')
    else:
        form = CommentForm()

    return render(request, 'mainapp/add_comment.html', {'form': form, 'post': post})



# Profile view
# def profile(request, username):
#     user_profile = get_object_or_404(UserProfile, user__username=username)
#     return render(request, 'mainapp/profile.html', {'user_profile': user_profile})



def profile(request, username):
    user_profile = get_object_or_404(UserProfile, user__username=username)

    # Count solved problems
    solved_count = UserSolution.objects.filter(
        user=user_profile,
        solved=True
    ).count()

    # Difficulty-wise count
    easy_count = Problem.objects.filter(
        usersolution__user=user_profile,
        usersolution__solved=True,
        difficulty__iexact='easy'
    ).count()

    medium_count = Problem.objects.filter(
        usersolution__user=user_profile,
        usersolution__solved=True,
        difficulty__iexact='medium'
    ).count()

    hard_count = Problem.objects.filter(
        usersolution__user=user_profile,
        usersolution__solved=True,
        difficulty__iexact='hard'
    ).count()

    context = {
        'user_profile': user_profile,
        'solved_count': solved_count,
        'easy_count': easy_count,
        'medium_count': medium_count,
        'hard_count': hard_count,
    }
    return render(request, 'mainapp/profile.html', context)



@login_required
def edit_profile(request):
    user_profile = request.user.userprofile
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect('profile', username=request.user.username)
    else:
        form = UserProfileForm(instance=user_profile)
    return render(request, 'mainapp/edit_profile.html', {'form': form})



def leaderboard(request):
    # Get all time leaderboard
    all_time = UserProfile.objects.order_by('-total_points')[:100]

    # Get weekly leaderboard (users active in last 7 days)
    weekly = UserProfile.objects.filter(
        last_active_date__gte=timezone.now().date() - timedelta(days=7)
    ).order_by('-total_points')[:100]

    # Get daily leaderboard (users active today)
    daily = UserProfile.objects.filter(
        last_active_date=timezone.now().date()
    ).order_by('-total_points')[:100]

    # Get streak leaderboard
    streak = UserProfile.objects.order_by('-streak')[:100]

    # Get most active problem solvers
    active = UserProfile.objects.annotate(
        solve_count=Count('problems_solved')
    ).order_by('-solve_count')[:100]

    context = {
        'all_time': all_time,
        'weekly': weekly,
        'daily': daily,
        'streak': streak,
        'active': active,
    }
    return render(request, 'mainapp/leaderboard.html', context)


def user_stats(request, username):
    user_profile = get_object_or_404(UserProfile, user__username=username)

    # Get solved problems count by difficulty
    solved_problems = user_profile.problems_solved.all()
    easy_count = solved_problems.filter(difficulty='Easy').count()
    medium_count = solved_problems.filter(difficulty='Medium').count()
    hard_count = solved_problems.filter(difficulty='Hard').count()

    # Get recent activity
    recent_solutions = UserSolution.objects.filter(
        user=user_profile,
        solved=True
    ).order_by('-solved_at')[:10]

    # Get category stats
    category_stats = Tag.objects.filter(
        problem__usersolution__user=user_profile,
        problem__usersolution__solved=True
    ).annotate(
        count=Count('problem')
    ).order_by('-count')[:5]

    context = {
        'user_profile': user_profile,
        'easy_count': easy_count,
        'medium_count': medium_count,
        'hard_count': hard_count,
        'recent_solutions': recent_solutions,
        'category_stats': category_stats,
    }
    return render(request, 'mainapp/user_stats.html', context)