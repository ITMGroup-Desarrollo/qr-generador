import flet as ft
import qrcode
import qrcode.image.svg
import io
import base64
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime
from pathlib import Path

# ── Configuración ──────────────────────────────────────────
OUTPUT_DIR = str(Path.home() / "Downloads")
os.makedirs(OUTPUT_DIR, exist_ok=True)

LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "imagenes", "logo-ITM-1024x473.png")

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.txt")
try:
    with open(CONFIG_PATH, "r") as f:
        TUNNEL_URL = f.read().strip()
except:
    TUNNEL_URL = "http://localhost:8081"

# ── Servidor de descarga ───────────────────────────────────
class DownloadHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=OUTPUT_DIR, **kwargs)
    def log_message(self, format, *args):
        pass

def start_file_server():
    server = HTTPServer(("0.0.0.0", 8081), DownloadHandler)
    server.serve_forever()

threading.Thread(target=start_file_server, daemon=True).start()

# ── Generador de QR ────────────────────────────────────────
def generate_qr(data, color, formato):
    fill = "white" if color == "blanco" else "black"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"qr_{timestamp}.{formato}"
    filepath = os.path.join(OUTPUT_DIR, filename)

    if formato == "svg":
        factory = qrcode.image.svg.SvgFillImage
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=20, border=4)
        qr.add_data(data)
        qr.make(fit=True)
        img_svg = qr.make_image(image_factory=factory)
        svg_bytes = img_svg.to_string()
        with open(filepath, "wb") as f:
            f.write(svg_bytes)
        # Para preview usamos PNG
        qr2 = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
        qr2.add_data(data)
        qr2.make(fit=True)
        img_png = qr2.make_image(fill_color="black", back_color="white").convert("RGBA")
        buffer = io.BytesIO()
        img_png.save(buffer, format="PNG")
        b64_preview = base64.b64encode(buffer.getvalue()).decode()
        data_url = f"data:image/png;base64,{b64_preview}"
        return data_url, filepath, filename, b64_preview, "image/svg+xml"

    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fill, back_color="transparent").convert("RGBA")

    if color == "blanco":
        new_data = [(0, 0, 0, 0) if item[0] < 50 else item for item in img.getdata()]
        img.putdata(new_data)

    img.save(filepath, "PNG")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    b64 = base64.b64encode(buffer.getvalue()).decode()
    data_url = f"data:image/png;base64,{b64}"
    return data_url, filepath, filename, b64, "image/png"

# ── App principal ──────────────────────────────────────────
def main(page: ft.Page):
    page.title = "Generador de QR"
    page.bgcolor = "#ffffff"
    page.padding = 0
    page.scroll = "auto"
    page.theme_mode = "light"

    # Logo
    try:
        with open(LOGO_PATH, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()
        logo = ft.Image(src=f"data:image/png;base64,{logo_b64}", width=200, height=80  , fit="contain")
    except:
        logo = ft.Text("ITM Group®", size=24, weight="bold", color="#1B2D6B")

    # Campos
    text_input = ft.TextField(
        hint_text="Escribe un texto o URL",
        expand=True,
        color="#1B2D6B",
        border_color="#1B2D6B",
        focused_border_color="#1B2D6B",
        hint_style=ft.TextStyle(color="#bbbbbb"),
        bgcolor="#f5f7ff",
        text_size=14,
        border_radius=8,
    )

    color_dd = ft.Dropdown(
        value="blanco",
        expand=True,
        color="#1B2D6B",
        bgcolor="white",
        border_color="#1B2D6B",
        border_radius=8,
        options=[
            ft.dropdown.Option("blanco", "⬜ Blanco"),
            ft.dropdown.Option("negro", "⬛ Negro"),
        ],
    )

    formato_dd = ft.Dropdown(
        value="png",
        expand=True,
        color="#1B2D6B",
        bgcolor="white",
        border_color="#1B2D6B",
        border_radius=8,
        options=[
            ft.dropdown.Option("png", "PNG"),
            ft.dropdown.Option("svg", "SVG"),
        ],
    )

    # Modal
    modal_img = ft.Image(src="https://placehold.co/240x240/1B2D6B/1B2D6B", width=240, height=240, fit="contain")
    modal_label = ft.Text("", color="#1B2D6B", size=13, text_align="center", max_lines=2)
    modal_file = ft.Text("", color="#aaaaaa", size=11, text_align="center")

    current_filepath = {"value": None}
    current_filename = {"value": None}

    def close_modal(e):
        modal.open = False
        page.update()

    def descargar(e):
        if current_filepath["value"] and current_filename["value"]:
            if page.platform in ("android", "ios"):
                # En móvil: descargar via servidor local
                import asyncio
                async def _launch():
                    launcher = ft.UrlLauncher()
                    page.overlay.append(launcher)
                    page.update()
                    await launcher.launch_url(f"http://10.11.94.178:8081/{current_filename['value']}")
                page.run_task(_launch)
            else:
                import subprocess
                subprocess.Popen(f'explorer /select,"{current_filepath["value"]}"')

    modal = ft.AlertDialog(
        modal=True,
        title=ft.Text("QR Generado ✅", color="#1B2D6B", text_align="center", weight="bold"),
        content=ft.Column([
            ft.Container(
                content=modal_img,
                bgcolor="#1B2D6B",
                border_radius=10,
                padding=10,
                alignment=ft.Alignment(0, 0),
            ),
            modal_label,
            modal_file,
        ], horizontal_alignment="center", spacing=8, tight=True),
        actions=[
            ft.TextButton("Cerrar", on_click=close_modal),
            ft.ElevatedButton(
                "⬇ Descargar",
                bgcolor="#1B2D6B",
                color="white",
                on_click=descargar,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
            ),
        ],
        actions_alignment="end",
    )
    page.overlay.append(modal)

    # Historial
    history = ft.GridView(
        runs_count=2,
        max_extent=175,
        spacing=12,
        run_spacing=12,
        expand=False,
    )

    def abrir_modal(data_url, filepath, filename, label):
        current_filename["value"] = filename
        current_filepath["value"] = filepath
        modal_img.src = data_url
        modal_label.value = label
        modal_file.value = f"📁 {filename}"
        modal.open = True
        page.update()

    def mostrar_snack(msg):
        page.snack_bar = ft.SnackBar(ft.Text(msg, color="white"), bgcolor="#1B2D6B")
        page.snack_bar.open = True
        page.update()

    btn_generar = ft.ElevatedButton(
        "Generar QR",
        bgcolor="#1B2D6B",
        color="white",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        width=float("inf"),
        height=50,
    )

    def on_generate(e):
        if not text_input.value or not text_input.value.strip():
            mostrar_snack("⚠ Ingresa un texto o URL primero")
            return

        btn_generar.text = "Generando..."
        btn_generar.disabled = True
        page.update()

        try:
            data_url, filepath, filename, b64, mime = generate_qr(
                text_input.value.strip(), color_dd.value, formato_dd.value
            )
            bg = "#1B2D6B" if color_dd.value == "blanco" else "#f5f7ff"
            label = text_input.value.strip()

            def _abrir(e, du=data_url, fp=filepath, fn=filename, lbl=label):
                abrir_modal(du, fp, fn, lbl)

            card = ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Image(src=data_url, width=110, height=110, fit="contain"),
                        bgcolor=bg,
                        border_radius=8,
                        padding=6,
                        alignment=ft.Alignment(0, 0),
                        width=135,
                        height=125,
                    ),
                    ft.Text(label, color="#1B2D6B", size=10, max_lines=1, width=135, text_align="center"),
                    ft.ElevatedButton(
                        "Ver",
                        bgcolor="#1B2D6B",
                        color="white",
                        on_click=_abrir,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
                        height=32,
                        width=135,
                    ),
                ], horizontal_alignment="center", spacing=5, tight=True),
                bgcolor="white",
                border_radius=12,
                padding=8,
                border=ft.Border(
                    left=ft.BorderSide(1, "#1B2D6B"),
                    right=ft.BorderSide(1, "#1B2D6B"),
                    top=ft.BorderSide(1, "#1B2D6B"),
                    bottom=ft.BorderSide(1, "#1B2D6B"),
                ),
            )

            history.controls.insert(0, card)
            abrir_modal(data_url, filepath, filename, label)
            mostrar_snack("✅ QR guardado en C:\\Users\\dpech\\Downloads")

        except Exception as ex:
            import traceback
            print(traceback.format_exc(), flush=True)
            mostrar_snack(f"❌ Error: {ex}")
        finally:
            btn_generar.text = "Generar QR"
            btn_generar.disabled = False
            page.update()

    btn_generar.on_click = on_generate

    page.add(
        ft.Container(
            content=ft.Column([
                logo,
                ft.Text("Generador de QR", size=13, color="#1B2D6B", text_align="center"),
            ], horizontal_alignment="center", spacing=6),
            padding=ft.Padding(left=0, right=0, top=24, bottom=24),
            alignment=ft.Alignment(0, 0),
            width=float("inf"),
            border=ft.Border(bottom=ft.BorderSide(1, "#e0e0e0")),
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("Texto o URL", color="#1B2D6B", size=12, weight="bold"),
                ft.Row([text_input], expand=True),
                ft.Row([
                    ft.Column([ft.Text("Color", color="#1B2D6B", size=12, weight="bold"), color_dd], spacing=4, expand=True),
                    ft.Column([ft.Text("Formato", color="#1B2D6B", size=12, weight="bold"), formato_dd], spacing=4, expand=True),
                ], spacing=12),
                btn_generar,
                ft.Divider(color="#e0e0e0", height=20),
                ft.Text("Historial", size=16, weight="bold", color="#1B2D6B", text_align="center", width=float("inf")),
                history,
            ], spacing=12),
            padding=ft.Padding(left=16, right=16, top=20, bottom=20),
        ),
    )


ft.app(main, view=ft.AppView.WEB_BROWSER, port=8550)