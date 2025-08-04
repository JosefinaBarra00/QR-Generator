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

# Definición de colores EXACTA del código base actualizado
# Del codigo_base.py línea 21
COLORES = {
    "Z": (135, 135, 135),  # Gris  
    "A": (213, 43, 30),    # Rojo
    "B": (0, 133, 66),     # Verde
    "C": (0, 101, 189),    # Azul
    "D": (240, 171, 0),    # Amarillo
    "F": (215, 31, 133),   # Rosa
    "G": (117, 48, 119),   # Púrpura
    "H": (255, 88, 0),     # Naranja
    "I": (249, 227, 0),    # Amarillo claro
    "J": (0, 0, 0),        # Negro
    "P": (0, 38, 100),     # Azul marino
    "Q": (104, 69, 13),    # Marrón
    "M": (198, 191, 110),  # Beige
    "L": (78, 84, 87),     # Gris oscuro
    "N": (178, 175, 175),  # Gris claro
    "S": (0, 161, 222),    # Celeste
    "T": (127, 127, 126),  # Gris
    "R": (56, 142, 60),    # Verde oscuro
    "R1": (56, 142, 60),   # Verde oscuro
    "R2": (56, 142, 60),   # Verde oscuro
    "R3": (56, 142, 60),   # Verde oscuro
    "R4": (56, 142, 60),   # Verde oscuro
    "V": (255, 234, 200),  # Crema
}

# Color por defecto para letras no definidas
COLOR_DEFAULT = (128, 128, 128)  # Gris medio

def get_color_for_letter(letra):
    """Obtener color para una letra, incluyendo soporte para colores personalizados"""
    letra = letra.upper()
    
    # Verificar colores personalizados primero
    if hasattr(st, 'session_state') and 'custom_colors' in st.session_state:
        if letra in st.session_state.custom_colors:
            return st.session_state.custom_colors[letra]
    
    # Luego verificar colores predefinidos
    return COLORES.get(letra, COLOR_DEFAULT)






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

def generate_qr_label(localidad, abr, letra, dimensions=(6614, 6850)):
    """Generar una etiqueta QR EXACTAMENTE igual al código base actualizado"""
    
    # Convertir letra y abr a string como en el código original
    letra = str(letra)
    abr = str(abr)
    
    # Formatear el texto a máximo 2 líneas si tiene espacios
    if " " in abr:
        abr = format_text_to_two_lines(abr)
    
    # Obtener color exacto del código base (con fallback para colores personalizados)
    color = get_color_for_letter(letra)
    
    # Crear imagen con dimensiones exactas del código actualizado
    img = Image.new('RGB', dimensions, color=color)
    
    # Crear fuentes según el código actualizado
    fnt = create_font(1500)   # Fuente principal
    fnt2 = create_font(1250)  # Para R
    fnt3 = create_font(1000)  # Para R1
    fnt4 = create_font(850)   # Para R2
    fnt5 = create_font(650)   # Para R3
    fnt6 = create_font(450)   # Para R4
    
    d = ImageDraw.Draw(img)
    
    # Determinar fuente y posición Y según la letra
    if letra == 'R':
        fnt = fnt2
        y = 500
    elif letra == 'R1':
        fnt = fnt3
        y = 500
    elif letra == 'R2':
        fnt = fnt4
        y = 500
    elif letra == 'R3':
        fnt = fnt5
        y = 500
    elif letra == 'R4':
        fnt = fnt6
        y = 500
    elif abr.startswith('RETPLA'):
        fnt = fnt
        y = 100  # Aumentar margen superior para textos que comienzan con RETPLA
    else:
        fnt = fnt
        y = 10
    
    lines = abr.splitlines()
    
    # Calcular dimensiones del texto
    try:
        # Nuevo método para medir el ancho del texto más largo
        w1 = d.textbbox((0, 0), max(lines, key=len), font=fnt)[2]
    except AttributeError:
        # Método alternativo para versiones antiguas
        w1 = fnt.getsize(max(lines, key=len))[0]
    
    try:
        # Nuevo método para calcular la altura total del texto
        line_height = d.textbbox((0, 0), "A", font=fnt)[3]
        total_height = line_height * len(lines)
    except AttributeError:
        # Método alternativo para versiones antiguas
        line_height = fnt.getsize("A")[1]
        total_height = line_height * len(lines)
    
    # Dibujar cada línea individualmente
    y_start = y
    
    for i, line in enumerate(lines):
        try:
            line_width = d.textbbox((0, 0), line, font=fnt)[2]
        except AttributeError:
            line_width = fnt.getsize(line)[0]
        
        # Centrar horizontalmente cada línea
        x_pos = (img.size[0] - line_width) // 2
        y_pos = y_start + i * line_height
        
        d.text((x_pos, y_pos), line, font=fnt, fill=(255, 255, 255))
    
    # Generar código QR con configuración actualizada
    qr_big = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H, 
        box_size=180, 
        border=1
    )
    qr_big.add_data(localidad)
    qr_big.make(fit=True)
    img_qr_big = qr_big.make_image().convert('RGB')
    
    # Posicionar el código QR
    pos2 = ((img.size[0] - img_qr_big.size[0]) // 2, (img.size[1] - img_qr_big.size[1]) // 2 + 600)
    img.paste(img_qr_big, pos2)
    
    return img


def create_color_preview(color_rgb):
    """Crear una vista previa del color en formato HTML"""
    color_hex = f"#{color_rgb[0]:02x}{color_rgb[1]:02x}{color_rgb[2]:02x}"
    return f'<div style="display: inline-block; width: 20px; height: 20px; background-color: {color_hex}; border: 1px solid #ccc; border-radius: 3px; margin-right: 8px; vertical-align: middle;"></div>'


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
        is_custom = (hasattr(st, 'session_state') and 
                    'custom_colors' in st.session_state and 
                    letter.upper() in st.session_state.custom_colors)
        
        suffix = " ✨" if is_custom else ""
        
        return f'<div style="background-color: {color_hex}; color: {text_color}; padding: 5px; text-align: center; border-radius: 3px; font-weight: bold;">{letter}{suffix}</div>'
    
    return f'<div style="background-color: #808080; color: white; padding: 5px; text-align: center; border-radius: 3px; font-weight: bold;">{letter}</div>'


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
        
        **Paso 3:** 📥 Genera y descarga tus etiquetas QR
        
        ---
        
        ### 📊 Formato del archivo Excel
        Tu archivo debe tener exactamente estas columnas:
        - **Localidad**: Datos para el código QR (ej: A02-01-01-01)
        - **Abr**: Texto que aparecerá en la etiqueta (ej: A02-01)
        - **Letra**: Código de color (A-Z, ver colores abajo)
        
        🎯 **Formato Actualizado**: Esta app genera etiquetas grandes (6614x6850 px) con múltiples tamaños de fuente
        """
        )

        st.divider()

        # Configuración simple - solo formato original
        st.header("📏 Configuración de Etiquetas")
        
        pixel_width, pixel_height = 6614, 6850
        dpi = 600  # DPI del código original
        
        st.success(f"✅ Formato actualizado: {pixel_width} x {pixel_height} px (DPI: {dpi})")
        st.info("📝 Formato exacto del código base actualizado con etiquetas grandes")

        st.divider()

        # Sección de colores mejorada
        st.header("🎨 Configuración de Colores")
        
        # Opción para colores personalizados
        with st.expander("⚙️ Agregar Color Personalizado", expanded=False):
            st.markdown("Define un color para una letra que no esté en la lista:")
            
            col_custom1, col_custom2 = st.columns(2)
            with col_custom1:
                custom_letter = st.text_input(
                    "Letra:", 
                    max_chars=1, 
                    placeholder="Ej: Ñ",
                    help="Ingresa una sola letra"
                ).upper()
            
            with col_custom2:
                custom_color = st.color_picker(
                    "Color:", 
                    value="#808080",
                    help="Selecciona el color de fondo"
                )
            
            if custom_letter and st.button("➕ Agregar Color Personalizado"):
                # Convertir color hex a RGB
                hex_color = custom_color.lstrip('#')
                rgb_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                
                # Agregar al diccionario de colores en sesión
                if 'custom_colors' not in st.session_state:
                    st.session_state.custom_colors = {}
                
                st.session_state.custom_colors[custom_letter] = rgb_color
                st.success(f"✅ Color agregado para la letra '{custom_letter}'")
                st.rerun()
        
        # Mostrar colores personalizados si existen
        if 'custom_colors' in st.session_state and st.session_state.custom_colors:
            st.subheader("🔧 Colores Personalizados")
            custom_colors_per_row = 4
            custom_items = list(st.session_state.custom_colors.items())
            
            for i in range(0, len(custom_items), custom_colors_per_row):
                custom_cols = st.columns(custom_colors_per_row)
                for j, (letter, color) in enumerate(custom_items[i : i + custom_colors_per_row]):
                    if j < len(custom_cols):
                        with custom_cols[j]:
                            color_preview = create_color_preview(color)
                            st.markdown(
                                f"{color_preview}{letter} ✨", unsafe_allow_html=True
                            )
        
        st.subheader("🎨 Colores Predefinidos")
        st.markdown("*Colores del código base original*")

        # Crear grid de colores ordenado alfabéticamente (4 columnas para mejor uso del espacio)
        colors_per_row = 4
        # Los colores ya están ordenados alfabéticamente en el diccionario
        color_items = list(COLORES.items())

        for i in range(0, len(color_items), colors_per_row):
            cols = st.columns(colors_per_row)
            for j, (letter, color) in enumerate(color_items[i : i + colors_per_row]):
                if j < len(cols):
                    with cols[j]:
                        color_preview = create_color_preview(color)
                        st.markdown(
                            f"{color_preview}{letter}", unsafe_allow_html=True
                        )
                        
        # Mostrar color por defecto
        st.info("📝 **Nota**: Las letras no definidas usarán color gris por defecto")
        default_preview = create_color_preview(COLOR_DEFAULT)
        st.markdown(f"{default_preview}Color por defecto para letras no definidas", unsafe_allow_html=True)

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
                "Letra": st.column_config.TextColumn(
                    "🎨 Letra (Color)",
                    help="La letra que determina el color de fondo (A-Z o personalizada)",
                    max_chars=1,
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
                            f"📐 Dimensiones: {pixel_width} x {pixel_height} px (Formato Grande)"
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

            # Opciones de generación mejoradas
            col_gen1, col_gen2 = st.columns(2)
            
            with col_gen1:
                if st.button("🚀 Generar Todas las Etiquetas", type="primary"):
                    if len(df_clean) > 0:
                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        # Crear directorio temporal para PDFs
                        with tempfile.TemporaryDirectory() as temp_dir:
                            pdf_files = []
                            success_count = 0

                            for idx, row in df_clean.iterrows():
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
                                    )

                                    # Generar nombre de archivo limpio
                                    safe_filename = str(row['Localidad']).replace('/', '-').replace('\\', '-')
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
                                    f"🎉 ¡{success_count} etiquetas generadas exitosamente!"
                                )
                                
                                # Botón de descarga prominente
                                st.download_button(
                                    label=f"📦 Descargar {success_count} Etiquetas (ZIP)",
                                    data=zip_buffer.getvalue(),
                                    file_name=f"etiquetas_qr_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                                    mime="application/zip",
                                    use_container_width=True
                                )
                            else:
                                st.error("❌ No se pudo generar ninguna etiqueta")

                            progress_bar.empty()
                            status_text.empty()
                            
            with col_gen2:
                # Generar etiqueta individual de muestra
                if st.button("🔍 Generar Etiqueta de Muestra"):
                    if len(df_clean) > 0:
                        try:
                            # Generar primera etiqueta como muestra
                            sample_img = generate_qr_label(
                                df_clean.iloc[0]["Localidad"],
                                df_clean.iloc[0]["Abr"],
                                df_clean.iloc[0]["Letra"],
                                (pixel_width, pixel_height),
                            )
                            
                            # Convertir a PDF en memoria
                            pdf_buffer = io.BytesIO()
                            sample_img.save(pdf_buffer, "PDF", resolution=float(dpi))
                            pdf_buffer.seek(0)
                            
                            st.download_button(
                                label=f"📥 Descargar Muestra: {df_clean.iloc[0]['Abr']}",
                                data=pdf_buffer.getvalue(),
                                file_name=f"muestra_{df_clean.iloc[0]['Localidad']}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                            
                        except Exception as e:
                            st.error(f"❌ Error generando muestra: {str(e)}")
        else:
            st.warning(
                "⚠️ No se encontraron entradas válidas. Por favor agrega datos arriba."
            )

        # Botón de datos de ejemplo mejorado
        st.divider()
        
        col_example1, col_example2 = st.columns(2)
        
        with col_example1:
            if st.button("📄 Cargar Datos de Ejemplo", use_container_width=True):
                # Agregar algunos colores personalizados de ejemplo
                if 'custom_colors' not in st.session_state:
                    st.session_state.custom_colors = {}
                
                # Agregar algunos colores personalizados de ejemplo
                st.session_state.custom_colors["Ñ"] = (255, 0, 255)  # Magenta
                st.session_state.custom_colors["@"] = (0, 255, 127)   # Verde brillante
                
                sample_data = pd.DataFrame(
                    {
                        "Localidad": ["A02-01-01-01", "B03-02-01-02", "C04-03-02-01", "R05-04-01-03", "R1-06-02-04", "R2-07-03-05"],
                        "Abr": [
                            "A02-01",
                            "B03-02",
                            "Almacén Central",
                            "Deposito Sur",
                            "Oficina Principal Norte",
                            "Zona de Carga",
                        ],
                        "Letra": ["A", "B", "C", "R", "R1", "R2"],  # Incluye letras R especiales
                    }
                )
                st.session_state.df_data = sample_data
                st.success("✅ Datos cargados con ejemplos de texto largo, colores personalizados y letras no definidas")
                st.rerun()
                
        with col_example2:
            if st.button("🔄 Limpiar Todo", use_container_width=True):
                st.session_state.df_data = pd.DataFrame(
                    {"Localidad": [""], "Abr": [""], "Letra": ["A"]}
                )
                # Limpiar colores personalizados también
                if 'custom_colors' in st.session_state:
                    st.session_state.custom_colors = {}
                st.success("🔄 Datos y colores personalizados limpiados")
                st.rerun()


if __name__ == "__main__":
    main()
