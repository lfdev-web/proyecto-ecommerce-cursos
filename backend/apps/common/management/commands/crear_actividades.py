"""
Crea las dos actividades evaluadas de cada curso: el cuestionario y el trabajo
práctico.

Es idempotente y NO borra nada, a propósito: en el servidor ya hay una base
sembrada con usuarios, compras y certificados, y volver a correr el seed
significaría perderla. Este comando solo agrega lo que falte, así que se puede
ejecutar sobre la base que ya está en producción.

    python manage.py crear_actividades
    python manage.py crear_actividades --curso "Docker desde cero"
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Assignment, Course
from apps.exams.models import AnswerOption, Exam, Question

from ._actividades_demo import CUESTIONARIOS, TRABAJOS
from ._catalogo_demo import PREGUNTAS


class Command(BaseCommand):
    help = 'Crea el cuestionario y el trabajo práctico de cada curso (idempotente).'

    def add_arguments(self, parser):
        parser.add_argument('--curso', type=str, default=None,
                            help='Título exacto de un curso; por defecto, todos.')

    @transaction.atomic
    def handle(self, *args, **options):
        # Las preguntas de los seis cursos que ya tenían examen final viven en
        # _catalogo_demo; las de los otros veinticuatro, en _actividades_demo.
        banco = {**PREGUNTAS, **CUESTIONARIOS}

        cursos = Course.objects.all()
        if options['curso']:
            cursos = cursos.filter(title=options['curso'])
            if not cursos.exists():
                self.stderr.write(self.style.ERROR(f'No existe el curso «{options["curso"]}».'))
                return

        # Los seis cursos sembrados antes de este cambio tienen el examen
        # titulado «Examen final — X». Ahora los treinta cursos tienen el mismo
        # tipo de actividad, así que el nombre se unifica: dos cursos abiertos
        # seguidos no pueden llamar a lo mismo de dos maneras distintas.
        renombrados = 0
        for examen in Exam.objects.filter(title__startswith='Examen final — '):
            examen.title = examen.title.replace('Examen final — ', 'Cuestionario — ', 1)
            examen.save(update_fields=['title'])
            renombrados += 1

        examenes = trabajos = 0
        sin_preguntas, sin_trabajo = [], []

        for course in cursos.order_by('title'):
            # ---- Actividad 1: cuestionario ----
            if not Exam.objects.filter(course=course).exists():
                preguntas = banco.get(course.title)
                if preguntas:
                    self._crear_examen(course, preguntas)
                    examenes += 1
                else:
                    sin_preguntas.append(course.title)

            # ---- Actividad 2: trabajo práctico ----
            if not Assignment.objects.filter(course=course).exists():
                datos = TRABAJOS.get(course.title)
                if datos:
                    titulo, consigna, etiqueta, url = datos
                    Assignment.objects.create(
                        course=course, title=titulo, instructions=consigna,
                        resource_label=etiqueta, resource_url=url, is_active=True,
                    )
                    trabajos += 1
                else:
                    sin_trabajo.append(course.title)

        self.stdout.write(self.style.SUCCESS(
            f'\nCuestionarios creados: {examenes}\nTrabajos prácticos creados: {trabajos}'))
        if renombrados:
            self.stdout.write(f'Exámenes renombrados a «Cuestionario»: {renombrados}')
        self.stdout.write(
            f'Total en la base — cuestionarios: {Exam.objects.count()}, '
            f'trabajos: {Assignment.objects.count()}, cursos: {Course.objects.count()}')

        # Los cursos que un docente creó a mano no tienen contenido escrito
        # aquí. No es un error: sus actividades las carga el docente desde el
        # admin. Pero conviene verlos listados para que nadie los dé por hechos.
        for titulo, faltante in (('cuestionario', sin_preguntas), ('trabajo', sin_trabajo)):
            if faltante:
                self.stdout.write(self.style.WARNING(
                    f'\nSin {titulo} (cárgalo desde el admin): ' + ', '.join(faltante)))

    # ------------------------------------------------------------------
    def _crear_examen(self, course, preguntas):
        examen = Exam.objects.create(
            course=course,
            title=f'Cuestionario — {course.title}',
            instructions=(
                f'Responde las {len(preguntas)} preguntas sobre el contenido del '
                f'curso. Necesitas 60% para aprobar. El cronómetro lo controla el '
                f'servidor: si se agota, el intento se califica con 0. '
                f'Tienes 3 intentos.'),
            time_limit_minutes=20,
            passing_score=Decimal('60.00'),
            max_attempts=3,
            is_active=True,
        )
        opciones = []
        for orden, (texto, ops) in enumerate(preguntas, start=1):
            pregunta = Question.objects.create(exam=examen, text=texto, order=orden, points=1)
            opciones.extend([
                AnswerOption(question=pregunta, text=t, is_correct=ok) for t, ok in ops
            ])
        AnswerOption.objects.bulk_create(opciones)
