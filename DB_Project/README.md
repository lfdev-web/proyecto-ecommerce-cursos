# DB_Project — Estructura de la base de datos (PostgreSQL 17)

Scripts DDL de las **50 tablas** del proyecto E-Commerce de Cursos Tecnológicos,
con nombres de tablas, columnas, restricciones e índices **en español**.

La estructura (tipos de datos, claves primarias, claves foráneas, restricciones
UNIQUE e índices) es idéntica a la base real del proyecto (`ecommerce_cursos_db`,
gestionada por Django en Docker); solo se tradujeron los nombres para la presentación.

> Esta carpeta es **solo para presentación/documentación**. El proyecto no usa
> estos scripts: la base real se gestiona con las migraciones de Django.

## Contenido (ejecutar en este orden)

| # | Script | Módulo | Tablas |
|---|--------|--------|--------|
| 01 | `01_usuarios.sql` | Usuarios, saldo, recargas y postulación a docente | 10 |
| 02 | `02_catalogo.sql` | Catálogo de cursos y aprobación | 8 |
| 03 | `03_ordenes.sql` | Carrito, órdenes, cupones y ganancias | 7 |
| 04 | `04_membresias.sql` | Planes y suscripciones | 7 |
| 05 | `05_biblioteca.sql` | Inscripciones, progreso, certificados y medallas | 8 |
| 06 | `06_examenes.sql` | Examen final, intentos y respuestas | 5 |
| 07 | `07_recomendaciones.sql` | Motor de recomendaciones (SVD) | 3 |
| 08 | `08_analitica.sql` | Navegación y embudo de conversión | 2 |

**Total: 50 tablas, 66 claves foráneas y 26 restricciones UNIQUE.**

El orden importa: cada script referencia tablas creadas en los anteriores.

## Verificación

Los scripts fueron ejecutados en una base limpia de PostgreSQL 17 y el resultado
se comparó contra la base real, columna por columna:

| Comprobación | Resultado |
|---|---|
| Los 8 scripts ejecutan en orden | Sin errores |
| Número de tablas | 50 = 50 |
| Número de columnas | 308 = 308 |
| Restricciones UNIQUE | 26 = 26 |
| Tipo de dato y nulabilidad en cada posición | **50 de 50 tablas coinciden exactamente** |
| Claves foráneas | 66 vs 68 (ver nota abajo) |

## Cómo montarla en pgAdmin 4 (y generar el MER)

1. Crear una base de datos nueva, por ejemplo `ecommerce_cursos_presentacion`.
2. Abrir el **Query Tool** sobre esa base y ejecutar los 8 scripts **en orden (01 → 08)**.
3. Clic derecho sobre la base → **Generate ERD** → se genera el diagrama
   entidad-relación automáticamente con las 50 tablas y sus relaciones.

## Un detalle de diseño: tablas de catálogo con clave natural

De las 50 tablas, **15 son catálogos** (roles, estados, tipos, niveles). Todas
usan una clave primaria natural — el código en texto — en lugar de un `id`
numérico:

```sql
CREATE TABLE public.estados_curso (
    codigo character varying(20) PRIMARY KEY,   -- 'PUBLICADO', 'BORRADOR'...
    nombre character varying(50) NOT NULL,
    descripcion text NOT NULL
);
```

La ventaja es que al consultar la base el valor se lee directamente
(`cursos.estado = 'PUBLICADO'`) sin necesidad de un JOIN para saber qué
significa un `estado_id = 3`. Es la razón por la que estas 14 tablas no tienen
columna `id`.

Los catálogos son: `roles`, `tipos_transaccion_saldo`, `estados_recarga`,
`estados_solicitud_docente`, `niveles_curso`, `estados_curso`,
`estados_solicitud_cupo`, `estados_orden`, `ciclos_facturacion`,
`audiencias_plan`, `niveles_plan`, `estados_membresia`, `tipos_inscripcion`,
`medallas` y `tipos_interaccion`.

## Equivalencia con la base real (nombres generados por Django)

| Nombre en la presentación | Nombre real en `ecommerce_cursos_db` |
|---|---|
| **Usuarios** | |
| roles | users_role |
| usuarios | users_customuser |
| usuarios_grupos | users_customuser_groups |
| usuarios_permisos | users_customuser_user_permissions |
| tipos_transaccion_saldo | users_wallettransactiontype |
| transacciones_saldo | users_wallettransaction |
| estados_recarga | users_rechargestatus |
| recargas_saldo | users_walletrecharge |
| estados_solicitud_docente | users_teacherapplicationstatus |
| solicitudes_docente | users_teacherapplication |
| **Catálogo** | |
| niveles_curso | catalog_courselevel |
| estados_curso | catalog_coursestatus |
| categorias | catalog_category |
| cursos | catalog_course |
| lecciones | catalog_lesson |
| resenas | catalog_review |
| estados_solicitud_cupo | catalog_slotrequeststatus |
| solicitudes_cupo | catalog_courseslotrequest |
| **Órdenes** | |
| estados_orden | orders_orderstatus |
| carritos | orders_cart |
| carrito_items | orders_cartitem |
| cupones | orders_coupon |
| ordenes | orders_order |
| orden_items | orders_orderitem |
| ganancias_docente | orders_instructorearning |
| **Membresías** | |
| ciclos_facturacion | memberships_billingcycle |
| audiencias_plan | memberships_planaudience |
| niveles_plan | memberships_plantier |
| estados_membresia | memberships_membershipstatus |
| planes_membresia | memberships_membershipplan |
| membresias_usuario | memberships_usermembership |
| pagos_membresia | memberships_membershippayment |
| **Biblioteca** | |
| tipos_inscripcion | library_enrollmenttype |
| inscripciones | library_enrollment |
| progreso_lecciones | library_lessonprogress |
| certificados | library_certificate |
| lista_deseos | library_wishlistitem |
| rachas_estudio | library_studystreak |
| medallas | library_achievement |
| medallas_usuario | library_userachievement |
| **Exámenes** | |
| examenes | exams_exam |
| preguntas | exams_question |
| opciones_respuesta | exams_answeroption |
| intentos_examen | exams_examattempt |
| respuestas_intento | exams_attemptanswer |
| **Recomendaciones** | |
| tipos_interaccion | recommendations_interactiontype |
| interacciones_usuario_curso | recommendations_usercourseinteraction |
| cache_recomendaciones | recommendations_recommendationcache |
| **Analítica** | |
| registros_navegacion | analytics_navigationlog |
| embudo_conversion | analytics_conversionfunnel |

## Notas

- **Las 2 claves foráneas de diferencia**: en la base real,
  `usuarios_grupos.grupo_id` y `usuarios_permisos.permiso_id` referencian tablas
  internas de Django (`auth_group`, `auth_permission`). Aquí se omiten esas 2 FK
  para que los scripts corran de forma independiente; las columnas sí existen.
  Por eso el total es 66 y no 68.
- **Índices**: se incluyen los que sirven a consultas reales (claves foráneas y
  los compuestos del dashboard). Se omiten los `varchar_pattern_ops` que Django
  crea automáticamente junto a cada índice de texto, porque solo sirven para
  búsquedas con `LIKE` y duplicarían la lista sin aportar al diagrama.
- La base real contiene además **15 tablas de infraestructura** (autenticación de
  Django, sesiones, Celery Beat, blacklist de JWT) que no forman parte del diseño
  propio y por eso no se incluyen. En total la base real tiene 63 tablas.
