from django.shortcuts import render

def view_dashboard(request):
    return render(request, 'pos/dashboard.html')