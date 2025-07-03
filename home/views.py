from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.models import CustomUser
from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    context = {
        'user': request.user,
    }
    return render(request, 'home/home.html', context)

@login_required
def account(request):
    context = {
        'user': request.user,
    }
    return render(request, 'home/home-account.html', context)