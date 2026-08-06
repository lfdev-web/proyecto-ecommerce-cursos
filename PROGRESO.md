# Progreso del proyecto — E-Commerce Inteligente de Cursos Tecnológicos

> Este archivo existe para que cualquier sesión nueva (con o sin memoria de la conversación anterior) pueda ponerse al día rápido. Si retomas este proyecto con Claude Code, pide que lea este archivo primero.

## Qué es el proyecto

Plataforma e-commerce de cursos tecnológicos para el mercado ecuatoriano. Proyecto universitario (sexto semestre). Modelo de negocio "La Empresa Nunca Pierde": prioriza LTV mediante membresías, recomendaciones ML (SVD) y venta cruzada.

- **Plazo:** ~3-4 semanas desde el inicio de esta fase de construcción.
- **Testing:** automatizado NO está en el alcance — lo valida un revisor externo (profesor/ingeniero) manualmente.
- **Deploy:** el usuario tiene servidor y dominio propios; el trabajo aquí es dejar Docker/Django listos para ese deploy, no desplegar nosotros.
- **Documentación:** no se exige PRD/TRD formal, solo un README + decisiones técnicas que sustenten el qué/cómo/por qué (pendiente de escribir, dejarlo para cuando el proyecto esté más maduro).

## Stack

- **Backend:** Django 5 + DRF, PostgreSQL 17, Redis, Celery (colas `default` y `ml_queue` aislada), JWT (simplejwt), WeasyPrint (PDFs), scikit-learn (SVD), drf-spectacular (Swagger en `/api/schema/swagger/`). Todo dockerizado.
- **Frontend:** React 19 + Vite, sin Tailwind (requisito explícito) — actualmente CSS vanilla con variables. **Ver nota de diseño abajo.**
- **Apps backend:** users, catalog, orders, recommendations, library, memberships, analytics, common.

## Decisiones clave ya tomadas (no las vuelvas a preguntar)

1. **Checkout combina Luhn + saldo simulado**, no se reemplaza uno por el otro. Cada usuario nace con **$500 fijos, sin recarga**.
2. **Docente tiene pantallas propias en el frontend**, más simples que las del alumno.
3. **Búsqueda de cursos por texto** — incluida, no es opcional.
4. **No se construye un panel superadmin CRUD custom.** Django Admin (`/admin/`) ya cubre casi todo el CRUD. Solo se construye en React el **dashboard de analítica** (gráficos), que Django Admin no puede mostrar bien.
5. **Recomendaciones (SVD)**: el pipeline de ML en `apps/recommendations/tasks.py` es real (TruncatedSVD), no scaffolding. Se reentrena cada noche a las 3am vía Celery Beat (ya configurado en `settings.py`).
6. **Certificados**: simulados, con PDF real generado por WeasyPrint, emitidos automáticamente vía señal al llegar al 100% de un curso.
7. **Cupones y referidos**: sistema de códigos de descuento (`Coupon`) + programa de referidos ($10 de bono simulado para ambas partes) ya implementado.
8. **Udemy se usa como referencia de estructura de pantallas, NO de diseño visual.**
9. Ver el plan completo con las 4 fases en `C:\Users\leonp\.claude\plans\floofy-honking-snowflake.md` (en esta misma máquina, fuera del repo).

## ⚠️ Nota importante sobre el diseño actual

El frontend actual es **funcional pero con una estética placeholder** (glassmorphism oscuro, gradiente morado/azul, iconos con emojis) que el usuario ya señaló que se ve "genérica de IA" y quiere rediseñar. **No asumas que el diseño actual es el definitivo.** La lógica de las páginas (qué datos muestran, qué llamadas hacen al backend) se puede mantener; lo que probablemente cambie es CSS, tipografía, paleta de colores y los iconos/emojis por algo más profesional (posiblemente un set de iconos SVG reales en vez de emojis).

## 🔶 SESIÓN 2026-07-14 — Rediseño de la BD por feedback del revisor (EN CURSO)

El revisor de la BD pidió: (a) certificados relacionados con usuario/tiempo del curso, (b) sistema de exámenes online con tiempo, (c) valores tipo rol/estado como **tablas catálogo** (lookup tables) con FK. Se acordó con el usuario el **paquete completo** (~38 tablas). Referencias validadas: Moodle (quiz→attempts→questions), Redgate e-learning data model.

### ✅ Hecho y verificado (migraciones aplicadas, `manage.py check` limpio, catálogo y login responden)

1. **8 tablas catálogo** con FK real y valores sembrados por migración de datos: `Role`, `WalletTransactionType` (users), `CourseLevel` (catalog), `OrderStatus` (orders), `BillingCycle`, `MembershipStatus` (memberships), `EnrollmentType` (library), `InteractionType` con columna `weight` (recommendations — el peso SVD ahora vive en la BD, ya no hardcodeado).
   - Patrón: PK natural `code` varchar + `db_column` conserva el nombre de columna original → el código usa `campo_id == 'CODIGO'`. Los TextChoices fueron eliminados.
   - **Analytics (EventType, FunnelStage) se dejó a propósito como texto**: tablas de log de alto volumen, defensa: decisión de rendimiento deliberada.
2. **App `apps.exams` completa (backend)**: `Exam` (1:1 curso, tiempo límite, nota mínima, máx. intentos), `Question`, `AnswerOption` (is_correct nunca viaja al cliente), `ExamAttempt` (tiempo validado server-side con gracia de 30s; expirado = nota 0), `AttemptAnswer`. Endpoints: `GET /api/exams/course/<id>/` (info+intentos), `POST .../start/` (exige 100% progreso), `POST /api/exams/attempts/<id>/submit/` (califica). Admin con inlines.
3. **Regla de certificación nueva**: 100% de lecciones **+ aprobar el examen final si el curso tiene uno activo** (signals.py). Al aprobar el examen se emite el certificado automáticamente.
4. **Snapshot histórico en `Certificate`**: student_name, course_title, course_duration_hours, completed_at — se llenan al emitir; los certificados viejos se rellenaron por migración de datos; el PDF ahora renderiza desde el snapshot.
5. **Auditoría en `Order`**: coupon (FK), discount_amount, card_last4, transaction_reference (antes no se registraba qué cupón/tarjeta se usó).
6. **`WalletTransaction` (libro mayor del saldo)**: cada cambio del balance (bienvenida $500, compras, membresías, bonos referido) queda registrado con tipo, monto con signo y saldo resultante. Helper: `record_wallet_transaction()` en users/models.py.
7. **Curso enriquecido**: level (FK a CourseLevel), language, cover_image, requirements, learning_outcomes — expuestos en serializers. `Review` ahora tiene CHECK 1-5 en BD.
8. `EnrollmentSerializer` expone `final_exam: {exam_id, passed}` para que el frontend decida mostrar "Rendir examen final".

### ✅ Completado en sesión 2026-07-18 (continuación de la tanda)

1. **Frontend del examen**: página `/examen/:courseId` (`ExamPage.jsx`) con 3 fases — info (instrucciones, intentos usados/restantes, historial), examen en curso (timer contra deadline fijado con `time_remaining_seconds` del server, autoenvío al llegar a 0, barra sticky con progreso de respuestas) y resultado (nota, aprobado/reprobado, aviso de certificado). Ruta protegida en `App.jsx`. En `MyLibraryPage`: botón "Rendir examen final" cuando `is_completed && final_exam && !passed`; certificado solo si existe `certificate`.
2. **Examen demo**: comando idempotente `manage.py seed_demo_exam` (5 preguntas de Python, 10 min, 70% mínimo, 3 intentos). También se sembraron **5 lecciones** para "Python desde cero" (el curso estaba sin lecciones — sin ellas nunca se llegaba al 100%).
3. **E2E verificado por API (28 checks OK)**: registro → login (saldo $500) → compra con cupón BIENVENIDA20 + Luhn → 100% lecciones → **sin certificado pese al 100%** (exige examen) → intento 1 reprobado a propósito (sigue sin certificado) → intento 2 aprobado 100% → certificado emitido con snapshot correcto (nombre/título/horas) → PDF válido descargado → reintento tras aprobar bloqueado (400). Además: la orden registró estado/cupón/descuento/****1111/referencia; el ledger registró WELCOME, PURCHASE, MEMBERSHIP y REFERRAL_BONUS (ambas partes) con `balance_after` cuadrando al centavo. Vite compila las páginas nuevas sin errores.

### ✅ También completado el 2026-07-18 (segunda tanda del día)

- **Examen probado en el navegador por el usuario** — flujo aprobado. Usuario demo: `alumno@demo.com` / `Demo1234!`.
- **Certificado PDF rediseñado**: WeasyPrint no soporta flexbox/100vh (por eso salía descuadrado) → centrado con dimensiones A4 fijas + `position:absolute + transform`. Diseño claro tipo documento (azul marino/dorado, serif) — el usuario aprobó los colores. Verificado renderizando el PDF a imagen.
- **Admins completados**: `library/admin.py` y `recommendations/admin.py` creados (certificados/interacciones/cache solo lectura; peso SVD editable en InteractionType). `users/admin.py`: saldo y referral_code visibles (readonly) + ledger `WalletTransaction` solo lectura. Los admin existentes funcionan bien con los FK de catálogo.
- **Racha de estudio en el frontend**: tarjeta 🔥 en Mi Biblioteca (racha actual + récord) consumiendo `GET /api/library/streak/`.
- **Protección de contenido + reproductor de lecciones** (¡el frontend no tenía forma de estudiar!):
  - `LessonSerializer` público ya NO expone `video_url` ni `content` (antes cualquiera los veía sin comprar).
  - Nuevos endpoints protegidos por inscripción: `GET /api/library/<eid>/lessons/` (temario+estado) y `GET .../lessons/<lid>/content/` (contenido real). Verificado: no-inscrito recibe 404.
  - Página `/aprender/:enrollmentId` (`CoursePlayerPage.jsx`): temario lateral con checkmarks, video embebido (YouTube→embed automático), material de lectura, "Marcar como completada y continuar" (avanza a la siguiente pendiente). Botón "Continuar aprendiendo" en cada tarjeta de Mi Biblioteca.

### ❌ Pendiente

1. **Regenerar `DB_Project/`** (pospuesto por el usuario: es material de presentación, se hará al final): 8 tablas catálogo con INSERTs, `movimientos_saldo` + tipo, 5 de exámenes, columnas nuevas → ~38 tablas. Actualizar README.md y RESUMEN_TABLAS.txt.

## Estado por fase (actualizado 2026-07-11)

### ✅ Fase 1 — Núcleo funcional: COMPLETA y verificada end-to-end
Seguridad (password de `powerbi_readonly` ya no hardcodeada, `DEBUG`/CORS por entorno), wallet + Luhn en checkout, búsqueda de cursos, certificados con PDF real. Frontend: auth completo (login/registro/JWT con refresh automático), catálogo, detalle de curso, carrito, checkout, biblioteca con descarga de certificado.

**Bugs reales encontrados y corregidos en el camino** (no eran nuestros, ya existían):
- Incompatibilidad `WeasyPrint 62.3` + `pydyf>=0.11` rompía la generación de PDFs → se fijó `pydyf==0.10.0` en `requirements.txt`.
- `CourseListSerializer.get_instructor_name` crasheaba (500) si el curso no tenía instructor asignado (campo nullable) → corregido.

### ✅ Fase 2 — Motor de negocio: COMPLETA y verificada
Wishlist real (conectada al motor de recomendaciones), reseñas conectadas al frontend, membresías (planes, suscripción, cancelación) con el mismo flujo Luhn+saldo, "recomendados para ti" y "cursos similares" en el frontend.

### 🔶 Fase 3 — Retención y crecimiento: ~60% hecho
- ✅ Cupones (`Coupon`, aplicados en checkout) — probado con cupón real `BIENVENIDA20` (20% off).
- ✅ Referidos: cada usuario tiene `referral_code`, bono de $10 para ambas partes, link compartible visible en "Mi biblioteca". Probado end-to-end.
- ✅ Rachas de estudio (`StudyStreak`): **backend completo y migrado**, endpoint `GET /api/library/streak/` listo. **Falta conectar al frontend** (no hay ninguna pantalla que la muestre todavía).
- ❌ Protección de contenido de video: no iniciado. Hoy `Lesson.video_url` es un campo plano sin control de acceso — cualquiera con el link puede verlo sin haber comprado el curso.

### ❌ Fase 4 — Admin/Docente + datos históricos + pulido: prácticamente sin empezar (~5%)
- `apps/library/admin.py` y `apps/recommendations/admin.py` — no existen todavía (Django Admin no cubre esas dos apps aún).
- ✅ **Panel Docente + `InstructorEarning`: HECHO y verificado (2026-07-18)**. Modelo `InstructorEarning` en orders (comisión 70% docente / 30% plataforma, congelada por venta): se crea en cada checkout y hay backfill por migración para las ventas históricas (1,946 ingresos generados). Endpoints solo-docente (`IsDocente`, alumno recibe 403): `GET /api/teacher/summary/` (KPIs), `GET /api/teacher/courses/` (cursos con alumnos/rating/ingresos), `GET /api/teacher/courses/<id>/students/` (alumnos con progreso). Frontend: `/panel-docente` (tarjetas KPI + tabla de cursos) y `/panel-docente/curso/:id` (lista de alumnos con barras de progreso); enlace "Panel docente" en el navbar solo para rol DOCENTE/ADMIN. **Decisión de alcance acordada:** el docente NO crea cursos desde el panel — la creación pasa por Django Admin (defensa: flujo de aprobación del administrador, como Udemy con instructores nuevos). Si sobra tiempo al final, se puede añadir el formulario de creación. Probar con `docente1@seed.demo` / `Demo1234!`.
- ✅ **Dashboard de analítica en frontend: HECHO y verificado (2026-07-18)**. Endpoint enriquecido: `top_viewed_courses` ahora trae título (no solo id) y se agregó bloque `kpis` (alumnos totales/nuevos 30d, órdenes 30d, ingresos 30d e históricos, certificados). Página `/dashboard` (solo ADMIN, alumno recibe 403): 6 tarjetas KPI + funnel de conversión con tasas entre etapas + eventos por tipo + top 10 cursos más vistos — barras horizontales CSS puras (una sola serie = un solo tono, sin librería de gráficos). Enlace "Dashboard" en navbar solo ADMIN; login redirige por rol (ADMIN→dashboard, DOCENTE→panel, ALUMNO→catálogo). El seed ahora genera **carritos abandonados** (funnel realista: VIEW→CART 43%, CART→CHECKOUT 68%, CHECKOUT→PURCHASE 77%; antes era 100% y delataba datos sintéticos). Admin de prueba: `admin@demo.com` / `Admin1234!` (también superuser de `/admin/`). **Nota Vite/Docker Windows:** se activó `usePolling` en vite.config.js — sin eso, Vite servía versiones viejas de archivos editados (los eventos de cambio no cruzan el bind mount).
- ✅ **Seed histórico de 5 años: HECHO y verificado (2026-07-18)** — `manage.py seed_demo_data` (con `--flush` para re-sembrar y `--years N`). Sembrado: 8 categorías, 5 docentes, 24 cursos nuevos con lecciones, 1,157 alumnos con crecimiento compuesto ~4.5% mensual, 1,303 órdenes (15% con cupón), 1,949 inscripciones con progreso realista, 504 certificados con snapshot, 216 reseñas, 7,136 interacciones SVD, 12,753 logs de navegación + funnel completo por sesión de compra, 2,468 movimientos de saldo (ledger consistente con el balance final de cada usuario), best-sellers calculados según compras reales. Truco usado para el `auto_now_add`: se desactiva el flag en el proceso del comando (no afecta al servidor) y se insertan fechas históricas con `bulk_create`. SVD reentrenado al final: `for-me/` devuelve `source: personalized`. Usuarios seed: `alumnoN@seed.demo` / docentes: `docenteN@seed.demo` (password `Demo1234!`).
- Pulido visual y responsive — pendiente, y ahora depende del rediseño que el usuario quiere hacer.
- Docker producción-ready — seguridad ya corregida, pero falta una pasada final de verificación antes de desplegar al servidor real.

## Cómo levantar el proyecto

```bash
docker compose up -d
```
- Backend: http://localhost:8000 (Swagger en `/api/schema/swagger/`)
- Frontend: http://localhost:3000
- Si recreas el contenedor `backend` mientras `frontend` sigue corriendo, reinicia `frontend` también (`docker compose restart frontend`) — el proxy de Vite cachea la IP interna de Docker y si el backend cambia de IP, el proxy queda apuntando a la IP vieja.

## Datos de prueba que quedaron sembrados (no son basura, se pueden usar)
- Curso "Python desde cero" (slug `python-desde-cero`)
- Plan de membresía "Plan Mensual" ($19.99/mes)
- Cupón `BIENVENIDA20` (20% de descuento)

## Sesión 2026-07-27 — Perfil + medallas + verificación E2E del flujo docente

### ✅ Perfil de usuario con foto, medallas y movimientos de saldo (idea tomada de review de plataformas similares: Duolingo/Platzi)
- **Medallas (gamificación)**: nuevas tablas `Achievement` (catálogo con PK natural `code`, ícono y orden editables desde el admin sin deploy) y `UserAchievement` (otorgada por el sistema, solo-lectura en admin). 10 medallas sembradas por migración de datos (`0009_seed_achievements`). Reglas en `apps/library/achievements.py` (`evaluate_achievements`, idempotente y a prueba de fallos): primera inscripción, 1/3/5 cursos completados, primer certificado, examen aprobado, examen perfecto (100%), racha 7/30 días, primera reseña. Señales conectadas en `library/signals.py` (progreso de lección, inscripción, certificado, intento de examen aprobado, reseña). El endpoint `GET /api/library/achievements/` re-evalúa al consultar → auto-repara a los usuarios históricos del seed (creados con bulk_create sin señales).
- **Ledger visible**: `GET /api/auth/wallet/transactions/` (historial del saldo simulado, ya existía el modelo).
- **Avatar**: el campo `avatar` ya existía en el modelo; ahora el serializer lo escribe como archivo y lo lee como `avatar_url` RELATIVA (`/media/...`) para funcionar igual detrás del proxy de Vite (dev) y nginx (prod). Proxy `/media` agregado a vite.config.js.
- **Frontend**: página `/perfil` (foto con subida y placeholder de iniciales, grid de medallas ganadas/bloqueadas, edición de datos, tabla de movimientos). El saldo del navbar ahora es link al perfil con mini-avatar.
- Verificado E2E: subida de PNG → `/media/avatars/...` servido 200; PATCH bio OK; alumno@demo.com tiene 7/10 medallas correctas según su historial real (5 cursos completados, examen 100%).

### ✅ Fase 1 del plan de cierre — flujo docente verificado end-to-end (28 verificaciones API)
- Cadena completa probada: plan docente activo ("Docente Oro", 6 cupos) → control de cupos correcto (bloquea solicitud sin cupo disponible y solicitudes duplicadas) → crear curso consume el espacio aprobado y nace en BORRADOR → enviar a revisión sin lecciones bloqueado (400) → lecciones creadas → IN_REVIEW → edición bloqueada en revisión → invisible en catálogo público → publicación (acción admin) → visible y comprable → checkout del alumno → comisión `InstructorEarning` generada con la tasa del PLAN del docente (Oro = 80%; sin plan = base 70%) → ledger cuadra al centavo.
- **Bug encontrado y corregido**: `TeacherLessonSerializer` exigía `order` aunque la vista promete colocarla al final si no se manda — ahora es opcional (`required=False, min_value=1`).
- Curso de prueba E2E (id 53) ocultado del catálogo (`is_active=False`); su orden/inscripción/comisión quedan como historial válido.

### Estado del plan de cierre
1. ✅ Fase 1 — funcionalidad cerrada y flujo docente verificado (+ perfil/medallas agregado por pedido del usuario).
2. ⏭️ Fase 2 — rediseño visual (necesita decisión de dirección del usuario; usar ui-ux-pro-max).
3. Fase 3 — security-review + find-dead-code. 4. Fase 4 — pasada de producción. 5. Fase 5 — DB_Project (~40 tablas ahora con medallas) + docs + slides. 6. Fase 6 — recorrido final de los 3 roles.

## Sesión 2026-07-28 — Fase 2: rediseño visual "Marketplace claro"

### Dirección elegida (opción A)
Morado confianza `#7C3AED` como marca + verde `#16A34A` para lo transaccional; titulares Poppins, texto Open Sans. Patrón marketplace: **el buscador es el llamado a la acción** (hero), navbar blanca de ancho completo, tarjetas limpias sin glassmorphism.

### Filtros del catálogo (backend + frontend)
`CourseListView` filtra por categoría, nivel, rango de precio y orden. El parámetro `ordering` pasa por una whitelist (`ORDERINGS`) para que nunca llegue crudo al ORM. Los cursos sin reseñas van al final del orden por calificación (`F('avg_rating').desc(nulls_last=True)`; Postgres pone NULL primero por defecto). Verificado a través del proxy de Vite: 9 casos, incluido `price_min=abc` que se ignora sin romper.

### Iconografía: emojis a SVG
25 emojis + el reloj y 3 flechas fueron reemplazados por SVG inline en 12 archivos. Los emojis dependen de la fuente del sistema y no se pueden tematizar; los SVG heredan `currentColor`. Nuevo `components/Icons.jsx` (23 iconos) y `components/Rating.jsx`, que unifica el componente de estrellas que estaba duplicado en catálogo y detalle de curso.

### Accesibilidad
- `--text-muted` pasó de `#9A95AE` (2.9:1, no pasaba WCAG AA) a `#6F6A85` (5.1:1).
- Anillo de foco visible por teclado (`:focus-visible`) en enlaces, botones y campos.
- `@media (prefers-reduced-motion: reduce)` desactiva animaciones y transiciones.
- Las estrellas son `aria-hidden` y ahora van acompañadas de texto `.sr-only` ("4.2 de 5 estrellas").
- El atributo `lang` del HTML pasó de `en` a `es` (toda la interfaz está en español).

### Responsive (375 / 768 / 900 / 1440)
- Menú hamburguesa bajo 900px (panel desplegable que se cierra solo al navegar).
- Rejillas fijas que estaban en estilos inline movidas a clases (`.layout-split`, `.layout-split-wide`, `.layout-split-even`, `.two-col`, `.sticky-side`) para poder adaptarlas con media queries; colapsan a una columna bajo 900px.
- Barra de filtros: 5 controles en fila pasan a rejilla de 2 columnas bajo 640px.
- `ProfilePage` pasó de estilos inline a clases (`.profile-header`, `.medal-grid`, `.txn-table`).
- Verificado en Chrome: **0 desbordes horizontales** en 11 rutas a 375px (catálogo, detalle, carrito, checkout, biblioteca, wishlist, membresías, perfil y las 3 del panel docente).

### Rendimiento
Las fuentes se cargan con `<link>` en `index.html` en vez de `@import` dentro del CSS (el `@import` serializa la descarga y retrasa el primer render). El `<link>` seguía apuntando a **Inter**, que ya no se usa.

### Bug encontrado y corregido
El panel del docente mostraba **"Ingresos totales (70%)"** fijo, pero la comisión depende del plan activo (Docente Oro = 80%). `TeacherSummaryView` ahora devuelve `commission_rate` y el KPI muestra el porcentaje real.

### Pendiente de la Fase 2
Ninguno. Siguiente: Fase 3 (security-review + find-dead-code).

### Nota para la Fase 4
El bundle pesa 635 kB (177 kB gzip) en un solo chunk. Se parte con `React.lazy` en las rutas pesadas.

## Sesión 2026-07-31 — Fase 3: revisión de seguridad

### Resultado del escaneo
0 críticos, 2 altos, 4 medios, 2 bajos. Sin hallazgos en: secretos hardcodeados, inyección SQL (100% ORM, sin `raw()`/`cursor.execute`), inyección de comandos, deserialización insegura, hashes débiles, TLS deshabilitado, SSRF y JWT con algoritmo `none`. Los 26 `get_object_or_404` acotan por `request.user` (sin IDOR), `is_correct` no aparece en ningún serializer y el número de tarjeta solo vive en memoria para Luhn.

### Corregido: SECRET_KEY y POSTGRES_PASSWORD con default embebido (alto)
`settings.py` traía `os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-default-key-dev-only')`. Si el `.env` no llegaba al contenedor en el servidor, Django arrancaba igual con una clave escrita en el código, y con ella se pueden firmar tokens de sesión válidos. El fallo era silencioso.

Nueva función `env_requerida_en_produccion(nombre, default_dev)`: en desarrollo (`DEBUG=True`) acepta el valor de respaldo; con `DEBUG=False` lanza `ImproperlyConfigured` y **el sistema no arranca**. Aplicada a `DJANGO_SECRET_KEY` y `POSTGRES_PASSWORD`.

Verificado: sin la variable y con `DEBUG=False` falla con mensaje explícito; con la variable presente, `manage.py check` pasa sin problemas.

### Corregido: sin límite de intentos de autenticación (alto)
No había throttling en ningún endpoint: el login aceptaba intentos ilimitados. Se añadió `DEFAULT_THROTTLE_CLASSES` (anon 60/min, user 300/min) más scopes específicos: `login` 8/min, `registro` 5/hora y `analitica` 90/min.

El scope `analitica` cierra de paso el hallazgo medio SEC-M01: `LogEventView` es público y escribía en `NavigationLog`/`ConversionFunnel` sin límite; esos datos alimentan el entrenamiento SVD, así que se podía envenenar el recomendador y falsear el dashboard.

**Caché compartida**: DRF guarda los contadores del throttle en la caché de Django, que por defecto es `LocMemCache` (por proceso). Con varios workers de gunicorn el límite real de login habría sido 8/min *por worker*. Se configuró `RedisCache` (backend nativo de Django, sin dependencias nuevas) derivando la URL de `REDIS_URL` y cambiándole el número de base (Celery usa la 0 y la 1), para no duplicar la contraseña de Redis en el `.env`.

Verificado en vivo: 8 intentos de login devuelven 401 y del noveno en adelante 429; el uso normal del catálogo no se ve afectado; el login legítimo sigue emitiendo tokens.

### Dependencias del frontend
`npm audit fix` resolvió 2 de 4 avisos altos (`postcss` path traversal y `brace-expansion` DoS, ambos solo de build). Quedan 2 sin arreglo hacia adelante: el aviso de `react-router` (GHSA-qwww-vcr4-c8h2) cubre el rango 7.12.0–8.2.0 y la única opción que ofrece npm es **bajar** a 7.11.0. Se decidió quedarse en 7.18.2 porque **el aviso es específico del modo RSC** (React Server Components) y esta app es una SPA clásica con `<Routes>`/`<Route>`, sin data router, sin `loader:`/`action:` y sin RSC — verificado por búsqueda en `src/`. Bajar 7 versiones menores o migrar a React Router 8 a semanas del cierre son peores tratos que documentar por qué no aplica.

### Pendiente (Fase 4, pasada de producción)
- SEC-M02: sin cabeceras de seguridad (`SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_CONTENT_TYPE_NOSNIFF`), todas condicionadas a `not DEBUG`.
- SEC-M03: la subida de avatar no valida tamaño ni dimensiones (Pillow sí valida que sea imagen real). Añadir tope en `validate_avatar`.
- SEC-B01: se confía en `X-Forwarded-For` sin validar el proxy (solo afecta el campo de analítica, ninguna decisión de autorización).
- `pip-audit`/`bandit`/`semgrep` no están instalados: las dependencias de Python **no se contrastaron contra CVEs conocidos**.

## Sesión 2026-07-31 (cont.) — Fase 3: código muerto

### Resultado
9 hallazgos reales en 83 archivos Python + 26 JSX. El backend está limpio para su tamaño.

Herramientas: ESLint 10 (ya instalado en el proyecto) para el frontend; análisis propio consciente de Django para el backend, porque `vulture` no está instalado y Docker se cayó a mitad de la sesión. **Limitación**: sin `vulture` no se analizaron variables locales ni atributos de instancia sin usar — esto es un piso, no un techo.

### Eliminado
- **6 imports sin usar**: `Question` y `AnswerOption` (`exams/views.py:11`), `timezone` y `LessonProgressSerializer` (`library/views.py:7,10`), `UserCourseInteraction` (`recommendations/views.py:6`), `EnrollmentType` (`seed_demo_data.py:31`).
- **`refreshUser`** en `TeacherApplicationPage.jsx:25` — se desestructuraba de `useAuth()` sin usarse. La función sigue viva y en uso real en CheckoutPage, MembershipsPage y ProfilePage.
- **Parámetro `auto`** de `handleSubmit()` en `ExamPage.jsx:47` — nunca se leía; el cuerpo no ramificaba según su valor. Se actualizó también la llamada del temporizador (`handleSubmit(true)` → `handleSubmit()`). El autoenvío por tiempo agotado funciona igual: el servidor cierra el intento y responde `expired=true`.
- **`Coupon.apply_discount()`** (`orders/models.py:181`) — cero llamadas. El checkout calculaba el descuento inline con la misma fórmula, así que la lógica estaba duplicada. No se cableó el método sino que se borró: el checkout debe elegir el **mejor** porcentaje entre cupón y membresía (`best_pct`), y un método que asumiera siempre `self.discount_pct` daría un descuento incorrecto. Se dejó un comentario en su lugar explicando dónde vive el cálculo real.

### Falsos positivos identificados (50 símbolos)
No son código muerto aunque no tengan llamadas explícitas: 31 clases `ModelAdmin` (`@admin.register`), 9 `AppConfig` (string en `INSTALLED_APPS`), 5 receptores de señal, 2 receptores anidados con `weak=False`, 7 métodos `get_*` que respaldan un `SerializerMethodField` (DRF los llama por nombre), `teacher_urls.py` (incluido por string en `core/urls.py:24`) y las 22 constantes de `settings.py` (Django las lee vía `settings.X`).

### Riesgo de reflexión: bajo
Solo dos `getattr` con nombre literal y valor por defecto en `catalog/serializers.py:100,104`, que leen anotaciones del queryset. Sin `importlib`, `eval`, `exec` ni `globals()`. En el frontend, ninguna llamada dinámica por corchetes.

### Verificación tras la limpieza
`manage.py check` sin problemas; ESLint sin hallazgos de `no-unused-vars`; 7 endpoints de los módulos tocados responden 200; y el checkout con el cupón `BIENVENIDA20` sobre un curso de $9.99 cobró exactamente **$7.99** (saldo 181.08 → 173.09), confirmando que el descuento del 20% se sigue aplicando bien.

### Nota
Quedan 10 avisos de ESLint que **no son código muerto**: 7 de `react-hooks/set-state-in-effect` y 2 de `exhaustive-deps` (el patrón "cargar datos en useEffect y meterlos al estado", que la regla nueva de React 19 desaconseja por renders en cascada) más 1 de `react-refresh`. La app funciona; es una advertencia de rendimiento. Conviene saberlo si el revisor corre el linter.

### Estado del plan
1. ✅ Fase 1 — funcionalidad + flujo docente verificado E2E.
2. ✅ Fase 2 — rediseño visual "Marketplace claro" + responsive + accesibilidad.
3. ✅ Fase 3 — security-review (2 altos corregidos) + código muerto (9 eliminados).
4. ⏭️ Fase 4 — pasada de producción: cabeceras de seguridad, límite de tamaño del avatar, `X-Forwarded-For`, atributo `version` obsoleto en docker-compose, code-splitting del bundle (635 kB).
5. Fase 5 — DB_Project (~40 tablas) + documentación + diapositivas.
6. Fase 6 — recorrido manual final de los 3 roles.

## Sesión 2026-07-31 (cont.) — Fase 4: pasada de producción

### Hallazgo principal: no existía ruta de despliegue
Lo más grave de esta fase no estaba en la lista original. El proyecto **no tenía forma de correr en producción**:

- El backend arrancaba con `manage.py runserver`, que es de un solo hilo y cuya documentación prohíbe explícitamente usar en producción.
- El frontend corría el servidor de desarrollo de Vite: **nunca se compilaba**. Servía el código fuente sin minificar, con el websocket de recarga en caliente expuesto.
- No había proxy inverso, así que las cabeceras HTTPS recién añadidas no tenían nada que terminara el TLS.
- Postgres y Redis publicaban sus puertos al host — aceptable en local, una puerta abierta en un servidor público.

**Construido**: `docker-compose.prod.yml` (gunicorn con 3 trabajadores, `collectstatic` automático, sin puertos de base expuestos, volúmenes nombrados para estáticos y media), `frontend/Dockerfile.prod` (multietapa: compila con `NODE_ENV=production` y sirve con nginx), `frontend/nginx.conf` (proxy inverso, `try_files` para las rutas de React, caché inmutable para los assets con hash, `client_max_body_size 5M`) y `DESPLIEGUE.md` (guía paso a paso, HTTPS con Caddy, comprobaciones posteriores, respaldos).

### Endurecimiento de Django (todo bajo `if not DEBUG`)
`SECURE_PROXY_SSL_HEADER`, `SECURE_SSL_REDIRECT` (configurable por si el TLS se termina en un balanceador externo), HSTS a 1 hora —a propósito, para poder revertir rápido; se sube a 1 año cuando el HTTPS esté probado—, cookies de sesión y CSRF seguras, `SECURE_CONTENT_TYPE_NOSNIFF`, `X_FRAME_OPTIONS=DENY` y `CSRF_TRUSTED_ORIGINS` derivado de `CORS_ALLOWED_ORIGINS` (sin eso el Django Admin no acepta sus propios formularios).

### Resto de la fase
- **Avatar (SEC-M03)**: `validate_avatar` rechaza más de 2 MB o más de 2000x2000 px, más `DATA_UPLOAD_MAX_MEMORY_SIZE` de 5 MB como red de seguridad en Django.
- **X-Forwarded-For (SEC-B01)**: nueva función `_ip_del_cliente()` que solo lee la cabecera si `TRUSTED_PROXY_COUNT > 0`, y toma la IP contando desde el final (las de la izquierda las puede inventar el cliente). Con 0 usa `REMOTE_ADDR`, que no es falsificable.
- **docker-compose.yml**: eliminado el atributo `version` obsoleto que sacaba un warning en cada comando.
- **Code-splitting**: `App.jsx` con `React.lazy` + `Suspense`. Catálogo, login y registro siguen en el bundle principal (primera pantalla); las otras 15 rutas se cargan bajo demanda. Un alumno ya no se descarga el panel del docente ni el dashboard del admin.

### Dos bugs propios encontrados AL PROBAR, no al escribir
1. **gunicorn escuchaba en 127.0.0.1** → nginx daba 502. Causa: en un escalar plegado de YAML (`>`), las líneas **más indentadas conservan el salto de línea**. Los argumentos de gunicorn estaban más indentados, así que se ejecutaba `gunicorn core.wsgi:application` a secas, sin `--bind`. Corregido poniéndolos todos en una línea.
2. **El build de producción sobrescribió las imágenes de desarrollo**: ambos compose comparten nombre de proyecto y de servicio, así que `proyecto_ecommerce_cursos-frontend:latest` pasó a ser la imagen nginx y el entorno local quedó sirviendo la build de producción. Corregido con etiquetas `image:` propias (`cursostech-*:prod`). De paso, los 3 servicios de Celery ahora reutilizan la imagen del backend en vez de construir tres veces lo mismo.

### Tamaño del paquete
| | Antes | Ahora |
|---|---|---|
| Chunk principal | 635 kB (177 kB gzip) | **245 kB (78 kB gzip)** |
| Chunks de ruta | 0 | 17, bajo demanda |

Parte de la mejora venía de un error de medición: el contenedor tiene `NODE_ENV=development`, así que `vite build` generaba el **runtime de desarrollo de React**. El `Dockerfile.prod` fija `NODE_ENV=production` explícitamente.

### Verificación: se levantó el stack de producción completo y se probó
Se bajó el entorno de desarrollo, se construyeron y levantaron las imágenes de producción con `DEBUG=False` y se comprobó por el puerto 80: la SPA compilada carga (sirve `/assets/index-*.js`, no `/src/main.jsx`), la API responde por nginx en el mismo origen (25 cursos, 8 categorías, filtros), el login y 3 endpoints autenticados funcionan, las rutas internas de React recargadas directamente devuelven 200 (no 404), los estáticos del Django Admin se sirven (`base.css`, 22 kB) y nginx aplica `X-Content-Type-Options`, `X-Frame-Options` y `Referrer-Policy`.

`manage.py check --deploy`: **43 avisos, solo 3 de seguridad**, y los tres son artefactos de la prueba local (`SECURE_SSL_REDIRECT` apagado por no tener TLS, `SECRET_KEY` de desarrollo, y `HSTS_PRELOAD` desactivado a propósito). Los otros 40 son de `drf_spectacular` sobre la calidad del esquema Swagger: preexistentes, cosméticos, sin impacto en seguridad ni funcionamiento.

Después se restauró el `.env` desde respaldo y se reconstruyó el entorno de desarrollo. Verificado: sirve código fuente sin compilar, la API responde por el proxy de Vite, los 3 roles inician sesión y los 6 módulos diferidos se sirven correctamente.

**No verificado en esta sesión**: el render visual de las rutas diferidas en el navegador (la extensión de Chrome se desconectó). La evidencia indirecta es fuerte —el build de producción generó los 17 chunks, lo que prueba que todos los `import()` resuelven— pero no es lo mismo que verlo renderizar.

### Estado del plan
1. ✅ Fase 1 — funcionalidad + flujo docente E2E.
2. ✅ Fase 2 — rediseño "Marketplace claro" + responsive + accesibilidad.
3. ✅ Fase 3 — seguridad (2 altos) + código muerto (9).
4. ✅ Fase 4 — producción: ruta de despliegue completa, endurecimiento y code-splitting.
5. ⏭️ Fase 5 — DB_Project (~40 tablas) + documentación + diapositivas.
6. Fase 6 — recorrido manual final de los 3 roles.

## Sesión 2026-08-02 — Pasarela de pago simulada (recarga de saldo)

El saldo era fijo: $500 al registrarse y sin forma de recargar (era una asunción explícita del plan original). Se añadió la recarga a través de una pasarela simulada.

### Diseño elegido
Flujo de **dos pasos con redirección**, como una pasarela real:
1. `/recargar` — el alumno elige el monto y se crea una *intención* en estado PENDIENTE.
2. `/pasarela/:token` — pantalla con identidad visual propia (fondo oscuro, marca "PasarelaPay", **sin navbar**) donde ingresa la tarjeta y autoriza o cancela.
3. Comprobante con referencia, últimos 4 dígitos y saldo actualizado.

La pantalla lleva un aviso permanente **"Modo simulación — no se procesan pagos reales"**: no debe poder confundirse con una pasarela de verdad.

### Por qué una intención guardada y no una llamada directa
El monto **no viaja desde el navegador al autorizar**: se lee de la intención guardada en la base. Si viajara en la petición, cualquiera podría iniciar una recarga de $5 y autorizar $5000 modificando el cuerpo.

Además, la fila se bloquea con `select_for_update()` y se verifica que siga PENDIENTE antes de tocar el saldo. **Sin eso, reenviar la autorización acreditaba dos veces.** Verificado: el segundo envío responde 409 y el saldo no cambia.

### Fallos deterministas por número de tarjeta
`apps/users/gateway.py` decide aprobar o rechazar según el número, usando los de prueba estándar de la industria (los mismos que publica Stripe, todos válidos por Luhn):

| Tarjeta | Resultado |
|---|---|
| `4242424242424242`, `4539578763621486`, `5555555555554444` | Aprueban |
| `4000000000000002` | Rechazada por el banco |
| `4000000000009995` | Fondos insuficientes |
| `4000000000000069` | Tarjeta vencida |
| `4000000000000127` | CVV incorrecto |
| `4000000000000119` | Error de procesamiento |

Se eligió determinista en vez de aleatorio a propósito: un rechazo al azar se ve más realista pero hace imposible demostrar el manejo de errores de forma confiable — podría fallar justo en el camino feliz durante la defensa, o negarse a fallar cuando se quiere mostrar el error. La pantalla lista estas tarjetas en un desplegable de ayuda.

### Modelos nuevos
- `RechargeStatus` (catálogo): PENDING, APPROVED, DECLINED, CANCELLED, EXPIRED.
- `WalletRecharge`: token UUID (para que no se adivine el de otro usuario), monto, estado, últimos 4 dígitos, motivo del rechazo, referencia y fechas. Las intenciones caducan a los 15 minutos.
- Nuevo tipo de movimiento `RECHARGE` en el libro mayor.
- Migraciones `0008` (modelos) y `0009` (siembra de catálogos).

Límites: entre $5 y $500 por recarga, sin tope acumulado. El número de tarjeta nunca se guarda.

### Problema propio encontrado al probar
El throttle quedó en **20 recargas por hora**, y se agotó durante las pruebas dejando la cuenta bloqueada ~54 minutos. En la defensa, un revisor jugando con la recarga se habría topado con lo mismo. Cambiado a **15 por minuto**: frena igual un script de "card testing" (probar muchos números seguidos, que es el riesgo real), pero una persona nunca lo alcanza y, si lo alcanza, se libera en 60 segundos. La pantalla ahora traduce el 429 a un mensaje claro en vez del texto crudo de DRF.

### Verificación
Backend por API: recarga aprobada acredita bien; reenvío de la misma autorización devuelve 409 sin duplicar el saldo; las 5 tarjetas de fallo devuelven 402 con su motivo correcto y sin tocar el saldo; los límites rechazan $4.99, $500.01 y montos negativos.

En el navegador, flujo completo: perfil → recargar → pasarela → rechazo con motivo → reintento → aprobación → comprobante → vuelta al sitio. Saldo $510.01 → $535.01, reflejado en el libro mayor con su referencia.

### PENDIENTE
`DB_Project/` quedó **desactualizado**: ahora son **50 tablas**, no 48. Faltan `users_rechargestatus` y `users_walletrecharge` en `01_usuarios.sql`, el README y `RESUMEN_TABLAS.txt`.

## Sesión 2026-08-02 (cont.) — DB_Project a 50 tablas + revisión completa

### DB_Project actualizado
Se añadieron `estados_recarga` y `recargas_saldo` a `01_usuarios.sql` (que pasa de 8 a 10 tablas), se renumeró `RESUMEN_TABLAS.txt` (1..50 correlativo) y se corrigieron los totales del README.

**Verificado de nuevo contra la base real**: los 8 scripts ejecutan en orden sin errores en una base limpia; 50 tablas = 50, 308 columnas = 308, 26 UNIQUE = 26, y **50 de 50 tablas coinciden exactamente** en tipo y nulabilidad en cada posición, 0 diferencias. Las claves foráneas dan 66 vs 68 por las 2 que apuntan a tablas internas de Django (`auth_group`, `auth_permission`), omitidas a propósito como siempre.

Los catálogos pasan de 14 a 15 con `estados_recarga`.

### Revisión de seguridad
Sin hallazgos nuevos. Se mantiene todo lo verificado antes (0 secretos, 0 inyección SQL/comandos, 0 deserialización insegura, 0 cripto débil, 0 TLS deshabilitado, todas las vistas con `permission_classes`).

**Prueba adversarial del módulo nuevo** — el docente intenta usar el token de recarga del alumno:

| Intento | Resultado |
|---|---|
| `GET` detalle de la recarga ajena | 404 bloqueado |
| `POST` autorizar la recarga ajena | 404 bloqueado |
| `POST` cancelar la recarga ajena | 404 bloqueado |
| `GET` sin autenticación | 401 bloqueado |

El saldo del docente no se movió ($450.01 antes y después). Las 4 vistas de recarga acotan por `user=request.user`, así que un token filtrado no sirve para nada en otra cuenta.

También confirmado: el número de tarjeta solo aparece como campo `write_only` del serializer y como variable local en la vista — nunca se persiste.

### Código muerto
**Un hallazgo real, propio**: `RECHARGE_MIN` y `RECHARGE_MAX` estaban importados en `apps/users/views.py` pero solo se usan en `serializers.py`. Eliminado el import. Verificado después: `manage.py check` limpio, la recarga de $10 se aprueba y el límite sigue rechazando $1.

El frontend no tiene código muerto (ESLint: 0 `no-unused-vars`). Los otros 10 avisos siguen siendo los mismos de siempre (7 `set-state-in-effect`, 2 `exhaustive-deps`, 1 `react-refresh`), preexistentes y sin relación con la pasarela.

Los 9 "métodos nunca llamados" que reporta el análisis del backend siguen siendo los falsos positivos conocidos: 7 respaldan un `SerializerMethodField` y 2 son receptores de señal anidados.

## Sesión 2026-08-02 (cont.) — Simulación histórica completa

Se reescribió `seed_demo_data` para que la plataforma se vea como un producto en uso desde hace 5 años, no como una demo vacía.

### Decisiones tomadas con el usuario
| Tema | Elección |
|---|---|
| Videos | YouTube real, con atribución al autor |
| Imágenes | Descarga al sembrar (queda offline después) |
| Volumen | Alto: ~1.200 usuarios, 30 cursos |
| Contenido | Temario propio por curso |
| Exámenes | 6 cursos representativos (punto medio propuesto y aprobado) |

### Verificaciones previas que cambiaron el plan
Antes de escribir el seed se probaron las dependencias externas desde el contenedor:

- **Unsplash ya no sirve**: `source.unsplash.com` devuelve 503, fue descontinuado. Se usa **picsum.photos**, que sirve fotos del mismo catálogo y acepta semilla determinista: la portada de un curso NO cambia entre corridas del seed.
- **Los 53 IDs de video probados eran válidos**, pero **3 no eran del tema que yo creía** (`fis26HvvDII` es Android, no Docker; `8jLOx1hD3_o` es C++, no ciberseguridad). Por eso el mapeo se hizo leyendo el **título real** que devuelve oEmbed, no confiando en la etiqueta. También se descartó `RGKi6LSPDLU` por estar en hindi.

### Cómo funciona ahora
- **`_catalogo_demo.py`**: 30 cursos con descripción, resultados, requisitos y **temario propio** (174 lecciones con contenido específico del tema). Antes eran 8 títulos genéricos repetidos en los 24 cursos, que es lo que más delataba la simulación.
- **Videos validados en tiempo de siembra**: el seed consulta oEmbed antes de asignar. Si un video fue eliminado, la lección queda con su contenido escrito en vez de un reproductor roto. Resultado: 36 de 36 válidos.
- **Atribución**: el contenido de la lección incluye título y autor reales, y bajo el reproductor hay un enlace «Ver en YouTube» al video original.
- **Portadas y avatares** descargados a `/media` (35 archivos, 1.7 MB).
- **Membresías de docente**: sin plan activo el instructor no tiene cupos y no puede publicar. Ahora los 5 docentes tienen «Docente VIP».
- **Recargas históricas** (201, con 32 rechazadas para que el historial no sea irrealmente perfecto) y **medallas con la fecha del hecho que las gatilló** (1.829), no la de hoy.

### Bug encontrado al verificar
Las portadas devolvían `course_covers/x.jpg` sin el prefijo `/media/`, así que el navegador las resolvía como ruta relativa y daban 404. **Estaba latente**: como ningún curso tenía portada antes, nunca se notó.

Al investigarlo apareció que `Course.cover_image` es un **`URLField`**, no un `ImageField` (el docente pega una URL). El primer intento de arreglo —un `SerializerMethodField` que llamaba `.url`— reventaba con `AttributeError: 'str' object has no attribute 'url'`. La corrección correcta fue en el seed: guardar la ruta `/media/...` completa. Verificado: las 30 portadas responden 200, también a través del proxy de Vite.

### Estado final
1.165 usuarios · 30 cursos · 174 lecciones (36 con video) · 6 exámenes · 1.292 órdenes · 1.962 inscripciones · 487 certificados · 229 reseñas · 1.829 medallas · 201 recargas · 14.334 eventos de navegación. **Rango histórico: 2021-08-28 a 2026-08-02.**

El motor SVD se reentrenó en 6,8 s y generó recomendaciones personalizadas para 1.157 usuarios (verificado: los alumnos del seed reciben `source: personalized`, no el fallback).

Respaldo en `respaldos/respaldo_2026-08-02_simulacion_completa.sql` (4,9 MB).

### Nota para la defensa
Los videos son de terceros (freeCodeCamp, Programming with Mosh, Traversy Media, TechWorld with Nana, entre otros) y están embebidos con atribución visible y enlace al original. Si preguntan por la procedencia, esa es la respuesta: es contenido público embebido mediante el reproductor oficial de YouTube, acreditado a su autor.

### Corrección: las portadas no correspondían al tema

El usuario detectó que las portadas descargadas no tenían relación con los cursos (caracoles, personas caminando, paisajes). Era correcto: **picsum devuelve fotos aleatorias**, no por tema.

Se probó la alternativa obvia —**loremflickr**, que sí filtra por etiquetas— y resultó peor: para `python,programming,code` devolvió la foto de un gato en una pantalla e-ink, y para `cybersecurity,security,network` una estatua de gato en una calle de Turquía. Además las imágenes traen la licencia y el nombre del fotógrafo quemados encima. Solo `database,sql,server` acertó, con una captura de SQL Server de calidad amateur y marca de agua. Fuente descartada.

**Solución: generar las portadas** (`_portadas.py` con Pillow, ya instalado). Cada portada usa el **título real del curso** y un **color propio por categoría** (morado programación, azul web, rojo ciberseguridad, ámbar datos, etc.), con degradado, retícula tenue y etiqueta de nivel. Ventajas frente a la foto de banco:

- **Siempre corresponde**, porque se construye con los datos del curso.
- Determinista y sin dependencia de internet (`--sin-media` ya no la afecta).
- Sin marcas de agua ni preguntas de licencia.
- El catálogo se lee de un vistazo: el color identifica el área.

Defecto corregido durante la revisión: la etiqueta de nivel se superponía al título en títulos largos. Ahora el bloque de título se apila hacia arriba desde la etiqueta, así nunca se montan.

**Segundo hallazgo**: las tarjetas de «Recomendados para ti» seguían con el icono de relleno. `CourseRecommendationSerializer` no incluía `cover_image` ni el nivel, aunque el frontend reutiliza el mismo componente de tarjeta del catálogo. Se añadieron esos campos y, para no introducir un N+1 (una consulta por curso al leer categoría, nivel e instructor), se agregó `select_related` a las tres consultas de recomendaciones.

Verificado: 30 de 30 portadas responden 200 (directo y por el proxy de Vite), y las recomendaciones y los cursos similares muestran su portada.
