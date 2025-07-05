from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db.models import Q
from accounts.models import CustomUser
from accounts.forms import CustomUserChangeForm
from .forms import UserSearchForm # Add this import

# Staff check decorator
def staff_required(view_func):
    return user_passes_test(
        lambda u: u.is_active and u.is_staff,
        login_url='home:index'  # Redirect if not staff
    )(view_func)

@staff_required
def admin_menu(request):
    form = UserSearchForm(request.GET or None)
    users = None

    if form.is_valid():
        username = form.cleaned_data.get('username')
        name = form.cleaned_data.get('name')
        grade = form.cleaned_data.get('grade')
        age = form.cleaned_data.get('age')
        search_type = form.cleaned_data.get('search_type', 'AND')

        query = Q()
        # Build query based on search_type
        if search_type == 'OR':
            # OR search: any condition match
            if username:
                query |= Q(username__icontains=username)
            if name:
                query |= Q(name__icontains=name)
            if grade:
                query |= Q(grade=grade)
            if age:
                query |= Q(age=age)
        else:
            # AND search: all conditions must match
            if username:
                query &= Q(username__icontains=username)
            if name:
                query &= Q(name__icontains=name)
            if grade:
                query &= Q(grade=grade)
            if age:
                query &= Q(age=age)
        
        # Only execute search if at least one field is filled
        if query:
            users = CustomUser.objects.filter(query)
        else:
            # If form is submitted but no criteria, show no one
            users = CustomUser.objects.none()

    return render(request, 'adminmenu/adminhome.html', {'form': form, 'users': users})


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