from rest_framework import serializers

from .models import Exam, Question, AnswerOption, ExamAttempt


class AnswerOptionPublicSerializer(serializers.ModelSerializer):
    """
    Opciones SIN el campo is_correct — la respuesta correcta nunca viaja al cliente.
    """
    class Meta:
        model = AnswerOption
        fields = ('id', 'text')


class QuestionPublicSerializer(serializers.ModelSerializer):
    options = AnswerOptionPublicSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ('id', 'text', 'order', 'points', 'options')


class ExamPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = ('id', 'title', 'instructions', 'time_limit_minutes', 'passing_score', 'max_attempts')


class ExamAttemptSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamAttempt
        fields = ('id', 'attempt_number', 'started_at', 'submitted_at', 'score', 'passed')


class SubmitAnswerSerializer(serializers.Serializer):
    question = serializers.IntegerField()
    option = serializers.IntegerField(allow_null=True, required=False)


class SubmitAttemptSerializer(serializers.Serializer):
    answers = SubmitAnswerSerializer(many=True)
