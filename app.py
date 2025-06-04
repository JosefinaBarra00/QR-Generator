import streamlit as st
import qrcode
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
from datetime import datetime
import io
import zipfile
import tempfile
import os

# Configuración de página
st.set_page_config(page_title="Generador de Etiquetas QR", page_icon="🏷️", layout="wide")

# Definición de colores solo para letras del abecedario (ordenadas alfabéticamente)
COLORES = {
    "A": (213, 43, 30),  # Rojo
    "B": (0, 133, 66),  # Verde
    "C": (0, 101, 189),  # Azul
    "D": (240, 171, 0),  # Amarillo
    "E": (117, 48, 119),  # Púrpura
    "F": (215, 31, 133),  # Rosa
    "G": (255, 88, 0),  # Naranja
    "H": (249, 227, 0),  # Amarillo claro
    "I": (0, 0, 0),  # Negro
    "J": (0, 38, 100),  # Azul marino
    "K": (104, 69, 13),  # Marrón
    "L": (78, 84, 87),  # Gris oscuro
    "M": (198, 191, 110),  # Beige
    "N": (178, 175, 175),  # Gris claro
    "O": (135, 135, 135),  # Gris medio
    "P": (0, 161, 222),  # Celeste
    "Q": (127, 127, 126),  # Gris
    "R": (56, 142, 60),  # Verde oscuro
    "S": (255, 234, 200),  # Crema
    "T": (165, 42, 42),  # Marrón rojizo
    "U": (75, 0, 130),  # Índigo
    "V": (255, 20, 147),  # Rosa fuerte
    "W": (0, 128, 128),  # Verde azulado
    "X": (128, 0, 128),  # Magenta
    "Y": (255, 215, 0),  # Dorado
    "Z": (47, 79, 79),  # Gris verde
}


def calculate_optimal_font_size(text, image_width, max_font_size=None):
    """Calcular el tamaño óptimo de fuente basado en la longitud del texto"""
    text_length = len(text.replace("\n", "").replace(" ", ""))

    # Tamaño base proporcional al ancho de la imagen
    base_size = image_width // 6

    if max_font_size:
        base_size = min(base_size, max_font_size)

    # Ajustar según la longitud del texto
    if text_length <= 5:
        return int(base_size * 1.2)  # Texto corto - fuente más grande
    elif text_length <= 10:
        return int(base_size * 1.0)  # Texto medio - fuente normal
    elif text_length <= 15:
        return int(base_size * 0.8)  # Texto largo - fuente más pequeña
    elif text_length <= 20:
        return int(base_size * 0.65)  # Texto muy largo
    else:
        return int(base_size * 0.5)  # Texto extremadamente largo


def format_text_to_two_lines(text):
    """Formatear texto para tener máximo 2 líneas, dividiendo por espacios inteligentemente"""
    words = text.split()

    if len(words) <= 1:
        return text

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


def create_default_font(size):
    """Crear una fuente por defecto si la fuente personalizada no está disponible"""
    try:
        return ImageFont.truetype("arial.ttf", size)
    except:
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


def generate_qr_label(localidad, abr, letra, dimensions=(6614, 6850)):
    """Generar una etiqueta QR con los parámetros dados"""

    # Formatear texto de abreviación si es necesario
    if " " in abr and len(abr) > 15:
        abr = format_text_to_two_lines(abr)

    color = COLORES.get(
        letra, (0, 0, 0)
    )  # Por defecto negro si no se encuentra la letra

    # Crear imagen con dimensiones personalizadas
    img = Image.new("RGB", dimensions, color=color)

    # Calcular tamaño de fuente óptimo
    font_size = calculate_optimal_font_size(abr, dimensions[0])

    # Crear fuente
    fnt = create_default_font(font_size)

    d = ImageDraw.Draw(img)

    # Generar código QR primero para calcular posiciones
    qr_size = min(dimensions) // 35  # Tamaño QR proporcional a las dimensiones
    qr_big = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=qr_size, border=1
    )
    qr_big.add_data(localidad)
    qr_big.make(fit=True)
    img_qr_big = qr_big.make_image().convert("RGB")

    # Posicionar código QR en el centro vertical de la imagen
    qr_x = (img.size[0] - img_qr_big.size[0]) // 2
    qr_y = (img.size[1] - img_qr_big.size[1]) // 2

    # Calcular posición del texto ENCIMA del QR
    lines = abr.splitlines()

    # Calcular dimensiones del texto
    try:
        line_height = d.textbbox((0, 0), "Ag", font=fnt)[
            3
        ]  # Usar caracteres con ascendentes y descendentes
    except AttributeError:
        line_height = fnt.getsize("Ag")[1]

    total_text_height = line_height * len(lines)

    # Posicionar texto encima del QR con espacio
    text_spacing = int(dimensions[1] * 0.03)  # 3% de la altura como espacio
    text_start_y = qr_y - total_text_height - text_spacing

    # Asegurar que el texto no se salga por arriba
    if text_start_y < int(dimensions[1] * 0.05):  # Margen mínimo del 5%
        text_start_y = int(dimensions[1] * 0.05)

    # Dibujar cada línea del texto
    for i, line in enumerate(lines):
        try:
            line_width = d.textbbox((0, 0), line, font=fnt)[2]
        except AttributeError:
            line_width, _ = fnt.getsize(line)

        x_pos = (img.size[0] - line_width) // 2
        y_pos = text_start_y + i * line_height

        # Dibujar texto con sombra para mejor legibilidad
        # Sombra
        d.text((x_pos + 2, y_pos + 2), line, font=fnt, fill=(0, 0, 0, 128))
        # Texto principal
        d.text((x_pos, y_pos), line, font=fnt, fill=(255, 255, 255))

    # Pegar el código QR
    img.paste(img_qr_big, (qr_x, qr_y))

    return img


def create_color_preview(color_rgb):
    """Crear una vista previa del color en formato HTML"""
    color_hex = f"#{color_rgb[0]:02x}{color_rgb[1]:02x}{color_rgb[2]:02x}"
    return f'<div style="display: inline-block; width: 20px; height: 20px; background-color: {color_hex}; border: 1px solid #ccc; border-radius: 3px; margin-right: 8px; vertical-align: middle;"></div>'


def create_color_cell(letter):
    """Crear celda con color de fondo para la tabla"""
    if letter in COLORES:
        color_rgb = COLORES[letter]
        color_hex = f"#{color_rgb[0]:02x}{color_rgb[1]:02x}{color_rgb[2]:02x}"
        # Calcular si necesitamos texto blanco o negro basado en el brillo del color
        brightness = (
            color_rgb[0] * 299 + color_rgb[1] * 587 + color_rgb[2] * 114
        ) / 1000
        text_color = "white" if brightness < 128 else "black"
        return f'<div style="background-color: {color_hex}; color: {text_color}; padding: 5px; text-align: center; border-radius: 3px; font-weight: bold;">{letter}</div>'
    return letter


def main():
    # CSS personalizado para mostrar colores en la tabla
    st.markdown(
        """
    <style>
    .stDataFrame [data-testid="stDataFrameResizeHandle"] {
        display: none !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.title("🏷️ Generador de Etiquetas QR")
    st.markdown("### ✨ Crea etiquetas PDF personalizadas con códigos QR y texto")

    # Barra lateral para configuración
    with st.sidebar:
        st.header("📋 Instrucciones")
        st.markdown(
            """
        ### 🚀 ¿Cómo usar esta herramienta?
        
        **Paso 1:** 📂 Sube tu archivo Excel o agrega datos manualmente
        
        **Paso 2:** ✏️ Revisa y edita los datos en la tabla
        
        **Paso 3:** ⚙️ Configura las dimensiones de tu etiqueta
        
        **Paso 4:** 📥 Genera y descarga tus PDFs
        
        ---
        
        ### 📊 Formato del archivo Excel
        Tu archivo debe tener exactamente estas columnas:
        - **Localidad**: Datos para el código QR
        - **Abr**: Texto que aparecerá en la etiqueta
        - **Letra**: Código de color (A-Z)
        
        💡 **Tip**: El tamaño de la fuente se ajusta automáticamente según la longitud del texto
        """
        )

        st.divider()

        # Configuración de dimensiones
        st.header("📏 Configuración de Dimensiones")

        col_unit1, col_unit2 = st.columns(2)
        with col_unit1:
            unit = st.selectbox(
                "Unidad de medida:",
                ["mm", "cm", "m", "píxeles"],
                index=0,
                help="Selecciona la unidad para las dimensiones",
            )

        with col_unit2:
            dpi = st.number_input(
                "DPI:",
                min_value=72,
                max_value=600,
                value=300,
                step=50,
                help="Resolución de impresión (dots per inch)",
            )

        col_dim1, col_dim2 = st.columns(2)
        with col_dim1:
            if unit == "mm":
                width = st.number_input(
                    "Ancho (mm):", min_value=10, max_value=500, value=210, step=5
                )
            elif unit == "cm":
                width = st.number_input(
                    "Ancho (cm):", min_value=1, max_value=50, value=21, step=1
                )
            elif unit == "m":
                width = st.number_input(
                    "Ancho (m):", min_value=0.1, max_value=5.0, value=0.21, step=0.01
                )
            else:
                width = st.number_input(
                    "Ancho (px):", min_value=100, max_value=10000, value=6614, step=100
                )

        with col_dim2:
            if unit == "mm":
                height = st.number_input(
                    "Alto (mm):", min_value=10, max_value=500, value=297, step=5
                )
            elif unit == "cm":
                height = st.number_input(
                    "Alto (cm):", min_value=1, max_value=50, value=29.7, step=1
                )
            elif unit == "m":
                height = st.number_input(
                    "Alto (m):", min_value=0.1, max_value=5.0, value=0.297, step=0.01
                )
            else:
                height = st.number_input(
                    "Alto (px):", min_value=100, max_value=10000, value=6850, step=100
                )

        # Convertir dimensiones a píxeles
        if unit != "píxeles":
            pixel_width, pixel_height = get_dimensions_in_pixels(
                width, height, unit, dpi
            )
            st.info(f"📐 Dimensiones finales: {pixel_width} x {pixel_height} píxeles")
        else:
            pixel_width, pixel_height = int(width), int(height)

        st.divider()

        # Mostrar colores disponibles con vista previa visual
        st.header("🎨 Colores Disponibles")
        st.markdown("*Letras ordenadas alfabéticamente*")

        # Crear grid de colores (3 columnas para mejor visualización)
        colors_per_row = 3
        color_items = list(COLORES.items())

        for i in range(0, len(color_items), colors_per_row):
            cols = st.columns(colors_per_row)
            for j, (letter, color) in enumerate(color_items[i : i + colors_per_row]):
                if j < len(cols):
                    with cols[j]:
                        color_preview = create_color_preview(color)
                        st.markdown(
                            f"{color_preview}**{letter}**", unsafe_allow_html=True
                        )

    # Área de contenido principal
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("📝 Entrada de Datos")

        # Opción 1: Subir archivo Excel
        st.subheader("🗂️ Opción 1: Subir Archivo Excel")
        uploaded_file = st.file_uploader(
            "Selecciona tu archivo Excel",
            type=["xlsx", "xls"],
            help="📋 Sube un archivo Excel con las columnas: Localidad, Abr, Letra",
        )

        # Inicializar estado de sesión para datos
        if "df_data" not in st.session_state:
            st.session_state.df_data = pd.DataFrame(
                {"Localidad": [""], "Abr": [""], "Letra": ["A"]}
            )

        # Cargar datos del Excel si se sube
        if uploaded_file is not None:
            try:
                df_uploaded = pd.read_excel(uploaded_file)
                required_cols = ["Localidad", "Abr", "Letra"]
                if all(col in df_uploaded.columns for col in required_cols):
                    st.session_state.df_data = df_uploaded[required_cols].copy()
                    st.success(
                        f"✅ Se cargaron {len(df_uploaded)} filas desde el archivo Excel"
                    )
                else:
                    st.error(
                        f"❌ El archivo Excel debe contener las columnas: {', '.join(required_cols)}"
                    )
            except Exception as e:
                st.error(f"❌ Error al leer el archivo Excel: {str(e)}")

        st.divider()

        # Opción 2: Entrada manual de datos
        st.subheader("✏️ Opción 2: Entrada Manual de Datos")

        # Editor de datos
        edited_df = st.data_editor(
            st.session_state.df_data,
            num_rows="dynamic",
            column_config={
                "Localidad": st.column_config.TextColumn(
                    "🏢 Localidad (Datos QR)",
                    help="Los datos que se codificarán en el código QR",
                    required=True,
                ),
                "Abr": st.column_config.TextColumn(
                    "📝 Abreviación (Texto)",
                    help="El texto que se mostrará en la etiqueta (se ajusta automáticamente)",
                    required=True,
                ),
                "Letra": st.column_config.SelectboxColumn(
                    "🎨 Letra (Color)",
                    help="La letra que determina el color de fondo (A-Z)",
                    options=list(COLORES.keys()),
                    required=True,
                ),
            },
            use_container_width=True,
            key="data_editor",
        )

        # Actualizar estado de sesión
        st.session_state.df_data = edited_df

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
                st.info(f"📝 Mostrando las primeras 5 filas de {len(df_clean)} total")

    with col2:
        st.header("👀 Vista Previa y Generar")

        if len(df_clean) > 0:
            st.success(f"✅ {len(df_clean)} entradas válidas listas")

            # Vista previa de la primera entrada
            if st.checkbox("🔍 Mostrar Vista Previa", value=True):
                with st.expander("Vista Previa de la Primera Etiqueta", expanded=True):
                    try:
                        preview_img = generate_qr_label(
                            df_clean.iloc[0]["Localidad"],
                            df_clean.iloc[0]["Abr"],
                            df_clean.iloc[0]["Letra"],
                            (pixel_width, pixel_height),
                        )
                        # Redimensionar para vista previa manteniendo proporción
                        aspect_ratio = preview_img.height / preview_img.width
                        preview_width = 250
                        preview_height = int(preview_width * aspect_ratio)
                        preview_img_small = preview_img.resize(
                            (preview_width, preview_height)
                        )
                        st.image(
                            preview_img_small,
                            caption="Vista previa de la primera etiqueta",
                        )

                        # Mostrar información de dimensiones
                        st.info(
                            f"📐 Dimensiones: {pixel_width} x {pixel_height} px ({width} x {height} {unit})"
                        )

                        # Mostrar información del texto
                        text_length = len(df_clean.iloc[0]["Abr"])
                        st.info(
                            f"📝 Texto: '{df_clean.iloc[0]['Abr']}' ({text_length} caracteres)"
                        )

                    except Exception as e:
                        st.error(f"Error en vista previa: {str(e)}")

            st.divider()

            # Opciones de generación
            st.subheader("📥 Opciones de Descarga")

            # Generación de PDFs individuales
            if st.button("🚀 Generar Todos los PDFs", type="primary"):
                if len(df_clean) > 0:
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # Crear directorio temporal para PDFs
                    with tempfile.TemporaryDirectory() as temp_dir:
                        pdf_files = []

                        for idx, row in df_clean.iterrows():
                            status_text.text(
                                f"🏷️ Generando etiqueta {idx + 1} de {len(df_clean)}..."
                            )
                            progress_bar.progress((idx + 1) / len(df_clean))

                            try:
                                # Generar imagen
                                img = generate_qr_label(
                                    row["Localidad"],
                                    row["Abr"],
                                    row["Letra"],
                                    (pixel_width, pixel_height),
                                )

                                # Guardar como PDF
                                pdf_path = os.path.join(
                                    temp_dir, f"{row['Localidad']}_{idx + 1}.pdf"
                                )
                                img.save(pdf_path, "PDF", resolution=float(dpi))
                                pdf_files.append(pdf_path)

                            except Exception as e:
                                st.error(
                                    f"❌ Error generando etiqueta {idx + 1}: {str(e)}"
                                )

                        # Crear archivo ZIP
                        if pdf_files:
                            zip_buffer = io.BytesIO()
                            with zipfile.ZipFile(
                                zip_buffer, "w", zipfile.ZIP_DEFLATED
                            ) as zip_file:
                                for pdf_path in pdf_files:
                                    zip_file.write(pdf_path, os.path.basename(pdf_path))

                            zip_buffer.seek(0)

                            # Ofrecer descarga
                            st.success(
                                f"🎉 ¡Se generaron {len(pdf_files)} etiquetas PDF!"
                            )
                            st.download_button(
                                label="📦 Descargar ZIP con todos los PDFs",
                                data=zip_buffer.getvalue(),
                                file_name=f"etiquetas_qr_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                                mime="application/zip",
                            )

                        progress_bar.empty()
                        status_text.empty()
        else:
            st.warning(
                "⚠️ No se encontraron entradas válidas. Por favor agrega datos arriba."
            )

        # Botón de datos de ejemplo
        if st.button("📄 Cargar Datos de Ejemplo"):
            sample_data = pd.DataFrame(
                {
                    "Localidad": ["LOC001", "LOC002", "LOC003", "LOC004", "LOC005"],
                    "Abr": [
                        "Casa",
                        "Oficina Principal",
                        "Almacén Norte",
                        "Sucursal Centro Comercial",
                        "Depósito",
                    ],
                    "Letra": ["A", "B", "C", "D", "E"],
                }
            )
            st.session_state.df_data = sample_data
            st.rerun()


if __name__ == "__main__":
    main()
