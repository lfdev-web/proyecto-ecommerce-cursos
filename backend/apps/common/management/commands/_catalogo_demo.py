"""
Catálogo de cursos para la siembra de datos de demostración.

Cada curso trae su temario PROPIO: las lecciones hablan del tema real del
curso, no de títulos genéricos repetidos. Ese detalle es lo que evita que se
note la simulación al abrir dos cursos seguidos.

Los identificadores de video son de YouTube y fueron VERIFICADOS uno por uno
con el endpoint oEmbed: el título y el autor que devuelve YouTube confirman
que el video corresponde al tema del curso. El seed los vuelve a validar
antes de asignarlos, así que si alguno se elimina en el futuro, la lección
simplemente queda con su contenido escrito en lugar de mostrar un video roto.

Formato de cada curso:
    (titulo, categoria, nivel, precio, descripcion, resultados, requisitos,
     [(titulo_leccion, minutos, id_video_o_None, contenido), ...])
"""

# Categorías tal como existen en la base (catalog_category.name)
PROG = 'Programación'
WEB = 'Desarrollo Web'
BD = 'Bases de Datos'
DATOS = 'Ciencia de Datos'
IA = 'Inteligencia Artificial'
CLOUD = 'Cloud y DevOps'
CIBER = 'Ciberseguridad'
MOVIL = 'Desarrollo Móvil'

CURSOS = [
    # ---------------------------------------------------------------- Programación
    (
        'Python desde cero', PROG, 'BASICO', '19.99',
        'Aprende a programar en Python partiendo de cero absoluto. Cubrimos variables, '
        'estructuras de control, funciones, colecciones y manejo de archivos, con '
        'ejercicios prácticos en cada lección y un proyecto final.',
        '- Escribir programas en Python desde cero\n'
        '- Manejar listas, diccionarios, tuplas y conjuntos\n'
        '- Crear funciones reutilizables y módulos propios\n'
        '- Leer y escribir archivos de texto y CSV\n'
        '- Manejar errores con try/except',
        '- Una computadora con Windows, macOS o Linux\n- No se necesita experiencia previa',
        [
            ('Instalación de Python y primer programa', 25, 'rfscVS0vtbw',
             'Instalamos Python y un editor, y escribimos el primer "Hola mundo". '
             'Explicamos qué es el intérprete y cómo ejecutar un archivo .py.'),
            ('Variables y tipos de datos', 30, None,
             'Enteros, decimales, cadenas y booleanos. Cómo convertir entre tipos y '
             'por qué Python no necesita declarar el tipo por adelantado.'),
            ('Condicionales: if, elif y else', 35, None,
             'Tomar decisiones en el código. Operadores de comparación y lógicos, y el '
             'papel de la indentación en Python.'),
            ('Bucles for y while', 40, None,
             'Repetir tareas sin duplicar código. Recorrer listas, usar range(), y '
             'cuándo conviene cada tipo de bucle.'),
            ('Listas, tuplas y diccionarios', 45, None,
             'Las tres colecciones que más se usan. Cuándo elegir cada una y las '
             'operaciones más frecuentes sobre ellas.'),
            ('Funciones y módulos', 35, None,
             'Agrupar código reutilizable, parámetros por defecto, valores de retorno '
             'y cómo separar el programa en varios archivos.'),
            ('Archivos y manejo de errores', 30, None,
             'Leer y escribir archivos con "with open", y capturar errores para que el '
             'programa no se caiga ante datos inesperados.'),
        ],
    ),
    (
        'Programación orientada a objetos en Python', PROG, 'INTERMEDIO', '29.99',
        'Da el salto de escribir scripts a diseñar programas. Clases, herencia, '
        'encapsulamiento y polimorfismo aplicados con ejemplos que se construyen a lo '
        'largo del curso.',
        '- Diseñar clases con responsabilidades claras\n'
        '- Aplicar herencia y composición sin abusar de ellas\n'
        '- Entender los cuatro pilares de la POO\n'
        '- Escribir código más fácil de mantener y extender',
        '- Saber programar en Python a nivel básico\n- Conocer funciones y colecciones',
        [
            ('Los cuatro pilares de la POO', 30, '1ONhXmQuWP8',
             'Abstracción, encapsulamiento, herencia y polimorfismo explicados con '
             'ejemplos concretos, sin la jerga habitual.'),
            ('Clases, objetos y el método __init__', 40, None,
             'Cómo se define una clase, qué es una instancia y para qué sirve el '
             'constructor. Diferencia entre atributos de clase y de instancia.'),
            ('Encapsulamiento y propiedades', 35, None,
             'Proteger el estado interno de un objeto. El uso de guion bajo por '
             'convención y el decorador @property.'),
            ('Herencia y composición', 45, None,
             'Cuándo heredar y cuándo componer. El problema de las jerarquías '
             'profundas y por qué "preferir composición" es un buen consejo.'),
            ('Métodos especiales (dunder)', 35, None,
             '__str__, __repr__, __eq__ y __len__. Cómo hacer que tus objetos se '
             'comporten como los tipos nativos de Python.'),
            ('Proyecto: modelar un sistema de biblioteca', 50, None,
             'Aplicamos todo lo visto para modelar libros, socios y préstamos con '
             'clases bien definidas.'),
        ],
    ),
    (
        'JavaScript moderno desde cero', PROG, 'BASICO', '24.99',
        'JavaScript actual (ES6+) explicado desde el principio: sintaxis, funciones, '
        'objetos, arreglos y manipulación del DOM, con ejercicios en el navegador.',
        '- Dominar la sintaxis moderna de JavaScript\n'
        '- Manipular el DOM y responder a eventos\n'
        '- Trabajar con arreglos usando map, filter y reduce\n'
        '- Entender el alcance de las variables y las closures',
        '- Nociones básicas de HTML\n- No se necesita experiencia en programación',
        [
            ('Qué es JavaScript y cómo ejecutarlo', 30, 'PkZNo7MFNFg',
             'El papel de JavaScript en la web, la consola del navegador y las tres '
             'formas de incluir código en una página.'),
            ('let, const y tipos de datos', 35, None,
             'Por qué "var" quedó atrás. Diferencia entre let y const, y los tipos '
             'primitivos del lenguaje.'),
            ('Funciones y funciones flecha', 40, None,
             'Declaraciones, expresiones y funciones flecha. Parámetros por defecto y '
             'el operador rest.'),
            ('Arreglos: map, filter y reduce', 45, None,
             'Los tres métodos que cambian la forma de escribir JavaScript. Ejemplos '
             'que reemplazan bucles enteros por una línea.'),
            ('Objetos y desestructuración', 35, None,
             'Crear y recorrer objetos, la sintaxis de desestructuración y el operador '
             'de propagación.'),
            ('Manipulación del DOM', 45, None,
             'Seleccionar elementos, cambiar contenido y estilos, y responder a los '
             'eventos del usuario.'),
        ],
    ),
    (
        'TypeScript para proyectos reales', PROG, 'INTERMEDIO', '29.99',
        'Añade tipos a tu JavaScript y detecta errores antes de ejecutar. Interfaces, '
        'genéricos y configuración práctica de tsconfig para proyectos de verdad.',
        '- Tipar variables, funciones y objetos\n'
        '- Escribir interfaces y tipos reutilizables\n'
        '- Usar genéricos sin complicarte\n'
        '- Configurar TypeScript en un proyecto existente',
        '- JavaScript moderno (ES6+)\n- Haber trabajado con npm',
        [
            ('Por qué TypeScript', 30, 'gp5H0Vw39yw',
             'Qué problemas resuelve realmente y cuáles no. El costo de adoptarlo y '
             'cuándo vale la pena.'),
            ('Tipos básicos y inferencia', 35, None,
             'string, number, boolean, arreglos y tuplas. Por qué muchas veces no hace '
             'falta escribir el tipo.'),
            ('Interfaces y type aliases', 40, None,
             'Describir la forma de un objeto. Cuándo usar interface y cuándo type, y '
             'cómo extenderlos.'),
            ('Genéricos', 45, None,
             'Escribir funciones y tipos que trabajan con cualquier tipo sin perder la '
             'verificación.'),
            ('Configuración y migración gradual', 35, None,
             'tsconfig.json explicado opción por opción, y cómo migrar un proyecto '
             'JavaScript sin reescribirlo todo.'),
        ],
    ),
    (
        'C++ de principiante a avanzado', PROG, 'AVANZADO', '44.99',
        'Un recorrido completo por C++ moderno: memoria, punteros, plantillas y la '
        'biblioteca estándar, con énfasis en entender qué pasa por debajo.',
        '- Manejar memoria dinámica con seguridad\n'
        '- Usar punteros y referencias correctamente\n'
        '- Escribir plantillas genéricas\n'
        '- Aprovechar la STL: vectores, mapas y algoritmos',
        '- Experiencia previa programando en algún lenguaje\n- Nociones de compilación',
        [
            ('Compilación y primer programa', 40, '8jLOx1hD3_o',
             'Del código fuente al ejecutable: preprocesador, compilador y enlazador. '
             'Compilamos y ejecutamos el primer programa.'),
            ('Tipos, referencias y punteros', 50, None,
             'La diferencia que más confunde al llegar a C++. Qué guarda realmente una '
             'variable y qué hace el operador &.'),
            ('Memoria dinámica y RAII', 55, None,
             'new y delete, por qué generan fugas, y cómo RAII y los punteros '
             'inteligentes resuelven el problema.'),
            ('Clases, constructores y destructores', 50, None,
             'El ciclo de vida de un objeto en C++ y la regla de los tres/cinco.'),
            ('Plantillas y programación genérica', 45, None,
             'Funciones y clases que funcionan con cualquier tipo, resueltas en tiempo '
             'de compilación.'),
            ('La biblioteca estándar (STL)', 50, None,
             'vector, map, set y los algoritmos más útiles. Por qué casi nunca hace '
             'falta escribir tu propia estructura de datos.'),
        ],
    ),
    (
        'Estructuras de datos y algoritmos', PROG, 'AVANZADO', '44.99',
        'Las estructuras y algoritmos que se preguntan en entrevistas técnicas y que '
        'de verdad usarás: listas, árboles, grafos, ordenamiento y búsqueda, con su '
        'análisis de complejidad.',
        '- Analizar la complejidad de un algoritmo (Big O)\n'
        '- Implementar listas enlazadas, pilas, colas y árboles\n'
        '- Recorrer grafos con BFS y DFS\n'
        '- Elegir la estructura adecuada para cada problema',
        '- Saber programar con soltura en algún lenguaje\n- Manejar recursividad básica',
        [
            ('Complejidad y notación Big O', 45, 'RBSGKlAvoiM',
             'Cómo medir el costo de un algoritmo sin cronómetro. Los órdenes más '
             'comunes y qué significan en la práctica.'),
            ('Arreglos y listas enlazadas', 50, None,
             'Costo real de insertar, borrar y buscar en cada una, y por qué a veces '
             'la lista enlazada es peor de lo que parece.'),
            ('Pilas y colas', 40, None,
             'Dos estructuras simples con muchísimas aplicaciones: deshacer, recorridos '
             'y planificación de tareas.'),
            ('Árboles binarios de búsqueda', 55, None,
             'Inserción, búsqueda y recorridos. Qué pasa cuando el árbol se '
             'desbalancea y por qué existen los árboles AVL.'),
            ('Tablas hash', 45, None,
             'Cómo logran búsquedas en tiempo constante y qué ocurre ante colisiones.'),
            ('Grafos: BFS y DFS', 55, None,
             'Representación con listas de adyacencia y los dos recorridos '
             'fundamentales, con ejemplos de caminos mínimos.'),
            ('Algoritmos de ordenamiento', 50, None,
             'Burbuja, inserción, merge sort y quicksort comparados por complejidad y '
             'por comportamiento real.'),
        ],
    ),

    # ---------------------------------------------------------------- Desarrollo Web
    (
        'HTML y CSS: bases sólidas', WEB, 'BASICO', '9.99',
        'Construye páginas web bien estructuradas y con diseño adaptable. HTML '
        'semántico, CSS moderno, Flexbox y Grid explicados desde cero.',
        '- Escribir HTML semántico y accesible\n'
        '- Maquetar con Flexbox y CSS Grid\n'
        '- Crear diseños adaptables a móvil\n'
        '- Organizar el CSS de forma mantenible',
        '- Solo un navegador y un editor de texto\n- Sin conocimientos previos',
        [
            ('Estructura de un documento HTML', 25, None,
             'Las etiquetas imprescindibles, la diferencia entre bloque y línea, y por '
             'qué el HTML semántico importa para la accesibilidad.'),
            ('Texto, enlaces e imágenes', 30, None,
             'Encabezados jerárquicos, listas, enlaces internos y externos, e imágenes '
             'con su texto alternativo.'),
            ('Formularios', 35, None,
             'Campos, etiquetas asociadas, validación nativa del navegador y buenas '
             'prácticas de usabilidad.'),
            ('CSS: selectores y el modelo de caja', 40, None,
             'Cómo apuntar a los elementos y cómo se calculan márgenes, bordes y '
             'relleno. El valor de box-sizing.'),
            ('Flexbox', 45, None,
             'Alinear y distribuir elementos en una dimensión. Los ejes principal y '
             'transversal explicados con ejemplos visuales.'),
            ('CSS Grid y diseño adaptable', 45, None,
             'Maquetación en dos dimensiones y media queries para adaptar el diseño a '
             'cualquier pantalla.'),
        ],
    ),
    (
        'React en la práctica', WEB, 'INTERMEDIO', '39.99',
        'Construye interfaces modernas con React: componentes, hooks, estado y '
        'consumo de APIs, aplicando todo en un proyecto que crece a lo largo del curso.',
        '- Componer interfaces con componentes reutilizables\n'
        '- Manejar estado con useState y useReducer\n'
        '- Consumir APIs REST y manejar los estados de carga y error\n'
        '- Navegar entre vistas con React Router',
        '- JavaScript moderno (ES6+)\n- HTML y CSS\n- Nociones de npm',
        [
            ('Componentes y JSX', 35, 'bMknfKXIFA8',
             'Qué es un componente, cómo se compone la interfaz y qué hace JSX por '
             'debajo.'),
            ('Props y composición', 40, None,
             'Pasar datos de padre a hijo, children, y por qué la composición evita '
             'componentes gigantes.'),
            ('Estado con useState', 45, None,
             'Qué es el estado, cuándo un dato debe serlo, y el error clásico de '
             'mutarlo directamente.'),
            ('Efectos con useEffect', 50, None,
             'Sincronizar con sistemas externos, el arreglo de dependencias y la '
             'función de limpieza.'),
            ('Consumo de APIs y manejo de errores', 45, None,
             'Cargar datos al montar, mostrar el estado de carga y qué hacer cuando la '
             'petición falla.'),
            ('Rutas con React Router', 40, None,
             'Navegación entre vistas, parámetros de URL y rutas protegidas.'),
            ('Proyecto: panel con datos reales', 55, None,
             'Integramos todo en una aplicación que lista, filtra y detalla información '
             'traída de una API.'),
        ],
    ),
    (
        'JavaScript asíncrono y consumo de APIs', WEB, 'INTERMEDIO', '29.99',
        'Entiende de una vez el event loop, las promesas y async/await. Cómo consumir '
        'APIs sin caer en el infierno de los callbacks.',
        '- Entender el event loop y por qué JavaScript no se bloquea\n'
        '- Trabajar con promesas y async/await\n'
        '- Consumir APIs REST con fetch\n'
        '- Manejar errores y peticiones en paralelo',
        '- JavaScript básico\n- Haber usado funciones y objetos',
        [
            ('El event loop explicado', 40, 'jS4aFq5-91M',
             'Por qué un solo hilo puede atender muchas cosas a la vez. La pila, la '
             'cola de tareas y los microtasks.'),
            ('Callbacks y sus problemas', 30, None,
             'El patrón original de asincronía en JavaScript y por qué anidarlos se '
             'vuelve inmanejable.'),
            ('Promesas', 45, None,
             'Los tres estados de una promesa, encadenamiento con then y captura de '
             'errores con catch.'),
            ('async / await', 40, None,
             'Escribir código asíncrono que se lee como síncrono, y el manejo de '
             'errores con try/catch.'),
            ('fetch y consumo de APIs', 45, None,
             'Peticiones GET y POST, cabeceras, códigos de estado y por qué fetch no '
             'rechaza ante un 404.'),
            ('Peticiones en paralelo', 35, None,
             'Promise.all y Promise.allSettled para no encadenar esperas innecesarias.'),
        ],
    ),
    (
        'APIs REST con Node.js y Express', WEB, 'INTERMEDIO', '34.99',
        'Diseña y construye una API REST completa con Node y Express: rutas, '
        'middleware, autenticación con JWT y conexión a base de datos.',
        '- Diseñar rutas REST coherentes\n'
        '- Escribir middleware propio\n'
        '- Autenticar usuarios con JWT\n'
        '- Conectar la API a una base de datos',
        '- JavaScript moderno\n- Nociones de HTTP',
        [
            ('Node.js y el primer servidor', 40, 'Oe421EPjeBE',
             'Qué es Node, cómo funciona npm y cómo levantar un servidor HTTP mínimo.'),
            ('Express: rutas y parámetros', 45, None,
             'Definir endpoints, leer parámetros de ruta y de consulta, y devolver '
             'respuestas JSON.'),
            ('Diseño de una API REST', 40, '-MTSQjw5DrM',
             'Recursos, verbos HTTP y códigos de estado. Cómo nombrar rutas de forma '
             'que se entiendan solas.'),
            ('Middleware', 40, None,
             'La cadena de middleware de Express, para qué sirve, y cómo escribir uno '
             'propio para registro y validación.'),
            ('Autenticación con JWT', 50, None,
             'Emitir y verificar tokens, proteger rutas y por qué el token no debe '
             'guardar información sensible.'),
            ('Conexión a base de datos', 45, None,
             'Persistir los datos, separar la capa de acceso y manejar errores de '
             'conexión.'),
        ],
    ),
    (
        'Django 5 profesional', WEB, 'INTERMEDIO', '44.99',
        'El framework web de Python de punta a punta: modelos, vistas, plantillas, '
        'el ORM, el panel de administración y una API REST con Django REST Framework.',
        '- Modelar datos con el ORM de Django\n'
        '- Escribir vistas y plantillas\n'
        '- Aprovechar el panel de administración\n'
        '- Construir una API con Django REST Framework',
        '- Python intermedio\n- Nociones de HTML y de bases de datos',
        [
            ('Instalación y estructura de un proyecto', 35, 'F5mRW0jo-U4',
             'Proyecto contra aplicación, el archivo settings y qué hace cada comando '
             'de manage.py.'),
            ('Modelos y migraciones', 50, None,
             'Definir el modelo de datos en Python y dejar que Django genere el '
             'esquema SQL. Qué hace realmente una migración.'),
            ('El ORM: consultas', 50, None,
             'filter, exclude, annotate y select_related. Cómo evitar el problema de '
             'las N+1 consultas.'),
            ('Vistas y plantillas', 45, None,
             'Vistas basadas en funciones y en clases, el sistema de plantillas y el '
             'paso de contexto.'),
            ('El panel de administración', 35, None,
             'Registrar modelos, personalizar listados y filtros, y por qué ahorra '
             'semanas de trabajo.'),
            ('API REST con DRF', 55, None,
             'Serializers, vistas genéricas, permisos y autenticación con tokens.'),
            ('Señales y tareas en segundo plano', 40, None,
             'Reaccionar a eventos del modelo y delegar trabajo pesado a Celery.'),
        ],
    ),

    # ---------------------------------------------------------------- Bases de Datos
    (
        'SQL para análisis de datos', BD, 'BASICO', '14.99',
        'Consulta bases de datos relacionales como un analista: desde el SELECT '
        'básico hasta funciones de ventana, con ejemplos sobre un modelo de ventas.',
        '- Escribir consultas con JOIN de varias tablas\n'
        '- Agrupar y agregar datos con GROUP BY\n'
        '- Usar subconsultas y CTEs\n'
        '- Aplicar funciones de ventana',
        '- Nociones de qué es una base de datos\n- Sin experiencia previa en SQL',
        [
            ('SELECT, WHERE y ORDER BY', 35, 'HXV3zeQKqGY',
             'La consulta más usada del mundo. Filtrar filas, elegir columnas y '
             'ordenar resultados.'),
            ('JOIN: combinar tablas', 50, None,
             'INNER, LEFT y RIGHT JOIN explicados con diagramas. El error clásico de '
             'olvidar la condición y generar un producto cartesiano.'),
            ('Agregaciones y GROUP BY', 45, None,
             'COUNT, SUM, AVG y la diferencia entre WHERE y HAVING.'),
            ('Subconsultas y CTEs', 45, None,
             'Consultas dentro de consultas y cómo WITH las vuelve legibles.'),
            ('Funciones de ventana', 50, None,
             'ROW_NUMBER, RANK y SUM OVER: cálculos por grupo sin perder el detalle '
             'de cada fila.'),
        ],
    ),
    (
        'Diseño de bases de datos relacionales', BD, 'INTERMEDIO', '24.99',
        'Antes de escribir SQL hay que diseñar bien. Modelo entidad-relación, '
        'normalización, claves e índices, con los errores más comunes y cómo evitarlos.',
        '- Construir un modelo entidad-relación\n'
        '- Normalizar hasta la tercera forma normal\n'
        '- Elegir claves primarias y foráneas adecuadas\n'
        '- Decidir qué indexar y qué no',
        '- Saber lo básico de SQL\n- Nociones de qué es una tabla',
        [
            ('Entidades, atributos y relaciones', 40, 'ztHopE5Wnpc',
             'Traducir un problema del mundo real a un modelo de datos. Cardinalidad '
             'y participación.'),
            ('Claves primarias y foráneas', 35, None,
             'Claves naturales contra claves subrogadas, y qué garantiza realmente la '
             'integridad referencial.'),
            ('Normalización', 50, None,
             'Primera, segunda y tercera forma normal explicadas con un ejemplo que se '
             'va corrigiendo paso a paso.'),
            ('Cuándo desnormalizar', 35, None,
             'La normalización no siempre gana. Casos legítimos para duplicar datos a '
             'propósito.'),
            ('Índices', 45, None,
             'Cómo aceleran las consultas, cuánto cuestan al escribir, y por qué '
             'indexar todo es contraproducente.'),
        ],
    ),
    (
        'PostgreSQL avanzado', BD, 'AVANZADO', '34.99',
        'Saca provecho real de PostgreSQL: tipos avanzados, JSONB, transacciones, '
        'niveles de aislamiento y lectura de planes de ejecución.',
        '- Usar JSONB y tipos avanzados\n'
        '- Entender transacciones y niveles de aislamiento\n'
        '- Leer un plan de ejecución con EXPLAIN\n'
        '- Optimizar consultas lentas',
        '- SQL intermedio\n- Haber trabajado con alguna base relacional',
        [
            ('Más allá del SQL estándar', 40, 'qw--VYLpxG4',
             'Qué ofrece PostgreSQL que otros motores no: arreglos, tipos '
             'personalizados y extensiones.'),
            ('JSONB', 45, None,
             'Guardar documentos dentro de una base relacional sin renunciar a las '
             'consultas ni a los índices.'),
            ('Transacciones y aislamiento', 50, None,
             'ACID en la práctica. Lecturas sucias, no repetibles y fantasmas, y qué '
             'nivel las previene.'),
            ('Bloqueos y concurrencia', 45, None,
             'SELECT FOR UPDATE, interbloqueos y cómo diseñar para que dos procesos no '
             'se pisen.'),
            ('EXPLAIN y optimización', 55, None,
             'Leer un plan de ejecución, identificar escaneos secuenciales '
             'innecesarios y decidir el índice correcto.'),
        ],
    ),
    (
        'MongoDB para desarrolladores', BD, 'INTERMEDIO', '24.99',
        'Bases de datos de documentos: cuándo convienen y cuándo no. Modelado, '
        'consultas, el framework de agregación e índices en MongoDB.',
        '- Modelar datos en documentos\n'
        '- Consultar y actualizar colecciones\n'
        '- Usar el framework de agregación\n'
        '- Saber cuándo NO usar MongoDB',
        '- Nociones de bases de datos\n- JavaScript básico ayuda',
        [
            ('Documentos contra tablas', 35, 'c2M-rlkkT5o',
             'En qué se diferencia realmente de una base relacional, y los casos donde '
             'cada una gana.'),
            ('Consultas y actualizaciones', 40, None,
             'find, los operadores de consulta, y las formas de actualizar documentos.'),
            ('Modelado: incrustar o referenciar', 45, None,
             'La decisión más importante en MongoDB, con las reglas prácticas para '
             'elegir bien.'),
            ('Framework de agregación', 50, None,
             'La tubería de etapas: match, group, project y lookup.'),
            ('Índices y rendimiento', 35, None,
             'Índices simples y compuestos, y cómo verificar que la consulta los usa.'),
        ],
    ),

    # ---------------------------------------------------------------- Ciencia de Datos
    (
        'Introducción a la ciencia de datos', DATOS, 'BASICO', '19.99',
        'Qué hace realmente un científico de datos: el flujo completo desde la '
        'pregunta de negocio hasta la conclusión, con las herramientas del oficio.',
        '- Entender el flujo de un proyecto de datos\n'
        '- Distinguir análisis descriptivo, predictivo y prescriptivo\n'
        '- Conocer las herramientas del ecosistema\n'
        '- Plantear preguntas que los datos puedan responder',
        '- Nociones de matemáticas de bachillerato\n- No se necesita programar',
        [
            ('Qué es la ciencia de datos', 30, 'ua-CiDNNj30',
             'Dónde termina la estadística, dónde empieza el aprendizaje automático y '
             'qué aporta la programación.'),
            ('El flujo de un proyecto', 40, None,
             'Pregunta, obtención, limpieza, análisis, modelo y comunicación. Por qué '
             'la limpieza se lleva la mayor parte del tiempo.'),
            ('Tipos de análisis', 35, None,
             'Descriptivo, diagnóstico, predictivo y prescriptivo, con ejemplos de '
             'cada uno.'),
            ('Herramientas del ecosistema', 35, None,
             'Python, R, SQL, cuadernos Jupyter y herramientas de visualización: qué '
             'usar para qué.'),
            ('Comunicar resultados', 40, None,
             'El análisis que nadie entiende no sirve. Cómo presentar hallazgos a '
             'quien toma decisiones.'),
        ],
    ),
    (
        'Análisis de datos con Python y Pandas', DATOS, 'INTERMEDIO', '34.99',
        'Pandas a fondo: cargar, limpiar, transformar y resumir datos reales. El '
        'curso está construido sobre conjuntos de datos con los problemas de siempre.',
        '- Cargar datos desde CSV, Excel y bases de datos\n'
        '- Limpiar valores faltantes y duplicados\n'
        '- Agrupar y resumir con groupby\n'
        '- Combinar varias fuentes con merge',
        '- Python básico\n- Nociones de estructuras de datos',
        [
            ('Series y DataFrames', 40, 'r-uOLxNrNk8',
             'Las dos estructuras de Pandas, cómo se indexan y por qué el índice '
             'importa más de lo que parece.'),
            ('Cargar y explorar datos', 45, 'vmEHCJofslg',
             'read_csv y sus opciones, y los primeros comandos para entender un '
             'conjunto de datos desconocido.'),
            ('Limpieza de datos', 50, None,
             'Valores faltantes, duplicados, tipos mal inferidos y textos '
             'inconsistentes: el trabajo real del análisis.'),
            ('Filtrado y transformación', 45, None,
             'Selección por condiciones, columnas calculadas y apply frente a las '
             'operaciones vectorizadas.'),
            ('groupby y tablas dinámicas', 50, None,
             'Resumir por categorías, agregaciones múltiples y pivot_table.'),
            ('Combinar fuentes con merge', 40, None,
             'Los tipos de unión en Pandas y cómo detectar cuando una unión duplicó '
             'filas sin que te dieras cuenta.'),
        ],
    ),
    (
        'Visualización de datos con Python', DATOS, 'INTERMEDIO', '29.99',
        'Gráficos que comunican: qué gráfico usar para cada pregunta, y cómo '
        'construirlos con Matplotlib y Seaborn sin pelear con la biblioteca.',
        '- Elegir el gráfico correcto para cada dato\n'
        '- Construir figuras con Matplotlib\n'
        '- Usar Seaborn para gráficos estadísticos\n'
        '- Evitar los errores que distorsionan la lectura',
        '- Python básico\n- Conocer Pandas ayuda mucho',
        [
            ('Qué gráfico usar', 35, 'GPVsHOlRBBI',
             'Comparación, distribución, composición y relación: cada pregunta pide un '
             'tipo de gráfico distinto.'),
            ('Matplotlib: figura y ejes', 45, None,
             'El modelo de objetos de Matplotlib. Por qué entender figura contra ejes '
             'resuelve la mayoría de las frustraciones.'),
            ('Gráficos estadísticos con Seaborn', 45, None,
             'Distribuciones, cajas, violines y mapas de calor con una línea de código.'),
            ('Errores que distorsionan', 35, None,
             'Ejes truncados, gráficos de torta con demasiadas porciones y escalas '
             'engañosas.'),
            ('Preparar gráficos para presentar', 40, None,
             'Títulos, etiquetas, anotaciones y exportación con la resolución adecuada.'),
        ],
    ),
    (
        'Estadística aplicada con Python', DATOS, 'BASICO', '24.99',
        'La estadística que de verdad se usa en análisis de datos, explicada con '
        'código en lugar de demostraciones: descriptiva, distribuciones y pruebas.',
        '- Resumir datos con medidas de tendencia y dispersión\n'
        '- Entender las distribuciones más comunes\n'
        '- Interpretar correlación sin confundirla con causalidad\n'
        '- Aplicar pruebas de hipótesis básicas',
        '- Python básico\n- Matemáticas de bachillerato',
        [
            ('Estadística descriptiva', 40, 'LHBE6Q9XlzI',
             'Media, mediana, moda y desviación estándar. Cuándo la media engaña y la '
             'mediana no.'),
            ('Distribuciones', 45, None,
             'Normal, binomial y de Poisson, y cómo reconocer cuál se ajusta a tus '
             'datos.'),
            ('Correlación', 40, None,
             'Coeficiente de Pearson, correlación contra causalidad y el peligro de '
             'las variables ocultas.'),
            ('Muestreo e intervalos de confianza', 45, None,
             'Por qué una muestra puede hablar por la población, y qué significa '
             'realmente un intervalo del 95%.'),
            ('Pruebas de hipótesis', 50, None,
             'La lógica del valor p, el error de interpretarlo como probabilidad de '
             'acertar, y las pruebas más usadas.'),
        ],
    ),

    # ---------------------------------------------------------------- IA
    (
        'Machine Learning con scikit-learn', IA, 'AVANZADO', '49.99',
        'Aprendizaje automático aplicado: regresión, clasificación, validación y '
        'evaluación de modelos con scikit-learn, sin perderse en la matemática.',
        '- Entrenar modelos de regresión y clasificación\n'
        '- Preparar datos: escalado y codificación\n'
        '- Validar con partición y validación cruzada\n'
        '- Elegir métricas adecuadas a cada problema',
        '- Python intermedio\n- Pandas y NumPy\n- Estadística básica',
        [
            ('Qué es el aprendizaje automático', 40, 'i_LwzRVP7bg',
             'Supervisado contra no supervisado, y en qué se diferencia de programar '
             'reglas a mano.'),
            ('Preparación de los datos', 50, None,
             'Escalado, codificación de variables categóricas y por qué el orden de '
             'las operaciones importa.'),
            ('Regresión lineal', 45, '7eh4d6sabA0',
             'El modelo más simple y el más explicable. Qué significan realmente los '
             'coeficientes.'),
            ('Clasificación', 50, None,
             'Regresión logística, árboles de decisión y bosques aleatorios.'),
            ('Sobreajuste y validación', 50, None,
             'Por qué un modelo perfecto en entrenamiento suele ser malo en '
             'producción. Validación cruzada.'),
            ('Métricas de evaluación', 45, None,
             'Exactitud, precisión, exhaustividad y F1. Por qué la exactitud engaña '
             'con clases desbalanceadas.'),
        ],
    ),
    (
        'Redes neuronales explicadas', IA, 'INTERMEDIO', '39.99',
        'Entiende qué hace realmente una red neuronal por dentro: neuronas, capas, '
        'función de pérdida y retropropagación, con intuición visual antes que fórmulas.',
        '- Entender qué calcula una neurona\n'
        '- Seguir el flujo de una red hacia adelante\n'
        '- Comprender el descenso de gradiente\n'
        '- Saber qué hace la retropropagación',
        '- Álgebra básica\n- Nociones de programación',
        [
            ('Qué es una red neuronal', 40, 'aircAruvnKk',
             'De la neurona individual a la red completa, explicado visualmente con el '
             'ejemplo del reconocimiento de dígitos.'),
            ('Capas, pesos y sesgos', 45, None,
             'Cómo se combinan las entradas y qué representa cada parámetro.'),
            ('Funciones de activación', 35, None,
             'Por qué sin ellas la red entera colapsa a una función lineal. Sigmoide, '
             'ReLU y sus variantes.'),
            ('Función de pérdida y descenso de gradiente', 50, None,
             'Cómo mide la red su propio error y cómo se corrige paso a paso.'),
            ('Retropropagación', 50, None,
             'El algoritmo que reparte la culpa del error entre todos los pesos, sin '
             'la maraña de índices.'),
        ],
    ),
    (
        'Deep Learning con TensorFlow', IA, 'AVANZADO', '54.99',
        'Del perceptrón a las redes convolucionales y recurrentes, implementando '
        'todo con TensorFlow y Keras sobre problemas reales.',
        '- Construir redes con Keras\n'
        '- Entrenar redes convolucionales para imágenes\n'
        '- Aplicar redes recurrentes a secuencias\n'
        '- Usar transferencia de aprendizaje',
        '- Python intermedio\n- Fundamentos de aprendizaje automático\n- NumPy',
        [
            ('TensorFlow y Keras', 45, 'tPYj3fFJGjk',
             'El ecosistema, la API secuencial y la funcional, y cómo se entrena un '
             'modelo en unas pocas líneas.'),
            ('Red neuronal densa', 50, None,
             'Primer modelo completo: arquitectura, compilación, entrenamiento y '
             'evaluación.'),
            ('Redes convolucionales', 55, None,
             'Convolución y agrupamiento explicados con imágenes. Por qué funcionan '
             'tan bien en visión.'),
            ('Regularización', 45, None,
             'Abandono, parada temprana y aumento de datos para combatir el '
             'sobreajuste.'),
            ('Transferencia de aprendizaje', 50, None,
             'Reutilizar un modelo entrenado por otros y ajustarlo a tu problema con '
             'pocos datos.'),
            ('Redes recurrentes', 50, None,
             'Secuencias y series temporales: RNN, LSTM y para qué sirve cada una.'),
        ],
    ),

    # ---------------------------------------------------------------- Cloud y DevOps
    (
        'Docker desde cero', CLOUD, 'INTERMEDIO', '34.99',
        'Contenedores explicados de verdad: imágenes, capas, volúmenes, redes y '
        'Docker Compose, con ejemplos que resuelven el "en mi máquina funciona".',
        '- Entender qué es realmente un contenedor\n'
        '- Escribir Dockerfiles eficientes\n'
        '- Manejar volúmenes y redes\n'
        '- Orquestar varios servicios con Compose',
        '- Manejo básico de la terminal\n- Nociones de Linux ayudan',
        [
            ('Contenedores contra máquinas virtuales', 40, '3c-iBn73dDE',
             'Qué comparte un contenedor con el anfitrión y por qué arranca en '
             'segundos.'),
            ('Imágenes y capas', 45, 'pTFZFxd4hOI',
             'Cómo se construye una imagen, por qué el orden de las instrucciones '
             'afecta la caché, y cómo reducir el tamaño final.'),
            ('El Dockerfile', 50, None,
             'Las instrucciones más usadas y los errores que hacen la imagen enorme o '
             'insegura.'),
            ('Volúmenes y persistencia', 40, None,
             'Los datos sobreviven al contenedor solo si lo decides. Volúmenes '
             'nombrados contra montajes.'),
            ('Redes entre contenedores', 40, None,
             'Cómo se ven entre sí, la resolución por nombre de servicio y la '
             'publicación de puertos.'),
            ('Docker Compose', 50, None,
             'Definir un sistema completo en un archivo y levantarlo con un comando.'),
        ],
    ),
    (
        'Kubernetes para desarrolladores', CLOUD, 'AVANZADO', '49.99',
        'Orquestación de contenedores en serio: pods, despliegues, servicios, '
        'configuración y escalado, desde el punto de vista de quien desarrolla.',
        '- Entender la arquitectura de Kubernetes\n'
        '- Desplegar aplicaciones con Deployments\n'
        '- Exponer servicios y gestionar el tráfico\n'
        '- Manejar configuración y secretos',
        '- Docker a nivel práctico\n- Nociones de redes',
        [
            ('Arquitectura de Kubernetes', 50, 'X48VuDVv0do',
             'Plano de control, nodos y el modelo declarativo: le dices qué quieres, '
             'no cómo lograrlo.'),
            ('Pods y ReplicaSets', 45, None,
             'La unidad mínima de despliegue y cómo se mantiene el número de réplicas '
             'deseado.'),
            ('Deployments y actualizaciones', 50, None,
             'Despliegues progresivos, reversión y estrategias de actualización sin '
             'cortar el servicio.'),
            ('Servicios e Ingress', 50, None,
             'Cómo se llega a un pod que cambia de IP constantemente, y cómo se expone '
             'al exterior.'),
            ('ConfigMaps y Secrets', 40, None,
             'Separar la configuración de la imagen, y las limitaciones reales de los '
             'Secrets.'),
            ('Escalado y sondas de salud', 45, None,
             'Escalado automático, y las sondas que le dicen a Kubernetes si tu '
             'aplicación está viva y lista.'),
        ],
    ),
    (
        'AWS: primeros pasos en la nube', CLOUD, 'BASICO', '29.99',
        'Los servicios de AWS que realmente vas a usar al principio: cómputo, '
        'almacenamiento, bases de datos y control de acceso, sin marear con el catálogo completo.',
        '- Entender el modelo de responsabilidad compartida\n'
        '- Lanzar y conectarte a una instancia EC2\n'
        '- Guardar archivos en S3\n'
        '- Controlar accesos con IAM',
        '- Nociones de redes e internet\n- Manejo de terminal',
        [
            ('Qué es la nube y qué ofrece AWS', 35, 'ubCNZRNjhyo',
             'Modelos de servicio, regiones y zonas de disponibilidad, y el modelo de '
             'responsabilidad compartida.'),
            ('IAM: usuarios, roles y políticas', 45, None,
             'El servicio que más se descuida y el que más problemas causa. Principio '
             'de menor privilegio.'),
            ('EC2: servidores virtuales', 50, None,
             'Lanzar una instancia, grupos de seguridad, pares de llaves y cómo no '
             'dejar el puerto 22 abierto al mundo.'),
            ('S3: almacenamiento de objetos', 40, None,
             'Cubetas, objetos, clases de almacenamiento y el error clásico de dejar '
             'una cubeta pública.'),
            ('Bases de datos gestionadas', 40, None,
             'RDS contra instalar tu propio motor: qué ganas y qué cedes.'),
            ('Costos y cómo no llevarte un susto', 35, None,
             'Capa gratuita, alertas de facturación y los servicios que se cobran '
             'aunque no los uses.'),
        ],
    ),

    # ---------------------------------------------------------------- Ciberseguridad
    (
        'Fundamentos de ciberseguridad', CIBER, 'BASICO', '29.99',
        'Los conceptos que todo profesional de tecnología debería manejar: amenazas, '
        'criptografía, autenticación y buenas prácticas, sin necesidad de ser especialista.',
        '- Reconocer las amenazas más comunes\n'
        '- Entender cifrado simétrico y asimétrico\n'
        '- Aplicar autenticación robusta\n'
        '- Identificar intentos de ingeniería social',
        '- Nociones de redes e internet\n- Sin conocimientos previos de seguridad',
        [
            ('El panorama de amenazas', 35, 'inWWhr5tnEA',
             'Malware, phishing, ransomware y ataques de denegación: qué son y cómo '
             'llegan.'),
            ('La tríada CIA', 30, 'bPVaOlJ6ln0',
             'Confidencialidad, integridad y disponibilidad como marco para pensar '
             'cualquier decisión de seguridad.'),
            ('Criptografía en la práctica', 50, None,
             'Cifrado simétrico y asimétrico, funciones hash y firmas digitales, sin '
             'la matemática de fondo.'),
            ('Contraseñas y autenticación', 45, None,
             'Por qué el hash con sal importa, qué aporta el segundo factor y cómo se '
             'roban las credenciales.'),
            ('Ingeniería social', 40, None,
             'El eslabón más débil casi nunca es técnico. Casos reales y cómo '
             'reconocerlos.'),
            ('Higiene de seguridad', 35, None,
             'Actualizaciones, respaldos, menor privilegio y segmentación: lo aburrido '
             'que sí funciona.'),
        ],
    ),
    (
        'Hacking ético y pruebas de penetración', CIBER, 'AVANZADO', '54.99',
        'Metodología de pruebas de penetración con autorización: reconocimiento, '
        'escaneo, explotación y reporte. Enfocado en aprender a defender entendiendo cómo se ataca.',
        '- Aplicar una metodología estructurada de pentesting\n'
        '- Hacer reconocimiento y escaneo de una red\n'
        '- Identificar vulnerabilidades comunes\n'
        '- Redactar un informe de hallazgos útil',
        '- Redes y protocolos TCP/IP\n- Manejo de Linux\n'
        '- IMPORTANTE: estas técnicas solo se aplican sobre sistemas propios o con autorización escrita',
        [
            ('Ética, alcance y autorización', 40, '3FNYvj2U0HM',
             'Lo primero no es técnico: qué es un alcance, por qué la autorización '
             'escrita es innegociable y dónde está el límite legal.'),
            ('Metodología de una prueba', 45, None,
             'Las fases de una prueba de penetración y qué se busca en cada una.'),
            ('Reconocimiento', 50, None,
             'Información pública, enumeración de subdominios y cuánto se puede '
             'averiguar sin tocar el objetivo.'),
            ('Escaneo y enumeración', 50, 'qiQR5rTSshw',
             'Puertos, servicios y versiones. Cómo se construye el mapa de la '
             'superficie de ataque.'),
            ('Vulnerabilidades web comunes', 55, None,
             'Inyección, autenticación rota y configuración insegura, con el enfoque '
             'del OWASP Top 10.'),
            ('El informe', 40, None,
             'Un hallazgo sin informe claro no sirve. Severidad, evidencia y '
             'recomendaciones accionables.'),
        ],
    ),

    # ---------------------------------------------------------------- Móvil
    (
        'Desarrollo Android desde cero', MOVIL, 'BASICO', '29.99',
        'Tu primera aplicación Android: Android Studio, actividades, interfaces, '
        'navegación y persistencia, paso a paso.',
        '- Manejar Android Studio con soltura\n'
        '- Construir interfaces y navegar entre pantallas\n'
        '- Entender el ciclo de vida de una actividad\n'
        '- Guardar datos localmente',
        '- Nociones de programación\n- Java o Kotlin básico ayuda',
        [
            ('Android Studio y el primer proyecto', 40, 'fis26HvvDII',
             'Instalación, estructura de un proyecto, el emulador y cómo ejecutar en '
             'un dispositivo real.'),
            ('Interfaces y layouts', 50, None,
             'Componer pantallas, contenedores y adaptación a distintos tamaños.'),
            ('Ciclo de vida de una actividad', 45, None,
             'El concepto que más errores causa al principio: qué pasa al girar la '
             'pantalla o recibir una llamada.'),
            ('Navegación entre pantallas', 40, None,
             'Intents, paso de datos y la pila de retroceso.'),
            ('Listas con RecyclerView', 50, None,
             'Mostrar colecciones de forma eficiente y el patrón adaptador.'),
            ('Persistencia local', 40, None,
             'Preferencias y base de datos local para que los datos sobrevivan al '
             'cierre.'),
        ],
    ),
    (
        'Kotlin para Android', MOVIL, 'INTERMEDIO', '34.99',
        'El lenguaje oficial de Android a fondo: sintaxis, null safety, funciones de '
        'extensión y corrutinas, con enfoque en lo que cambia respecto a Java.',
        '- Escribir Kotlin idiomático\n'
        '- Aprovechar la seguridad ante nulos\n'
        '- Usar funciones de extensión y lambdas\n'
        '- Manejar asincronía con corrutinas',
        '- Programación orientada a objetos\n- Java básico ayuda pero no es obligatorio',
        [
            ('Sintaxis y diferencias con Java', 40, 'F9UC9DY-vIU',
             'Lo que Kotlin quita y lo que agrega. Por qué el mismo programa ocupa la '
             'mitad de líneas.'),
            ('Seguridad ante nulos', 45, None,
             'El sistema de tipos que elimina la excepción de puntero nulo. Los '
             'operadores ?., ?: y !!.'),
            ('Funciones, lambdas y extensiones', 50, None,
             'Funciones de orden superior y cómo extender clases existentes sin '
             'heredar de ellas.'),
            ('Clases de datos y sealed', 40, None,
             'Modelar datos con muchas menos líneas, y jerarquías cerradas para '
             'estados bien definidos.'),
            ('Corrutinas', 55, None,
             'Asincronía sin callbacks: alcances, dispatchers y cómo no bloquear el '
             'hilo principal.'),
        ],
    ),
    (
        'Flutter: apps multiplataforma', MOVIL, 'INTERMEDIO', '39.99',
        'Una sola base de código para Android e iOS. Widgets, estado, navegación y '
        'consumo de APIs con Flutter y Dart.',
        '- Componer interfaces con widgets\n'
        '- Manejar el estado de la aplicación\n'
        '- Navegar entre pantallas\n'
        '- Consumir APIs REST y mostrar los datos',
        '- Programación orientada a objetos\n- Nociones de desarrollo móvil ayudan',
        [
            ('Flutter y Dart: primeros pasos', 45, 'VPvVD8t02U8',
             'Instalación, estructura del proyecto y por qué Flutter dibuja su propia '
             'interfaz en vez de usar los componentes nativos.'),
            ('Todo es un widget', 50, 'x0uinJvhNxI',
             'Widgets con y sin estado, el árbol de widgets y cómo se reconstruye.'),
            ('Composición de interfaces', 50, None,
             'Filas, columnas, contenedores y las reglas de restricción que explican '
             'los errores de desbordamiento.'),
            ('Manejo del estado', 55, None,
             'setState y sus límites, y cuándo conviene elevar el estado o usar un '
             'gestor externo.'),
            ('Navegación y rutas', 40, None,
             'Navegar entre pantallas, pasar y recibir datos.'),
            ('Consumo de APIs', 45, None,
             'Peticiones HTTP, decodificación de JSON y manejo de estados de carga y '
             'error.'),
        ],
    ),
]

# Preguntas del cuestionario (Actividad 1) de estos seis cursos, los primeros
# que lo tuvieron. Los otros veinticuatro están en _actividades_demo.CUESTIONARIOS;
# el comando `crear_actividades` junta los dos diccionarios. Estos conservan sus
# cinco preguntas originales en lugar de las tres de los demás.
# Cada opción es (texto, es_correcta).
PREGUNTAS = {
    'Python desde cero': [
        ('¿Cuál es la forma correcta de declarar una variable en Python?', [
            ('nombre = "Ana"', True), ('var nombre = "Ana"', False),
            ('String nombre = "Ana"', False), ('let nombre = "Ana"', False)]),
        ('¿Qué estructura permite elementos duplicados y mantiene el orden?', [
            ('La lista', True), ('El conjunto (set)', False),
            ('El diccionario', False), ('Ninguna de las anteriores', False)]),
        ('¿Qué palabra clave define una función?', [
            ('def', True), ('function', False), ('func', False), ('define', False)]),
        ('¿Cuál es el resultado de len([1, 2, 3])?', [
            ('3', True), ('2', False), ('6', False), ('Genera un error', False)]),
        ('¿Cuál es la forma recomendada de abrir un archivo?', [
            ('with open("datos.txt") as f:', True), ('open("datos.txt").read()', False),
            ('file = load("datos.txt")', False), ('read("datos.txt")', False)]),
    ],
    'SQL para análisis de datos': [
        ('¿Qué cláusula filtra filas ANTES de agrupar?', [
            ('WHERE', True), ('HAVING', False), ('GROUP BY', False), ('ORDER BY', False)]),
        ('¿Qué tipo de JOIN conserva todas las filas de la tabla izquierda?', [
            ('LEFT JOIN', True), ('INNER JOIN', False),
            ('CROSS JOIN', False), ('RIGHT JOIN', False)]),
        ('¿Qué función cuenta filas?', [
            ('COUNT()', True), ('SUM()', False), ('TOTAL()', False), ('NUM()', False)]),
        ('¿Qué pasa si haces JOIN sin condición de unión?', [
            ('Se genera un producto cartesiano', True), ('La consulta falla', False),
            ('Devuelve cero filas', False), ('Une por la clave primaria', False)]),
        ('¿Para qué sirve una CTE (WITH)?', [
            ('Para nombrar una subconsulta y hacerla legible', True),
            ('Para crear una tabla permanente', False),
            ('Para crear un índice', False), ('Para hacer respaldos', False)]),
    ],
    'React en la práctica': [
        ('¿Qué hook maneja estado local en un componente?', [
            ('useState', True), ('useEffect', False), ('useMemo', False), ('useRef', False)]),
        ('¿Qué es JSX?', [
            ('Una sintaxis que se transforma en llamadas a funciones', True),
            ('Un motor de plantillas HTML', False),
            ('Un preprocesador de CSS', False), ('Un formato de datos', False)]),
        ('¿Qué ocurre si omites el arreglo de dependencias de useEffect?', [
            ('El efecto se ejecuta en cada render', True),
            ('El efecto se ejecuta una sola vez', False),
            ('El efecto nunca se ejecuta', False), ('React lanza un error', False)]),
        ('¿Cómo se pasan datos de un componente padre a un hijo?', [
            ('Mediante props', True), ('Mediante estado global', False),
            ('Modificando el DOM', False), ('No es posible', False)]),
        ('¿Por qué no se debe modificar el estado directamente?', [
            ('React no detecta el cambio y no vuelve a renderizar', True),
            ('Genera un error de compilación', False),
            ('Es más lento', False), ('Sí se puede modificar directamente', False)]),
    ],
    'Docker desde cero': [
        ('¿Qué comparte un contenedor con el sistema anfitrión?', [
            ('El núcleo (kernel)', True), ('La memoria RAM completa', False),
            ('El sistema de archivos completo', False), ('Nada en absoluto', False)]),
        ('¿Qué instrucción del Dockerfile define el comando por defecto?', [
            ('CMD', True), ('RUN', False), ('COPY', False), ('FROM', False)]),
        ('¿Dónde deben ir los datos que deben sobrevivir al contenedor?', [
            ('En un volumen', True), ('En la imagen', False),
            ('En la capa de escritura del contenedor', False), ('En /tmp', False)]),
        ('¿Por qué el orden de las instrucciones afecta el tiempo de construcción?', [
            ('Por la caché de capas de Docker', True),
            ('Porque Docker las ejecuta en paralelo', False),
            ('No afecta en nada', False), ('Por el tamaño del contexto', False)]),
        ('En Docker Compose, ¿cómo se comunican dos servicios?', [
            ('Por el nombre del servicio, que resuelve por DNS interno', True),
            ('Solo por dirección IP fija', False),
            ('Mediante archivos compartidos', False),
            ('No pueden comunicarse', False)]),
    ],
    'Fundamentos de ciberseguridad': [
        ('¿Qué significa la "I" de la tríada CIA?', [
            ('Integridad', True), ('Identificación', False),
            ('Investigación', False), ('Infraestructura', False)]),
        ('¿Para qué sirve la sal (salt) al guardar contraseñas?', [
            ('Para que dos contraseñas iguales no produzcan el mismo hash', True),
            ('Para poder recuperar la contraseña original', False),
            ('Para cifrar la contraseña', False),
            ('Para acelerar el inicio de sesión', False)]),
        ('¿Qué caracteriza al cifrado asimétrico?', [
            ('Usa un par de llaves: una pública y una privada', True),
            ('Usa la misma llave para cifrar y descifrar', False),
            ('No usa llaves', False), ('Solo sirve para firmar', False)]),
        ('¿Qué es el phishing?', [
            ('Engañar a una persona para que entregue información', True),
            ('Un tipo de virus informático', False),
            ('Un ataque de denegación de servicio', False),
            ('Una técnica de cifrado', False)]),
        ('¿Qué establece el principio de menor privilegio?', [
            ('Dar solo los permisos necesarios para la tarea', True),
            ('Dar permisos de administrador a todos', False),
            ('Quitar todos los permisos', False),
            ('Rotar los permisos cada mes', False)]),
    ],
    'Análisis de datos con Python y Pandas': [
        ('¿Cuál es la estructura bidimensional de Pandas?', [
            ('DataFrame', True), ('Series', False), ('Array', False), ('Panel', False)]),
        ('¿Qué método muestra las primeras filas de un DataFrame?', [
            ('head()', True), ('first()', False), ('top()', False), ('start()', False)]),
        ('¿Qué hace groupby()?', [
            ('Agrupa filas por los valores de una o más columnas', True),
            ('Ordena el DataFrame', False),
            ('Elimina duplicados', False), ('Combina dos DataFrames', False)]),
        ('¿Qué riesgo tiene un merge mal planteado?', [
            ('Puede duplicar filas sin que lo notes', True),
            ('Siempre lanza un error', False),
            ('Borra el DataFrame original', False), ('No tiene ningún riesgo', False)]),
        ('¿Por qué se prefieren las operaciones vectorizadas sobre apply()?', [
            ('Son considerablemente más rápidas', True),
            ('Son más fáciles de leer siempre', False),
            ('apply() no existe en Pandas', False),
            ('No hay diferencia', False)]),
    ],
}
