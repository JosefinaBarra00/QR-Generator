# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **QR Label Generator** built with Streamlit that creates customized QR code labels with colored backgrounds and formatted text. The application generates PDF labels that can be downloaded individually or as a batch ZIP file.

## Key Architecture

### Core Application (`app.py`)
- **Main UI**: Streamlit-based web interface with sidebar configuration and main content area
- **QR Generation**: Uses `qrcode` library with high error correction for label creation
- **Label Creation**: Generates images with custom dimensions, colored backgrounds, and formatted text overlays
- **Export System**: Creates individual PDF files and packages them in ZIP archives for download

### Color System
- **Predefined Colors**: 26 colors mapped to letters A-Z (`COLORES` dictionary in `app.py:15-42`)
- **Color Application**: Each label gets a background color based on the "Letra" field
- **Visual Preview**: Color swatches displayed in UI for user reference

### Text Formatting System
- **Auto Font Sizing**: Dynamic font size calculation based on text length and image dimensions (`calculate_optimal_font_size()` in `app.py:45-65`)
- **Multi-line Text**: Intelligent text wrapping for long abbreviations (`format_text_to_two_lines()` in `app.py:68-88`)
- **Text Positioning**: Centers text above QR code with proportional spacing

### Dimension System
- **Unit Conversion**: Supports mm, cm, m, and pixels with DPI-aware conversion (`app.py:99-124`)
- **Default Dimensions**: 6614 x 6850 pixels (approximately A4 size at 300 DPI)
- **Flexible Sizing**: User-configurable dimensions through sidebar controls

## Common Development Tasks

### Running the Application
```bash
streamlit run app.py
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Key Dependencies
- **streamlit**: Web UI framework
- **qrcode[pil]**: QR code generation with PIL support
- **Pillow**: Image processing and PDF creation
- **pandas**: Data handling for Excel files
- **openpyxl**: Excel file reading

## Data Flow

1. **Input**: Excel files with columns `Localidad` (QR data), `Abr` (display text), `Letra` (color code)
2. **Processing**: Generate QR codes, apply colors, format text, create images
3. **Output**: Individual PDF files packaged in ZIP archive

## File Structure

- `app.py`: Main application with all functionality
- `requirements.txt`: Python dependencies
- `Ubuntu-Bold.ttf`: Custom font file for text rendering

## Font Handling

The application tries to use a custom Ubuntu Bold font but falls back to system fonts if unavailable (`create_default_font()` in `app.py:91-96`). When working with fonts, ensure proper fallback mechanisms are in place.