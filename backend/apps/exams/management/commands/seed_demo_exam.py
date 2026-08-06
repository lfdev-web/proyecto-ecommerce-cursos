from django.core.management.base import BaseCommand, CommandError

from apps.catalog.models import Course
from apps.exams.models import Exam, Question, AnswerOption


QUESTIONS = [
    {
        'text': '¿Cuál es la forma correcta de imprimir "Hola mundo" en Python 3?',
        'points': 2,
        'options': [
            ('print("Hola mundo")', True),
            ('echo "Hola mundo"', False),
            ('console.log("Hola mundo")', False),
            ('printf("Hola mundo")', False),
        ],
    },
    {
        'text': '¿Qué tipo de dato devuelve la función input()?',
        'points': 2,
        'options': [
            ('str', True),
            ('int', False),
            ('float', False),
            ('Depende de lo que escriba el usuario', False),
        ],
    },
    {
        'text': '¿Cuál de estas estructuras es INMUTABLE en Python?',
        'points': 2,
        'options': [
            ('Tupla (tuple)', True),
            ('Lista (list)', False),
            ('Diccionario (dict)', False),
            ('Conjunto (set)', False),
        ],
    },
    {
        'text': '¿Qué imprime este código?  x = [1, 2, 3];  print(len(x))',
        'points': 2,
        'options': [
            ('3', True),
            ('2', False),
            ('[1, 2, 3]', False),
            ('Error', False),
        ],
    },
    {
        'text': '¿Cómo se define una función en Python?',
        'points': 2,
        'options': [
            ('def mi_funcion():', True),
            ('function mi_funcion() {}', False),
            ('func mi_funcion():', False),
            ('define mi_funcion():', False),
        ],
    },
]


class Command(BaseCommand):
    help = 'Crea el examen final de demostración para un curso (por defecto: python-desde-cero). Idempotente.'

    def add_arguments(self, parser):
        parser.add_argument('--course-slug', default='python-desde-cero')

    def handle(self, *args, **options):
        slug = options['course_slug']
        try:
            course = Course.objects.get(slug=slug)
        except Course.DoesNotExist:
            raise CommandError(f'No existe un curso con slug "{slug}".')

        exam, created = Exam.objects.get_or_create(
            course=course,
            defaults={
                'title': f'Examen final — {course.title}',
                'instructions': (
                    'Responde todas las preguntas antes de que termine el tiempo. '
                    'Necesitas al menos 70% para aprobar y obtener tu certificado.'
                ),
                'time_limit_minutes': 10,
                'passing_score': 70,
                'max_attempts': 3,
                'is_active': True,
            },
        )

        if not created:
            self.stdout.write(self.style.WARNING(
                f'El curso "{course.title}" ya tiene examen (id={exam.id}); no se modificó.'
            ))
            return

        for order, q in enumerate(QUESTIONS, start=1):
            question = Question.objects.create(
                exam=exam, text=q['text'], order=order, points=q['points'],
            )
            AnswerOption.objects.bulk_create([
                AnswerOption(question=question, text=text, is_correct=is_correct)
                for text, is_correct in q['options']
            ])

        self.stdout.write(self.style.SUCCESS(
            f'Examen creado para "{course.title}": {len(QUESTIONS)} preguntas, '
            f'{exam.time_limit_minutes} min, nota mínima {exam.passing_score}%, '
            f'{exam.max_attempts} intentos.'
        ))
