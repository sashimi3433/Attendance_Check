from django.shortcuts import render
from accounts.models import CustomUser

def index(request):
    context = {
        'user': request.user,
    }
    return render(request, 'home/home.html', context)

def account(request):
    context = {
        'user': request.user,
    }
    return render(request, 'home/home-account.html', context)