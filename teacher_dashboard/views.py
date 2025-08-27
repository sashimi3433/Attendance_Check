from django.shortcuts import render
from accounts.models import Lesson, Teacher
from django.contrib.auth.decorators import login_required
from accounts.views import user_type_required
import logging

logger = logging.getLogger(__name__)

@user_type_required('teacher')
def index(request):
    logger.info("Teacher dashboard index view called")
    logger.info(f"Template dirs: {request.GET}")
    try:
        return render(request, 'teacher_dashboard/index.html')
    except Exception as e:
        logger.error(f"Error rendering template: {e}")
        raise

@user_type_required('teacher')
def list_lessons(request):
    try:
        # Ensure teacher profile exists
        teacher, created = Teacher.objects.get_or_create(
            user=request.user,
            defaults={'subject': 'デフォルト科目'}
        )
        if created:
            logger.info(f"Created teacher profile for user: {request.user.username}")
        lessons = Lesson.objects.filter(teacher=teacher).order_by('-created_at')
        return render(request, 'teacher_dashboard/list_lessons.html', {'lessons': lessons})
    except Exception as e:
        logger.error(f"Error rendering template: {e}")
        raise

@user_type_required('teacher')
def generate_lesson(request):
    if request.method == 'POST':
        # request.userに対応するTeacherインスタンスを取得または作成
        teacher, created = Teacher.objects.get_or_create(
            user=request.user,
            defaults={'subject': 'デフォルト科目'}  # 新規作成時のデフォルト値
        )
        
        for i in range(int(request.POST['lesson_count'])):
            Lesson.objects.create(
                subject=request.POST['lesson_name'],
                teacher=teacher,
                lesson_times= i+1,
            )
        return render(request, 'teacher_dashboard/success.html')
    return render(request, 'teacher_dashboard/generate_lesson.html')

locations = {
    'Room207': '207教室',
    'Room208': '208教室',
    'Room204': '204教室',
}

@user_type_required('teacher')
def start_checkin(request):
    # Determine user type safely
    user_type = 'unknown'
    if hasattr(request.user, 'invitation_code') and request.user.invitation_code:
        user_type = request.user.invitation_code.type
    elif hasattr(request.user, 'teacher_profile'):
        user_type = 'teacher'
    else:
        user_type = 'student'  # Default assumption

    logger.info(f"start_checkin called by user: {request.user.username}, type: {user_type}")
    logger.info(f"User has teacher_profile: {hasattr(request.user, 'teacher_profile')}")
    if hasattr(request.user, 'teacher_profile'):
        logger.info(f"Teacher profile exists: {request.user.teacher_profile}")
    else:
        logger.error("User does not have teacher_profile")
    if request.method == 'POST':
        lesson_id = request.POST['lesson_id']
        location = request.POST['location']
        lesson = Lesson.objects.get(id=lesson_id)
        lesson.location = location
        lesson.reception = True
        lesson.save()
        return render(request, 'teacher_dashboard/success.html')
    # Ensure teacher profile exists
    teacher, created = Teacher.objects.get_or_create(
        user=request.user,
        defaults={'subject': 'デフォルト科目'}
    )
    if created:
        logger.info(f"Created teacher profile for user: {request.user.username}")
    lessons = Lesson.objects.filter(teacher=teacher, reception=False)
    return render(request, 'teacher_dashboard/start_checkin.html', {'lessons': lessons, 'locations': locations.values()})

@user_type_required('teacher')
def edit_lesson(request, lesson_id):
    try:
        lesson = Lesson.objects.get(id=lesson_id, teacher__user=request.user)
    except Lesson.DoesNotExist:
        return render(request, 'teacher_dashboard/error.html', {'message': '授業が見つかりません。'})

    if request.method == 'POST':
        lesson.subject = request.POST['subject']
        lesson.lesson_times = request.POST['lesson_times']
        lesson.location = request.POST['location']
        lesson_date_str = request.POST.get('lesson_date')
        if lesson_date_str:
            from django.utils.dateparse import parse_datetime
            lesson.lesson_date = parse_datetime(lesson_date_str)
        else:
            lesson.lesson_date = None
        lesson.reception = 'reception' in request.POST
        lesson.save()
        return render(request, 'teacher_dashboard/success.html', {'message': '授業を更新しました。'})

    return render(request, 'teacher_dashboard/edit_lesson.html', {'lesson': lesson, 'locations': locations.values()})
