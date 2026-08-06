"""
Generador de portadas de curso.

Se generan en vez de descargar fotos de banco porque las fuentes libres sin
clave de API (picsum, loremflickr) devuelven imágenes que NO corresponden al
tema: un curso de ciberseguridad terminaba con la foto de un gato. Una
portada equivocada distrae más de lo que aporta.

La portada generada siempre corresponde al curso, porque se construye con su
propio título y el color de su categoría. Además es determinista, no depende
de ningún servicio externo y no arrastra marcas de agua ni licencias.
"""
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ANCHO, ALTO = 800, 450

NEGRITA = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
NORMAL = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

# Un color por categoría: el catálogo se lee de un vistazo y cada área tiene
# identidad propia, como en las plataformas reales.
COLORES = {
    'Programación': ((124, 58, 237), (91, 33, 182)),        # morado (marca)
    'Desarrollo Web': ((2, 132, 199), (3, 105, 161)),        # azul
    'Bases de Datos': ((13, 148, 136), (15, 118, 110)),      # verde azulado
    'Ciencia de Datos': ((217, 119, 6), (180, 83, 9)),       # ámbar
    'Inteligencia Artificial': ((219, 39, 119), (157, 23, 77)),  # magenta
    'Cloud y DevOps': ((79, 70, 229), (67, 56, 202)),        # índigo
    'Ciberseguridad': ((220, 38, 38), (153, 27, 27)),        # rojo
    'Desarrollo Móvil': ((5, 150, 105), (4, 120, 87)),       # verde
}
POR_DEFECTO = ((100, 96, 122), (36, 31, 53))

NOMBRE_NIVEL = {'BASICO': 'Básico', 'INTERMEDIO': 'Intermedio', 'AVANZADO': 'Avanzado'}


def _degradado(draw, desde, hasta):
    """Degradado vertical simple, línea por línea."""
    for y in range(ALTO):
        t = y / ALTO
        draw.line(
            [(0, y), (ANCHO, y)],
            fill=tuple(round(desde[i] + (hasta[i] - desde[i]) * t) for i in range(3)),
        )


def _malla(draw):
    """Retícula tenue: da textura sin competir con el texto."""
    for x in range(0, ANCHO, 40):
        draw.line([(x, 0), (x, ALTO)], fill=(255, 255, 255, 8), width=1)
    for y in range(0, ALTO, 40):
        draw.line([(0, y), (ANCHO, y)], fill=(255, 255, 255, 8), width=1)


def generar_portada(titulo, categoria, nivel, destino):
    """Crea la portada y la guarda. Devuelve True si quedó escrita."""
    destino = Path(destino)
    if destino.exists() and destino.stat().st_size > 0:
        return True
    destino.parent.mkdir(parents=True, exist_ok=True)

    desde, hasta = COLORES.get(categoria, POR_DEFECTO)
    img = Image.new('RGB', (ANCHO, ALTO), desde)
    draw = ImageDraw.Draw(img, 'RGBA')
    _degradado(draw, desde, hasta)
    _malla(draw)

    # Círculos difusos en la esquina: rompen la planitud del degradado
    draw.ellipse([ANCHO - 190, -110, ANCHO + 90, 170], fill=(255, 255, 255, 18))
    draw.ellipse([ANCHO - 120, 40, ANCHO + 60, 220], fill=(255, 255, 255, 12))

    f_categoria = ImageFont.truetype(NORMAL, 20)
    f_nivel = ImageFont.truetype(NEGRITA, 17)

    # Categoría, arriba
    draw.text((52, 48), categoria.upper(), font=f_categoria, fill=(255, 255, 255, 205))

    # La etiqueta de nivel ocupa la franja inferior; el título se apila HACIA
    # ARRIBA desde ahí, para que nunca se monten uno sobre otro por más largo
    # que sea el título.
    ETIQUETA_Y = ALTO - 76
    TITULO_BASE = ETIQUETA_Y - 26   # borde inferior del bloque de título

    # Se reduce el tamaño de letra hasta que el título quepa en 3 líneas
    for tam, ancho_car in ((52, 22), (44, 26), (38, 30), (32, 36)):
        lineas = textwrap.wrap(titulo, width=ancho_car)
        if len(lineas) <= 3:
            break
    f_titulo = ImageFont.truetype(NEGRITA, tam)
    alto_linea = tam + 10

    y = TITULO_BASE - len(lineas) * alto_linea
    for linea in lineas:
        draw.text((52, y), linea, font=f_titulo, fill=(255, 255, 255))
        y += alto_linea

    # Etiqueta del nivel
    etiqueta = NOMBRE_NIVEL.get(nivel, nivel).upper()
    caja = draw.textbbox((0, 0), etiqueta, font=f_nivel)
    ancho_txt, alto_txt = caja[2] - caja[0], caja[3] - caja[1]
    draw.rounded_rectangle(
        [52, ETIQUETA_Y, 52 + ancho_txt + 32, ETIQUETA_Y + alto_txt + 18],
        radius=999, fill=(255, 255, 255, 45),
    )
    draw.text((68, ETIQUETA_Y + 8), etiqueta, font=f_nivel, fill=(255, 255, 255, 240))

    img.save(destino, 'JPEG', quality=88, optimize=True)
    return True
