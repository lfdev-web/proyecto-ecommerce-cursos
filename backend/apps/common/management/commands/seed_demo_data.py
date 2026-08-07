"""
Seed histórico de demostración: ~5 años de usuarios, compras, progreso,
reseñas, interacciones y logs de navegación con crecimiento mes a mes.

Uso:
    python manage.py seed_demo_data              # siembra (aborta si ya existe)
    python manage.py seed_demo_data --flush      # borra el seed anterior y re-siembra
    python manage.py seed_demo_data --years 3    # menos historia
    python manage.py seed_demo_data --sin-media  # no descarga imágenes ni valida videos

Notas técnicas:
- Los campos auto_now_add ignoran fechas pasadas: se desactivan temporalmente
  en este proceso (no afecta al servidor) para poder insertar historia.
- bulk_create NO dispara señales ni save() custom: los efectos que normalmente
  producen las señales (progreso, certificados, pesos SVD, ledger del saldo)
  se calculan aquí explícitamente y de forma consistente.
- Los videos de YouTube se VALIDAN con el endpoint oEmbed antes de asignarlos.
  Si alguno fue eliminado por su autor, la lección queda solo con su contenido
  escrito en vez de mostrar un reproductor roto.
- Las imágenes se descargan una sola vez a MEDIA_ROOT. La semilla de picsum es
  el slug del curso, así que la portada de un curso NO cambia entre corridas.
"""
import json
import random
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.users.models import (
    CustomUser, RechargeStatus, WalletRecharge, WalletTransaction,
)
from apps.catalog.models import Assignment, Category, Course, Lesson, Review
from apps.exams.models import Exam
from apps.memberships.models import MembershipPlan, PlanAudience, UserMembership
from apps.orders.models import Order, OrderItem, OrderStatus, Coupon, InstructorEarning
from apps.library.models import (
    Achievement, Certificate, Enrollment, LessonProgress, StudyStreak,
    UserAchievement, WishlistItem,
)
from apps.recommendations.models import InteractionType, UserCourseInteraction
from apps.analytics.models import NavigationLog, ConversionFunnel

from ._catalogo_demo import CURSOS
from ._portadas import generar_portada

SEED_DOMAIN = 'seed.demo'
SESSION_PREFIX = 'seed-'

CATEGORIES = [
    ('Programación', 'Lenguajes y fundamentos de programación'),
    ('Desarrollo Web', 'Frontend, backend y frameworks web'),
    ('Ciencia de Datos', 'Análisis de datos, estadística y visualización'),
    ('Inteligencia Artificial', 'Machine learning y modelos de IA'),
    ('Cloud y DevOps', 'Infraestructura, contenedores y despliegue'),
    ('Ciberseguridad', 'Seguridad ofensiva y defensiva'),
    ('Bases de Datos', 'Modelado, SQL y NoSQL'),
    ('Desarrollo Móvil', 'Aplicaciones Android e iOS'),
]

DOCENTES = [
    ('Carlos', 'Mendoza'), ('María', 'Salazar'), ('Andrés', 'Vera'),
    ('Lucía', 'Paredes'), ('Jorge', 'Cabrera'),
]

FIRST_NAMES = [
    'Juan', 'Ana', 'Luis', 'Carmen', 'Pedro', 'Sofía', 'Diego', 'Valeria', 'Miguel', 'Camila',
    'José', 'Daniela', 'Andrés', 'Gabriela', 'Fernando', 'Paola', 'Ricardo', 'Andrea', 'David', 'Karla',
]
LAST_NAMES = [
    'García', 'Rodríguez', 'Martínez', 'López', 'Sánchez', 'Pérez', 'Torres', 'Flores', 'Vargas', 'Castro',
    'Morales', 'Ortiz', 'Silva', 'Rojas', 'Mendez', 'Guerrero', 'Navarro', 'Campos', 'Vega', 'Ríos',
]


def _disable_auto_dates(*model_fields):
    """Desactiva auto_now_add/auto_now en este proceso para poder sembrar historia."""
    for model, field_names in model_fields:
        for field in model._meta.fields:
            if field.name in field_names:
                field.auto_now_add = False
                field.auto_now = False


# ---------------------------------------------------------------------------
# Videos: validación contra YouTube
# ---------------------------------------------------------------------------

def _consultar_video(video_id):
    """
    Pregunta a YouTube si el video existe y es público, y devuelve su título y
    autor reales. Se usa el endpoint oEmbed porque no requiere clave de API.
    Devuelve (video_id, ok, titulo, autor).
    """
    url = (f'https://www.youtube.com/oembed'
           f'?url=https://www.youtube.com/watch?v={video_id}&format=json')
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'seed-demo/1.0'})
        with urllib.request.urlopen(req, timeout=12) as r:
            d = json.loads(r.read())
            return video_id, True, d.get('title', ''), d.get('author_name', '')
    except Exception:
        return video_id, False, '', ''


def validar_videos(ids):
    """Valida en paralelo. Devuelve {video_id: (titulo, autor)} solo con los vivos."""
    vivos = {}
    with ThreadPoolExecutor(max_workers=10) as pool:
        for vid, ok, titulo, autor in pool.map(_consultar_video, ids):
            if ok:
                vivos[vid] = (titulo, autor)
    return vivos


# ---------------------------------------------------------------------------
# Imágenes: descarga a MEDIA_ROOT
# ---------------------------------------------------------------------------

def _descargar(url, destino):
    """Descarga si el archivo aún no existe. Devuelve True si quedó disponible."""
    if destino.exists() and destino.stat().st_size > 0:
        return True
    try:
        destino.parent.mkdir(parents=True, exist_ok=True)
        # nginx sirve /media como otro usuario: sin recorrido en el directorio
        # da 403 aunque el archivo sea legible (ver settings.MEDIA_ROOT).
        destino.parent.chmod(0o755)
        req = urllib.request.Request(url, headers={'User-Agent': 'seed-demo/1.0'})
        with urllib.request.urlopen(req, timeout=25) as r:
            datos = r.read()
        if len(datos) < 500:  # respuesta de error disfrazada
            return False
        destino.write_bytes(datos)
        return True
    except Exception:
        return False


def crear_portada(titulo, categoria, nivel, slug):
    """
    Portada del curso, GENERADA en vez de descargada.

    Las fuentes de fotos libres sin clave de API devuelven imágenes que no
    corresponden al tema: se probó picsum (aleatoria) y loremflickr (por
    etiquetas), y un curso de ciberseguridad terminaba ilustrado con la foto
    de un gato, además de traer marcas de agua. Una portada equivocada
    distrae más de lo que aporta.

    La portada generada usa el título real del curso y el color de su
    categoría, así que siempre corresponde, es determinista y no depende de
    ningún servicio externo.

    Course.cover_image es un URLField, por eso se devuelve la ruta /media/...
    completa y no la relativa al MEDIA_ROOT.
    """
    relativa = f'course_covers/{slug}.jpg'
    destino = Path(settings.MEDIA_ROOT) / relativa
    try:
        generar_portada(titulo, categoria, nivel, destino)
        return f'{settings.MEDIA_URL}{relativa}'
    except Exception:
        return ''


def descargar_avatar(semilla):
    """
    Foto de perfil determinista por usuario. A diferencia de la portada,
    CustomUser.avatar SÍ es un ImageField, así que se guarda la ruta relativa
    al MEDIA_ROOT (sin prefijo) y Django construye la URL con .url.
    """
    relativa = f'avatars/{semilla}.jpg'
    destino = Path(settings.MEDIA_ROOT) / relativa
    url = f'https://i.pravatar.cc/300?u={semilla}'
    return relativa if _descargar(url, destino) else ''


class Command(BaseCommand):
    help = 'Siembra ~5 años de datos históricos de demostración con crecimiento mes a mes.'

    def add_arguments(self, parser):
        parser.add_argument('--years', type=int, default=5)
        parser.add_argument('--flush', action='store_true', help='Borra el seed anterior antes de sembrar')
        parser.add_argument('--sin-media', action='store_true', dest='sin_media',
                            help='No descarga imágenes ni valida videos (para trabajar sin internet)')

    def handle(self, *args, **options):
        random.seed(42)  # Reproducible

        already = CustomUser.objects.filter(email__endswith='@' + SEED_DOMAIN).exists()
        if already and not options['flush']:
            self.stdout.write(self.style.WARNING(
                'Ya existe un seed anterior. Usa --flush para borrarlo y re-sembrar.'))
            return
        if options['flush']:
            self._flush()

        _disable_auto_dates(
            (Order, {'created_at', 'updated_at'}),
            (Enrollment, {'enrolled_at'}),
            (Review, {'created_at'}),
            (UserCourseInteraction, {'created_at'}),
            (WalletTransaction, {'created_at'}),
            (Certificate, {'issued_at'}),
            (WishlistItem, {'added_at'}),
            (Course, {'created_at', 'updated_at'}),
            (InstructorEarning, {'created_at'}),
            (WalletRecharge, {'created_at'}),
            (UserAchievement, {'earned_at'}),
            (UserMembership, {'started_at'}),
        )

        months = options['years'] * 12
        now = timezone.now()
        start = now - timedelta(days=months * 30)
        con_media = not options['sin_media']

        with transaction.atomic():
            courses = self._seed_catalog(start, con_media=con_media)
            self._seed_activity(courses, months, now, start)
            self._seed_recargas(now)
            self._seed_medallas()
            self._crear_usuarios_demo()

        self.stdout.write(self.style.SUCCESS('\nSeed completado:'))
        for label, qs in [
            ('Usuarios seed', CustomUser.objects.filter(email__endswith='@' + SEED_DOMAIN)),
            ('Cursos', Course.objects.all()),
            ('Órdenes', Order.objects.all()),
            ('Inscripciones', Enrollment.objects.all()),
            ('Certificados', Certificate.objects.all()),
            ('Reseñas', Review.objects.all()),
            ('Interacciones SVD', UserCourseInteraction.objects.all()),
            ('Logs de navegación', NavigationLog.objects.all()),
            ('Movimientos de saldo', WalletTransaction.objects.all()),
            ('Recargas de saldo', WalletRecharge.objects.all()),
            ('Exámenes', Exam.objects.all()),
            ('Medallas otorgadas', UserAchievement.objects.all()),
            ('Cursos con portada', Course.objects.exclude(cover_image='')),
            ('Lecciones con video', Lesson.objects.exclude(video_url='').exclude(video_url__isnull=True)),
        ]:
            self.stdout.write(f'  {label}: {qs.count()}')

        # Entrenar el modelo SVD con la historia recién sembrada
        from apps.recommendations.tasks import train_svd_and_update_recommendations
        train_svd_and_update_recommendations.delay()
        self.stdout.write(self.style.SUCCESS(
            '\nEntrenamiento SVD encolado en ml_queue (verifica en ~1 min con GET /api/recommendations/for-me/).'))

    # ------------------------------------------------------------------
    def _flush(self):
        self.stdout.write('Borrando seed anterior...')
        NavigationLog.objects.filter(session_id__startswith=SESSION_PREFIX).delete()
        ConversionFunnel.objects.filter(session_id__startswith=SESSION_PREFIX).delete()
        CustomUser.objects.filter(email__endswith='@' + SEED_DOMAIN).delete()
        slugs = [slugify(c[0]) for c in CURSOS]
        Course.objects.filter(slug__in=slugs).delete()

    # ------------------------------------------------------------------
    def _seed_recargas(self, now):
        """
        Historial de recargas a través de la pasarela simulada, incluyendo
        intentos rechazados: un historial donde todo salió bien no se parece
        a la realidad y no permite mostrar el manejo de errores.
        """
        usuarios = list(CustomUser.objects.filter(
            email__endswith='@' + SEED_DOMAIN, role_id='ALUMNO'
        ).order_by('id')[:400])
        if not usuarios:
            return

        motivos = [
            'La tarjeta fue rechazada por el banco emisor.',
            'Fondos insuficientes en la tarjeta.',
            'La tarjeta está vencida.',
        ]
        recargas, movimientos, saldos = [], [], {}

        for user in usuarios:
            if random.random() > 0.35:      # solo ~1 de cada 3 recarga alguna vez
                continue
            vida = max((now - user.date_joined).days, 1)
            for _ in range(random.choices([1, 2, 3], weights=[60, 30, 10])[0]):
                cuando = user.date_joined + timedelta(
                    days=random.randint(1, vida), hours=random.randint(8, 22))
                if cuando > now:
                    continue
                monto = Decimal(random.choice(['10.00', '25.00', '50.00', '100.00']))
                aprobada = random.random() < 0.82
                recargas.append(WalletRecharge(
                    user=user, amount=monto,
                    status_id=RechargeStatus.APPROVED if aprobada else RechargeStatus.DECLINED,
                    card_last4=f'{random.randint(0, 9999):04d}',
                    decline_reason='' if aprobada else random.choice(motivos),
                    reference=f'RCG-{uuid.uuid4().hex[:8].upper()}' if aprobada else '',
                    created_at=cuando, completed_at=cuando + timedelta(seconds=random.randint(20, 180)),
                ))
                if aprobada:
                    saldos[user.id] = saldos.get(user.id, user.balance) + monto
                    movimientos.append((user, monto, saldos[user.id], cuando,
                                        recargas[-1].reference))

        WalletRecharge.objects.bulk_create(recargas, batch_size=500)
        WalletTransaction.objects.bulk_create([
            WalletTransaction(
                user=u, transaction_type_id='RECHARGE', amount=monto,
                balance_after=saldo, created_at=cuando,
                description=f'Recarga de saldo — {ref}')
            for u, monto, saldo, cuando, ref in movimientos
        ], batch_size=500)

        # El saldo del usuario debe reflejar las recargas acreditadas
        for user in usuarios:
            if user.id in saldos:
                user.balance = saldos[user.id]
        CustomUser.objects.bulk_update(
            [u for u in usuarios if u.id in saldos], ['balance'], batch_size=500)

        aprobadas = sum(1 for r in recargas if r.status_id == RechargeStatus.APPROVED)
        self.stdout.write(
            f'  Recargas: {len(recargas)} ({aprobadas} aprobadas, '
            f'{len(recargas) - aprobadas} rechazadas)')

    # ------------------------------------------------------------------
    def _crear_usuarios_demo(self):
        """
        Las cuatro cuentas conocidas para recorrer la aplicación: administrador,
        docente, alumno y revisor.

        Se crean AQUÍ y no solo en reset_demo_data porque quien despliega corre
        `seed_demo_data` y esperaba encontrarlas: buscarlas y que no existan es
        un tropiezo innecesario. Se crean al final y sin historial, así quedan
        limpias para hacer el recorrido desde cero sin ensuciar las
        estadísticas del seed.
        """
        from apps.common.demo_accounts import CUENTAS, crear_cuentas_demo

        creadas = crear_cuentas_demo(log=lambda _: None)
        if creadas:
            self.stdout.write(f'  Cuentas de demostración creadas: {creadas}')
            for email, clave, _, _, _ in CUENTAS:
                self.stdout.write(f'    {email} / {clave}')

    # ------------------------------------------------------------------
    def _seed_medallas(self):
        """
        Otorga las medallas que corresponden al historial sembrado, con la
        fecha del hecho que las gatilló. Sin esto, las medallas aparecerían
        recién al abrir el perfil (el endpoint las re-evalúa) y todas
        llevarían la fecha de hoy, lo que delataría la simulación.
        """
        codigos = set(Achievement.objects.values_list('code', flat=True))
        if not codigos:
            return

        otorgadas = []
        vistos = set()

        def dar(user_id, codigo, cuando):
            if codigo in codigos and (user_id, codigo) not in vistos:
                vistos.add((user_id, codigo))
                otorgadas.append(UserAchievement(
                    user_id=user_id, achievement_id=codigo, earned_at=cuando))

        # Primera inscripción y cursos completados
        por_usuario = {}
        for e in Enrollment.objects.values('user_id', 'enrolled_at', 'is_completed'):
            d = por_usuario.setdefault(e['user_id'], {'primera': None, 'completados': 0, 'ultima': None})
            if d['primera'] is None or e['enrolled_at'] < d['primera']:
                d['primera'] = e['enrolled_at']
            if e['is_completed']:
                d['completados'] += 1
                if d['ultima'] is None or e['enrolled_at'] > d['ultima']:
                    d['ultima'] = e['enrolled_at']

        for user_id, d in por_usuario.items():
            dar(user_id, 'FIRST_ENROLLMENT', d['primera'])
            if d['completados'] >= 1:
                dar(user_id, 'FIRST_COURSE', d['ultima'] or d['primera'])
            if d['completados'] >= 3:
                dar(user_id, 'THREE_COURSES', d['ultima'] or d['primera'])
            if d['completados'] >= 5:
                dar(user_id, 'FIVE_COURSES', d['ultima'] or d['primera'])

        for c in Certificate.objects.values('enrollment__user_id', 'issued_at'):
            dar(c['enrollment__user_id'], 'FIRST_CERTIFICATE', c['issued_at'])

        for r in Review.objects.values('user_id', 'created_at'):
            dar(r['user_id'], 'FIRST_REVIEW', r['created_at'])

        for s in StudyStreak.objects.values('user_id', 'longest_streak'):
            marca = timezone.now() - timedelta(days=random.randint(30, 400))
            if s['longest_streak'] >= 7:
                dar(s['user_id'], 'STREAK_7', marca)
            if s['longest_streak'] >= 30:
                dar(s['user_id'], 'STREAK_30', marca)

        UserAchievement.objects.bulk_create(otorgadas, batch_size=1000, ignore_conflicts=True)
        self.stdout.write(f'  Medallas otorgadas: {len(otorgadas)}')

    # ------------------------------------------------------------------
    def _seed_catalog(self, start, con_media=True):
        self.stdout.write('Sembrando categorías, docentes y cursos...')

        categories = {}
        for name, desc in CATEGORIES:
            cat, _ = Category.objects.get_or_create(
                slug=slugify(name), defaults={'name': name, 'description': desc})
            categories[name] = cat

        # --- Docentes, con foto de perfil ---
        password = make_password('Demo1234!')
        docentes = []
        for i, (fn, ln) in enumerate(DOCENTES):
            correo = f'docente{i + 1}@{SEED_DOMAIN}'
            docentes.append(CustomUser(
                email=correo, password=password,
                first_name=fn, last_name=ln, role_id='DOCENTE',
                date_joined=start, is_email_verified=True,
                avatar=descargar_avatar(f'doc{i + 1}') if con_media else '',
            ))
        docentes = CustomUser.objects.bulk_create(docentes)
        self._dar_plan_docente(docentes, start)

        # --- Validación de los videos ANTES de asignarlos ---
        ids_video = {vid for _, _, _, _, _, _, _, lecs in CURSOS
                     for (_, _, vid, _) in lecs if vid}
        if con_media and ids_video:
            self.stdout.write(f'  Validando {len(ids_video)} videos con YouTube...')
            self.videos_vivos = validar_videos(ids_video)
            caidos = len(ids_video) - len(self.videos_vivos)
            self.stdout.write(
                f'  Videos válidos: {len(self.videos_vivos)} de {len(ids_video)}'
                + (f' ({caidos} ya no existen; esas lecciones quedan sin video)' if caidos else ''))
        else:
            self.videos_vivos = {}

        # --- Cursos ---
        courses = []
        for i, (titulo, categoria, nivel, precio, desc, resultados, requisitos, _lecs) in enumerate(CURSOS):
            # La mayoría existe desde el inicio; algunos se lanzaron después,
            # para que el catálogo no parezca creado todo el mismo día.
            created = start + timedelta(days=random.choice([0, 0, 0, 90, 180, 365, 540]))
            slug = slugify(titulo)
            courses.append(Course(
                title=titulo, slug=slug, description=desc,
                price=Decimal(precio), category=categories[categoria],
                instructor=docentes[i % len(docentes)],
                level_id=nivel, language='Español',
                requirements=requisitos, learning_outcomes=resultados,
                # La portada se genera siempre: no depende de internet, así que
                # --sin-media no la afecta (esa bandera es para los videos y avatares).
                cover_image=crear_portada(titulo, categoria, nivel, slug),
                is_active=True, status_id='PUBLISHED',
                created_at=created, updated_at=created, published_at=created,
            ))
        courses = Course.objects.bulk_create(courses)
        if con_media:
            con_portada = sum(1 for c in courses if c.cover_image)
            self.stdout.write(f'  Portadas descargadas: {con_portada} de {len(courses)}')

        # --- Lecciones, con su contenido propio ---
        lessons, con_video = [], 0
        for course, (*_, lecs) in zip(courses, CURSOS):
            for orden, (titulo_lec, minutos, vid, contenido) in enumerate(lecs, start=1):
                url = ''
                if vid and vid in self.videos_vivos:
                    url = f'https://www.youtube.com/watch?v={vid}'
                    con_video += 1
                    titulo_yt, autor = self.videos_vivos[vid]
                    # La atribución viaja con la lección: el reproductor la muestra
                    # bajo el video, y así queda claro de quién es el material.
                    contenido = (f'{contenido}\n\n'
                                 f'Video: «{titulo_yt}» — material de {autor}, '
                                 f'usado con fines educativos.')
                lessons.append(Lesson(
                    course=course, title=titulo_lec, order=orden,
                    duration_minutes=minutos, content=contenido, video_url=url,
                ))
        Lesson.objects.bulk_create(lessons)
        self.stdout.write(f'  {len(lessons)} lecciones ({con_video} con video)')

        self._seed_actividades()
        self._seed_promociones(courses)
        return courses

    # ------------------------------------------------------------------
    def _seed_actividades(self):
        """
        Las dos actividades evaluadas de cada curso (cuestionario y trabajo
        práctico). Se delega en `crear_actividades` en lugar de duplicar la
        lógica: ese comando también se ejecuta suelto en el servidor, sobre una
        base ya sembrada, y las dos rutas deben producir exactamente lo mismo.
        """
        from django.core.management import call_command
        call_command('crear_actividades', verbosity=0)
        self.stdout.write(
            f'  {Exam.objects.count()} cuestionarios y '
            f'{Assignment.objects.count()} trabajos prácticos creados')

    # ------------------------------------------------------------------
    def _seed_promociones(self, courses):
        """
        Deja algunos cursos en oferta para que el carrete de la portada tenga
        contenido desde el primer arranque. Las fechas de término se reparten
        para que la cuenta regresiva muestre plazos distintos y no todos
        vencan el mismo día.
        """
        OFERTAS = [
            ('machine-learning-con-scikit-learn', 40, 2),
            ('flutter-apps-multiplataforma', 35, 4),
            ('react-en-la-practica', 30, 3),
            ('docker-desde-cero', 30, 5),
            ('hacking-etico-y-pruebas-de-penetracion', 25, 7),
            ('sql-para-analisis-de-datos', 20, 10),
        ]
        por_slug = {c.slug: c in courses and c for c in courses}
        ahora = timezone.now()
        aplicadas = 0
        for slug, pct, dias in OFERTAS:
            course = por_slug.get(slug)
            if not course:
                continue
            course.promo_price = (
                course.price * Decimal(100 - pct) / Decimal(100)
            ).quantize(Decimal('0.01'))
            course.promo_until = ahora + timedelta(days=dias)
            course.save(update_fields=['promo_price', 'promo_until'])
            aplicadas += 1
        self.stdout.write(f'  {aplicadas} cursos en oferta (carrete de la portada)')

    # ------------------------------------------------------------------
    def _dar_plan_docente(self, docentes, start):
        """
        Sin un plan de docente activo, el instructor no tiene cupos y no puede
        publicar cursos. Se les asigna el plan de mayor nivel disponible para
        que el panel del docente tenga sentido desde el primer momento.
        """
        plan = (MembershipPlan.objects
                .filter(audience_id=PlanAudience.DOCENTE, is_active=True)
                .order_by('-course_slots').first())
        if not plan:
            return
        UserMembership.objects.bulk_create([
            UserMembership(
                user=d, plan=plan, audience_id=PlanAudience.DOCENTE,
                status_id='ACTIVE', started_at=start,
                expires_at=timezone.now() + timedelta(days=365),
                auto_renew=True,
            ) for d in docentes
        ])
        self.stdout.write(f'  Plan «{plan.name}» activado para {len(docentes)} docentes')

    # ------------------------------------------------------------------
    def _seed_activity(self, courses, months, now, start):
        self.stdout.write(f'Sembrando {months} meses de actividad (crecimiento ~4.5% mensual)...')

        weights = dict(InteractionType.objects.values_list('code', 'weight'))
        coupon, _ = Coupon.objects.get_or_create(
            code='BIENVENIDA20', defaults={'discount_pct': Decimal('20.00'), 'is_active': True})
        password = make_password('Demo1234!')
        lessons_by_course = {}
        for lesson in Lesson.objects.filter(course__in=courses).order_by('order'):
            lessons_by_course.setdefault(lesson.course_id, []).append(lesson)

        users, wallet_txs, orders_data = [], [], []
        user_counter = 0

        # 1) Crear usuarios por mes con crecimiento compuesto
        for month in range(months):
            month_start = start + timedelta(days=month * 30)
            new_users = max(1, round(4 * (1.045 ** month)))
            for _ in range(new_users):
                user_counter += 1
                joined = month_start + timedelta(
                    days=random.randint(0, 29), hours=random.randint(8, 22))
                if joined > now:
                    joined = now - timedelta(hours=1)
                users.append(CustomUser(
                    email=f'alumno{user_counter}@{SEED_DOMAIN}', password=password,
                    first_name=random.choice(FIRST_NAMES), last_name=random.choice(LAST_NAMES),
                    role_id='ALUMNO', date_joined=joined, is_email_verified=True,
                ))
        users = CustomUser.objects.bulk_create(users, batch_size=500)
        self.stdout.write(f'  {len(users)} alumnos creados. Generando compras y actividad...')

        # 2) Actividad por usuario
        enrollments, progresses, certificates, reviews = [], [], [], []
        interactions, nav_logs, funnels, wishlist_items, streaks = [], [], [], [], []
        purchase_count_by_course = {}

        available = [c for c in courses]
        for user in users:
            balance = Decimal('500.00')
            wallet_txs.append(WalletTransaction(
                user=user, transaction_type_id='WELCOME', amount=Decimal('500.00'),
                balance_after=balance, description='Saldo simulado de bienvenida',
                created_at=user.date_joined))

            lifetime_days = max((now - user.date_joined).days, 1)

            # Navegación exploratoria (con o sin compra)
            browsed = random.sample(available, k=min(random.randint(2, 6), len(available)))
            for course in browsed:
                seen_at = user.date_joined + timedelta(
                    days=random.randint(0, lifetime_days), minutes=random.randint(0, 720))
                if seen_at > now:
                    seen_at = now - timedelta(hours=1)
                if course.created_at > seen_at:
                    continue
                session = SESSION_PREFIX + uuid.uuid4().hex
                interactions.append(UserCourseInteraction(
                    user=user, course=course, interaction_type_id='VIEW',
                    weight=weights['VIEW'], created_at=seen_at))
                nav_logs.append(NavigationLog(
                    user=user, session_id=session, event_type='COURSE_VIEW',
                    metadata={'course_id': course.id}, timestamp=seen_at))
                funnels.append(ConversionFunnel(
                    session_id=session, user=user, stage='VIEW',
                    course_id=course.id, reached_at=seen_at))

                # Carritos abandonados: agregan al carrito (y a veces llegan al
                # checkout) pero no compran — así el funnel tiene caídas reales
                if random.random() < 0.25:
                    cart_at = seen_at + timedelta(minutes=random.randint(2, 40))
                    interactions.append(UserCourseInteraction(
                        user=user, course=course, interaction_type_id='CART_ADD',
                        weight=weights['CART_ADD'], created_at=cart_at))
                    nav_logs.append(NavigationLog(
                        user=user, session_id=session, event_type='CART_ADD',
                        metadata={'course_id': course.id}, timestamp=cart_at))
                    funnels.append(ConversionFunnel(
                        session_id=session, user=user, stage='CART',
                        course_id=course.id, reached_at=cart_at))
                    if random.random() < 0.40:
                        chk_at = cart_at + timedelta(minutes=random.randint(1, 15))
                        nav_logs.append(NavigationLog(
                            user=user, session_id=session, event_type='CHECKOUT_START',
                            metadata={'course_id': course.id}, timestamp=chk_at))
                        funnels.append(ConversionFunnel(
                            session_id=session, user=user, stage='CHECKOUT',
                            course_id=course.id, reached_at=chk_at))

            if random.random() < 0.30:  # Búsquedas
                nav_logs.append(NavigationLog(
                    user=user, session_id=SESSION_PREFIX + uuid.uuid4().hex,
                    event_type='SEARCH', metadata={'search_term': random.choice(
                        ['python', 'react', 'sql', 'docker', 'machine learning', 'excel'])},
                    timestamp=user.date_joined + timedelta(days=random.randint(0, lifetime_days))))

            # Wishlist (20% de usuarios)
            if random.random() < 0.20:
                for course in random.sample(browsed, k=min(random.randint(1, 2), len(browsed))):
                    added = user.date_joined + timedelta(days=random.randint(0, lifetime_days))
                    if added > now or course.created_at > added:
                        continue
                    wishlist_items.append(WishlistItem(user=user, course=course, added_at=added))
                    interactions.append(UserCourseInteraction(
                        user=user, course=course, interaction_type_id='WISHLIST',
                        weight=weights['WISHLIST'], created_at=added))

            # Compras: 30% solo mira; el resto hace 1-3 órdenes
            if random.random() < 0.30:
                continue
            n_orders = random.choices([1, 2, 3], weights=[55, 30, 15])[0]
            owned = set()
            for _ in range(n_orders):
                order_at = user.date_joined + timedelta(
                    days=random.randint(0, lifetime_days), hours=random.randint(0, 12))
                if order_at > now:
                    order_at = now - timedelta(hours=random.randint(1, 48))
                candidates = [c for c in available
                              if c.id not in owned and c.created_at <= order_at]
                if not candidates:
                    continue
                bought = random.sample(candidates, k=min(random.randint(1, 2), len(candidates)))
                total = sum(c.price for c in bought)
                use_coupon = random.random() < 0.15
                discount = (total * Decimal('0.20')).quantize(Decimal('0.01')) if use_coupon else Decimal('0.00')
                final_total = total - discount
                if final_total > balance:
                    continue
                balance -= final_total

                session = SESSION_PREFIX + uuid.uuid4().hex
                orders_data.append({
                    'user': user, 'total': final_total, 'discount': discount,
                    'coupon': coupon if use_coupon else None, 'at': order_at,
                    'courses': bought, 'session': session,
                })
                wallet_txs.append(WalletTransaction(
                    user=user, transaction_type_id='PURCHASE', amount=-final_total,
                    balance_after=balance, description='Compra de cursos',
                    created_at=order_at))

                for course in bought:
                    owned.add(course.id)
                    purchase_count_by_course[course.id] = purchase_count_by_course.get(course.id, 0) + 1
                    interactions.append(UserCourseInteraction(
                        user=user, course=course, interaction_type_id='PURCHASE',
                        weight=weights['PURCHASE'], created_at=order_at))
                    # Funnel completo de la sesión de compra
                    for minutes_ago, event, stage in [
                            (30, 'COURSE_VIEW', 'VIEW'), (20, 'CART_ADD', 'CART'),
                            (5, 'CHECKOUT_START', 'CHECKOUT'), (0, 'PURCHASE', 'PURCHASE')]:
                        at = order_at - timedelta(minutes=minutes_ago)
                        nav_logs.append(NavigationLog(
                            user=user, session_id=session, event_type=event,
                            metadata={'course_id': course.id}, timestamp=at))
                        funnels.append(ConversionFunnel(
                            session_id=session, user=user, stage=stage,
                            course_id=course.id, reached_at=at))

                    # Inscripción + progreso
                    course_lessons = lessons_by_course.get(course.id, [])
                    roll = random.random()
                    if roll < 0.25:
                        pct = 100.0
                    elif roll < 0.65:
                        pct = round(random.uniform(20, 85), 2)
                    else:
                        pct = round(random.uniform(0, 20), 2)
                    n_done = round(len(course_lessons) * pct / 100)
                    pct = round(n_done / len(course_lessons) * 100, 2) if course_lessons else 0.0

                    enrollment = Enrollment(
                        user=user, course=course, enrollment_type_id='PURCHASED',
                        enrolled_at=order_at, progress_percentage=pct,
                        is_completed=(pct >= 100.0))
                    enrollments.append(enrollment)

                    last_done_at = order_at
                    for i, lesson in enumerate(course_lessons[:n_done]):
                        last_done_at = order_at + timedelta(days=(i + 1) * random.randint(1, 4))
                        if last_done_at > now:
                            last_done_at = now - timedelta(hours=1)
                        progresses.append(LessonProgress(
                            enrollment=enrollment, lesson=lesson, is_completed=True,
                            watch_percentage=100.0, completed_at=last_done_at))

                    if pct >= 100.0 and course_lessons:
                        hours = (Decimal(sum(l.duration_minutes for l in course_lessons))
                                 / Decimal('60')).quantize(Decimal('0.01'))
                        certificates.append(Certificate(
                            enrollment=enrollment, issued_at=last_done_at,
                            student_name=f'{user.first_name} {user.last_name}',
                            course_title=course.title, course_duration_hours=hours,
                            completed_at=last_done_at))
                        if random.random() < 0.45:
                            reviews.append(Review(
                                user=user, course=course,
                                rating=random.choice([5, 5, 5, 4, 4, 3]),
                                comment=random.choice([
                                    'Excelente curso, muy completo.', 'Buen contenido y bien explicado.',
                                    'Me sirvió mucho para mi trabajo.', 'Recomendado, el instructor explica claro.',
                                    'Buen curso aunque algunas partes van rápido.']),
                                created_at=last_done_at + timedelta(days=1)))
                            interactions.append(UserCourseInteraction(
                                user=user, course=course, interaction_type_id='REVIEW',
                                weight=weights['REVIEW'], created_at=last_done_at + timedelta(days=1)))

            # Rachas para usuarios con actividad reciente
            if random.random() < 0.10:
                current = random.randint(1, 14)
                streaks.append(StudyStreak(
                    user=user, current_streak=current,
                    longest_streak=max(current, random.randint(1, 30)),
                    last_activity_date=now.date()))

        # 3) Insertar todo en bloque
        self.stdout.write('  Insertando en la base de datos...')
        orders = Order.objects.bulk_create([
            Order(user=od['user'], status_id=OrderStatus.COMPLETED, total_amount=od['total'],
                  coupon=od['coupon'], discount_amount=od['discount'],
                  card_last4=f'{random.randint(0, 9999):04d}',
                  transaction_reference=f'DEMO-SEED-{i}',
                  created_at=od['at'], updated_at=od['at'])
            for i, od in enumerate(orders_data)
        ], batch_size=500)
        order_items = OrderItem.objects.bulk_create([
            OrderItem(order=order, course=course, price_at_purchase=course.price)
            for order, od in zip(orders, orders_data) for course in od['courses']
        ], batch_size=500)
        # Comisión histórica del docente por cada venta (70/30)
        item_dates = {order.id: od['at'] for order, od in zip(orders, orders_data)}
        InstructorEarning.objects.bulk_create([
            InstructorEarning(
                order_item=item, instructor_id=item.course.instructor_id, course=item.course,
                gross_amount=item.price_at_purchase,
                commission_rate=InstructorEarning.INSTRUCTOR_RATE,
                net_amount=(item.price_at_purchase * InstructorEarning.INSTRUCTOR_RATE).quantize(Decimal('0.01')),
                created_at=item_dates[item.order_id])
            for item in order_items if item.course.instructor_id
        ], batch_size=500)

        Enrollment.objects.bulk_create(enrollments, batch_size=500)
        LessonProgress.objects.bulk_create(progresses, batch_size=1000)
        Certificate.objects.bulk_create(certificates, batch_size=500)
        Review.objects.bulk_create(reviews, batch_size=500)
        WishlistItem.objects.bulk_create(wishlist_items, batch_size=500)
        StudyStreak.objects.bulk_create(streaks, batch_size=500)
        UserCourseInteraction.objects.bulk_create(interactions, batch_size=1000)
        NavigationLog.objects.bulk_create(nav_logs, batch_size=1000)
        ConversionFunnel.objects.bulk_create(funnels, batch_size=1000)
        WalletTransaction.objects.bulk_create(wallet_txs, batch_size=1000)

        # Saldo final consistente con el ledger
        for user in users:
            last_tx = max((t for t in wallet_txs if t.user_id == user.id),
                          key=lambda t: t.created_at, default=None)
            if last_tx:
                user.balance = last_tx.balance_after
        CustomUser.objects.bulk_update(users, ['balance'], batch_size=500)

        # Best sellers reales según las compras sembradas
        top3 = sorted(purchase_count_by_course, key=purchase_count_by_course.get, reverse=True)[:3]
        Course.objects.filter(id__in=top3).update(is_best_seller=True)

        coupon.times_used = Order.objects.filter(coupon=coupon).count()
        coupon.save(update_fields=['times_used'])
