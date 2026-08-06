# Siembra del catálogo de medallas (lookup table), igual que los demás catálogos:
# los códigos son estables (los usa achievements.py); nombre/ícono/orden son
# editables desde el admin sin tocar código.
from django.db import migrations

ACHIEVEMENTS = [
    ('FIRST_ENROLLMENT', 'Primer paso', 'Te inscribiste en tu primer curso', '🚀', 10),
    ('FIRST_COURSE', 'Meta cumplida', 'Completaste tu primer curso al 100%', '🎯', 20),
    ('THREE_COURSES', 'En racha', 'Completaste 3 cursos', '🥉', 30),
    ('FIVE_COURSES', 'Imparable', 'Completaste 5 cursos', '🥇', 40),
    ('FIRST_CERTIFICATE', 'Certificado', 'Obtuviste tu primer certificado', '📜', 50),
    ('EXAM_PASSED', 'Aprobado', 'Aprobaste un examen final', '✅', 60),
    ('PERFECT_EXAM', 'Puntaje perfecto', 'Aprobaste un examen con el 100% de la nota', '💯', 70),
    ('STREAK_7', 'Semana constante', 'Estudiaste 7 días seguidos', '🔥', 80),
    ('STREAK_30', 'Hábito de hierro', 'Estudiaste 30 días seguidos', '⚡', 90),
    ('FIRST_REVIEW', 'Voz de la comunidad', 'Escribiste tu primera reseña', '💬', 100),
]


def seed_achievements(apps, schema_editor):
    Achievement = apps.get_model('library', 'Achievement')
    for code, name, description, icon, sort_order in ACHIEVEMENTS:
        Achievement.objects.update_or_create(
            code=code,
            defaults={'name': name, 'description': description, 'icon': icon, 'sort_order': sort_order},
        )


def unseed_achievements(apps, schema_editor):
    Achievement = apps.get_model('library', 'Achievement')
    Achievement.objects.filter(code__in=[a[0] for a in ACHIEVEMENTS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0008_achievement_userachievement'),
    ]

    operations = [
        migrations.RunPython(seed_achievements, unseed_achievements),
    ]
