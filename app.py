import streamlit as st
import qrcode
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
from datetime import datetime
import io
import zipfile
import tempfile
import os
import base64
import json

# Configuración de página
st.set_page_config(page_title="Generador de Etiquetas QR", layout="wide")

# Definición de colores EXACTA del código base actualizado
# Del codigo_base.py línea 21
COLORES = {
    "A": (213, 43, 30),  # Rojo
    "B": (0, 133, 66),  # Verde
    "C": (0, 101, 189),  # Azul
    "D": (240, 171, 0),  # Amarillo
    "E": (135, 135, 135),  # Gris (era Z)
    "F": (215, 31, 133),  # Rosa
    "G": (117, 48, 119),  # Púrpura
    "H": (255, 88, 0),  # Naranja
    "I": (249, 227, 0),  # Amarillo claro
    "J": (0, 0, 0),  # Negro
    "K": (78, 84, 87),  # Gris oscuro (era L)
    "L": (198, 191, 110),  # Beige (era M)
    "M": (255, 0, 255),  # Magenta
    "N": (0, 38, 100),  # Azul marino (era P)
    "O": (104, 69, 13),  # Marrón (era Q)
    "P": (255, 215, 0),  # Dorado
    "Q": (0, 161, 222),  # Celeste (era S)
    "R": (64, 224, 208),  # Turquesa claro
    "S": (255, 234, 200),  # Crema (era V)
    "T": (0, 128, 128),  # Turquesa
    "U": (138, 43, 226),  # Violeta
    "V": (255, 20, 147),  # Rosa intenso/Fucsia
    "W": (255, 255, 255),  # Blanco
    "X": (128, 0, 64),  # Vino/Borgoña
}

# Color por defecto para letras no definidas
COLOR_DEFAULT = (128, 128, 128)  # Gris medio

# Colores personalizados predefinidos que pueden ser usados por todos los usuarios
# Estos colores estarán disponibles por defecto en la app
DEFAULT_CUSTOM_COLORS = {
    # Puedes agregar aquí colores adicionales que quieras que estén disponibles por defecto
    # Ejemplo: "Ñ": (255, 0, 255),  # Magenta
}


def load_custom_colors():
    """
    Cargar colores personalizados.
    En Streamlit Cloud, los colores personalizados solo existen durante la sesión del usuario.
    Si quieres que ciertos colores estén disponibles para todos los usuarios,
    agrégalos al diccionario DEFAULT_CUSTOM_COLORS arriba.
    """
    # Retornar los colores predefinidos para nuevas sesiones
    return dict(DEFAULT_CUSTOM_COLORS)


def save_custom_colors(colors):
    """
    En Streamlit Cloud, los colores solo se guardan en session_state durante la sesión actual.
    Los colores personalizados son específicos de cada usuario y se pierden al cerrar la app.

    Para hacer colores permanentes para TODOS los usuarios:
    1. Agrega el color al diccionario DEFAULT_CUSTOM_COLORS en el código
    2. Haz commit y push del cambio a tu repositorio
    3. Streamlit Cloud actualizará automáticamente la app
    """
    # Esta función se mantiene para compatibilidad pero no hace nada
    # ya que en Streamlit Cloud no se puede escribir en el sistema de archivos
    pass


def get_color_for_letter(letra):
    """Obtener color para una letra, incluyendo soporte para colores personalizados"""
    letra = letra.upper()

    # Verificar colores personalizados primero
    if hasattr(st, "session_state") and "custom_colors" in st.session_state:
        if letra in st.session_state.custom_colors:
            return st.session_state.custom_colors[letra]

    # Luego verificar colores predefinidos
    return COLORES.get(letra, COLOR_DEFAULT)


def get_text_color_for_background(bg_color):
    """
    Determina si el texto debe ser blanco o negro basándose en la luminosidad del fondo.
    Usa la fórmula de luminosidad relativa recomendada por W3C.

    Args:
        bg_color: Tupla RGB del color de fondo (R, G, B)

    Returns:
        Tupla RGB: (255, 255, 255) para blanco o (0, 0, 0) para negro
    """
    # Calcular luminosidad relativa usando la fórmula W3C
    # https://www.w3.org/TR/WCAG20/#relativeluminancedef
    r, g, b = bg_color

    # Convertir valores RGB a escala 0-1
    r, g, b = r / 255.0, g / 255.0, b / 255.0

    # Aplicar corrección gamma
    def adjust(c):
        if c <= 0.03928:
            return c / 12.92
        else:
            return ((c + 0.055) / 1.055) ** 2.4

    r, g, b = adjust(r), adjust(g), adjust(b)

    # Calcular luminosidad
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b

    # Si la luminosidad es mayor a 0.5, usar texto negro; sino, blanco
    return (0, 0, 0) if luminance > 0.5 else (255, 255, 255)


def create_font(size):
    """Crear fuente usando Ubuntu-Bold.ttf o fuente por defecto"""
    try:
        # Intentar usar la fuente Ubuntu-Bold.ttf del directorio actual
        return ImageFont.truetype("Ubuntu-Bold.ttf", size)
    except:
        try:
            # Intentar fuente del sistema
            return ImageFont.truetype("arial.ttf", size)
        except:
            # Fuente por defecto como último recurso
            return ImageFont.load_default()


def mm_to_pixels(mm, dpi=300):
    """Convertir milímetros a píxeles"""
    return int((mm / 25.4) * dpi)


def cm_to_pixels(cm, dpi=300):
    """Convertir centímetros a píxeles"""
    return int((cm / 2.54) * dpi)


def m_to_pixels(m, dpi=300):
    """Convertir metros a píxeles"""
    return int((m * 100 / 2.54) * dpi)


def get_dimensions_in_pixels(width, height, unit, dpi=300):
    """Convertir dimensiones a píxeles según la unidad especificada"""
    if unit == "mm":
        return mm_to_pixels(width, dpi), mm_to_pixels(height, dpi)
    elif unit == "cm":
        return cm_to_pixels(width, dpi), cm_to_pixels(height, dpi)
    elif unit == "m":
        return m_to_pixels(width, dpi), m_to_pixels(height, dpi)
    else:
        return width, height  # píxeles


def format_text_to_two_lines(text):
    """Formatea el texto para que tenga como máximo 2 líneas, dividiendo por espacios de manera inteligente"""
    words = text.split()

    if len(words) <= 1:
        return text

    # Calculamos la longitud total y la dividimos para hacer dos líneas de longitud similar
    total_chars = sum(len(word) for word in words) + len(words) - 1
    target_chars_per_line = total_chars / 2

    current_line = ""
    current_chars = 0

    for i, word in enumerate(words[:-1]):
        if current_chars + len(word) <= target_chars_per_line:
            current_line += word + " "
            current_chars += len(word) + 1
        else:
            return current_line.strip() + "\n" + " ".join(words[i:])

    return words[0] + "\n" + " ".join(words[1:])


def generate_qr_label(
    localidad,
    abr,
    letra,
    dimensions=(6614, 6850),
    text_color_mode="Automático",
    custom_text_color=None,
    logo_image=None,
    logo_size_percent=25,
    text_position="Arriba del QR",
):
    """Generar una etiqueta QR con posicionamiento dinámico

    Args:
        localidad: Código QR a generar
        abr: Texto a mostrar sobre el QR
        letra: Letra que determina el color de fondo
        dimensions: Tupla (ancho, alto) en píxeles
        text_color_mode: "Automático", "Blanco", "Negro", o "Personalizado"
        custom_text_color: Tupla RGB (R, G, B) para modo personalizado
        logo_image: Imagen PIL para insertar en el centro del QR (opcional)
        logo_size_percent: Porcentaje del tamaño del QR que ocupará el logo (10-40)
        text_position: "Arriba del QR" o "Abajo del QR"
    """

    # Convertir letra y abr a string como en el código original
    letra = str(letra)
    abr = str(abr)

    # Obtener color exacto del código base (con fallback para colores personalizados)
    color = get_color_for_letter(letra)

    # Determinar color del texto según el modo seleccionado
    if text_color_mode == "Blanco":
        text_color = (255, 255, 255)
    elif text_color_mode == "Negro":
        text_color = (0, 0, 0)
    elif text_color_mode == "Personalizado" and custom_text_color:
        text_color = custom_text_color
    else:  # Automático
        text_color = get_text_color_for_background(color)

    # Crear imagen con dimensiones exactas del código actualizado
    img = Image.new("RGB", dimensions, color=color)

    d = ImageDraw.Draw(img)

    # La posición Y se calculará después para centrar el texto verticalmente

    # Calcular box_size del QR proporcionalmente a las dimensiones
    # Dimensiones de referencia (originales): 6614 x 6850
    # Box size de referencia: 180
    reference_width = 6614
    reference_box_size = 180

    # Escalar box_size proporcionalmente al ancho
    scale_factor = dimensions[0] / reference_width
    box_size = int(reference_box_size * scale_factor)

    # Asegurar que box_size sea al menos 10 para legibilidad
    box_size = max(10, box_size)

    # Generar código QR primero para conocer su posición
    qr_big = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=box_size, border=1
    )
    qr_big.add_data(localidad)
    qr_big.make(fit=True)
    img_qr_big = qr_big.make_image().convert("RGB")

    # Redimensionar el QR a un tamaño fijo para que todos los QR tengan el mismo tamaño
    # independientemente de la cantidad de datos que contengan
    # Tamaño de referencia basado en QR de versión 25 (12 caracteres aprox)
    fixed_qr_size = int(4860 * scale_factor)
    if img_qr_big.size[0] != fixed_qr_size:
        img_qr_big = img_qr_big.resize((fixed_qr_size, fixed_qr_size), Image.Resampling.LANCZOS)

    # Posición del QR y espacio para texto según la ubicación seleccionada
    reference_height = 6850
    reference_offset = 600
    qr_offset = int(reference_offset * scale_factor)

    # Margen proporcional
    reference_margin = 100
    margin = int(reference_margin * scale_factor)

    if text_position == "Arriba del QR":
        # Texto arriba: QR se desplaza hacia abajo (comportamiento original)
        qr_y_fixed = (dimensions[1] - img_qr_big.size[1]) // 2 + qr_offset
        # Espacio disponible para el texto (desde arriba hasta el QR con margen)
        available_height = qr_y_fixed - margin
    else:
        # Texto abajo: QR se desplaza hacia arriba
        qr_y_fixed = (dimensions[1] - img_qr_big.size[1]) // 2 - qr_offset
        # Espacio disponible para el texto (desde abajo del QR hasta el final con margen)
        available_height = dimensions[1] - (qr_y_fixed + img_qr_big.size[1]) - margin

    max_width = (
        dimensions[0] * 0.98
    )  # Aumentado de 0.95 a 0.98 para usar más espacio horizontal

    y_temp = 0  # Usamos 0 temporalmente para los cálculos

    # Tamaño de fuente base proporcional a las dimensiones
    reference_font_size = 1500
    base_font_size = int(reference_font_size * scale_factor)
    min_font_size = int(200 * scale_factor)

    # Estrategia inteligente de formateo
    if " " in abr:
        # Tiene espacio - evaluar si conviene 1 o 2 líneas

        # Para textos cortos (7 caracteres o menos), usar 1 línea directamente
        if len(abr) <= 7:
            lines = [abr]
            fnt = create_font(base_font_size)
        else:
            # Opción 1: Probar en 1 línea con tamaño máximo
            font_size_1line = base_font_size
            fnt_test = create_font(font_size_1line)

            try:
                text_width_1line = d.textbbox((0, 0), abr, font=fnt_test)[2]
                bbox = d.textbbox((0, 0), "Ag", font=fnt_test)
                line_height_1line = bbox[3] - bbox[1]
            except AttributeError:
                text_width_1line = fnt_test.getsize(abr)[0]
                line_height_1line = fnt_test.getsize("Ag")[1]

            text_bottom_1line = line_height_1line

            # Si cabe en 1 línea sin solapar el QR, usar 1 línea
            if text_width_1line <= max_width and text_bottom_1line <= available_height:
                lines = [abr]
                fnt = create_font(base_font_size)
            else:
                # Opción 2: Intentar ajustar el tamaño en 1 línea antes de dividir
                optimal_font_size_1line = min_font_size

                # Buscar el tamaño máximo para 1 línea
                temp_min = min_font_size
                temp_max = base_font_size

                while temp_min <= temp_max:
                    font_size = (temp_min + temp_max) // 2
                    fnt_test = create_font(font_size)

                    try:
                        text_width = d.textbbox((0, 0), abr, font=fnt_test)[2]
                        bbox = d.textbbox((0, 0), "Ag", font=fnt_test)
                        line_height = bbox[3] - bbox[1]
                    except AttributeError:
                        text_width = fnt_test.getsize(abr)[0]
                        line_height = fnt_test.getsize("Ag")[1]

                    text_bottom = line_height

                    if text_width <= max_width and text_bottom <= available_height:
                        optimal_font_size_1line = font_size
                        temp_min = font_size + 1
                    else:
                        temp_max = font_size - 1

                # Opción 3: Dividir en 2 líneas y buscar tamaño óptimo
                abr_2lines = format_text_to_two_lines(abr)
                lines_2 = abr_2lines.splitlines()

                optimal_font_size_2lines = min_font_size
                temp_min_2 = min_font_size
                temp_max_2 = base_font_size

                while temp_min_2 <= temp_max_2:
                    font_size = (temp_min_2 + temp_max_2) // 2
                    fnt_test = create_font(font_size)

                    try:
                        bbox = d.textbbox((0, 0), "Ag", font=fnt_test)
                        line_height = bbox[3] - bbox[1]
                    except AttributeError:
                        line_height = fnt_test.getsize("Ag")[1]

                    text_bottom = len(lines_2) * line_height

                    # Verificar también que cada línea quepa en ancho
                    max_line_width = 0
                    for line in lines_2:
                        try:
                            lw = d.textbbox((0, 0), line, font=fnt_test)[2]
                        except AttributeError:
                            lw = fnt_test.getsize(line)[0]
                        max_line_width = max(max_line_width, lw)

                    # Verificar si cabe en altura y ancho
                    if text_bottom <= available_height and max_line_width <= max_width:
                        optimal_font_size_2lines = font_size
                        temp_min_2 = font_size + 1  # Intentar con tamaño mayor
                    else:
                        temp_max_2 = font_size - 1  # Reducir tamaño

                # Elegir la opción que da el tamaño de fuente más grande
                if optimal_font_size_1line >= optimal_font_size_2lines:
                    lines = [abr]
                    fnt = create_font(optimal_font_size_1line)
                else:
                    lines = lines_2
                    fnt = create_font(optimal_font_size_2lines)
    else:
        # No tiene espacio - ajustar solo por ancho usando búsqueda binaria
        lines = [abr]

        # Búsqueda binaria para encontrar el tamaño óptimo de fuente
        optimal_font_size = min_font_size
        temp_min = min_font_size
        temp_max = base_font_size

        while temp_min <= temp_max:
            font_size = (temp_min + temp_max) // 2
            fnt_test = create_font(font_size)

            try:
                text_width = d.textbbox((0, 0), abr, font=fnt_test)[2]
            except AttributeError:
                text_width = fnt_test.getsize(abr)[0]

            if text_width <= max_width:
                optimal_font_size = font_size
                temp_min = font_size + 1  # Intentar con tamaño mayor
            else:
                temp_max = font_size - 1  # Reducir tamaño

        fnt = create_font(optimal_font_size)

    # Calcular altura real de línea usando bbox que es más preciso
    try:
        # Medir la altura real de una línea de texto
        bbox = d.textbbox((0, 0), "Ag", font=fnt)
        line_height = bbox[3] - bbox[1]
    except AttributeError:
        # Método alternativo para versiones antiguas
        line_height = fnt.getsize("Ag")[1]

    # Calcular altura total del bloque de texto
    total_text_height = len(lines) * line_height

    # Calcular posición Y del texto según la ubicación seleccionada
    if text_position == "Arriba del QR":
        # Centrar verticalmente en el espacio disponible (desde arriba hasta el QR)
        y_start = (available_height - total_text_height) // 2
    else:
        # Centrar verticalmente en el espacio debajo del QR
        # El espacio comienza después del QR más el margen
        space_below_qr_start = qr_y_fixed + img_qr_big.size[1]
        # Calcular el espacio real disponible (desde el final del QR hasta el final de la imagen)
        space_below_qr_total = dimensions[1] - space_below_qr_start
        # Centrar el texto en ese espacio, pero subirlo un poco (ajuste de -20%)
        adjustment = int(space_below_qr_total * 0.10)
        y_start = (
            space_below_qr_start
            + (space_below_qr_total - total_text_height) // 2
            - adjustment
        )

    # Dibujar cada línea individualmente
    for i, line in enumerate(lines):
        try:
            line_width = d.textbbox((0, 0), line, font=fnt)[2]
        except AttributeError:
            line_width = fnt.getsize(line)[0]

        # Centrar horizontalmente cada línea
        x_pos = (img.size[0] - line_width) // 2
        y_pos = y_start + i * line_height

        d.text((x_pos, y_pos), line, font=fnt, fill=text_color)

    # Posicionar el código QR en su posición fija (nunca cambia)
    qr_x = (img.size[0] - img_qr_big.size[0]) // 2
    pos2 = (qr_x, qr_y_fixed)
    img.paste(img_qr_big, pos2)

    # Insertar logo en el centro del QR si se proporciona
    if logo_image is not None:
        # Calcular tamaño del logo basado en el porcentaje del QR
        logo_max_size = int(img_qr_big.size[0] * (logo_size_percent / 100))

        # Redimensionar logo manteniendo aspecto ratio
        logo = logo_image.copy()
        logo.thumbnail((logo_max_size, logo_max_size), Image.Resampling.LANCZOS)

        # Crear fondo blanco para el logo (para mejor visibilidad)
        # El fondo blanco es un poco más grande que el logo
        padding = int(logo_max_size * 0.1)  # 10% de padding
        bg_size = (logo.size[0] + padding * 2, logo.size[1] + padding * 2)
        logo_bg = Image.new("RGB", bg_size, "white")

        # Pegar el logo en el centro del fondo blanco
        logo_bg_x = (bg_size[0] - logo.size[0]) // 2
        logo_bg_y = (bg_size[1] - logo.size[1]) // 2

        # Si el logo tiene transparencia, usar composite, sino paste directo
        if logo.mode == "RGBA":
            # Crear una versión RGB del logo para el fondo
            logo_rgb = Image.new("RGB", logo.size, "white")
            logo_rgb.paste(
                logo, mask=logo.split()[3] if len(logo.split()) == 4 else None
            )
            logo_bg.paste(logo_rgb, (logo_bg_x, logo_bg_y))
        else:
            logo_bg.paste(logo, (logo_bg_x, logo_bg_y))

        # Calcular posición del logo en el centro del QR
        qr_center_x = qr_x + img_qr_big.size[0] // 2
        qr_center_y = qr_y_fixed + img_qr_big.size[1] // 2

        logo_pos_x = qr_center_x - logo_bg.size[0] // 2
        logo_pos_y = qr_center_y - logo_bg.size[1] // 2

        # Pegar el logo con fondo blanco en el centro del QR
        img.paste(logo_bg, (logo_pos_x, logo_pos_y))

    return img


def create_color_preview(color_rgb):
    """Crear una vista previa del color en formato HTML"""
    color_hex = f"#{color_rgb[0]:02x}{color_rgb[1]:02x}{color_rgb[2]:02x}"
    return f'<div style="width: 20px; height: 20px; flex-shrink: 0; background-color: {color_hex}; border: 1px solid #ccc; border-radius: 3px;"></div>'


def create_color_cell(letter):
    """Crear celda con color de fondo para la tabla"""
    # Obtener color (predefinido o personalizado)
    color_rgb = get_color_for_letter(letter)

    if color_rgb:
        color_hex = f"#{color_rgb[0]:02x}{color_rgb[1]:02x}{color_rgb[2]:02x}"
        # Calcular si necesitamos texto blanco o negro basado en el brillo del color
        brightness = (
            color_rgb[0] * 299 + color_rgb[1] * 587 + color_rgb[2] * 114
        ) / 1000
        text_color = "white" if brightness < 128 else "black"

        # Agregar indicador si es color personalizado
        is_custom = (
            hasattr(st, "session_state")
            and "custom_colors" in st.session_state
            and letter.upper() in st.session_state.custom_colors
        )

        suffix = " ✨" if is_custom else ""

        return f'<div style="background-color: {color_hex}; color: {text_color}; padding: 5px; text-align: center; border-radius: 3px; font-weight: bold;">{letter}{suffix}</div>'

    return f'<div style="background-color: #808080; color: white; padding: 5px; text-align: center; border-radius: 3px; font-weight: bold;">{letter}</div>'


def main():
    # Cargar colores personalizados desde archivo al iniciar
    if "custom_colors" not in st.session_state:
        st.session_state.custom_colors = load_custom_colors()

    # CSS personalizado para diseño responsive y colores
    st.markdown(
        """
    <style>
    /* Ocultar resize handle de dataframe */
    .stDataFrame [data-testid="stDataFrameResizeHandle"] {
        display: none !important;
    }

    /* Contenedor de colores responsive */
    .color-item {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        white-space: nowrap;
        padding: 6px 8px;
        background-color: rgba(240, 242, 246, 0.5);
        border-radius: 4px;
        min-height: 32px;
    }

    /* Evitar que las columnas de Streamlit se compriman demasiado */
    [data-testid="column"] {
        min-width: 60px !important;
        padding: 0 8px !important;
    }

    /* Responsive para pantallas pequeñas */
    @media (max-width: 768px) {
        [data-testid="column"] {
            min-width: 50px !important;
        }
        .color-item {
            font-size: 0.9em;
        }
    }

    /* Mejorar espaciado en móviles */
    @media (max-width: 640px) {
        .stButton button {
            width: 100% !important;
        }
        [data-testid="column"] {
            min-width: 40px !important;
        }
    }

    /* Sidebar responsive */
    section[data-testid="stSidebar"] {
        overflow-y: auto !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.title("Generador de Etiquetas QR")

    # Barra lateral para configuración
    with st.sidebar:
        st.header("📋 Información")

        # Instrucciones como expander
        with st.expander("¿Cómo usar esta herramienta?", expanded=False):
            st.markdown(
                """
            **Paso 1:** Sube tu archivo Excel o agrega datos manualmente

            **Paso 2:** Revisa y edita los datos en la tabla

            **Paso 3:** Genera y descarga tus etiquetas QR
            """
            )

        # Formato Excel como expander
        with st.expander("Formato del archivo Excel", expanded=False):
            st.markdown(
                """
            Tu archivo debe tener exactamente estas columnas:
            - **Localidad**: Datos para el código QR (ej: A02-01-01-01)
            - **Abr**: Texto que aparecerá en la etiqueta (ej: A02-01)
            - **Letra**: Código de color (A-Z, ver colores abajo)
            """
            )

        st.divider()

        # Configuración de dimensiones
        st.header("🔧 Tamaño etiquetas")

        # Dimensiones por defecto (código original)
        default_width_cm = 28.0
        default_height_cm = 29.0
        dpi = 600  # DPI del código original

        # Inicializar estado de dimensiones personalizadas si no existe
        if "use_custom_dimensions" not in st.session_state:
            st.session_state.use_custom_dimensions = False
        if "custom_width_cm" not in st.session_state:
            st.session_state.custom_width_cm = default_width_cm
        if "custom_height_cm" not in st.session_state:
            st.session_state.custom_height_cm = default_height_cm

        # Opción para usar dimensiones personalizadas
        use_custom_dimensions = st.checkbox("Personalizar dimensiones", value=False)

        if use_custom_dimensions:
            col_w, col_h = st.columns(2)

            with col_w:
                custom_width_cm = st.number_input(
                    "Ancho (cm)",
                    min_value=10.0,
                    max_value=100.0,
                    value=default_width_cm,
                    step=0.5,
                    help="Ancho de la etiqueta en centímetros",
                )

            with col_h:
                custom_height_cm = st.number_input(
                    "Alto (cm)",
                    min_value=10.0,
                    max_value=100.0,
                    value=default_height_cm,
                    step=0.5,
                    help="Alto de la etiqueta en centímetros",
                )

            # Convertir cm a píxeles
            pixel_width = int((custom_width_cm / 2.54) * dpi)
            pixel_height = int((custom_height_cm / 2.54) * dpi)

        else:
            # Usar dimensiones por defecto
            pixel_width = 6614
            pixel_height = 6850
            st.success(f"Por defecto: {default_width_cm}x{default_height_cm} cm")

        st.divider()

        # Configuración de posición del texto
        st.subheader("📍 Posición del Texto")

        text_position = st.radio(
            "Ubicación del texto:",
            options=["Arriba del QR", "Abajo del QR"],
            index=0,
            help="Elige dónde mostrar el texto en relación al código QR",
            horizontal=True,
        )

        st.divider()

        # Configuración de color de texto
        st.subheader("✍️ Color del Texto")

        text_color_mode = st.radio(
            "Modo de color de texto:",
            options=["Automático", "Blanco", "Negro", "Personalizado"],
            index=0,
            help="Automático: El color se ajusta según la luminosidad del fondo",
        )

        custom_text_color = None
        if text_color_mode == "Personalizado":

            custom_text_hex = st.color_picker(
                "Selecciona el color del texto:",
                value="#FFFFFF",
                help="Elige un color personalizado para el texto",
            )

            # Convertir hex a RGB
            hex_color = custom_text_hex.lstrip("#")
            custom_text_color = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

        st.divider()

        # Configuración de logo/imagen en el centro del QR
        st.subheader("🖼️ Logo dentro del QR")

        qr_logo = st.file_uploader(
            "Sube una imagen para el centro del QR (opcional):",
            type=["png", "jpg", "jpeg"],
            help="La imagen se redimensionará automáticamente y se insertará en el centro del QR",
        )

        if qr_logo:
            # Mostrar preview de la imagen subida
            col_prev1, col_prev2, col_prev3 = st.columns([1, 1, 1])
            with col_prev2:
                st.image(qr_logo, caption="Logo seleccionado", width=150)

            # Opción para ajustar el tamaño del logo
            logo_size_percent = st.slider(
                "Tamaño del logo (% del QR):",
                min_value=10,
                max_value=40,
                value=25,
                step=5,
                help="Porcentaje del tamaño del QR que ocupará el logo. 25% es recomendado para mantener legibilidad del QR",
            )
        else:
            logo_size_percent = 25

        # Convertir el logo a imagen PIL si existe
        logo_pil = None
        if qr_logo:
            try:
                logo_pil = Image.open(qr_logo)
                # Convertir a RGB si es necesario (para manejar RGBA, etc)
                if logo_pil.mode not in ("RGB", "RGBA"):
                    logo_pil = logo_pil.convert("RGB")
            except Exception as e:
                st.error(f"Error al cargar la imagen: {e}")
                logo_pil = None

        st.divider()

        # Sección de colores mejorada
        st.header("🎨 Configuración de Colores")

        # Opción para colores personalizados
        with st.expander("Agregar Color Personalizado", expanded=False):
            st.markdown(
                """
                **Define un color para una letra que no esté en la lista.**

                Los colores personalizados están disponibles solo durante tu sesión actual.
                """
            )

            col_custom1, col_custom2 = st.columns(2)
            with col_custom1:
                custom_letter = st.text_input(
                    "Letra:",
                    max_chars=1,
                    placeholder="Ej: Ñ",
                    help="Ingresa una sola letra",
                ).upper()

            with col_custom2:
                custom_color = st.color_picker(
                    "Color:", value="#808080", help="Selecciona el color de fondo"
                )

            if custom_letter and st.button("Agregar Color Personalizado"):
                # Convertir color hex a RGB
                hex_color = custom_color.lstrip("#")
                rgb_color = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

                # Agregar al diccionario de colores en sesión
                if "custom_colors" not in st.session_state:
                    st.session_state.custom_colors = {}

                st.session_state.custom_colors[custom_letter] = rgb_color

                st.success(f"✅ Color '{custom_letter}' agregado para esta sesión")
                st.rerun()

        # Mostrar colores personalizados si existen
        if "custom_colors" in st.session_state and st.session_state.custom_colors:
            st.subheader("🔧 Colores Personalizados")

            # Grid flexible con flex-wrap
            custom_items = list(st.session_state.custom_colors.items())
            custom_html = '<div style="display: flex; flex-wrap: wrap; gap: 12px; margin: 10px 0;">'
            for letter, color in custom_items:
                color_preview = create_color_preview(color)
                custom_html += f'<div class="color-item" style="min-width: 60px;">{color_preview}<span style="font-weight: bold;">{letter} ✨</span></div>'
            custom_html += "</div>"

            st.markdown(custom_html, unsafe_allow_html=True)

        st.subheader("Colores Predefinidos")

        # Grid flexible que se adapta al espacio disponible
        color_items = list(COLORES.items())

        # Crear un contenedor flex responsive en lugar de columnas fijas
        colors_html = (
            '<div style="display: flex; flex-wrap: wrap; gap: 12px; margin: 10px 0;">'
        )
        for letter, color in color_items:
            color_preview = create_color_preview(color)
            colors_html += f'<div class="color-item" style="min-width: 50px;">{color_preview}<span style="font-weight: bold;">{letter}</span></div>'
        colors_html += "</div>"

        st.markdown(colors_html, unsafe_allow_html=True)

        # Mostrar color por defecto
        default_preview = create_color_preview(COLOR_DEFAULT)

    # Área de contenido principal
    col1, col2 = st.columns([2, 1])

    with col1:
        # Opción 1: Subir archivo Excel
        st.header("🗂️ Opción 1: Subir Archivo Excel")

        # Botón para descargar plantilla Excel
        # Crear Excel de plantilla vacía (solo columnas)
        template_df = pd.DataFrame({"Localidad": [], "Abr": [], "Letra": []})

        # Convertir a Excel en memoria
        template_buffer = io.BytesIO()
        with pd.ExcelWriter(template_buffer, engine="openpyxl") as writer:
            template_df.to_excel(writer, index=False, sheet_name="Etiquetas")
        template_buffer.seek(0)

        st.download_button(
            label="Descargar Plantilla Excel",
            data=template_buffer.getvalue(),
            file_name="plantilla_etiquetas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Descarga un archivo Excel vacío con el formato correcto",
            use_container_width=False,
        )

        # Subir archivo Excel
        uploaded_file = st.file_uploader(
            "Selecciona tu archivo Excel",
            type=["xlsx", "xls"],
            help="📋 Sube un archivo Excel con las columnas: Localidad, Abr, Letra",
        )

        # Inicializar estado de sesión para datos
        if "df_data" not in st.session_state:
            st.session_state.df_data = pd.DataFrame(
                {"Localidad": [""], "Abr": [""], "Letra": [""]}
            )

        # Cargar datos del Excel si se sube
        if uploaded_file is not None:
            try:
                df_uploaded = pd.read_excel(uploaded_file)

                # Normalizar nombres de columnas (eliminar espacios y convertir a minúsculas)
                df_uploaded.columns = df_uploaded.columns.str.strip().str.lower()

                # Mapeo de columnas flexibles
                column_mapping = {}
                required_cols = {
                    "localidad": ["localidad", "local", "location", "codigo"],
                    "abr": [
                        "abr",
                        "abreviacion",
                        "abreviación",
                        "texto",
                        "text",
                        "nombre",
                    ],
                    "letra": ["letra", "color", "letter"],
                }

                # Buscar cada columna requerida
                found_cols = {}
                for target_col, possible_names in required_cols.items():
                    for col in df_uploaded.columns:
                        if col in possible_names:
                            found_cols[target_col] = col
                            break

                # Verificar si se encontraron todas las columnas
                if len(found_cols) == 3:
                    # Renombrar columnas al formato estándar
                    df_mapped = df_uploaded.rename(
                        columns={
                            found_cols["localidad"]: "Localidad",
                            found_cols["abr"]: "Abr",
                            found_cols["letra"]: "Letra",
                        }
                    )

                    st.session_state.df_data = df_mapped[
                        ["Localidad", "Abr", "Letra"]
                    ].copy()
                    st.success(
                        f"✅ Se cargaron {len(df_mapped)} filas desde el archivo Excel"
                    )
                else:
                    missing = []
                    if "localidad" not in found_cols:
                        missing.append("Localidad (o similar)")
                    if "abr" not in found_cols:
                        missing.append("Abr/Abreviación (o similar)")
                    if "letra" not in found_cols:
                        missing.append("Letra/Color (o similar)")

                    st.error(
                        f"❌ No se encontraron las columnas necesarias. Faltan: {', '.join(missing)}"
                    )
                    st.info(
                        "Columnas aceptadas: Localidad/Local/Codigo, Abr/Abreviacion/Texto/Nombre, Letra/Color"
                    )
            except Exception as e:
                st.error(f"❌ Error al leer el archivo Excel: {str(e)}")

        st.divider()

        # Opción 2: Entrada manual de datos
        st.header("✏️ Opción 2: Entrada Manual de Datos")

        # Editor de datos
        edited_df = st.data_editor(
            st.session_state.df_data,
            num_rows="dynamic",
            column_config={
                "Localidad": st.column_config.TextColumn(
                    "Localidad (Datos QR)",
                    help="Los datos que se codificarán en el código QR",
                    required=True,
                ),
                "Abr": st.column_config.TextColumn(
                    "Abreviación (Texto)",
                    help="El texto que se mostrará en la etiqueta (se ajusta automáticamente)",
                    required=True,
                ),
                "Letra": st.column_config.TextColumn(
                    "Letra (Color)",
                    help="La letra que determina el color de fondo (A-Z o personalizada)",
                    max_chars=1,
                    required=True,
                ),
            },
            use_container_width=True,
            key="data_editor",
        )

        # Remover filas vacías
        df_clean = edited_df.dropna(subset=["Localidad", "Abr"]).reset_index(drop=True)
        df_clean = df_clean[df_clean["Localidad"].str.strip() != ""].reset_index(
            drop=True
        )

        # Mostrar tabla con colores visuales
        if len(df_clean) > 0:
            st.subheader("🎨 Vista Previa de Colores Seleccionados")

            # Crear DataFrame para mostrar con colores
            display_df = df_clean.copy()
            display_df["Color Visual"] = display_df["Letra"].apply(create_color_cell)

            # Mostrar como HTML para que se vean los colores
            html_table = "<table style='width: 100%; border-collapse: collapse;'>"
            html_table += "<tr style='background-color: #f0f0f0; font-weight: bold;'>"
            html_table += (
                "<th style='padding: 10px; border: 1px solid #ddd;'>Localidad</th>"
            )
            html_table += (
                "<th style='padding: 10px; border: 1px solid #ddd;'>Abreviación</th>"
            )
            html_table += (
                "<th style='padding: 10px; border: 1px solid #ddd;'>Letra</th>"
            )
            html_table += (
                "<th style='padding: 10px; border: 1px solid #ddd;'>Color</th>"
            )
            html_table += "</tr>"

            for _, row in df_clean.head(
                5
            ).iterrows():  # Mostrar solo las primeras 5 filas
                html_table += "<tr>"
                html_table += f"<td style='padding: 8px; border: 1px solid #ddd;'>{row['Localidad']}</td>"
                html_table += f"<td style='padding: 8px; border: 1px solid #ddd;'>{row['Abr']}</td>"
                html_table += f"<td style='padding: 8px; border: 1px solid #ddd;'>{row['Letra']}</td>"
                html_table += f"<td style='padding: 8px; border: 1px solid #ddd;'>{create_color_cell(row['Letra'])}</td>"
                html_table += "</tr>"
            html_table += "</table>"

            st.markdown(html_table, unsafe_allow_html=True)

            if len(df_clean) > 5:
                st.info(f"Mostrando las primeras 5 filas de {len(df_clean)} total")

            # Mostrar leyenda de iconos
            st.markdown(
                """
                **Leyenda:** 
                - ✨ = Color personalizado
                - Sin icono = Color predefinido
                - Gris = Color por defecto (letra no definida)
                """
            )

    with col2:
        st.header("👀 Vista Previa")

        if len(df_clean) > 0:
            # Vista previa con selector mejorado
            if st.checkbox("Mostrar Vista Previa", value=True):
                # Sistema de navegación eficiente
                total_etiquetas = len(df_clean)

                # Inicializar índice de navegación en session_state
                if "preview_index" not in st.session_state:
                    st.session_state.preview_index = 1

                # Asegurar que el índice esté dentro de los límites
                if st.session_state.preview_index > total_etiquetas:
                    st.session_state.preview_index = total_etiquetas
                elif st.session_state.preview_index < 1:
                    st.session_state.preview_index = 1

                # Botones de navegación
                col_prev, col_next = st.columns(2)

                with col_prev:
                    if st.button(
                        "⬅️ Anterior",
                        disabled=(st.session_state.preview_index <= 1),
                        use_container_width=True,
                        key="btn_prev",
                    ):
                        st.session_state.preview_index = max(1, st.session_state.preview_index - 1)
                        st.rerun()

                with col_next:
                    if st.button(
                        "Siguiente ➡️",
                        disabled=(st.session_state.preview_index >= total_etiquetas),
                        use_container_width=True,
                        key="btn_next",
                    ):
                        st.session_state.preview_index = min(total_etiquetas, st.session_state.preview_index + 1)
                        st.rerun()

                # Number input con on_change callback
                def update_preview():
                    # Esta función se ejecuta cuando el number_input cambia
                    pass

                st.number_input(
                    f"Ir a etiqueta (1-{total_etiquetas}):",
                    min_value=1,
                    max_value=total_etiquetas,
                    value=st.session_state.preview_index,
                    step=1,
                    key="preview_index",  # ← Key igual al nombre en session_state
                    on_change=update_preview,
                )

                # Convertir a índice base 0 para acceder al dataframe
                selected_preview = st.session_state.preview_index - 1

                # Mostrar info de la etiqueta actual
                st.markdown(
                    f"<div style='text-align: center; padding: 5px; background-color: rgba(240, 242, 246, 0.5); border-radius: 4px; margin: 10px 0;'>"
                    f"<strong>{df_clean.iloc[selected_preview]['Abr']}</strong> · "
                    f"Letra {df_clean.iloc[selected_preview]['Letra']} · "
                    f"Etiqueta {selected_preview + 1}/{total_etiquetas}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

                with st.expander("Vista Previa de Etiqueta", expanded=True):
                    try:
                        preview_img = generate_qr_label(
                            df_clean.iloc[selected_preview]["Localidad"],
                            df_clean.iloc[selected_preview]["Abr"],
                            df_clean.iloc[selected_preview]["Letra"],
                            (pixel_width, pixel_height),
                            text_color_mode,
                            custom_text_color,
                            logo_pil,
                            logo_size_percent,
                            text_position,
                        )
                        # Redimensionar para vista previa manteniendo proporción
                        aspect_ratio = preview_img.height / preview_img.width
                        preview_width = 250
                        preview_height = int(preview_width * aspect_ratio)
                        preview_img_small = preview_img.resize(
                            (preview_width, preview_height)
                        )

                        # Centrar la imagen usando columnas
                        col1, col2, col3 = st.columns([1, 2, 1])
                        with col2:
                            st.image(
                                preview_img_small,
                                caption=f"Etiqueta {selected_preview + 1}: {df_clean.iloc[selected_preview]['Localidad']}",
                                use_container_width=True,
                            )

                    except Exception as e:
                        st.error(f"Error en vista previa: {str(e)}")

            st.divider()

            # Opciones de generación
            st.subheader("📥 Opciones de Descarga")

            # Opciones de generación mejoradas
            col_gen1, col_gen2 = st.columns(2)

            with col_gen1:
                # Inicializar estado de sesión para controlar la cancelación
                if "generating" not in st.session_state:
                    st.session_state.generating = False
                if "cancel_generation" not in st.session_state:
                    st.session_state.cancel_generation = False
                if "zip_ready" not in st.session_state:
                    st.session_state.zip_ready = False

                # Mostrar descarga automática si el ZIP está listo
                if st.session_state.zip_ready and "zip_data" in st.session_state:
                    st.success(
                        f"🎉 ¡{st.session_state.success_count} etiquetas generadas exitosamente! Descargando archivo..."
                    )

                    # Convertir a base64 para descarga automática
                    b64 = base64.b64encode(st.session_state.zip_data).decode()
                    filename = st.session_state.zip_filename

                    # HTML con auto-descarga que funciona en Streamlit
                    download_html = f"""
                        <html>
                        <body>
                        <script>
                            // Crear elemento de descarga automática
                            const link = document.createElement('a');
                            link.href = 'data:application/zip;base64,{b64}';
                            link.download = '{filename}';
                            link.style.display = 'none';
                            document.body.appendChild(link);

                            // Ejecutar descarga inmediatamente
                            setTimeout(function() {{
                                link.click();
                                document.body.removeChild(link);
                            }}, 500);
                        </script>
                        </body>
                        </html>
                    """

                    # Renderizar HTML de descarga
                    st.components.v1.html(download_html, height=0)

                    # Limpiar estado después de iniciar descarga
                    st.session_state.zip_ready = False
                    del st.session_state.zip_data
                    del st.session_state.zip_filename
                    del st.session_state.success_count

                if not st.session_state.generating and not st.session_state.zip_ready:
                    if st.button("Generar Todas las Etiquetas", type="primary"):
                        st.session_state.generating = True
                        st.session_state.cancel_generation = False
                        st.session_state.zip_ready = False
                        st.rerun()
                else:
                    # Mostrar botón de cancelar
                    if st.button("Cancelar Generación", type="secondary"):
                        st.session_state.cancel_generation = True
                        st.session_state.generating = False
                        st.warning("⚠️ Generación cancelada por el usuario")
                        st.rerun()

                # Proceso de generación
                if st.session_state.generating and len(df_clean) > 0:
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # Crear directorio temporal para PDFs
                    with tempfile.TemporaryDirectory() as temp_dir:
                        pdf_files = []
                        success_count = 0
                        cancelled = False

                        for idx, row in df_clean.iterrows():
                            # Verificar si se canceló
                            if st.session_state.cancel_generation:
                                cancelled = True
                                break

                            status_text.text(
                                f"🏷️ Procesando: {row['Abr']} ({idx + 1}/{len(df_clean)})"
                            )
                            progress_bar.progress((idx + 1) / len(df_clean))

                            try:
                                # Generar imagen
                                img = generate_qr_label(
                                    row["Localidad"],
                                    row["Abr"],
                                    row["Letra"],
                                    (pixel_width, pixel_height),
                                    text_color_mode,
                                    custom_text_color,
                                    logo_pil,
                                    logo_size_percent,
                                    text_position,
                                )

                                # Generar nombre de archivo limpio
                                safe_filename = (
                                    str(row["Localidad"])
                                    .replace("/", "-")
                                    .replace("\\", "-")
                                )
                                pdf_path = os.path.join(
                                    temp_dir, f"{safe_filename}_{idx + 1}.pdf"
                                )

                                # Guardar como PDF con DPI correcto
                                img.save(pdf_path, "PDF", resolution=float(dpi))
                                pdf_files.append(pdf_path)
                                success_count += 1

                            except Exception as e:
                                st.error(
                                    f"❌ Error en etiqueta {idx + 1} ({row['Abr']}): {str(e)}"
                                )

                        # Crear archivo ZIP si no se canceló
                        if not cancelled and pdf_files:
                            zip_buffer = io.BytesIO()
                            with zipfile.ZipFile(
                                zip_buffer, "w", zipfile.ZIP_DEFLATED
                            ) as zip_file:
                                for pdf_path in pdf_files:
                                    zip_file.write(pdf_path, os.path.basename(pdf_path))

                            zip_buffer.seek(0)

                            # Guardar en session state para descarga
                            st.session_state.zip_data = zip_buffer.getvalue()
                            st.session_state.zip_filename = f"etiquetas_qr_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                            st.session_state.success_count = success_count
                            st.session_state.zip_ready = True

                        elif cancelled:
                            st.warning("⚠️ Generación cancelada")
                        else:
                            st.error("❌ No se pudo generar ninguna etiqueta")

                        progress_bar.empty()
                        status_text.empty()

                        # Resetear estado
                        st.session_state.generating = False
                        st.session_state.cancel_generation = False

                        # Rerun para activar descarga
                        if not cancelled and pdf_files:
                            st.rerun()

            with col_gen2:
                # Generar etiqueta individual de muestra
                if st.button("Generar Etiqueta de Muestra"):
                    if len(df_clean) > 0:
                        try:
                            # Generar primera etiqueta como muestra
                            sample_img = generate_qr_label(
                                df_clean.iloc[0]["Localidad"],
                                df_clean.iloc[0]["Abr"],
                                df_clean.iloc[0]["Letra"],
                                (pixel_width, pixel_height),
                                text_color_mode,
                                custom_text_color,
                                logo_pil,
                                logo_size_percent,
                                text_position,
                            )

                            # Convertir a PDF en memoria
                            pdf_buffer = io.BytesIO()
                            sample_img.save(pdf_buffer, "PDF", resolution=float(dpi))
                            pdf_buffer.seek(0)

                            st.download_button(
                                label=f"Descargar Muestra: {df_clean.iloc[0]['Abr']}",
                                data=pdf_buffer.getvalue(),
                                file_name=f"muestra_{df_clean.iloc[0]['Localidad']}.pdf",
                                mime="application/pdf",
                                use_container_width=True,
                            )

                        except Exception as e:
                            st.error(f"❌ Error generando muestra: {str(e)}")
        else:
            st.warning(
                "No se encontraron entradas válidas. Por favor agrega datos arriba."
            )

        # Botón de datos de ejemplo mejorado
        st.divider()

        col_example1, col_example2 = st.columns(2)

        with col_example1:
            if st.button("Cargar Datos de Ejemplo", use_container_width=True):
                # Agregar algunos colores personalizados de ejemplo
                if "custom_colors" not in st.session_state:
                    st.session_state.custom_colors = {}

                sample_data = pd.DataFrame(
                    {
                        "Localidad": [
                            "A02-01-01-01",
                            "B03-02-01-02",
                            "C04-03-02-01",
                            "R05-04-01-03",
                            "G06-02-04",
                            "H07-03-05",
                        ],
                        "Abr": [
                            "A02-01",
                            "B03-02",
                            "Almacén Central",
                            "Deposito Sur",
                            "CARPA G",
                            "Zona de Carga",
                        ],
                        "Letra": ["A", "B", "C", "R", "G", "H"],
                    }
                )
                st.session_state.df_data = sample_data
                st.success(
                    "✅ Datos cargados con ejemplos de texto largo, colores personalizados y letras no definidas"
                )
                st.rerun()

        with col_example2:
            if st.button("Limpiar Todo", use_container_width=True):
                st.session_state.df_data = pd.DataFrame(
                    {"Localidad": [""], "Abr": [""], "Letra": ["A"]}
                )

                # Resetear dimensiones personalizadas a valores por defecto
                st.session_state.use_custom_dimensions = False
                st.session_state.custom_width_cm = 28.0
                st.session_state.custom_height_cm = 29.0

                # Limpiar también las keys de los widgets
                if "checkbox_custom_dims" in st.session_state:
                    del st.session_state.checkbox_custom_dims
                if "input_width_cm" in st.session_state:
                    del st.session_state.input_width_cm
                if "input_height_cm" in st.session_state:
                    del st.session_state.input_height_cm

                # Limpiar colores personalizados también
                if "custom_colors" in st.session_state:
                    st.session_state.custom_colors = {}

                st.success("Datos, colores y dimensiones limpiados")
                st.rerun()


if __name__ == "__main__":
    main()
