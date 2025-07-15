import tkinter as tk
import cv2
import numpy as np
import os # Importa il modulo os per gestire i percorsi dei file
# Importa le classi e le funzioni dai moduli personalizzati
from interactive_shapes import InteractiveRectangle, InteractiveCircle, InteractiveEllipse, InteractivePolygon, InteractivePolyline, cv2_to_tk_image, HANDLE_SIZE, ROTATION_HANDLE_OFFSET
from mouse_events import MouseEventHandler
from image_utils import create_blank_cv_image, load_cv_image
from annotation_exporter import export_annotations_to_json # Importa la nuova funzione di esportazione

# --- Classe Principale dell'Applicazione ---
class ImageEditorApp:
    """
    Applicazione Tkinter per l'editing interattivo di immagini con rettangoli, cerchi, ovali, poligoni e polilinee trascinabili, ridimensionabili e ruotabili.
    """
    def __init__(self, root, image_path=None):
        self.root = root
        self.root.title("Editor di Forme Interattive")

        self.original_cv_image = None
        self.current_cv_image = None
        self.tk_image = None

        self.active_shape = None # La forma attualmente selezionata/trascinata (può essere Rectangle, Circle, Ellipse, Polygon, Polyline)
        self.shapes = []         # Lista di tutte le forme sull'immagine

        self.drag_state = None # Stato del trascinamento: "new_rect", "new_circle", "new_ellipse", "drawing_polygon", "drawing_polyline", "move_shape", "resize_shape", "rotate_rect", "move_vertex"
        self.start_x = 0       # Coordinata X iniziale del clic del mouse
        self.start_y = 0       # Coordinata Y iniziale del clic del mouse

        self.current_draw_mode = "rectangle" # Modalità di disegno iniziale
        self.current_image_path = image_path # Memorizza il percorso dell'immagine corrente

        # Crea il Canvas per visualizzare l'immagine e disegnare le forme
        self.canvas = tk.Canvas(root, bg="black", width=800, height=600)
        self.canvas.pack(padx=10, pady=10)

        # Crea un'istanza del gestore eventi del mouse, passandogli un riferimento a questa app
        self.mouse_handler = MouseEventHandler(self) 

        # Lega gli eventi del mouse ai metodi del gestore eventi
        self.canvas.bind("<Button-1>", self.mouse_handler.on_mouse_down)        # Clic singolo (sinistro)
        self.canvas.bind("<B1-Motion>", self.mouse_handler.on_mouse_drag)       # Trascinamento con clic sinistro
        self.canvas.bind("<ButtonRelease-1>", self.mouse_handler.on_mouse_up) # Rilascio clic sinistro
        self.canvas.bind("<Double-Button-1>", self.mouse_handler.on_mouse_double_click) # Doppio clic sinistro per chiudere poligoni/finalizzare polilinee
        
        # Crea un frame per i pulsanti di selezione della forma
        self.button_frame = tk.Frame(root)
        self.button_frame.pack(pady=5)

        tk.Button(self.button_frame, text="Disegna Rettangolo", command=lambda: self.set_draw_mode("rectangle")).pack(side=tk.LEFT, padx=5)
        tk.Button(self.button_frame, text="Disegna Cerchio", command=lambda: self.set_draw_mode("circle")).pack(side=tk.LEFT, padx=5)
        tk.Button(self.button_frame, text="Disegna Ovale", command=lambda: self.set_draw_mode("ellipse")).pack(side=tk.LEFT, padx=5)
        tk.Button(self.button_frame, text="Disegna Poligono", command=lambda: self.set_draw_mode("polygon")).pack(side=tk.LEFT, padx=5)
        tk.Button(self.button_frame, text="Disegna Polilinea", command=lambda: self.set_draw_mode("polyline")).pack(side=tk.LEFT, padx=5)
        
        # Nuovo pulsante per esportare le annotazioni
        tk.Button(self.button_frame, text="Esporta Annotazioni JSON", command=self.export_current_annotations).pack(side=tk.LEFT, padx=20)


        # Carica un'immagine di esempio o crea uno sfondo nero
        if image_path:
            self._load_initial_image(image_path)
        else:
            self._create_initial_blank_image(800, 600)

        self.draw_all_shapes()

    def set_draw_mode(self, mode):
        """Imposta la modalità di disegno corrente."""
        self.current_draw_mode = mode
        # Resetta la forma attiva e lo stato di trascinamento quando si cambia modalità
        self.active_shape = None
        self.drag_state = None
        self.draw_all_shapes() # Ridisegna per pulire eventuali stati di disegno parziali
        print(f"Modalità di disegno impostata su: {mode}")

    def _load_initial_image(self, path):
        """Carica un'immagine iniziale usando la funzione utility."""
        img = load_cv_image(path)
        if img is None:
            self._create_initial_blank_image(800, 600)
        else:
            self.original_cv_image = img
            self.current_cv_image = self.original_cv_image.copy()
            self.update_canvas_image()

    def _create_initial_blank_image(self, width, height):
        """Crea un'immagine nera vuota iniziale usando la funzione utility."""
        self.original_cv_image = create_blank_cv_image(width, height)
        self.current_cv_image = self.original_cv_image.copy()
        self.update_canvas_image()

    def update_canvas_image(self):
        """Converte l'immagine OpenCV corrente in un formato Tkinter e la visualizza sul canvas."""
        self.tk_image = cv2_to_tk_image(self.current_cv_image)
        self.canvas.config(width=self.tk_image.width(), height=self.tk_image.height())
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.canvas.tag_lower(self.tk_image)

    def draw_all_shapes(self):
        """Ridisegna l'immagine di sfondo e tutte le forme interattive sul canvas."""
        self.update_canvas_image() 
        for shape in self.shapes: # Itera su tutte le forme
            shape.draw() 

    def export_current_annotations(self):
        """
        Esporta le annotazioni correnti delle forme disegnate in un file JSON.
        Il nome del file sarà basato sul nome dell'immagine caricata, o un default.
        """
        if self.current_cv_image is None:
            print("Nessuna immagine caricata per esportare le annotazioni.")
            return

        # Prepara il nome del file JSON
        if self.current_image_path:
            base_name = os.path.splitext(os.path.basename(self.current_image_path))[0]
            json_filename = f"{base_name}_annotations.json"
        else:
            json_filename = "blank_image_annotations.json"
        
        # Chiama la funzione di esportazione dal modulo annotation_exporter
        export_annotations_to_json(
            self.shapes, 
            self.current_cv_image.shape[1], # Larghezza immagine
            self.current_cv_image.shape[0], # Altezza immagine
            json_filename
        )


# --- Funzione Main (punto di ingresso del programma) ---
if __name__ == "__main__":
    # Assicurati di avere Pillow installato: pip install Pillow
    # Puoi caricare un'immagine esistente fornendo il percorso:
    # Esempio: image_path = "percorso/alla/tua/immagine.jpg"
    image_path = None 

    root = tk.Tk()
    app = ImageEditorApp(root, image_path)
    root.mainloop()
