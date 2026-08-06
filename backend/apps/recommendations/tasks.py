import logging
import numpy as np
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(queue='ml_queue', bind=True, max_retries=3)
def train_svd_and_update_recommendations(self):
    """
    Tarea de entrenamiento nocturno del modelo SVD (Singular Value Decomposition).
    Se ejecuta en la cola AISLADA 'ml_queue' (concurrency=1) para evitar
    errores de OOM Killer al procesar matrices grandes con scikit-learn.

    Flujo:
    1. Extrae todas las interacciones (user_id, course_id, weight) de la BD.
    2. Construye la matriz de utilidad usuario x curso.
    3. Aplica SVD truncado para descomponer la matriz en factores latentes.
    4. Reconstruye la matriz completa con predicciones de rating.
    5. Guarda las recomendaciones top-N por usuario en RecommendationCache.
    """
    try:
        from sklearn.decomposition import TruncatedSVD
        from scipy.sparse import csr_matrix
        from django.contrib.auth import get_user_model
        from apps.recommendations.models import UserCourseInteraction, RecommendationCache
        from apps.catalog.models import Course

        User = get_user_model()

        logger.info("Iniciando entrenamiento SVD de recomendaciones...")

        # --- 1. Extracción de datos ---
        interactions = list(
            UserCourseInteraction.objects.values_list('user_id', 'course_id', 'weight')
        )

        if len(interactions) < 10:
            logger.warning("Datos insuficientes para el entrenamiento SVD (mínimo 10 interacciones).")
            return

        # --- 2. Construcción de la matriz de utilidad ---
        user_ids = sorted(set(i[0] for i in interactions))
        course_ids = sorted(set(i[1] for i in interactions))

        user_index = {uid: idx for idx, uid in enumerate(user_ids)}
        course_index = {cid: idx for idx, cid in enumerate(course_ids)}

        rows = [user_index[i[0]] for i in interactions]
        cols = [course_index[i[1]] for i in interactions]
        data = [i[2] for i in interactions]

        utility_matrix = csr_matrix(
            (data, (rows, cols)),
            shape=(len(user_ids), len(course_ids))
        )

        # --- 3. Aplicar SVD Truncado ---
        # n_components: número de factores latentes (temas ocultos).
        # Valor conservador para evitar sobreajuste con pocos datos.
        n_components = min(20, len(course_ids) - 1, len(user_ids) - 1)
        if n_components < 2:
            logger.warning("No hay suficientes usuarios o cursos para SVD.")
            return

        svd = TruncatedSVD(n_components=n_components, random_state=42)
        user_factors = svd.fit_transform(utility_matrix)
        course_factors = svd.components_  # shape: (n_components, n_courses)

        # --- 4. Reconstruir la matriz completa de predicciones ---
        predicted_ratings = np.dot(user_factors, course_factors)

        # IDs de cursos activos en la plataforma
        active_course_ids = list(Course.objects.filter(is_active=True, status_id='PUBLISHED').values_list('id', flat=True))

        # --- 5. Guardar recomendaciones por usuario ---
        TOP_N = 10  # Número máximo de recomendaciones por usuario

        updated_count = 0
        for user_idx, user_id in enumerate(user_ids):
            # Obtener cursos ya interactuados por el usuario (para excluirlos)
            interacted_course_ids = set(
                i[1] for i in interactions if i[0] == user_id
            )

            # Calcular scores predichos para cursos activos NO interactuados
            scored_courses = []
            for course_id in active_course_ids:
                if course_id in interacted_course_ids:
                    continue  # No recomendar lo que ya conoce
                if course_id in course_index:
                    score = predicted_ratings[user_idx][course_index[course_id]]
                    scored_courses.append((course_id, score))

            # Ordenar por score descendente y tomar el top N
            top_courses = sorted(scored_courses, key=lambda x: x[1], reverse=True)[:TOP_N]
            top_course_ids = [c[0] for c in top_courses]

            RecommendationCache.objects.update_or_create(
                user_id=user_id,
                defaults={'recommended_course_ids': top_course_ids}
            )
            updated_count += 1

        logger.info(f"SVD completado. Recomendaciones actualizadas para {updated_count} usuarios.")

    except Exception as exc:
        logger.error(f"Error en el entrenamiento SVD: {exc}")
        raise self.retry(exc=exc, countdown=60 * 10)  # Reintentar en 10 minutos
