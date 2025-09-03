from django.shortcuts import render, get_object_or_404
from accounts.models import Lesson, Teacher, Kiosk, CustomUser
from attendance_token.models import AttendanceRecord
from django.contrib.auth.decorators import login_required
from accounts.views import user_type_required
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Count
import csv
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
                target_grade=request.POST.get('target_grade', ''),
                target_major=request.POST.get('target_major', ''),
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

        # 以前のアクティブなレッスンを終了
        previous_active_lessons = Lesson.objects.filter(teacher=lesson.teacher, is_active=True)
        for prev_lesson in previous_active_lessons:
            prev_lesson.is_active = False
            prev_lesson.save()
            # 関連するAttendanceRecordのend_timeを設定
            from attendance_token.models import AttendanceRecord
            AttendanceRecord.objects.filter(lesson=prev_lesson, end_time__isnull=True).update(end_time=timezone.now())

        # Kioskのcurrent_lessonをリセット
        Kiosk.objects.filter(current_lesson__in=previous_active_lessons).update(current_lesson=None)

        lesson.location = location
        lesson.reception = True
        lesson.is_active = True
        lesson.save()

        # 対応するKioskのcurrent_lessonを設定
        kiosk = Kiosk.objects.filter(location=location).first()
        if kiosk:
            kiosk.current_lesson = lesson
            kiosk.save()

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
        lesson.target_grade = request.POST.get('target_grade', '')
        lesson.target_major = request.POST.get('target_major', '')
        lesson.save()
        return render(request, 'teacher_dashboard/success.html', {'message': '授業を更新しました。'})

    return render(request, 'teacher_dashboard/edit_lesson.html', {'lesson': lesson, 'locations': locations.values()})

@user_type_required('teacher')
def end_lesson(request, lesson_id):
    try:
        lesson = Lesson.objects.get(id=lesson_id, teacher__user=request.user, is_active=True)
    except Lesson.DoesNotExist:
        return render(request, 'teacher_dashboard/error.html', {'message': 'アクティブな授業が見つかりません。'})

    if request.method == 'POST':
        # レッスンを終了
        lesson.is_active = False
        lesson.reception = False
        lesson.save()

        # 関連するAttendanceRecordのend_timeを設定
        from attendance_token.models import AttendanceRecord
        AttendanceRecord.objects.filter(lesson=lesson, end_time__isnull=True).update(end_time=timezone.now())

        # Kioskのcurrent_lessonをリセット
        Kiosk.objects.filter(current_lesson=lesson).update(current_lesson=None)

        return render(request, 'teacher_dashboard/success.html', {'message': '授業を終了しました。'})

    return render(request, 'teacher_dashboard/end_lesson.html', {'lesson': lesson})

@user_type_required('teacher')
def attendance_list(request, lesson_id=None):
    """出席者一覧ページ - 授業選択と出席者表示"""
    try:
        # 講師のプロフィールを取得または作成
        teacher, created = Teacher.objects.get_or_create(
            user=request.user,
            defaults={'subject': 'デフォルト科目'}
        )
        
        # 講師の授業一覧を取得
        lessons = Lesson.objects.filter(teacher=teacher).order_by('-lesson_date', '-created_at')
        
        context = {
            'lessons': lessons,
            'selected_lesson': None,
            'attendance_records': [],
            'total_count': 0,
            'present_count': 0,
            'late_count': 0,
            'grades': [],
            'majors': []
        }
        
        if lesson_id:
            # 特定の授業が選択された場合
            selected_lesson = get_object_or_404(Lesson, id=lesson_id, teacher=teacher)
            
            # フィルタリングパラメータを取得
            status_filter = request.GET.get('status', '')
            grade_filter = request.GET.get('grade', '')
            major_filter = request.GET.get('major', '')
            
            # 出席記録を取得
            attendance_records = AttendanceRecord.objects.filter(
                lesson=selected_lesson
            ).select_related('user').order_by('-attended_at')
            
            # フィルタリングを適用
            if status_filter:
                attendance_records = attendance_records.filter(status=status_filter)
            if grade_filter:
                attendance_records = attendance_records.filter(user__grade=grade_filter)
            if major_filter:
                attendance_records = attendance_records.filter(user__major=major_filter)
            
            # 統計情報を計算
            total_count = attendance_records.count()
            present_count = attendance_records.filter(status='present').count()
            late_count = attendance_records.filter(status='late').count()
            
            # フィルタリング用の選択肢を取得
            all_records = AttendanceRecord.objects.filter(lesson=selected_lesson).select_related('user')
            grades = list(set([record.user.grade for record in all_records if record.user.grade]))
            majors = list(set([record.user.major for record in all_records if record.user.major]))
            grades.sort()
            majors.sort()
            
            context.update({
                'selected_lesson': selected_lesson,
                'attendance_records': attendance_records,
                'total_count': total_count,
                'present_count': present_count,
                'late_count': late_count,
                'grades': grades,
                'majors': majors,
                'current_filters': {
                    'status': status_filter,
                    'grade': grade_filter,
                    'major': major_filter
                }
            })
        
        return render(request, 'teacher_dashboard/attendance_list.html', context)
        
    except Exception as e:
        logger.error(f"Error in attendance_list view: {e}")
        return render(request, 'teacher_dashboard/error.html', {'message': 'エラーが発生しました。'})

@user_type_required('teacher')
def attendance_detail(request, record_id):
    """個別出席記録の詳細表示"""
    try:
        # 講師のプロフィールを取得
        teacher = get_object_or_404(Teacher, user=request.user)
        
        # 出席記録を取得（講師の授業のもののみ）
        attendance_record = get_object_or_404(
            AttendanceRecord.objects.select_related('user', 'lesson'),
            id=record_id,
            lesson__teacher=teacher
        )
        
        # 該当学生の他の出席記録も取得
        student_records = AttendanceRecord.objects.filter(
            user=attendance_record.user,
            lesson__teacher=teacher
        ).select_related('lesson').order_by('-attended_at')
        
        context = {
            'attendance_record': attendance_record,
            'student_records': student_records,
            'student': attendance_record.user
        }
        
        return render(request, 'teacher_dashboard/attendance_detail.html', context)
        
    except Exception as e:
        logger.error(f"Error in attendance_detail view: {e}")
        return render(request, 'teacher_dashboard/error.html', {'message': 'エラーが発生しました。'})

@user_type_required('teacher')
def attendance_export(request, lesson_id):
    """出席者データのCSVエクスポート"""
    try:
        # 講師のプロフィールを取得
        teacher = get_object_or_404(Teacher, user=request.user)
        
        # 授業を取得（講師の授業のみ）
        lesson = get_object_or_404(Lesson, id=lesson_id, teacher=teacher)
        
        # 出席記録を取得
        attendance_records = AttendanceRecord.objects.filter(
            lesson=lesson
        ).select_related('user').order_by('user__name')
        
        # CSVレスポンスを作成
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="attendance_{lesson.subject}_{lesson.lesson_date.strftime("%Y%m%d") if lesson.lesson_date else "unknown"}.csv"'
        
        # BOMを追加（Excelでの文字化け防止）
        response.write('\ufeff')
        
        writer = csv.writer(response)
        
        # ヘッダー行を書き込み
        writer.writerow([
            '学生番号',
            '氏名',
            '学年',
            '専攻',
            '出席状況',
            '出席時間',
            '終了時間',
            '場所'
        ])
        
        # データ行を書き込み
        for record in attendance_records:
            writer.writerow([
                record.user.username,
                record.user.name or record.user.username,
                record.user.grade or '',
                record.user.major or '',
                '出席' if record.status == 'present' else '遅刻' if record.status == 'late' else record.status,
                record.attended_at.strftime('%Y-%m-%d %H:%M:%S') if record.attended_at else '',
                record.end_time.strftime('%Y-%m-%d %H:%M:%S') if record.end_time else '',
                record.location or ''
            ])
        
        return response
        
    except Exception as e:
        logger.error(f"Error in attendance_export view: {e}")
        return render(request, 'teacher_dashboard/error.html', {'message': 'CSVエクスポートでエラーが発生しました。'})
