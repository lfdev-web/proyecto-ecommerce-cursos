from django.contrib import admin

from .models import Exam, Question, AnswerOption, ExamAttempt, AttemptAnswer


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    show_change_link = True  # Las opciones se editan entrando a la pregunta


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'time_limit_minutes', 'passing_score', 'max_attempts', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'course__title')
    inlines = [QuestionInline]


class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 2


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'exam', 'order', 'points')
    list_filter = ('exam',)
    inlines = [AnswerOptionInline]


class AttemptAnswerInline(admin.TabularInline):
    model = AttemptAnswer
    extra = 0
    can_delete = False
    readonly_fields = ('question', 'selected_option', 'is_correct')


@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'attempt_number', 'started_at', 'submitted_at', 'score', 'passed')
    list_filter = ('passed',)
    readonly_fields = ('enrollment', 'attempt_number', 'started_at', 'submitted_at', 'score', 'passed')
    inlines = [AttemptAnswerInline]
