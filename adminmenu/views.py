from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from accounts.models import CustomUser
from accounts.forms import CustomUserChangeForm

# Staff check decorator
def staff_required(view_func):
    return user_passes_test(
        lambda u: u.is_active and u.is_staff,
        login_url='home:index'  # Redirect if not staff
    )(view_func)

@staff_required
def admin_menu(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        # Check if user exists
        if CustomUser.objects.filter(pk=user_id).exists():
            return redirect('adminmenu:user_detail', user_id=user_id)
        else:
            messages.error(request, '指定されたIDのユーザーは見つかりませんでした。')
            return render(request, 'adminmenu/adminhome.html')
            
    return render(request, 'adminmenu/adminhome.html')

@staff_required
def user_detail(request, user_id):
    target_user = get_object_or_404(CustomUser, pk=user_id)
    return render(request, 'adminmenu/user_detail.html', {'target_user': target_user})

@staff_required
def edit_user(request, user_id):
    target_user = get_object_or_404(CustomUser, pk=user_id)
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=target_user)
        if form.is_valid():
            form.save()
            messages.success(request, f'{target_user.username}の情報を更新しました。')
            return redirect('adminmenu:user_detail', user_id=user_id)
    else:
        form = CustomUserChangeForm(instance=target_user)
    return render(request, 'adminmenu/edit_user.html', {'form': form, 'target_user': target_user})