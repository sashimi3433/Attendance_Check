from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def view_dashboard(request):
    # キオスクアカウントの場合はQRスキャナーページにリダイレクト
    if request.user.type == 'kiosk':
        return redirect('checkin:qr_scanner')
    
    return render(request, 'pos/dashboard.html')