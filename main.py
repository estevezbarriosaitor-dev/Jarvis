import json
import os
import threading
import time
import subprocess
import sys
import requests
import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

if getattr(sys, 'frozen', False):
    # Si el programa está congelado (compilado con PyInstaller)
    # usamos la carpeta donde se encuentra el archivo .exe
    BASE_PATH = os.path.dirname(sys.executable)
else:
    # Si se ejecuta como script normal .py
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

JSON_PATH = os.path.join(BASE_PATH, 'games.json')

def get_resource_path(relative_path):
    """Obtiene la ruta del recurso, compatible con PyInstaller (carpeta temporal) y desarrollo."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

ICON_PATH = get_resource_path("logo.ico")

# Constante para 165 FPS (1/165 ≈ 0.00606 segundos)
FRAME_DELAY = 1/165

class GameManager(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Gestor de Juegos")
        
        self.overrideredirect(True)
        self.attributes("-alpha", 0.90)
        self.transparent_color = "#000001"
        self.configure(fg_color=self.transparent_color)
        self.wm_attributes("-transparentcolor", self.transparent_color)
        self.attributes('-topmost', 'true')
        
        # Establecer icono si existe
        if os.path.exists(ICON_PATH):
            try:
                self.iconbitmap(ICON_PATH)
            except:
                pass

        self.target_w = 400
        self.target_h = 600
        self.target_x = self.parent.winfo_x() + self.parent.winfo_width() + 10
        self.target_y = self.parent.winfo_y()
        self.geometry(f"10x{self.target_h}+{self.target_x}+{self.target_y}")

        # Fondo con bordes redondeados
        self.bg_frame = ctk.CTkFrame(self, fg_color="#0a0a0a", corner_radius=20, border_width=2, border_color="#FFFFFF")
        self.bg_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Barra superior con botón de cerrar
        self.top_bar = ctk.CTkFrame(self.bg_frame, fg_color="transparent")
        self.top_bar.pack(fill="x", padx=10, pady=10)
        
        self.close_btn = ctk.CTkButton(self.top_bar, text="✖", width=40, height=40, command=self.close_with_animation, fg_color="transparent", text_color="#FFFFFF", hover_color="#333333", border_width=1, border_color="#FFFFFF")
        self.close_btn.pack(side="left")

        self.title_label = ctk.CTkLabel(self.bg_frame, text="Administrar Biblioteca", font=ctk.CTkFont("Consolas", 20, "bold"), text_color="#FFFFFF")
        self.title_label.pack(pady=5)

        self.scroll_frame = ctk.CTkScrollableFrame(self.bg_frame, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.add_btn = ctk.CTkButton(self.bg_frame, text="+ Añadir Juego Manualmente", fg_color="#FFFFFF", text_color="#000000", hover_color="#CCCCCC", command=self.add_game_dialog)
        self.add_btn.pack(pady=20)

        self.refresh_list()
        
        # Ocultar widgets temporalmente para la animación
        self.scroll_frame.pack_forget()
        self.add_btn.pack_forget()
        self.title_label.pack_forget()
        self.top_bar.pack_forget()
        
        self.after(50, self.animate_slide_in)

    def animate_slide_in(self):
        def anim():
            steps = 30  # Más pasos para 165 FPS
            for i in range(1, steps + 1):
                w = int(self.target_w * (i/steps))
                if w < 10: w = 10
                self.geometry(f"{w}x{self.target_h}+{self.target_x}+{self.target_y}")
                self.update()
                time.sleep(FRAME_DELAY)
            
            # Restaurar widgets
            self.top_bar.pack(fill="x", padx=10, pady=10)
            self.title_label.pack(pady=5)
            self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
            self.add_btn.pack(pady=20)
            
        threading.Thread(target=anim, daemon=True).start()

    def close_with_animation(self):
        """Cierra la ventana con una animación de minimizado fluida a 165 FPS"""
        # Ocultar todos los widgets inmediatamente
        self.top_bar.pack_forget()
        self.title_label.pack_forget()
        self.scroll_frame.pack_forget()
        self.add_btn.pack_forget()
        
        def animate_close():
            steps = 45  # Más pasos para una animación más fluida a 165 FPS
            current_w = self.winfo_width()
            current_h = self.winfo_height()
            current_x = self.winfo_x()
            current_y = self.winfo_y()
            
            # Animación de minimizado
            for i in range(1, steps + 1):
                # Usar ease-out para una animación más natural
                t = i / steps
                # Función ease-out: empieza rápido y termina lento
                ease_t = 1 - (1 - t) ** 2
                
                w = int(current_w * (1 - ease_t))
                h = int(current_h * (1 - ease_t))
                if w < 2: w = 2
                if h < 2: h = 2
                x = current_x + (current_w - w) // 2
                y = current_y + (current_h - h) // 2
                self.geometry(f"{w}x{h}+{x}+{y}")
                self.update()
                time.sleep(FRAME_DELAY)
            
            # Mostrar mensaje final
            if len(self.parent.games_data) == 0:
                self.parent.type_text("[JARVIS] Aún no tienes juegos. Añade algunos para que pueda ayudarte.")
            else:
                self.parent.type_text("[JARVIS] Sistemas actualizados.\n¿A qué jugamos hoy?")
            
            self.destroy()
        
        threading.Thread(target=animate_close, daemon=True).start()

    def refresh_list(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        sorted_games = sorted(self.parent.games_data, key=lambda x: x['name'].lower())
        for game in sorted_games:
            frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
            frame.pack(fill="x", pady=2)
            
            name_label = ctk.CTkLabel(frame, text=game['name'], font=ctk.CTkFont("Consolas", 14), text_color="#FFFFFF")
            name_label.pack(side="left", padx=5)

            del_btn = ctk.CTkButton(frame, text="Borrar", width=50, fg_color="#7a2b2b", hover_color="#541e1e", text_color="#FFFFFF",
                                    command=lambda g=game: self.delete_game(g))
            del_btn.pack(side="right")

    def delete_game(self, game):
        if game in self.parent.games_data:
            self.parent.games_data.remove(game)
        self.parent.save_games_data()
        self.refresh_list()

    def add_game_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Añadir Juego")
        dialog.geometry("300x250")
        dialog.attributes('-topmost', 'true')
        
        ctk.CTkLabel(dialog, text="Nombre del Juego:").pack(pady=(20,0))
        name_entry = ctk.CTkEntry(dialog)
        name_entry.pack()

        ctk.CTkLabel(dialog, text="Ruta completa al .exe o acceso directo:").pack(pady=(20,0))
        path_entry = ctk.CTkEntry(dialog)
        path_entry.pack()

        def save_new():
            n = name_entry.get().strip()
            p = path_entry.get().strip()
            if n and p:
                self.parent.games_data.append({"name": n, "path": p})
                self.parent.save_games_data()
                self.refresh_list()
                dialog.destroy()

        save_btn = ctk.CTkButton(dialog, text="Guardar", command=save_new, fg_color="#FFFFFF", text_color="#000000", hover_color="#CCCCCC")
        save_btn.pack(pady=20)

TRANSLATIONS = {
    "Español": {
        "welcome": "[JARVIS] Sistemas Iniciados.\n¿Has añadido o borrado algo en el escritorio?",
        "scanning": "[JARVIS] Analizando...",
        "ready": "[JARVIS] Todo listo. ¿Qué te apetece hacer hoy?",
        "empty": "[JARVIS] Tu biblioteca está vacía.\nAñade tus juegos en el Gestor (🎮).",
        "back_center": "⤴ Volver al Centro",
        "close": "✖ Cerrar",
        "send": "Enviar",
        "placeholder": "Escribe aquí...",
        "yes": "SÍ",
        "no": "NO",
        "pinned": "[JARVIS] Modo anclado activado. Siempre estaré visible.",
        "unpinned": "[JARVIS] Modo anclado desactivado.",
        "companion_active": "[JARVIS] Acompañante activo.",
        "back_to_center": "[JARVIS] De vuelta al centro.\n¿Qué más necesitas?",
        "amnesia": "[JARVIS] Protocolo de amnesia ejecutado. He olvidado nuestra conversación actual.",
        "lang_upd": "Idioma actualizado a",
        "searching": "Consultando sistemas...",
        "closing_game": "He enviado la señal de cierre a",
        "no_game_open": "No he abierto ningún juego recientemente.",
        "add_games_first": "Primero añade juegos en el Gestor (🎮).",
        "here_is_all": "Aquí tienes todo. Elige uno:",
        "opening": "Abriendo",
        "matches_found": "Encontré varias coincidencias:",
        "not_found": "No encontré eso. Quizás quieras alguno de estos:"
    },
    "English": {
        "welcome": "[JARVIS] Systems Initialized.\nHave you added or deleted anything on the desktop?",
        "scanning": "[JARVIS] Analyzing...",
        "ready": "[JARVIS] All ready. What do you feel like doing today?",
        "empty": "[JARVIS] Your library is empty.\nAdd your games in the Manager (🎮).",
        "back_center": "⤴ Back to Center",
        "close": "✖ Close",
        "send": "Send",
        "placeholder": "Type here...",
        "yes": "YES",
        "no": "NO",
        "pinned": "[JARVIS] Pinned mode activated. I will always be visible.",
        "unpinned": "[JARVIS] Pinned mode deactivated.",
        "companion_active": "[JARVIS] Companion active.",
        "back_to_center": "[JARVIS] Back to center.\nWhat else do you need?",
        "amnesia": "[JARVIS] Amnesia protocol executed. I have forgotten our current conversation.",
        "lang_upd": "Language updated to",
        "searching": "Consulting systems...",
        "closing_game": "I have sent the close signal to",
        "no_game_open": "I haven't opened any games recently.",
        "add_games_first": "First add games in the Manager (🎮).",
        "here_is_all": "Here is everything. Choose one:",
        "opening": "Opening",
        "matches_found": "I found several matches:",
        "not_found": "I didn't find that. Maybe you want one of these:"
    },
    "Русский": {
        "welcome": "[JARVIS] Системы инициализированы.\nВы что-то добавили или удалили на рабочем столе?",
        "scanning": "[JARVIS] Анализ...",
        "ready": "[JARVIS] Все готово. Что вы хотите сделать сегодня?",
        "empty": "[JARVIS] Ваша библиотека пуста.\nДобавьте игры в Менеджере (🎮).",
        "back_center": "⤴ Вернуться в центр",
        "close": "✖ Закрыть",
        "send": "Отправить",
        "placeholder": "Пишите здесь...",
        "yes": "ДА",
        "no": "НЕТ",
        "pinned": "[JARVIS] Закрепленный режим включен. Я всегда буду на виду.",
        "unpinned": "[JARVIS] Закрепленный режим выключен.",
        "companion_active": "[JARVIS] Компаньон активен.",
        "back_to_center": "[JARVIS] Снова в центре.\nЧто еще вам нужно?",
        "amnesia": "[JARVIS] Протокол амнезии выполнен. Я забыл наш текущий разговор.",
        "lang_upd": "Язык обновлен на",
        "searching": "Опрос систем...",
        "closing_game": "Я отправил сигнал закрытия для",
        "no_game_open": "Я не открывал никаких игр в последнее время.",
        "add_games_first": "Сначала добавьте игры в Менеджере (🎮).",
        "here_is_all": "Вот и все. Выберите одну:",
        "opening": "Открытие",
        "matches_found": "Я нашел несколько совпадений:",
        "not_found": "Я этого не нашел. Может быть, вы хотите что-то из этого:"
    },
    "Deutsch": {
        "welcome": "[JARVIS] Systeme initialisiert.\nHaben Sie etwas auf dem Desktop hinzugefügt oder gelöscht?",
        "scanning": "[JARVIS] Analysiere...",
        "ready": "[JARVIS] Alles bereit. Was möchten Sie heute tun?",
        "empty": "[JARVIS] Deine Bibliothek ist leer.\nFüge deine Spiele im Manager hinzu (🎮).",
        "back_center": "⤴ Zurück zur Mitte",
        "close": "✖ Schließen",
        "send": "Senden",
        "placeholder": "Hier schreiben...",
        "yes": "JA",
        "no": "NEIN",
        "pinned": "[JARVIS] Pin-Modus aktiviert. Ich werde immer sichtbar sein.",
        "unpinned": "[JARVIS] Pin-Modus deaktiviert.",
        "companion_active": "[JARVIS] Begleiter aktiv.",
        "back_to_center": "[JARVIS] Zurück in der Mitte.\nWas brauchst du noch?",
        "amnesia": "[JARVIS] Amnesie-Protokoll ausgeführt. Ich habe unser aktuelles Gespräch vergessen.",
        "lang_upd": "Sprache aktualisiert auf",
        "searching": "Systeme abfragen...",
        "closing_game": "Ich habe das Schließsignal gesendet an",
        "no_game_open": "Ich habe in letzter Zeit keine Spiele geöffnet.",
        "add_games_first": "Füge zuerst Spiele im Manager hinzu (🎮).",
        "here_is_all": "Hier ist alles. Wähle eines aus:",
        "opening": "Öffne",
        "matches_found": "Ich habe mehrere Treffer gefunden:",
        "not_found": "Ich habe das nicht gefunden. Vielleicht möchtest du eines davon:"
    },
    "Português": {
        "welcome": "[JARVIS] Sistemas Inicializados.\nAdicionou ou eliminou algo no ambiente de trabalho?",
        "scanning": "[JARVIS] A analisar...",
        "ready": "[JARVIS] Tudo pronto. O que lhe apetece fazer hoje?",
        "empty": "[JARVIS] A sua biblioteca está vazia.\nAdicione os seus jogos no Gestor (🎮).",
        "back_center": "⤴ Voltar ao Centro",
        "close": "✖ Fechar",
        "send": "Enviar",
        "placeholder": "Escreva aqui...",
        "yes": "SIM",
        "no": "NÃO",
        "pinned": "[JARVIS] Modo fixado ativado. Estarei sempre visível.",
        "unpinned": "[JARVIS] Modo fixado desativado.",
        "companion_active": "[JARVIS] Companheiro ativo.",
        "back_to_center": "[JARVIS] De volta ao centro.\nO que mais precisa?",
        "amnesia": "[JARVIS] Protocolo de amnésia executado. Esqueci a nossa conversa atual.",
        "lang_upd": "Idioma atualizado para",
        "searching": "A consultar sistemas...",
        "closing_game": "Enviei o sinal de fecho para",
        "no_game_open": "Não abri nenhum jogo recentemente.",
        "add_games_first": "Primeiro adicione jogos no Gestor (🎮).",
        "here_is_all": "Aqui está tudo. Escolha um:",
        "opening": "A abrir",
        "matches_found": "Encontrei várias correspondências:",
        "not_found": "Não encontrei isso. Talvez queira algum destes:"
    }
}

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Configuración")
        self.overrideredirect(True)
        self.attributes("-alpha", 0.95)
        self.transparent_color = "#000001"
        self.configure(fg_color=self.transparent_color)
        self.wm_attributes("-transparentcolor", self.transparent_color)
        self.attributes('-topmost', 'true')

        # Centrar relativo al padre
        w, h = 350, 400
        x = parent.winfo_x() + (parent.winfo_width() - w) // 2
        y = parent.winfo_y() + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.bg_frame = ctk.CTkFrame(self, fg_color="#0a0a0a", corner_radius=20, border_width=2, border_color="#FFFFFF")
        self.bg_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.title_label = ctk.CTkLabel(self.bg_frame, text="Panel de Control", font=ctk.CTkFont("Consolas", 20, "bold"), text_color="#FFFFFF")
        self.title_label.pack(pady=30)

        ctk.CTkLabel(self.bg_frame, text="Idioma de la Inteligencia:", font=ctk.CTkFont("Consolas", 14), text_color="#FFFFFF").pack(pady=(10, 5))
        
        self.languages = ["Español", "English", "Русский", "Deutsch", "中文", "日本語", "한국어", "Português", "Français", "Italiano"]
        self.lang_menu = ctk.CTkOptionMenu(
            self.bg_frame, 
            values=self.languages, 
            command=self.change_language,
            fg_color="#1a1a1a",
            button_color="#FFFFFF",
            button_hover_color="#CCCCCC",
            text_color="#FFFFFF",
            dropdown_fg_color="#1a1a1a",
            font=ctk.CTkFont("Consolas", 14)
        )
        self.lang_menu.set(self.parent.current_language)
        self.lang_menu.pack(pady=10)

        self.close_btn = ctk.CTkButton(self.bg_frame, text="Cerrar", command=self.destroy, fg_color="#FFFFFF", text_color="#000000", hover_color="#CCCCCC", font=ctk.CTkFont("Consolas", 14, "bold"))
        self.close_btn.pack(pady=50)

    def change_language(self, new_lang):
        self.parent.current_language = new_lang
        self.parent.chat_history = [] # Limpiar historia para evitar "fugas" de idioma
        self.parent.refresh_ui_text()
        self.parent.type_text(f"[JARVIS] {self.parent.get_text('lang_upd')} {new_lang}.")


class AIGameAssistant(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Jarvis Game Assistant")
        self.overrideredirect(True)
        self.attributes("-alpha", 0.90)
        self.transparent_color = "#000001"
        self.configure(fg_color=self.transparent_color)
        self.wm_attributes("-transparentcolor", self.transparent_color)
        self.attributes('-topmost', 'true')

        # Establecer icono si existe (con un pequeño delay para ctk)
        if os.path.exists(ICON_PATH):
            try:
                self.after(200, lambda: self.iconbitmap(ICON_PATH))
            except:
                pass

        self.screen_w = self.winfo_screenwidth()
        self.screen_h = self.winfo_screenheight()
        self.geometry(f"10x10+{self.screen_w//2}+{self.screen_h//2}")

        self.games_data = self.load_games_data()
        self.last_launched_game = None
        self.mode = "normal"
        self.monitoring = False
        self.is_pinned = False
        self.ollama_model = "gemma4:e4b" # Modelo detectado en el sistema
        self.chat_history = [] # Memoria de conversación
        self.manager_window = None # Referencia a la ventana del gestor
        self.settings_window = None # Referencia a la ventana de ajustes
        self.current_language = "Español"

        self.main_font = ctk.CTkFont(family="Consolas", size=20)
        self.title_font = ctk.CTkFont(family="Consolas", size=26, weight="bold")

        # Frame de fondo con bordes redondeados y contorno blanco
        self.bg_frame = ctk.CTkFrame(self, fg_color="#0a0a0a", corner_radius=20, border_width=2, border_color="#FFFFFF")
        self.bg_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Top frame con botones superiores
        self.top_frame = ctk.CTkFrame(self.bg_frame, fg_color="transparent")
        self.top_frame.pack(fill="x", padx=20, pady=10)
        
        self.close_btn = ctk.CTkButton(self.top_frame, text="✖ Cerrar", width=100, height=40, command=self.close_with_animation, fg_color="transparent", text_color="#FFFFFF", hover_color="#333333", border_width=1, border_color="#FFFFFF")
        self.close_btn.pack(side="left")

        self.manage_btn = ctk.CTkButton(self.top_frame, text="🎮", width=40, height=40, command=self.open_manager, fg_color="transparent", text_color="#FFFFFF", hover_color="#333333", border_width=1, border_color="#FFFFFF", state="disabled")
        self.manage_btn.pack(side="right")
        
        self.settings_btn = ctk.CTkButton(self.top_frame, text="⚙️", width=40, height=40, command=self.open_settings, fg_color="transparent", text_color="#FFFFFF", hover_color="#333333", border_width=1, border_color="#FFFFFF", state="disabled")
        self.settings_btn.pack(side="right", padx=10)
        
        self.pin_btn = ctk.CTkButton(self.top_frame, text="📌", width=40, height=40, command=self.toggle_pin, fg_color="transparent", text_color="#FFFFFF", hover_color="#333333", border_width=1, border_color="#FFFFFF", state="disabled")
        self.pin_btn.pack(side="right")

        # Botón Volver al Centro (debajo del gestor) - inicialmente oculto
        self.center_return_btn = ctk.CTkButton(self.bg_frame, text="⤴ Volver al Centro", width=200, height=40, command=self.return_to_center, fg_color="#333333", text_color="#FFFFFF", hover_color="#555555", border_width=1, border_color="#FFFFFF", state="disabled")

        # Caja de texto para mensajes de Jarvis (reemplaza a ai_label y msg_frame)
        self.ai_textbox = ctk.CTkTextbox(
            self.bg_frame, 
            fg_color="transparent",
            text_color="#FFFFFF",
            font=self.title_font,
            wrap="word",
            border_width=0,
            activate_scrollbars=True
        )
        self.ai_textbox.pack(pady=20, padx=40, fill="both", expand=True)
        self.ai_textbox.configure(state="disabled")

        # Frame central botones
        self.dynamic_frame = ctk.CTkFrame(self.bg_frame, fg_color="transparent")
        self.dynamic_frame.pack(pady=10, padx=20, fill="both", expand=True)

        # Bottom frame input
        self.input_frame = ctk.CTkFrame(self.bg_frame, fg_color="transparent")
        self.input_frame.pack(pady=30, padx=20, fill="x", side="bottom")

        self.user_input = ctk.CTkEntry(self.input_frame, placeholder_text="Escribe aquí...", font=self.main_font, height=60, text_color="#FFFFFF", placeholder_text_color="#888888", fg_color="#111111", border_color="#FFFFFF")
        self.user_input.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.user_input.bind("<Return>", lambda e: self.process_input())

        self.send_btn = ctk.CTkButton(self.input_frame, text="Enviar", width=120, height=60, command=self.process_input, state="disabled", fg_color="#FFFFFF", text_color="#000000", hover_color="#CCCCCC", font=ctk.CTkFont("Consolas", 18, "bold"))
        self.send_btn.pack(side="left")

        self.top_frame.pack_forget()
        self.ai_textbox.pack_forget()
        self.dynamic_frame.pack_forget()
        self.input_frame.pack_forget()

        self.after(100, self.expansion_animation)
        self.setup_startup()

    def setup_startup(self):
        """Configura el inicio automático al arrancar Windows detectando si es script o .exe."""
        try:
            # Ruta de la carpeta de Inicio (Startup) de Windows
            startup_folder = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
            bat_path = os.path.join(startup_folder, "Jarvis.bat")
            
            # Solo creamos el archivo si no existe
            if not os.path.exists(bat_path):
                # Detectar si estamos en un ejecutable (.exe) o en un script (.py)
                is_frozen = getattr(sys, 'frozen', False)
                
                if is_frozen:
                    # Si ya es un .exe (como Jarvis.exe), lo ejecutamos directamente
                    exec_path = sys.executable
                    cmd = f'start "" "{exec_path}"'
                else:
                    # Si es un script .py, usamos pythonw.exe + ruta del script para ocultar la consola
                    script_path = os.path.abspath(__file__)
                    python_exe = sys.executable
                    pythonw_exe = python_exe.replace("python.exe", "pythonw.exe")
                    exec_path = pythonw_exe if os.path.exists(pythonw_exe) else python_exe
                    cmd = f'start "" "{exec_path}" "{script_path}"'
                
                with open(bat_path, 'w', encoding='utf-8') as f:
                    f.write(f'@echo off\n')
                    f.write(f'{cmd}\n')
        except Exception as e:
            print(f"Error al configurar el inicio automático: {e}")

    def return_to_center(self):
        """Método específico para volver al centro desde el botón"""
        if self.mode == "companion":
            self.move_to_center()
        else:
            self.type_text("[JARVIS] Ya estoy en el centro.")

    def close_with_animation(self):
        """Cierra la aplicación principal con una animación de minimizado fluida a 165 FPS"""
        # Ocultar todos los widgets inmediatamente para que no se vean las letras
        self.top_frame.pack_forget()
        if hasattr(self, 'center_return_btn'):
            self.center_return_btn.pack_forget()
        self.ai_textbox.pack_forget()
        self.dynamic_frame.pack_forget()
        self.input_frame.pack_forget()
        
        # Limpiar el texto
        self.update_ai_text("")
        
        def animate_close():
            steps = 45  # Más pasos para una animación más fluida a 165 FPS
            current_w = self.winfo_width()
            current_h = self.winfo_height()
            current_x = self.winfo_x()
            current_y = self.winfo_y()
            
            # Animación de minimizado
            for i in range(1, steps + 1):
                t = i / steps
                ease_t = 1 - (1 - t) ** 2
                
                w = int(current_w * (1 - ease_t))
                h = int(current_h * (1 - ease_t))
                if w < 2: w = 2
                if h < 2: h = 2
                x = current_x + (current_w - w) // 2
                y = current_y + (current_h - h) // 2
                self.geometry(f"{w}x{h}+{x}+{y}")
                self.update()
                time.sleep(FRAME_DELAY)
            
            self.destroy()
        
        threading.Thread(target=animate_close, daemon=True).start()

    def load_games_data(self):
        try:
            if os.path.exists(JSON_PATH):
                with open(JSON_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "games" in data:
                        # Cargar idioma guardado
                        self.current_language = data.get("settings", {}).get("language", "Español")
                        return data.get("games", [])
                    elif isinstance(data, dict):
                        # Soporte para versiones anteriores del JSON
                        new_data = []
                        for k, v in data.items():
                            if isinstance(v, list):
                                new_data.extend(v)
                        return new_data
                    return data
            return []
        except:
            return []

    def save_games_data(self):
        try:
            full_data = {
                "games": self.games_data,
                "settings": {
                    "language": self.current_language
                }
            }
            with open(JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(full_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error al guardar datos: {e}")

    def expansion_animation(self):
        def animate():
            target_w = 1000
            target_h = 700
            steps = 45  # Más pasos para 165 FPS
            
            for i in range(1, steps + 1):
                # Usar ease-out para una expansión más natural
                t = i / steps
                ease_t = 1 - (1 - t) ** 2
                
                w = int(target_w * ease_t)
                h = int(target_h * ease_t)
                if w < 10: w = 10
                if h < 10: h = 10
                x = (self.screen_w - w) // 2
                y = (self.screen_h - h) // 2
                self.geometry(f"{w}x{h}+{x}+{y}")
                self.update()
                time.sleep(FRAME_DELAY)
                
            self.after(100, self.show_initial_prompt)

        threading.Thread(target=animate, daemon=True).start()

    def show_initial_prompt(self):
        self.top_frame.pack(fill="x", padx=20, pady=10)
        self.ai_textbox.pack(pady=20, padx=40, fill="both", expand=True)
        self.dynamic_frame.pack(pady=20, padx=20, fill="both", expand=True)
        self.input_frame.pack(pady=30, padx=20, fill="x", side="bottom")
        
        self.type_text("[JARVIS] Sistemas Iniciados.\n¿Has añadido o borrado algo en el escritorio?", self.ask_scan_buttons)

    def ask_scan_buttons(self):
        self.clear_dynamic()
        
        btn_frame = ctk.CTkFrame(self.dynamic_frame, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        btn_yes = ctk.CTkButton(btn_frame, text="SÍ", font=self.main_font, width=150, height=50, fg_color="#FFFFFF", text_color="#000000", hover_color="#CCCCCC", command=self.start_scan_animation)
        btn_yes.pack(side="left", padx=20)
        
        btn_no = ctk.CTkButton(btn_frame, text="NO", font=self.main_font, width=150, height=50, fg_color="transparent", text_color="#FFFFFF", border_width=2, border_color="#FFFFFF", hover_color="#333333", command=self.skip_scan)
        btn_no.pack(side="left", padx=20)

    def skip_scan(self):
        self.clear_dynamic()
        self.post_scan_check()

    def start_scan_animation(self):
        self.clear_dynamic()
        self.is_scanning = True
        
        def animate():
            frames = ["[ / ]", "[ - ]", "[ \\ ]", "[ | ]"]
            i = 0
            while self.is_scanning:
                try:
                    self.update_ai_text(f"{self.get_text('scanning')}\n{frames[i % len(frames)]}")
                except:
                    pass
                i += 1
                time.sleep(0.15)

        threading.Thread(target=animate, daemon=True).start()
        threading.Thread(target=self.scan_desktop, daemon=True).start()

    def scan_desktop(self):
        time.sleep(1.5)
        
        desktops = [
            os.path.join(os.environ['USERPROFILE'], 'Desktop'),
            os.path.join(os.environ.get('PUBLIC', 'C:\\Users\\Public'), 'Desktop'),
            os.path.join(os.environ['USERPROFILE'], 'OneDrive', 'Desktop'),
            os.path.join(os.environ['USERPROFILE'], 'OneDrive', 'Escritorio')
        ]
        
        # 1. Obtener archivos actuales del escritorio
        current_desktop_files = []
        for d in desktops:
            if os.path.exists(d):
                for root, dirs, files in os.walk(d):
                    for f in files:
                        current_desktop_files.append(os.path.join(root, f).lower())

        # 2. Detectar eliminaciones (solo para archivos que estaban en el escritorio)
        original_count = len(self.games_data)
        
        def is_desktop_path(path):
            p = path.lower()
            return any(p.startswith(d.lower()) for d in desktops)

        # Filtramos: mantenemos el juego si existe físicamente O si NO era una ruta del escritorio 
        # (para no borrar juegos añadidos manualmente desde otras carpetas)
        self.games_data = [
            g for g in self.games_data 
            if os.path.exists(g['path']) or not is_desktop_path(g['path'])
        ]
        
        # 3. Detectar nuevos archivos
        existing_paths = [g['path'].lower() for g in self.games_data]
        found_change = len(self.games_data) != original_count
        valid_extensions = ('.exe', '.lnk', '.url')

        for path in current_desktop_files:
            if path not in existing_paths:
                ext = os.path.splitext(path)[1].lower()
                if ext in valid_extensions:
                    name = os.path.splitext(os.path.basename(path))[0]
                    # Evitar archivos de sistema ocultos o temporales si los hubiera
                    if not name.startswith("~$"):
                        self.games_data.append({"name": name, "path": path})
                        existing_paths.append(path)
                        found_change = True
                        
        if found_change:
            self.save_games_data()

        self.is_scanning = False
        self.after(200, self.post_scan_check)

    def post_scan_check(self):
        self.manage_btn.configure(state="normal")
        self.settings_btn.configure(state="normal")
        self.pin_btn.configure(state="normal")
        self.center_return_btn.configure(state="normal")
        self.send_btn.configure(state="normal")
        if not self.is_pinned:
            self.attributes('-topmost', 'false')

        if len(self.games_data) == 0:
            self.type_text("[JARVIS] Tu biblioteca está vacía.\nAñade tus juegos en el Gestor (⚙️).")
        else:
            self.type_text("[JARVIS] Todo listo. ¿Qué te apetece hacer hoy?")

    def open_manager(self):
        """Abre el gestor de juegos asegurando que solo haya una instancia abierta."""
        if self.manager_window is None or not self.manager_window.winfo_exists():
            self.manager_window = GameManager(self)
        else:
            self.manager_window.deiconify() # Por si estuviera minimizada
            self.manager_window.focus()
            self.manager_window.lift() # Traer al frente

    def open_settings(self):
        """Abre el panel de configuración asegurando que solo haya una instancia."""
        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = SettingsWindow(self)
        else:
            self.settings_window.deiconify()
            self.settings_window.focus()
            self.settings_window.lift()

    def toggle_pin(self):
        self.is_pinned = not self.is_pinned
        if self.is_pinned:
            self.attributes('-topmost', 'true')
            self.pin_btn.configure(fg_color="#333333")
            self.type_text(self.get_text("pinned"))
        else:
            self.attributes('-topmost', 'false')
            self.pin_btn.configure(fg_color="transparent")
            self.type_text(self.get_text("unpinned"))

    def get_text(self, key):
        """Retorna el texto traducido según el idioma actual."""
        lang = self.current_language
        if lang not in TRANSLATIONS:
            return TRANSLATIONS["English"].get(key, key)
        return TRANSLATIONS[lang].get(key, TRANSLATIONS["English"].get(key, key))

    def refresh_ui_text(self):
        """Actualiza los textos de la interfaz al cambiar de idioma."""
        self.close_btn.configure(text=self.get_text("close"))
        self.center_return_btn.configure(text=self.get_text("back_center"))
        self.send_btn.configure(text=self.get_text("send"))
        self.user_input.configure(placeholder_text=self.get_text("placeholder"))

    def clear_dynamic(self):
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()

    def update_ai_text(self, text):
        """Actualiza el texto del textbox de forma segura."""
        self.ai_textbox.configure(state="normal")
        self.ai_textbox.delete("1.0", "end")
        self.ai_textbox.insert("1.0", text)
        self.ai_textbox.see("end")
        self.ai_textbox.configure(state="disabled")

    def type_text(self, text, callback=None):
        self.ai_textbox.configure(state="normal")
        self.ai_textbox.delete("1.0", "end")
        def writer():
            current_text = ""
            for char in text:
                current_text += char
                try:
                    self.after(0, lambda t=current_text: self.update_ai_text(t))
                except:
                    pass
                time.sleep(0.01)
            if callback:
                self.after(100, callback)
        threading.Thread(target=writer, daemon=True).start()

    def ask_ollama(self, prompt):
        """Consulta a Ollama con memoria y efecto de streaming seguro."""
        if self.mode != "companion":
            return # Seguridad extra

        self.update_ai_text(f"[JARVIS] {self.get_text('searching')}")
        self.user_input.configure(state="disabled")
        self.send_btn.configure(state="disabled")

        def stream_response():
            try:
                url = "http://127.0.0.1:11434/api/generate"
                
                # Construir el prompt con historia e idioma
                user_tag = "User" if self.current_language != "Español" else "Usuario"
                ai_tag = "Jarvis"
                
                full_prompt = f"You are Jarvis, a professional AI gaming assistant. MISSION: You MUST respond EXCLUSIVELY in the {self.current_language.upper()} language. Do not use any other language.\n"
                for h in self.chat_history[-5:]:
                    full_prompt += f"{user_tag}: {h['user']}\n{ai_tag}: {h['jarvis']}\n"
                full_prompt += f"{user_tag}: {prompt}\n{ai_tag}:"
                        

                payload = {
                    "model": self.ollama_model,
                    "prompt": full_prompt,
                    "stream": True
                }
                
                response = requests.post(url, json=payload, stream=True, timeout=60)
                
                if response.status_code != 200:
                    self.after(0, lambda: self.type_text("[JARVIS] No he podido contactar con el núcleo de Ollama."))
                    return

                current_response = ""
                self.after(0, lambda: self.update_ai_text("[JARVIS] "))
                
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line.decode('utf-8'))
                        chunk = data.get("response", "")
                        current_response += chunk
                        
                        text_to_show = f"[JARVIS] {current_response}"
                        self.after(0, lambda t=text_to_show: self.update_ai_text(t))
                            
                        if data.get("done"):
                            self.chat_history.append({"user": prompt, "jarvis": current_response})
                            break
                            
            except Exception as e:
                self.after(0, lambda: self.type_text(f"[JARVIS] Interrupción en la comunicación: {str(e)}"))
            finally:
                self.after(0, self.reenable_input)

        threading.Thread(target=stream_response, daemon=True).start()

    def reenable_input(self):
        self.user_input.configure(state="normal")
        self.send_btn.configure(state="normal")
        self.user_input.focus()

    def process_input(self):
        text = self.user_input.get().lower().strip()
        self.user_input.delete(0, 'end')
        
        if not text:
            return

        self.clear_dynamic()

        if text in ["cierra", "cerrar", "salir", "cierra el juego", "cerrar juego"]:
            if self.last_launched_game:
                os.system(f'taskkill /F /IM "{self.last_launched_game}.exe" /T >nul 2>&1')
                os.system(f'taskkill /F /IM "{self.last_launched_game.replace(" ", "")}.exe" /T >nul 2>&1')
                self.type_text(f"[JARVIS] {self.get_text('closing_game')} {self.last_launched_game}.")
                self.monitoring = False
            else:
                self.type_text(f"[JARVIS] {self.get_text('no_game_open')}")
            return

        if text in ["limpiar", "borrar historial", "olvida todo", "reset"]:
            self.chat_history = []
            self.type_text(self.get_text("amnesia"))
            return

        # MODO ACOMPAÑANTE: Prioridad absoluta a la IA Ollama
        if self.mode == "companion":
            self.ask_ollama(text)
            return

        # MODO NORMAL: Lógica de búsqueda y ejecución de juegos
        if len(self.games_data) == 0:
            self.type_text(f"[JARVIS] {self.get_text('add_games_first')}")
            return

        if text in ["jugar", "nada", "no se", "juegos", "todos", "lista", "que tienes"]:
            self.type_text(f"[JARVIS] {self.get_text('here_is_all')}")
            self.show_game_buttons(self.games_data)
            return

        matches = []
        for game in self.games_data:
            if text in game["name"].lower() or game["name"].lower() in text:
                matches.append(game)

        if len(matches) == 1:
            self.type_text(f"[JARVIS] {self.get_text('opening')}: {matches[0]['name']}...")
            self.launch_game(matches[0])
        elif len(matches) > 1:
            self.type_text(f"[JARVIS] {self.get_text('matches_found')}")
            self.show_game_buttons(matches)
        else:
            self.type_text(f"[JARVIS] {self.get_text('not_found')}")
            self.show_game_buttons(self.games_data)

    def show_game_buttons(self, games_list):
        scroll = ctk.CTkScrollableFrame(self.dynamic_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        btn_padx = 20 if self.mode == "companion" else 250
        btn_font = ctk.CTkFont("Consolas", 14) if self.mode == "companion" else self.main_font

        for game in games_list:
            btn = ctk.CTkButton(
                scroll, text=game["name"], font=btn_font,
                fg_color="transparent", hover_color="#333333", border_width=2, border_color="#FFFFFF", height=50, text_color="#FFFFFF",
                command=lambda g=game: self.launch_game(g)
            )
            btn.pack(pady=10, padx=btn_padx, fill="x")

    def monitor_game_process(self, game_name):
        exe_name = game_name.replace(" ", "") + ".exe"
        exe_name_full = game_name + ".exe"
        time.sleep(8)
        
        while self.monitoring:
            try:
                output = subprocess.check_output('tasklist', shell=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if exe_name.lower() not in output.lower() and exe_name_full.lower() not in output.lower():
                    self.monitoring = False
                    break
            except Exception:
                pass
            time.sleep(1.5)

    def launch_game(self, game):
        self.clear_dynamic()
        self.user_input.configure(state="disabled")
        self.send_btn.configure(state="disabled")
        self.last_launched_game = game["name"]
        
        # Activar modo anclado automáticamente al iniciar un juego
        if not self.is_pinned:
            self.is_pinned = True
            self.attributes('-topmost', 'true')
            self.pin_btn.configure(fg_color="#333333")
        
        def open_process():
            time.sleep(1)
            try:
                os.startfile(game["path"])
            except Exception as e:
                print(f"Error al abrir {game['name']}: {e}")
            
            self.monitoring = True
            threading.Thread(target=self.monitor_game_process, args=(game["name"],), daemon=True).start()

            if self.mode != "companion":
                self.after(500, self.move_to_right)
            else:
                self.after(500, lambda: self.type_text("[JARVIS] Abierto. Sigo en modo acompañante."))
                self.user_input.configure(state="normal")
                self.send_btn.configure(state="normal")

        threading.Thread(target=open_process, daemon=True).start()

    def move_to_right(self):
        self.mode = "companion"
        w = 400
        h = self.screen_h - 80 
        x = self.screen_w - w
        y = 0
        
        self.top_frame.pack_forget()
        self.ai_textbox.pack_forget()
        self.dynamic_frame.pack_forget()
        self.input_frame.pack_forget()

        self.ai_textbox.configure(font=ctk.CTkFont("Consolas", 14))
        self.user_input.configure(font=ctk.CTkFont("Consolas", 14))
        
        def animate_move():
            steps = 45  # Más pasos para 165 FPS
            current_w = 1000
            current_h = 700
            start_x = (self.screen_w - current_w) // 2
            start_y = (self.screen_h - current_h) // 2
            
            # Fase 1: Minimizar al centro
            for i in range(1, steps + 1):
                t = i / steps
                ease_t = 1 - (1 - t) ** 2
                
                temp_w = int(current_w * (1 - ease_t))
                temp_h = int(current_h * (1 - ease_t))
                if temp_w < 10: temp_w = 10
                if temp_h < 10: temp_h = 10
                temp_x = start_x + (current_w - temp_w) // 2
                temp_y = start_y + (current_h - temp_h) // 2
                self.geometry(f"{temp_w}x{temp_h}+{temp_x}+{temp_y}")
                self.update()
                time.sleep(FRAME_DELAY)
                
            # Fase 2: Maximizar a la derecha
            target_w = 400
            target_h = self.screen_h - 80
            target_x = self.screen_w - target_w
            target_y = 0
            
            for i in range(1, steps + 1):
                t = i / steps
                ease_t = 1 - (1 - t) ** 2
                
                temp_w = int(target_w * ease_t)
                temp_h = int(target_h * ease_t)
                if temp_w < 10: temp_w = 10
                if temp_h < 10: temp_h = 10
                temp_x = target_x + (target_w - temp_w) // 2
                temp_y = target_y + (target_h - temp_h) // 2
                self.geometry(f"{temp_w}x{temp_h}+{temp_x}+{temp_y}")
                self.update()
                time.sleep(FRAME_DELAY)
                
            self.geometry(f"{target_w}x{target_h}+{target_x}+{target_y}")
            
            # Restaurar UI y mostrar botón de volver al centro
            self.top_frame.pack(fill="x", padx=20, pady=10)
            self.center_return_btn.pack(pady=(0, 10))
            self.center_return_btn.configure(state="normal")
            self.ai_textbox.pack(pady=10, padx=20, fill="both", expand=True)
            self.dynamic_frame.pack(pady=10, padx=20, fill="both", expand=True)
            self.input_frame.pack(pady=30, padx=20, fill="x", side="bottom")

            self.type_text(self.get_text("companion_active"))
            self.user_input.configure(state="normal")
            self.send_btn.configure(state="normal")

        threading.Thread(target=animate_move, daemon=True).start()

    def move_to_center(self):
        if self.mode == "normal": 
            self.type_text("[JARVIS] Ya estoy en el centro.")
            return
        
        self.mode = "normal"
        self.monitoring = False
        self.clear_dynamic()
        self.user_input.configure(state="disabled")
        self.send_btn.configure(state="disabled")

        self.top_frame.pack_forget()
        self.center_return_btn.pack_forget()
        self.ai_textbox.pack_forget()
        self.dynamic_frame.pack_forget()
        self.input_frame.pack_forget()

        w = 1000
        h = 700
        x = (self.screen_w - w) // 2
        y = (self.screen_h - h) // 2

        self.ai_textbox.configure(font=self.title_font)
        self.user_input.configure(font=self.main_font)

        def animate_back():
            steps = 45  # Más pasos para 165 FPS
            current_w = 400
            current_h = self.screen_h - 80
            start_x = self.screen_w - current_w
            start_y = 0
            
            # Fase 1: Minimizar a la derecha
            for i in range(1, steps + 1):
                t = i / steps
                ease_t = 1 - (1 - t) ** 2
                
                temp_w = int(current_w * (1 - ease_t))
                temp_h = int(current_h * (1 - ease_t))
                if temp_w < 10: temp_w = 10
                if temp_h < 10: temp_h = 10
                temp_x = start_x + (current_w - temp_w) // 2
                temp_y = start_y + (current_h - temp_h) // 2
                self.geometry(f"{temp_w}x{temp_h}+{temp_x}+{temp_y}")
                self.update()
                time.sleep(FRAME_DELAY)

            # Fase 2: Maximizar al centro
            target_w = 1000
            target_h = 700
            target_x = (self.screen_w - target_w) // 2
            target_y = (self.screen_h - target_h) // 2

            for i in range(1, steps + 1):
                t = i / steps
                ease_t = 1 - (1 - t) ** 2
                
                temp_w = int(target_w * ease_t)
                temp_h = int(target_h * ease_t)
                if temp_w < 10: temp_w = 10
                if temp_h < 10: temp_h = 10
                temp_x = target_x + (target_w - temp_w) // 2
                temp_y = target_y + (target_h - temp_h) // 2
                self.geometry(f"{temp_w}x{temp_h}+{temp_x}+{temp_y}")
                self.update()
                time.sleep(FRAME_DELAY)

            self.geometry(f"{target_w}x{target_h}+{target_x}+{target_y}")
            
            # Restaurar UI (sin el botón de volver al centro)
            self.top_frame.pack(fill="x", padx=20, pady=10)
            self.ai_textbox.pack(pady=20, padx=40, fill="both", expand=True)
            self.dynamic_frame.pack(pady=10, padx=20, fill="both", expand=True)
            self.input_frame.pack(pady=30, padx=20, fill="x", side="bottom")

            self.type_text(self.get_text("back_to_center"))
            self.user_input.configure(state="normal")
            self.send_btn.configure(state="normal")

        threading.Thread(target=animate_back, daemon=True).start()

if __name__ == "__main__":
    app = AIGameAssistant()
    app.mainloop()