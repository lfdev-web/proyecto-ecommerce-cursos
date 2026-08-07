"""
Contenido de las dos actividades evaluadas de cada curso.

Antes, terminar un curso era pulsar «completada» en cada lección: nada
verificaba que el alumno hubiera aprendido algo. Ahora, para certificarse hacen
falta tres cosas — ver el 100% de las lecciones, aprobar el cuestionario y
entregar el trabajo práctico:

    Actividad 1 — Cuestionario   (apps.exams.Exam, se califica solo)
    Actividad 2 — Trabajo práctico (apps.catalog.Assignment + entrega de archivo)

Los seis cursos que ya tenían examen final conservan sus cinco preguntas
(están en _catalogo_demo.PREGUNTAS); aquí van las de los otros veinticuatro.

Cada consigna y cada recurso de apoyo corresponden al tema real del curso: el
enlace de «Python desde cero» lleva a un libro de Python, no a un texto
genérico. Los recursos son documentación oficial o libros de acceso libre.

Formatos:
    CUESTIONARIOS[titulo] = [(pregunta, [(opcion, es_correcta), ...]), ...]
    TRABAJOS[titulo]      = (titulo_entrega, consigna, etiqueta_recurso, url_recurso)
"""

# ---------------------------------------------------------------------------
# Actividad 1 — Cuestionario (solo los cursos que aún no tenían examen)
# ---------------------------------------------------------------------------

CUESTIONARIOS = {
    # ------------------------------------------------------------ Programación
    'Programación orientada a objetos en Python': [
        ('¿Qué hace el método __init__ de una clase?', [
            ('Inicializa los atributos del objeto recién creado', True),
            ('Reserva la memoria del objeto', False),
            ('Destruye el objeto al terminar', False),
            ('Se ejecuta solo si la clase hereda de otra', False)]),
        ('¿Qué describe mejor el polimorfismo?', [
            ('Que objetos distintos respondan al mismo método a su manera', True),
            ('Que una clase tenga muchos atributos', False),
            ('Que un objeto cambie de tipo en tiempo de ejecución', False),
            ('Que dos clases tengan el mismo nombre', False)]),
        ('¿Cuándo conviene composición en lugar de herencia?', [
            ('Cuando la relación es "tiene un" y no "es un"', True),
            ('Siempre: la herencia nunca debe usarse', False),
            ('Solo cuando la clase base es abstracta', False),
            ('Cuando se necesitan métodos privados', False)]),
    ],
    'JavaScript moderno desde cero': [
        ('¿Cuál es la diferencia principal entre let y const?', [
            ('const impide reasignar la variable', True),
            ('let solo funciona dentro de funciones', False),
            ('const crea objetos inmutables por completo', False),
            ('No hay diferencia, son sinónimos', False)]),
        ('¿Qué devuelve el operador === al comparar 1 y "1"?', [
            ('false, porque compara valor y tipo', True),
            ('true, porque convierte el texto a número', False),
            ('Lanza un error de tipos', False),
            ('undefined', False)]),
        ('¿Qué hace el método map() de un arreglo?', [
            ('Devuelve un arreglo nuevo con el resultado de transformar cada elemento', True),
            ('Modifica el arreglo original en su lugar', False),
            ('Filtra los elementos que cumplen una condición', False),
            ('Reduce el arreglo a un solo valor', False)]),
    ],
    'TypeScript para proyectos reales': [
        ('¿Qué aporta TypeScript sobre JavaScript?', [
            ('Verificación de tipos antes de ejecutar el código', True),
            ('Mayor velocidad de ejecución en el navegador', False),
            ('Un motor propio distinto al de JavaScript', False),
            ('Acceso a APIs que JavaScript no tiene', False)]),
        ('¿Qué significa que un tipo sea "union" (A | B)?', [
            ('El valor puede ser de cualquiera de los dos tipos', True),
            ('El valor debe cumplir ambos tipos a la vez', False),
            ('Es un tipo que hereda de A y de B', False),
            ('Es un arreglo que mezcla A y B', False)]),
        ('¿Por qué se desaconseja usar el tipo any?', [
            ('Desactiva la verificación de tipos y anula la ventaja de TypeScript', True),
            ('Hace más lento el programa compilado', False),
            ('No está permitido en versiones recientes', False),
            ('Solo puede usarse dentro de clases', False)]),
    ],
    'C++ de principiante a avanzado': [
        ('¿Qué diferencia hay entre una referencia y un puntero?', [
            ('La referencia no puede ser nula ni reasignarse a otro objeto', True),
            ('El puntero no puede modificar el valor apuntado', False),
            ('La referencia ocupa siempre 8 bytes más', False),
            ('No hay diferencia práctica', False)]),
        ('¿Qué problema resuelve std::unique_ptr?', [
            ('Libera la memoria automáticamente al salir del ámbito', True),
            ('Permite que dos punteros compartan el mismo objeto', False),
            ('Acelera la reserva de memoria en el heap', False),
            ('Evita tener que incluir cabeceras', False)]),
        ('¿Qué es RAII?', [
            ('Atar la vida de un recurso a la vida de un objeto', True),
            ('Un algoritmo de ordenamiento de la STL', False),
            ('Una forma de compilar sin enlazador', False),
            ('Una convención de nombres para clases', False)]),
    ],
    'Estructuras de datos y algoritmos': [
        ('¿Cuál es la complejidad de buscar en un arreglo ordenado con búsqueda binaria?', [
            ('O(log n)', True), ('O(n)', False), ('O(n log n)', False), ('O(1)', False)]),
        ('¿Cuándo conviene una tabla hash sobre un árbol balanceado?', [
            ('Cuando solo se necesita búsqueda por clave exacta, sin orden', True),
            ('Cuando hay que recorrer las claves en orden', False),
            ('Cuando se necesita el mínimo y el máximo con frecuencia', False),
            ('Siempre: la tabla hash es superior en todo', False)]),
        ('¿Qué estructura usa un recorrido en anchura (BFS) de un grafo?', [
            ('Una cola', True), ('Una pila', False),
            ('Un montículo (heap)', False), ('Una lista enlazada doble', False)]),
    ],
    # ---------------------------------------------------------- Desarrollo Web
    'HTML y CSS: bases sólidas': [
        ('¿Para qué sirven las etiquetas semánticas como <header> o <article>?', [
            ('Para que el navegador y los lectores de pantalla entiendan la estructura', True),
            ('Para aplicar estilos sin escribir CSS', False),
            ('Para que la página cargue más rápido', False),
            ('Para reemplazar el atributo class', False)]),
        ('En el modelo de caja, ¿qué hace box-sizing: border-box?', [
            ('Incluye el padding y el borde dentro del ancho declarado', True),
            ('Elimina el margen exterior del elemento', False),
            ('Convierte el elemento en flexible', False),
            ('Centra el contenido automáticamente', False)]),
        ('¿Cuál selector tiene mayor especificidad?', [
            ('#menu', True), ('.menu', False), ('nav ul li', False), ('ul', False)]),
    ],
    'JavaScript asíncrono y consumo de APIs': [
        ('¿Qué representa una Promise?', [
            ('El resultado futuro de una operación que aún no terminó', True),
            ('Un hilo de ejecución paralelo', False),
            ('Una función que se ejecuta al instante', False),
            ('Un tipo de bucle no bloqueante', False)]),
        ('¿Qué ocurre si no se maneja el rechazo de una promesa?', [
            ('El error queda sin capturar y puede pasar inadvertido', True),
            ('La promesa se reintenta sola', False),
            ('El programa se detiene siempre', False),
            ('El valor se convierte en null', False)]),
        ('Al usar fetch(), ¿cuándo se rechaza la promesa?', [
            ('Ante un fallo de red, no ante un 404 o un 500', True),
            ('Siempre que el servidor responda con error', False),
            ('Solo si la URL está mal escrita', False),
            ('Nunca: fetch jamás rechaza', False)]),
    ],
    'APIs REST con Node.js y Express': [
        ('¿Qué código de estado corresponde a un recurso creado con éxito?', [
            ('201', True), ('200', False), ('204', False), ('301', False)]),
        ('¿Qué caracteriza a un middleware en Express?', [
            ('Recibe (req, res, next) y puede cortar o continuar la cadena', True),
            ('Solo puede usarse en la ruta raíz', False),
            ('Se ejecuta después de enviar la respuesta', False),
            ('Es obligatorio para definir rutas', False)]),
        ('¿Por qué una API REST debe ser sin estado (stateless)?', [
            ('Cada petición debe llevar todo lo necesario para atenderse', True),
            ('Para que no se pueda usar autenticación', False),
            ('Para evitar el uso de bases de datos', False),
            ('Porque HTTP no permite guardar datos', False)]),
    ],
    'Django 5 profesional': [
        ('¿Qué hace el ORM de Django?', [
            ('Traduce clases de Python a tablas y consultas SQL', True),
            ('Genera automáticamente el HTML de las páginas', False),
            ('Administra el servidor de producción', False),
            ('Comprime los archivos estáticos', False)]),
        ('¿Para qué sirve select_related en una consulta?', [
            ('Para traer las relaciones en un solo JOIN y evitar el problema N+1', True),
            ('Para filtrar los campos que se devuelven', False),
            ('Para ordenar el resultado', False),
            ('Para cachear la consulta en Redis', False)]),
        ('¿Qué pasa si cambias un modelo y no creas la migración?', [
            ('La base de datos queda desincronizada del código', True),
            ('Django actualiza la tabla automáticamente al arrancar', False),
            ('El cambio se ignora sin consecuencias', False),
            ('Se borra la tabla y se vuelve a crear', False)]),
    ],
    # ------------------------------------------------------- Bases de Datos
    'Diseño de bases de datos relacionales': [
        ('¿Qué elimina la segunda forma normal (2FN)?', [
            ('Las dependencias parciales de una clave compuesta', True),
            ('Los valores nulos de la tabla', False),
            ('Las claves foráneas duplicadas', False),
            ('Los índices redundantes', False)]),
        ('¿Qué garantiza una clave foránea?', [
            ('Que el valor exista en la tabla referenciada (integridad referencial)', True),
            ('Que el valor sea único en su propia tabla', False),
            ('Que la columna no acepte nulos', False),
            ('Que se cree un índice único automáticamente', False)]),
        ('¿Cómo se representa una relación muchos a muchos?', [
            ('Con una tabla intermedia que guarda las dos claves', True),
            ('Con una columna que acepte varios valores', False),
            ('Con dos claves primarias en la misma tabla', False),
            ('No se puede representar en el modelo relacional', False)]),
    ],
    'PostgreSQL avanzado': [
        ('¿Qué muestra EXPLAIN ANALYZE que no muestra EXPLAIN?', [
            ('Los tiempos reales, porque ejecuta la consulta', True),
            ('El plan de ejecución estimado', False),
            ('Las columnas indexadas de la tabla', False),
            ('Los permisos necesarios para la consulta', False)]),
        ('¿Cuándo NO sirve un índice B-tree sobre una columna de texto?', [
            ('En búsquedas que empiezan con comodín, como LIKE \'%dato\'', True),
            ('En comparaciones de igualdad', False),
            ('En ordenamientos con ORDER BY', False),
            ('En rangos con BETWEEN', False)]),
        ('¿Qué hace VACUUM en PostgreSQL?', [
            ('Recupera el espacio de las filas muertas que dejan UPDATE y DELETE', True),
            ('Reconstruye todos los índices desde cero', False),
            ('Cierra las conexiones inactivas', False),
            ('Hace una copia de seguridad de la base', False)]),
    ],
    'MongoDB para desarrolladores': [
        ('¿Cuándo conviene incrustar un documento en lugar de referenciarlo?', [
            ('Cuando siempre se leen juntos y el tamaño está acotado', True),
            ('Siempre: incrustar es mejor en todos los casos', False),
            ('Cuando el documento hijo crece sin límite', False),
            ('Cuando varios documentos padre comparten el mismo hijo', False)]),
        ('¿Qué es el aggregation pipeline?', [
            ('Una secuencia de etapas que transforman los documentos', True),
            ('Un sistema de respaldo incremental', False),
            ('El mecanismo de replicación entre nodos', False),
            ('Un lenguaje de definición de esquemas', False)]),
        ('¿Qué significa que MongoDB sea "schemaless"?', [
            ('No impone un esquema fijo, pero el diseño de datos sigue importando', True),
            ('Que no se pueden validar los documentos', False),
            ('Que todos los documentos deben ser iguales', False),
            ('Que no admite índices', False)]),
    ],
    # ---------------------------------------------------- Ciencia de Datos
    'Introducción a la ciencia de datos': [
        ('¿En qué etapa se suele invertir la mayor parte del tiempo?', [
            ('En limpiar y preparar los datos', True),
            ('En entrenar el modelo', False),
            ('En presentar los resultados', False),
            ('En instalar las librerías', False)]),
        ('¿Qué diferencia hay entre correlación y causalidad?', [
            ('Que dos variables se muevan juntas no prueba que una cause la otra', True),
            ('Son sinónimos en estadística', False),
            ('La correlación es más fuerte que la causalidad', False),
            ('La causalidad se mide con el coeficiente de Pearson', False)]),
        ('¿Qué riesgo tiene eliminar todas las filas con valores faltantes?', [
            ('Perder información y sesgar la muestra', True),
            ('Ninguno, es la práctica recomendada', False),
            ('Que el archivo ocupe más espacio', False),
            ('Que se dupliquen las filas restantes', False)]),
    ],
    'Visualización de datos con Python': [
        ('¿Qué gráfico conviene para comparar una variable numérica entre categorías?', [
            ('Un gráfico de barras', True), ('Un gráfico de dispersión', False),
            ('Un gráfico de pastel con 20 porciones', False), ('Un histograma', False)]),
        ('¿Por qué truncar el eje Y puede ser engañoso?', [
            ('Exagera visualmente diferencias que son pequeñas', True),
            ('Hace que el gráfico tarde más en dibujarse', False),
            ('Impide poner una leyenda', False),
            ('No tiene ningún efecto sobre la lectura', False)]),
        ('¿Para qué sirve un histograma?', [
            ('Para ver cómo se distribuye una variable numérica', True),
            ('Para comparar dos variables categóricas', False),
            ('Para mostrar la evolución en el tiempo', False),
            ('Para mostrar proporciones de un total', False)]),
    ],
    'Estadística aplicada con Python': [
        ('¿Cuándo es preferible la mediana sobre la media?', [
            ('Cuando hay valores extremos que distorsionan el promedio', True),
            ('Cuando la muestra es muy grande', False),
            ('Cuando los datos son categóricos', False),
            ('Nunca: la media siempre es mejor', False)]),
        ('¿Qué indica un valor p pequeño?', [
            ('Que el resultado sería poco probable si la hipótesis nula fuera cierta', True),
            ('Que la hipótesis alternativa es verdadera', False),
            ('Que el efecto observado es grande', False),
            ('Que la muestra es representativa', False)]),
        ('¿Qué expresa un intervalo de confianza del 95%?', [
            ('Un rango de valores compatibles con los datos observados', True),
            ('Que el 95% de los datos cae dentro del intervalo', False),
            ('Que hay 95% de probabilidad de acertar el dato siguiente', False),
            ('El error máximo de medición del instrumento', False)]),
    ],
    # ------------------------------------------------ Inteligencia Artificial
    'Machine Learning con scikit-learn': [
        ('¿Por qué se separa un conjunto de prueba?', [
            ('Para medir el desempeño con datos que el modelo nunca vio', True),
            ('Para tener más datos de entrenamiento', False),
            ('Para acelerar el entrenamiento', False),
            ('Para balancear las clases', False)]),
        ('¿Qué es el sobreajuste (overfitting)?', [
            ('El modelo memoriza el entrenamiento y falla con datos nuevos', True),
            ('El modelo es demasiado simple para los datos', False),
            ('El entrenamiento tarda demasiado', False),
            ('Hay más columnas que filas', False)]),
        ('Con clases muy desbalanceadas, ¿por qué la exactitud (accuracy) engaña?', [
            ('Se puede acertar el 99% prediciendo siempre la clase mayoritaria', True),
            ('Porque no se puede calcular', False),
            ('Porque siempre da valores negativos', False),
            ('Porque depende del orden de las filas', False)]),
    ],
    'Redes neuronales explicadas': [
        ('¿Para qué sirve una función de activación no lineal?', [
            ('Para que la red pueda aprender relaciones no lineales', True),
            ('Para que el entrenamiento sea más rápido', False),
            ('Para normalizar los datos de entrada', False),
            ('Para reducir la cantidad de capas', False)]),
        ('¿Qué hace la retropropagación (backpropagation)?', [
            ('Calcula el gradiente del error respecto a cada peso', True),
            ('Ejecuta la red hacia adelante para predecir', False),
            ('Elimina las neuronas que no aportan', False),
            ('Divide los datos en lotes', False)]),
        ('¿Qué controla la tasa de aprendizaje (learning rate)?', [
            ('El tamaño del paso al ajustar los pesos', True),
            ('El número de capas de la red', False),
            ('La cantidad de datos por época', False),
            ('El porcentaje de neuronas apagadas', False)]),
    ],
    'Deep Learning con TensorFlow': [
        ('¿Qué es un tensor?', [
            ('Un arreglo multidimensional de números', True),
            ('Una capa de la red neuronal', False),
            ('Un tipo de función de pérdida', False),
            ('Un formato de archivo de modelos', False)]),
        ('¿Por qué las CNN funcionan bien con imágenes?', [
            ('Detectan patrones locales y los reutilizan en toda la imagen', True),
            ('Porque procesan un píxel a la vez', False),
            ('Porque no necesitan entrenamiento', False),
            ('Porque convierten la imagen a texto', False)]),
        ('¿Qué es el transfer learning?', [
            ('Reutilizar un modelo ya entrenado y adaptarlo a un problema nuevo', True),
            ('Copiar los datos de un servidor a otro', False),
            ('Entrenar el mismo modelo en varias GPU', False),
            ('Convertir el modelo a otro formato', False)]),
    ],
    # ------------------------------------------------------- Cloud y DevOps
    'Kubernetes para desarrolladores': [
        ('¿Qué es un Pod?', [
            ('La unidad mínima que se despliega: uno o más contenedores juntos', True),
            ('Una máquina física del clúster', False),
            ('Un archivo de configuración YAML', False),
            ('Un balanceador de carga', False)]),
        ('¿Qué hace un Deployment?', [
            ('Mantiene el número deseado de réplicas y permite actualizaciones graduales', True),
            ('Expone el servicio hacia fuera del clúster', False),
            ('Guarda datos persistentes', False),
            ('Autentica a los usuarios del clúster', False)]),
        ('¿Dónde deben ir las contraseñas de una aplicación en Kubernetes?', [
            ('En un Secret, no en la imagen ni en el manifiesto', True),
            ('En un ConfigMap junto al resto de la configuración', False),
            ('En variables escritas en el Dockerfile', False),
            ('En un volumen público del clúster', False)]),
    ],
    'AWS: primeros pasos en la nube': [
        ('¿Qué establece el modelo de responsabilidad compartida?', [
            ('AWS asegura la nube; el cliente asegura lo que pone en ella', True),
            ('AWS se hace cargo de toda la seguridad', False),
            ('El cliente administra el hardware físico', False),
            ('La responsabilidad depende de la región elegida', False)]),
        ('¿Para qué sirve un rol de IAM?', [
            ('Para dar permisos temporales sin usar credenciales fijas', True),
            ('Para facturar por separado cada servicio', False),
            ('Para crear una red privada virtual', False),
            ('Para respaldar los datos automáticamente', False)]),
        ('¿Qué servicio conviene para archivos estáticos de una web?', [
            ('S3', True), ('RDS', False), ('EC2 con disco local', False), ('Lambda', False)]),
    ],
    # -------------------------------------------------------- Ciberseguridad
    'Hacking ético y pruebas de penetración': [
        ('¿Qué distingue a una prueba de penetración ética de un ataque real?', [
            ('Una autorización previa por escrito y un alcance definido', True),
            ('Que se use software libre', False),
            ('Que no se explote ninguna vulnerabilidad', False),
            ('Que se haga fuera del horario laboral', False)]),
        ('¿Cómo se previene la inyección SQL?', [
            ('Con consultas parametrizadas', True),
            ('Escondiendo los mensajes de error', False),
            ('Cambiando el puerto de la base de datos', False),
            ('Limitando la longitud del formulario', False)]),
        ('¿Qué es un XSS almacenado?', [
            ('Código del atacante que queda guardado y se ejecuta en otros usuarios', True),
            ('Un ataque que solo afecta a quien abre el enlace', False),
            ('Una forma de descifrar contraseñas', False),
            ('Un ataque contra la base de datos', False)]),
    ],
    # ----------------------------------------------------- Desarrollo Móvil
    'Desarrollo Android desde cero': [
        ('¿Qué es una Activity?', [
            ('Una pantalla con la que el usuario interactúa', True),
            ('Un servicio que corre en segundo plano', False),
            ('El archivo de configuración del proyecto', False),
            ('Una animación entre pantallas', False)]),
        ('¿Por qué importa el ciclo de vida de una Activity?', [
            ('El sistema puede pausarla o destruirla y hay que guardar el estado', True),
            ('Porque define el color de la interfaz', False),
            ('Porque determina el tamaño del APK', False),
            ('Porque controla la versión de Android', False)]),
        ('¿Para qué sirve el archivo AndroidManifest.xml?', [
            ('Declara componentes, permisos y datos de la aplicación', True),
            ('Contiene el código de las pantallas', False),
            ('Guarda las traducciones de los textos', False),
            ('Define los estilos visuales', False)]),
    ],
    'Kotlin para Android': [
        ('¿Qué diferencia hay entre val y var?', [
            ('val no admite reasignación; var sí', True),
            ('val solo sirve para números', False),
            ('var es privado por defecto', False),
            ('No hay diferencia', False)]),
        ('¿Qué problema resuelve el sistema de tipos nulos de Kotlin?', [
            ('Obliga a tratar los nulos y evita la mayoría de los NullPointerException', True),
            ('Elimina por completo los valores nulos del lenguaje', False),
            ('Convierte los nulos en cero automáticamente', False),
            ('Solo afecta a las variables globales', False)]),
        ('¿Qué es una corrutina?', [
            ('Una tarea que puede suspenderse sin bloquear el hilo', True),
            ('Un hilo del sistema operativo', False),
            ('Una función que se ejecuta al iniciar la app', False),
            ('Una clase que reemplaza a las Activity', False)]),
    ],
    'Flutter: apps multiplataforma': [
        ('¿Qué es un widget en Flutter?', [
            ('La descripción inmutable de una parte de la interfaz', True),
            ('Un archivo de recursos gráficos', False),
            ('Un componente nativo de Android', False),
            ('Un paquete externo obligatorio', False)]),
        ('¿Cuándo se usa un StatefulWidget en vez de un StatelessWidget?', [
            ('Cuando la interfaz debe cambiar durante la vida del widget', True),
            ('Cuando el widget tiene hijos', False),
            ('Cuando se usan imágenes', False),
            ('Siempre: StatelessWidget está obsoleto', False)]),
        ('¿Qué hace setState()?', [
            ('Avisa a Flutter de que el estado cambió para que vuelva a construir', True),
            ('Guarda el estado en el disco del dispositivo', False),
            ('Reinicia la aplicación', False),
            ('Envía el estado al servidor', False)]),
    ],
}


# ---------------------------------------------------------------------------
# Actividad 2 — Trabajo práctico (los 30 cursos)
# ---------------------------------------------------------------------------
# (titulo, consigna, etiqueta_recurso, url_recurso)

TRABAJOS = {
    'Python desde cero': (
        'Analizador de gastos en CSV',
        'Escribe un programa en Python que lea un archivo CSV con gastos '
        '(fecha, categoría, monto) y muestre por consola el total gastado por '
        'categoría y el mes con mayor gasto. Debe manejar con try/except el caso '
        'de que el archivo no exista.\n\n'
        'Entrega un archivo comprimido (ZIP) o un PDF con el código y una '
        'captura de la salida.',
        'Automate the Boring Stuff with Python (libro de acceso libre)',
        'https://automatetheboringstuff.com/',
    ),
    'Programación orientada a objetos en Python': (
        'Modelo de clases de una biblioteca',
        'Diseña e implementa las clases de una biblioteca: Libro, Socio y Préstamo. '
        'Usa herencia donde tenga sentido y justifica en un comentario por qué '
        'elegiste herencia o composición en cada caso. Incluye un pequeño programa '
        'que preste y devuelva un libro.\n\n'
        'Entrega el código y un diagrama de clases (puede ser una foto de un dibujo '
        'a mano) en un solo PDF o ZIP.',
        'Documentación oficial de Python — Clases',
        'https://docs.python.org/es/3/tutorial/classes.html',
    ),
    'JavaScript moderno desde cero': (
        'Lista de tareas sin frameworks',
        'Construye una lista de tareas con HTML, CSS y JavaScript puro: agregar, '
        'marcar como hecha y eliminar. Guarda el estado en localStorage para que '
        'sobreviva al recargar la página. Usa let/const, funciones flecha y métodos '
        'de arreglo (map, filter).\n\n'
        'Entrega los archivos en un ZIP junto a una captura de pantalla.',
        'JavaScript.info — El lenguaje JavaScript',
        'https://es.javascript.info/',
    ),
    'TypeScript para proyectos reales': (
        'Migración de un módulo a TypeScript',
        'Toma un archivo JavaScript de al menos 60 líneas (propio o del curso) y '
        'migralo a TypeScript: define interfaces para los datos, elimina todo uso '
        'de any y deja el proyecto compilando con strict activado.\n\n'
        'Entrega el antes y el después en un ZIP, más un párrafo explicando qué '
        'error de tipos encontró el compilador que antes pasaba inadvertido.',
        'TypeScript Handbook (documentación oficial)',
        'https://www.typescriptlang.org/docs/handbook/intro.html',
    ),
    'C++ de principiante a avanzado': (
        'Gestor de inventario con punteros inteligentes',
        'Implementa un pequeño gestor de inventario en C++ moderno: una clase '
        'Producto y un contenedor que la administre usando std::vector y '
        'std::unique_ptr. No debe quedar ni un new/delete manual.\n\n'
        'Entrega el código fuente y la salida de la compilación en un ZIP o PDF.',
        'cppreference — Referencia del lenguaje C++',
        'https://en.cppreference.com/w/cpp/language',
    ),
    'Estructuras de datos y algoritmos': (
        'Comparación empírica de dos algoritmos',
        'Implementa búsqueda lineal y búsqueda binaria sobre el mismo arreglo '
        'ordenado. Mide el tiempo con entradas de 1.000, 100.000 y 1.000.000 de '
        'elementos y grafica o tabula los resultados.\n\n'
        'Entrega el código y una conclusión de media página comparando los tiempos '
        'medidos con la complejidad teórica.',
        'Open Data Structures (libro de acceso libre)',
        'https://opendatastructures.org/',
    ),
    'HTML y CSS: bases sólidas': (
        'Página de presentación responsive',
        'Maqueta una página de presentación personal con HTML semántico '
        '(header, nav, main, section, footer) y CSS propio. Debe verse bien en '
        'celular y en escritorio usando Flexbox o Grid, sin ningún framework.\n\n'
        'Entrega el ZIP del sitio y dos capturas: una móvil y una de escritorio.',
        'MDN — Aprende desarrollo web',
        'https://developer.mozilla.org/es/docs/Learn',
    ),
    'React en la práctica': (
        'Buscador de cursos con estado y efectos',
        'Construye un componente que consuma una API pública, muestre los '
        'resultados en tarjetas y permita filtrarlos con un campo de búsqueda. '
        'Debe manejar los tres estados: cargando, error y vacío.\n\n'
        'Entrega el código en un ZIP y una captura de cada uno de los tres estados.',
        'React — Documentación oficial en español',
        'https://es.react.dev/learn',
    ),
    'JavaScript asíncrono y consumo de APIs': (
        'Cliente de API con manejo de errores',
        'Escribe una función que consulte una API pública con fetch y async/await, '
        'y que distinga tres situaciones: respuesta correcta, error HTTP (404/500) '
        'y fallo de red. Cada caso debe mostrar un mensaje distinto al usuario.\n\n'
        'Entrega el código y capturas de los tres casos (puedes forzar el fallo de '
        'red desactivando la conexión).',
        'MDN — Programación asíncrona en JavaScript',
        'https://developer.mozilla.org/es/docs/Learn/JavaScript/Asynchronous',
    ),
    'APIs REST con Node.js y Express': (
        'API REST de un recurso completo',
        'Construye una API en Express con las cinco operaciones sobre un recurso '
        '(listar, ver, crear, actualizar, eliminar). Devuelve los códigos de estado '
        'correctos (200, 201, 204, 400, 404) y valida la entrada.\n\n'
        'Entrega el código en un ZIP junto a la colección de pruebas '
        '(Postman, Thunder Client o un archivo .http).',
        'Express — Guía de enrutamiento',
        'https://expressjs.com/es/guide/routing.html',
    ),
    'Django 5 profesional': (
        'Aplicación Django con modelos relacionados',
        'Crea una aplicación con al menos tres modelos relacionados entre sí, sus '
        'migraciones, el registro en el admin y una vista de listado. Optimiza al '
        'menos una consulta con select_related o prefetch_related y explica qué '
        'problema N+1 resolvió.\n\n'
        'Entrega el proyecto en un ZIP y una captura del admin funcionando.',
        'Django — Tutorial oficial',
        'https://docs.djangoproject.com/es/5.0/intro/tutorial01/',
    ),
    'SQL para análisis de datos': (
        'Informe de ventas en SQL',
        'A partir de un conjunto de datos con ventas, escribe cinco consultas: '
        'total por mes, top 5 de productos, clientes sin compras en el último año '
        '(LEFT JOIN), promedio por categoría con HAVING, y una que use una CTE.\n\n'
        'Entrega un PDF con cada consulta y su resultado.',
        'PostgreSQL — Tutorial de SQL',
        'https://www.postgresql.org/docs/current/tutorial-sql.html',
    ),
    'Diseño de bases de datos relacionales': (
        'Modelo entidad-relación normalizado',
        'Diseña el modelo de datos de una clínica (pacientes, médicos, citas, '
        'especialidades). Entrega el diagrama entidad-relación y el script SQL con '
        'las claves primarias, foráneas y restricciones. El modelo debe estar al '
        'menos en tercera forma normal y debes justificar por escrito una decisión '
        'de normalización.\n\n'
        'Entrega todo en un solo PDF o ZIP.',
        'Database Design (libro abierto, BCcampus)',
        'https://opentextbc.ca/dbdesign01/',
    ),
    'PostgreSQL avanzado': (
        'Optimización de una consulta lenta',
        'Toma una consulta que tarde de forma perceptible sobre una tabla con al '
        'menos 100.000 filas. Captura su EXPLAIN ANALYZE, crea el índice adecuado y '
        'vuelve a capturarlo.\n\n'
        'Entrega un PDF con las dos salidas y una explicación de por qué el plan '
        'cambió y cuánto tiempo se ganó.',
        'PostgreSQL — Índices',
        'https://www.postgresql.org/docs/current/indexes.html',
    ),
    'MongoDB para desarrolladores': (
        'Modelado de datos: incrustar o referenciar',
        'Modela en MongoDB un blog con artículos, autores y comentarios. Decide para '
        'cada relación si incrustas o referencias, y justifica cada decisión según el '
        'patrón de lectura esperado. Incluye un aggregation pipeline que cuente los '
        'comentarios por artículo.\n\n'
        'Entrega los documentos de ejemplo, el pipeline y la justificación en un PDF.',
        'MongoDB — Guía de modelado de datos',
        'https://www.mongodb.com/docs/manual/data-modeling/',
    ),
    'Introducción a la ciencia de datos': (
        'Exploración de un conjunto de datos real',
        'Elige un conjunto de datos público, descríbelo (filas, columnas, tipos), '
        'documenta los valores faltantes y cómo decidiste tratarlos, y plantea tres '
        'preguntas que los datos permitan responder. Responde al menos una con un '
        'gráfico.\n\n'
        'Entrega el notebook exportado a PDF o HTML.',
        'Python Data Science Handbook (libro de acceso libre)',
        'https://jakevdp.github.io/PythonDataScienceHandbook/',
    ),
    'Análisis de datos con Python y Pandas': (
        'Limpieza y agregación con Pandas',
        'Carga un CSV con datos sucios (duplicados, nulos, tipos mal inferidos), '
        'límpialo documentando cada decisión, y produce una tabla resumen con '
        'groupby. Compara el tiempo de una operación vectorizada contra el mismo '
        'cálculo hecho con apply.\n\n'
        'Entrega el notebook exportado a PDF o HTML.',
        'pandas — 10 minutes to pandas',
        'https://pandas.pydata.org/docs/user_guide/10min.html',
    ),
    'Visualización de datos con Python': (
        'Tres gráficos con una historia',
        'A partir de un conjunto de datos, produce tres gráficos de tipos distintos '
        '(por ejemplo barras, histograma y líneas). Cada uno debe llevar título, '
        'etiquetas en los ejes y un párrafo explicando qué se ve y qué NO se puede '
        'concluir a partir de él.\n\n'
        'Entrega un PDF con los tres gráficos y sus explicaciones.',
        'Matplotlib — Tutoriales oficiales',
        'https://matplotlib.org/stable/tutorials/index.html',
    ),
    'Estadística aplicada con Python': (
        'Comparación de dos grupos',
        'Con un conjunto de datos que tenga dos grupos comparables, calcula las '
        'medidas descriptivas de cada uno, grafica sus distribuciones y aplica una '
        'prueba de hipótesis. Interpreta el valor p en una frase que un no '
        'estadístico pueda entender, y di explícitamente qué NO demuestra.\n\n'
        'Entrega el notebook exportado a PDF.',
        'Think Stats (libro de acceso libre)',
        'https://greenteapress.com/wp/think-stats-2e/',
    ),
    'Machine Learning con scikit-learn': (
        'Modelo de clasificación evaluado con honestidad',
        'Entrena un clasificador sobre un conjunto de datos público. Separa '
        'entrenamiento y prueba, reporta precisión, recall y F1 (no solo exactitud) '
        'y muestra la matriz de confusión. Explica si hay desbalance de clases y qué '
        'consecuencia tiene sobre las métricas.\n\n'
        'Entrega el notebook exportado a PDF o HTML.',
        'scikit-learn — Guía del usuario',
        'https://scikit-learn.org/stable/user_guide.html',
    ),
    'Redes neuronales explicadas': (
        'Una red neuronal a mano',
        'Con papel o una hoja de cálculo, propaga hacia adelante una red de dos '
        'entradas, una capa oculta de dos neuronas y una salida, con pesos que tú '
        'elijas. Calcula el error y aplica un paso de retropropagación mostrando '
        'las derivadas.\n\n'
        'Entrega las fotos o la hoja de cálculo en un PDF, con el procedimiento '
        'visible paso a paso.',
        '3Blue1Brown — Neural networks',
        'https://www.3blue1brown.com/topics/neural-networks',
    ),
    'Deep Learning con TensorFlow': (
        'Clasificador de imágenes con transfer learning',
        'Entrena un clasificador de imágenes partiendo de un modelo preentrenado. '
        'Grafica las curvas de pérdida de entrenamiento y validación, e identifica '
        'si hubo sobreajuste y en qué época empezó.\n\n'
        'Entrega el notebook exportado a PDF o HTML con las curvas visibles.',
        'TensorFlow — Guía para principiantes',
        'https://www.tensorflow.org/tutorials/quickstart/beginner?hl=es',
    ),
    'Docker desde cero': (
        'Dockerfile y Compose de una app real',
        'Escribe el Dockerfile de una aplicación pequeña (Python o Node) aplicando '
        'construcción en varias etapas, y un docker-compose.yml que la levante junto '
        'a una base de datos con un volumen persistente. La imagen final no debe '
        'contener credenciales.\n\n'
        'Entrega los archivos en un ZIP y la salida de `docker compose ps`.',
        'Docker — Buenas prácticas para escribir Dockerfiles',
        'https://docs.docker.com/build/building/best-practices/',
    ),
    'Kubernetes para desarrolladores': (
        'Despliegue de una aplicación en Kubernetes',
        'Escribe los manifiestos para desplegar una aplicación: Deployment con dos '
        'réplicas, Service que la exponga y un Secret con las credenciales (nunca en '
        'el manifiesto en texto plano). Documenta el comando para verificar que las '
        'réplicas están corriendo.\n\n'
        'Entrega los YAML en un ZIP y la salida de `kubectl get pods`.',
        'Kubernetes — Conceptos (documentación en español)',
        'https://kubernetes.io/es/docs/concepts/',
    ),
    'AWS: primeros pasos en la nube': (
        'Arquitectura de una aplicación web en AWS',
        'Diseña la arquitectura de una aplicación web con base de datos y archivos '
        'estáticos. Indica qué servicio usarías para cada pieza y por qué, cómo '
        'manejarías las credenciales y qué parte de la seguridad es responsabilidad '
        'tuya y cuál de AWS.\n\n'
        'Entrega un PDF con el diagrama y la justificación (no hace falta desplegar '
        'nada real).',
        'AWS — Well-Architected Framework',
        'https://aws.amazon.com/es/architecture/well-architected/',
    ),
    'Fundamentos de ciberseguridad': (
        'Análisis de riesgos de un sistema',
        'Elige un sistema que conozcas (una tienda en línea, un sistema académico) e '
        'identifica cinco riesgos de seguridad. Para cada uno indica qué parte de la '
        'tríada CIA afecta, su impacto y una medida de mitigación concreta.\n\n'
        'Entrega un PDF con la tabla de riesgos y las mitigaciones.',
        'OWASP Top 10',
        'https://owasp.org/www-project-top-ten/',
    ),
    'Hacking ético y pruebas de penetración': (
        'Informe de una prueba en un entorno autorizado',
        'Usando ÚNICAMENTE un laboratorio pensado para practicar (DVWA, OWASP Juice '
        'Shop o una máquina propia), documenta el hallazgo de una vulnerabilidad: '
        'alcance autorizado, pasos para reproducirla, impacto y recomendación de '
        'corrección.\n\n'
        'Entrega el informe en PDF. Cualquier prueba sobre sistemas de terceros sin '
        'autorización por escrito queda fuera de esta entrega y es ilegal.',
        'OWASP Web Security Testing Guide',
        'https://owasp.org/www-project-web-security-testing-guide/',
    ),
    'Desarrollo Android desde cero': (
        'App de dos pantallas con estado persistente',
        'Construye una aplicación con dos pantallas que se comuniquen entre sí. Debe '
        'conservar su estado al rotar el dispositivo y declarar correctamente sus '
        'componentes en el manifiesto.\n\n'
        'Entrega el proyecto en un ZIP y un video corto o capturas del flujo '
        'completo, incluida la rotación.',
        'Android — Guía para desarrolladores',
        'https://developer.android.com/guide?hl=es-419',
    ),
    'Kotlin para Android': (
        'Pantalla con datos remotos y corrutinas',
        'Implementa una pantalla que cargue datos de una API usando corrutinas, sin '
        'bloquear el hilo principal. Maneja los estados de carga y de error, y '
        'aprovecha los tipos nulos de Kotlin para que ningún campo opcional pueda '
        'romper la app.\n\n'
        'Entrega el proyecto en un ZIP y capturas de los estados de carga y error.',
        'Kotlin — Documentación oficial',
        'https://kotlinlang.org/docs/home.html',
    ),
    'Flutter: apps multiplataforma': (
        'App con navegación y estado compartido',
        'Construye una app con al menos dos pantallas y navegación entre ellas, '
        'donde un dato modificado en una se refleje en la otra. Explica por qué cada '
        'widget que creaste es Stateless o Stateful.\n\n'
        'Entrega el proyecto en un ZIP y capturas de ambas pantallas.',
        'Flutter — Documentación oficial',
        'https://docs.flutter.dev/',
    ),
}
