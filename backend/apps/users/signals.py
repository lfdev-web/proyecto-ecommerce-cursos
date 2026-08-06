from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import TeacherApplication, TeacherApplicationStatus, Role


@receiver(post_save, sender=TeacherApplication)
def promote_user_on_approval(sender, instance, **kwargs):
    """
    Cuando una solicitud de docente queda APROBADA, el usuario pasa a rol DOCENTE.
    Idempotente: si el usuario ya es DOCENTE (o ADMIN) no hace nada.
    """
    if instance.status_id != TeacherApplicationStatus.APPROVED:
        return

    user = instance.user
    if user.role_id not in (Role.DOCENTE, Role.ADMIN):
        user.role_id = Role.DOCENTE
        user.save(update_fields=['role'])
