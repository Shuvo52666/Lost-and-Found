from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render
from .forms import SignupForm

def signup(request):
    if request.user.is_authenticated:
        return redirect('feed')
    form = SignupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Welcome! Your account is ready.')
        return redirect('community_list')
    return render(request, 'accounts/signup.html', {'form': form})
