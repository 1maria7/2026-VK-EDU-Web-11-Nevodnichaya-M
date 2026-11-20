from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from .forms import ProfileEditForm, SignUpForm
from django.contrib.auth.decorators import login_required

login = LoginView.as_view(
    template_name="core/login.html",
    next_page="questions:index",
)

def signup(request):
    form = SignUpForm(
        request.POST if request.method == "POST" else None
    )

    if request.method == "POST" and form.is_valid():
        user = form.save()
        auth_login(request, user)
        return redirect("questions:index")

    return render(request, "core/signup.html", {"form": form})
@login_required(login_url="core:login")
def profile(request):
    form = ProfileEditForm(
        request.POST if request.method == "POST" else None,
        request.FILES if request.method == "POST" else None,
        instance=request.user,
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("core:profile")

    return render(request, "core/profile.html", {"form": form})
@require_POST
def logout(request):
    next_url = request.POST.get("next", "")

    if not url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = "questions:index"

    auth_logout(request)
    return redirect(next_url)
