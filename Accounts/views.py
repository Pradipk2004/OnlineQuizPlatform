from django.shortcuts import render, redirect
from AnswerManagement.forms import InsertAnswerForm
from ExamManagement.models import AttemptedExam, Exam
from .forms import UserLoginForm, UserRegisterForm, CreateProfileForm
from .models import Examinee, Examiner, Profile
from django.contrib.auth import (
    authenticate,
    login,
    logout
)
from django.contrib.auth.decorators import login_required

# ---------------------- LOGIN VIEW ----------------------
def login_view(request):
    if request.user.is_authenticated:
        return redirect('/dashboard')
    next = request.GET.get('next')
    form = UserLoginForm(request.POST or None)
    if form.is_valid():
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            if next:
                return redirect(next)
            return redirect('/dashboard')
    context = {'form': form}
    return render(request, "UserManagement/login.html", context)


# ---------------------- REGISTER VIEW ----------------------
def register_view(request):
    if request.user.is_authenticated:
        return redirect('/dashboard')
    form = UserRegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save(commit=False)
        t = int(form.cleaned_data.get('role'))
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        email = form.cleaned_data.get('email')

        user.set_password(password)
        user.is_active = True  # ✅ Activate directly (no email verification)
        user.save()

        # Assign role
        if t == 1:
            Examinee.objects.create(user=user, organization=form.cleaned_data.get('organization'))
        elif t == 2:
            Examiner.objects.create(user=user, organization=form.cleaned_data.get('organization'))

        # Auto-login the user
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return redirect('/dashboard')

    context = {'form': form}
    return render(request, "UserManagement/signup.html", context)


# ---------------------- LOGOUT VIEW ----------------------
def logout_view(request):
    logout(request)
    return redirect('/')


# ---------------------- DASHBOARD ----------------------
@login_required
def user_dash(request):
    examinee = Examinee.objects.filter(user=request.user)
    examiner = Examiner.objects.filter(user=request.user)
    form = InsertAnswerForm()

    if examinee.exists():
        exams = AttemptedExam.objects.filter(examinee=examinee[0])
        context = {
            "form": form,
            "exams": exams,
            "user": request.user,
            "examinee": True,
        }
    else:
        exams = Exam.objects.filter(examiner__user=request.user)
        context = {
            "exams": exams,
            "user": request.user,
            "examiner": True
        }

    return render(request, 'UserManagement/user_dash_base.html', context)


# ---------------------- PROFILE CREATION ----------------------
@login_required
def create_profile(request):
    form = CreateProfileForm()
    if request.method == "POST":
        form = CreateProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            return redirect('/dashboard')
    context = {'form': form}
    return render(request, "UserManagement/createprofile.html", context)


# ---------------------- SHOW PROFILE ----------------------
@login_required
def show_profile(request):
    examiner = Examiner.objects.filter(user=request.user)
    is_examiner = examiner.exists()
    profile = Profile.objects.filter(user=request.user).first()
    if profile:
        context = {'examiner': is_examiner, 'profile': profile}
        return render(request, "UserManagement/showprofile.html", context)
    return render(request, "UserManagement/noprofile.html", {"message": "You didn't create a profile."})
