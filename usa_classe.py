import tkinter as tk
import cv2
import numpy as np
# Importa le classi e le funzioni dai moduli personalizzati
from interactive_shapes import InteractiveRectangle, cv2_to_tk_image, HANDLE_SIZE, ROTATION_HANDLE_OFFSET
from mouse_events import MouseEventHandler
from image_utils import create_blank_cv_image, load_cv_image

# --- Classe Principale dell'Applicazione ---
class ImageEditorApp:
    """
    Applicazione Tkinter per l'editing interattivo di immagini con rettangoli trascinabili, ridimensionabili e ruotabili.
    """
    def __init__(self, root, image_path=None):
        self.root = root
        self.root.title("Editor Immagini Interattivo")

        self.original_cv_image = None # Immagine originale caricata con OpenCV
        self.current_cv_image = None  # Copia dell'immagine corrente (per visualizzazione)
        self.tk_image = None          # Oggetto PhotoImage per Tkinter

        self.active_rectangle = None # Il rettangolo attualmente selezionato/trascinato
        self.rectangles = []         # Lista di tutti i rettangoli sull'immagine

        self.drag_state = None # Stato del trascinamento: "new_rect", "move_rect", "resize_rect", "rotate_rect"
        self.start_x = 0       # Coordinata X iniziale del clic del mouse per il disegno di un nuovo rettangolo
        self.start_y = 0       # Coordinata Y iniziale del clic del mouse per il disegno di un nuovo rettangolo

        # Crea il Canvas per visualizzare l'immagine e disegnare le forme
        self.canvas = tk.Canvas(root, bg="black", width=800, height=600)
        self.canvas.pack(padx=10, pady=10)

        # Crea un'istanza del gestore eventi del mouse, passandogli un riferimento a questa app
        self.mouse_handler = MouseEventHandler(self) 

        # Lega gli eventi del mouse ai metodi del gestore eventi
        self.canvas.bind("<Button-1>", self.mouse_handler.on_mouse_down)        # Clic sinistro
        self.canvas.bind("<B1-Motion>", self.mouse_handler.on_mouse_drag)       # Trascinamento con clic sinistro
        self.canvas.bind("<ButtonRelease-1>", self.mouse_handler.on_mouse_up) # Rilascio clic sinistro
        
        # Carica un'immagine di esempio o crea uno sfondo nero usando le funzioni di image_utils
        if image_path:
            self._load_initial_image(image_path)
        else:
            self._create_initial_blank_image(800, 600)

        # Disegna tutti i rettangoli iniziali (se ce ne fossero)
        self.draw_all_rectangles()

    def _load_initial_image(self, path):
        """
        Carica un'immagine iniziale usando la funzione utility load_cv_image.
        """
        img = load_cv_image(path)
        if img is None:
            self._create_initial_blank_image(800, 600) # Crea un'immagine nera se il caricamento fallisce
        else:
            self.original_cv_image = img
            self.current_cv_image = self.original_cv_image.copy()
            self.update_canvas_image()

    def _create_initial_blank_image(self, width, height):
        """
        Crea un'immagine nera vuota iniziale usando la funzione utility create_blank_cv_image.
        """
        self.original_cv_image = create_blank_cv_image(width, height)
        self.current_cv_image = self.original_cv_image.copy()
        self.update_canvas_image()

    def update_canvas_image(self):
        """
        Converte l'immagine OpenCV corrente in un formato Tkinter e la visualizza sul canvas.
        """
        self.tk_image = cv2_to_tk_image(self.current_cv_image)
        # Aggiorna le dimensioni del canvas per adattarsi all'immagine
        self.canvas.config(width=self.tk_image.width(), height=self.tk_image.height())
        # Crea o aggiorna l'immagine di sfondo sul canvas
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.canvas.tag_lower(self.tk_image) # Assicura che l'immagine sia sotto le forme disegnate

    def draw_all_rectangles(self):
        """
        Ridisegna l'immagine di sfondo e tutte le forme interattive sul canvas.
        """
        # Ridisegna l'immagine di sfondo per pulire eventuali residui di forme precedenti
        self.update_canvas_image() 
        # Disegna ogni rettangolo interattivo presente nella lista
        for rect in self.rectangles:
            rect.draw() # Il metodo draw() della classe InteractiveRectangle gestisce il disegno sul canvas

    # I metodi on_mouse_down, on_mouse_drag, on_mouse_up sono stati spostati
    # nella classe MouseEventHandler per una migliore modularità.

# --- Funzione Main (punto di ingresso del programma) ---
if __name__ == "__main__":
    # Assicurati di avere Pillow installato: pip install Pillow
    # Puoi caricare un'immagine esistente fornendo il percorso:
    # Esempio: image_path = "percorso/alla/tua/immagine.jpg"
    image_path = None # Imposta a None per iniziare con uno sfondo nero

    root = tk.Tk()
    app = ImageEditorApp(root, image_path)
    root.mainloop()
