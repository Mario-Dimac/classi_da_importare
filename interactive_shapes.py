import tkinter as tk
from PIL import Image, ImageTk
import cv2
import numpy as np
import math

# --- Configurazioni Globali per le Forme ---
HANDLE_SIZE = 10 # Dimensione delle maniglie quadrate
COLOR_RECTANGLE_BORDER = "white"
COLOR_HANDLE_NORMAL = "red"
COLOR_HANDLE_ACTIVE = "blue"
COLOR_ROTATION_HANDLE = "green" # Colore per la maniglia di rotazione
ROTATION_HANDLE_OFFSET = 20 # Offset della maniglia di rotazione dal bordo superiore
COLOR_CIRCLE_BORDER = "yellow" # Colore per il cerchio
COLOR_ELLIPSE_BORDER = "purple" # Colore per l'ovale
COLOR_POLYGON_BORDER = "cyan" # Colore per il poligono
COLOR_POLYGON_VERTEX_HANDLE = "magenta" # Colore per le maniglie dei vertici del poligono
COLOR_POLYLINE_BORDER = "orange" # Nuovo colore per la polilinea
COLOR_POLYLINE_VERTEX_HANDLE = "lime" # Colore per le maniglie dei vertici della polilinea

# --- Classe per il Rettangolo Interattivo ---
class InteractiveRectangle:
    """
    Rappresenta un rettangolo disegnabile, ridimensionabile, ruotabile e riempibile su un canvas Tkinter.
    """
    def __init__(self, canvas, x1, y1, x2, y2, color=COLOR_RECTANGLE_BORDER, border_width=2, fill_color=""):
        self.canvas = canvas
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.color = color
        self.border_width = border_width
        self.fill_color = fill_color # Nuovo attributo per il colore di riempimento
        self.angle = 0 # Angolo di rotazione in radianti (0 gradi inizialmente)
        
        self.rect_id = None # ID del poligono che rappresenta il rettangolo
        self.handle_ids = [] # Lista di ID delle maniglie
        self.active_handle_index = -1 # Indice della maniglia attualmente attiva (-1 se nessuna, 0-7 per ridimensionamento, 8 per rotazione)

        # Variabili per il trascinamento/rotazione (inizializzate in on_mouse_down)
        self.start_drag_x = 0
        self.start_drag_y = 0
        self.start_angle = 0 # Angolo iniziale del rettangolo al momento del clic per la rotazione

    def draw(self):
        """
        Disegna il rettangolo ruotato e le sue maniglie sul canvas Tkinter.
        Rimuove le forme precedenti prima di ridisegnare.
        """
        self.delete_shapes() # Pulisce le forme precedenti

        # Calcola i 4 angoli del rettangolo ruotato
        rotated_corners = self._get_rotated_corners()
        # Converte la lista di tuple in una lista piatta per create_polygon
        polygon_points = []
        for p in rotated_corners:
            polygon_points.extend(p)

        # Disegna il rettangolo come un poligono, usando il colore di riempimento
        self.rect_id = self.canvas.create_polygon(
            *polygon_points,
            outline=self.color, width=self.border_width, fill=self.fill_color # Usa self.fill_color qui
        )

        # Disegna le maniglie di ridimensionamento e rotazione
        self.handle_ids = []
        handles = self._get_handles_coords()
        for i, (hx, hy) in enumerate(handles):
            if i == 8: # Maniglia di rotazione
                handle_color = COLOR_HANDLE_ACTIVE if i == self.active_handle_index else COLOR_ROTATION_HANDLE
            else: # Maniglie di ridimensionamento
                handle_color = COLOR_HANDLE_ACTIVE if i == self.active_handle_index else COLOR_HANDLE_NORMAL
            
            handle_id = self.canvas.create_rectangle(
                hx - HANDLE_SIZE // 2, hy - HANDLE_SIZE // 2,
                hx + HANDLE_SIZE // 2, hy + HANDLE_SIZE // 2,
                fill=handle_color, outline=handle_color
            )
            self.handle_ids.append(handle_id)

    def delete_shapes(self):
        """
        Rimuove il rettangolo e tutte le sue maniglie dal canvas Tkinter.
        """
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            self.rect_id = None
        for handle_id in self.handle_ids:
            self.canvas.delete(handle_id)
        self.handle_ids = []

    def _get_center(self):
        """
        Calcola il centro del rettangolo.
        """
        cx = (self.x1 + self.x2) // 2
        cy = (self.y1 + self.y2) // 2
        return cx, cy

    def _get_rotated_corners(self):
        """
        Calcola le coordinate dei 4 angoli del rettangolo dopo la rotazione.
        """
        cx, cy = self._get_center()
        
        # Coordinate dei 4 angoli non ruotati rispetto al centro
        half_w = (self.x2 - self.x1) / 2
        half_h = (self.y2 - self.y1) / 2

        corners_unrotated = [
            (-half_w, -half_h), # Top-left
            (half_w, -half_h),  # Top-right
            (half_w, half_h),   # Bottom-right
            (-half_w, half_h)   # Bottom-left
        ]

        rotated_corners = []
        for x_unrotated, y_unrotated in corners_unrotated:
            # Applica la rotazione
            x_rotated = x_unrotated * math.cos(self.angle) - y_unrotated * math.sin(self.angle)
            y_rotated = x_unrotated * math.sin(self.angle) + y_unrotated * math.cos(self.angle)
            
            # Trasla indietro al centro reale dell'immagine
            rotated_corners.append((cx + x_rotated, cy + y_rotated))
        
        return rotated_corners

    def _get_handles_coords(self):
        """
        Calcola e restituisce le coordinate centrali delle 8 maniglie di ridimensionamento
        e della 1 maniglia di rotazione, tenendo conto della rotazione del rettangolo.
        """
        cx, cy = self._get_center()
        
        # Calcola le posizioni delle 8 maniglie di ridimensionamento
        # rispetto al centro e poi ruotale
        half_w = (self.x2 - self.x1) / 2
        half_h = (self.y2 - self.y1) / 2

        handles_unrotated = [
            (-half_w, -half_h), # 0: Top-left
            (0, -half_h),       # 1: Top-mid
            (half_w, -half_h),  # 2: Top-right
            (-half_w, 0),       # 3: Mid-left
            (half_w, 0),        # 4: Mid-right
            (-half_w, half_h),  # 5: Bottom-left
            (0, half_h),        # 6: Bottom-mid
            (half_w, half_h)    # 7: Bottom-right
        ]
        
        rotated_handles = []
        for x_unrotated, y_unrotated in handles_unrotated:
            x_rotated = x_unrotated * math.cos(self.angle) - y_unrotated * math.sin(self.angle)
            y_rotated = x_unrotated * math.sin(self.angle) + y_unrotated * math.cos(self.angle)
            rotated_handles.append((cx + x_rotated, cy + y_rotated))

        # Aggiungi la maniglia di rotazione (indice 8)
        # Posizionala sopra il centro del lato superiore ruotato
        rot_handle_x_unrotated, rot_handle_y_unrotated = (0, -half_h - ROTATION_HANDLE_OFFSET)
        rot_handle_x_rotated = rot_handle_x_unrotated * math.cos(self.angle) - rot_handle_y_unrotated * math.sin(self.angle)
        rot_handle_y_rotated = rot_handle_x_unrotated * math.sin(self.angle) + rot_handle_y_unrotated * math.cos(self.angle)
        rotated_handles.append((cx + rot_handle_x_rotated, cy + rot_handle_y_rotated))

        return rotated_handles

    def check_hit(self, mouse_x, mouse_y):
        """
        Controlla se le coordinate del mouse colpiscono una maniglia o il corpo del rettangolo.
        Restituisce "handle" (con indice), "body" o None.
        """
        # Controlla prima le maniglie (incluse quelle di rotazione)
        handles = self._get_handles_coords()
        for i, (hx, hy) in enumerate(handles):
            if hx - HANDLE_SIZE // 2 <= mouse_x <= hx + HANDLE_SIZE // 2 and \
               hy - HANDLE_SIZE // 2 <= mouse_y <= hy + HANDLE_SIZE // 2:
                self.active_handle_index = i
                return "handle" # Colpita una maniglia
        
        # Controlla il corpo del rettangolo (usando l'ID del poligono per hit detection)
        if self.rect_id:
            # find_overlapping restituisce una tupla di ID degli oggetti sotto il punto
            overlapping_objects = self.canvas.find_overlapping(mouse_x, mouse_y, mouse_x, mouse_y)
            if self.rect_id in overlapping_objects:
                self.active_handle_index = -1 # Nessuna maniglia attiva se clicco sul corpo
                return "body" # Colpito il corpo del rettangolo
            
        self.active_handle_index = -1
        return None # Nessun hit

    def update_coords(self, new_x1, new_y1, new_x2, new_y2):
        """
        Aggiorna le coordinate del rettangolo, assicurandosi che x1 sia <= x2 e y1 sia <= y2.
        Questo metodo non gestisce la rotazione.
        """
        self.x1 = min(new_x1, new_x2)
        self.y1 = min(new_y1, new_y2)
        self.x2 = max(new_x1, new_x2)
        self.y2 = max(new_y1, new_y2)

    def rotate(self, current_mouse_x, current_mouse_y):
        """
        Aggiorna l'angolo di rotazione del rettangolo in base al movimento del mouse.
        """
        cx, cy = self._get_center()
        
        # Calcola l'angolo del mouse rispetto al centro del rettangolo
        # Angolo iniziale del clic (dal punto start_drag_x, start_drag_y)
        start_vec_x = self.start_drag_x - cx
        start_vec_y = self.start_drag_y - cy
        start_angle_rad = math.atan2(start_vec_y, start_vec_x)

        # Angolo corrente del mouse
        current_vec_x = current_mouse_x - cx
        current_vec_y = current_mouse_y - cy
        current_angle_rad = math.atan2(current_vec_y, current_vec_x)

        # Calcola la differenza angolare e aggiungila all'angolo iniziale del rettangolo
        angle_diff = current_angle_rad - start_angle_rad
        self.angle = self.start_angle + angle_diff

        # NON aggiornare self.start_drag_x e self.start_drag_y qui.
        # Questi devono rimanere il punto di clic iniziale per il calcolo della differenza angolare.

# --- Classe per il Cerchio Interattivo ---
class InteractiveCircle:
    """
    Rappresenta un cerchio disegnabile e ridimensionabile su un canvas Tkinter.
    """
    def __init__(self, canvas, cx, cy, radius, color=COLOR_CIRCLE_BORDER, border_width=2, fill_color=""):
        self.canvas = canvas
        self.cx = cx
        self.cy = cy
        self.radius = radius
        self.color = color
        self.border_width = border_width
        self.fill_color = fill_color # Nuovo attributo per il colore di riempimento
        
        self.oval_id = None # ID del cerchio (ovale) disegnato sul canvas
        self.handle_ids = [] # Lista di ID delle maniglie
        self.active_handle_index = -1 # Indice della maniglia attiva

        self.start_drag_x = 0
        self.start_drag_y = 0

    def draw(self):
        """
        Disegna il cerchio e le sue maniglie sul canvas Tkinter.
        Rimuove le forme precedenti prima di ridisegnare.
        """
        self.delete_shapes()

        # Calcola le coordinate del bounding box per create_oval
        x1 = self.cx - self.radius
        y1 = self.cy - self.radius
        x2 = self.cx + self.radius
        y2 = self.cy + self.radius

        self.oval_id = self.canvas.create_oval(
            x1, y1, x2, y2,
            outline=self.color, width=self.border_width, fill=self.fill_color # Usa self.fill_color qui
        )

        # Disegna le maniglie
        self.handle_ids = []
        handles = self._get_handles_coords()
        for i, (hx, hy) in enumerate(handles):
            handle_color = COLOR_HANDLE_ACTIVE if i == self.active_handle_index else COLOR_HANDLE_NORMAL
            handle_id = self.canvas.create_rectangle(
                hx - HANDLE_SIZE // 2, hy - HANDLE_SIZE // 2,
                hx + HANDLE_SIZE // 2, hy + HANDLE_SIZE // 2,
                fill=handle_color, outline=handle_color
            )
            self.handle_ids.append(handle_id)

    def delete_shapes(self):
        """
        Rimuove il cerchio e tutte le sue maniglie dal canvas Tkinter.
        """
        if self.oval_id:
            self.canvas.delete(self.oval_id)
            self.oval_id = None
        for handle_id in self.handle_ids:
            self.canvas.delete(handle_id)
        self.handle_ids = []

    def _get_handles_coords(self):
        """
        Calcola e restituisce le coordinate centrali delle 4 maniglie cardinali per il cerchio.
        """
        return [
            (self.cx, self.cy - self.radius), # Top
            (self.cx + self.radius, self.cy), # Right
            (self.cx, self.cy + self.radius), # Bottom
            (self.cx - self.radius, self.cy)  # Left
        ]

    def check_hit(self, mouse_x, mouse_y):
        """
        Controlla se le coordinate del mouse colpiscono una maniglia o il corpo del cerchio.
        Restituisce "handle" (con indice), "body" o None.
        """
        # Controlla le maniglie
        handles = self._get_handles_coords()
        for i, (hx, hy) in enumerate(handles):
            if hx - HANDLE_SIZE // 2 <= mouse_x <= hx + HANDLE_SIZE // 2 and \
               hy - HANDLE_SIZE // 2 <= mouse_y <= hy + HANDLE_SIZE // 2:
                self.active_handle_index = i
                return "handle"
        
        # Controlla il corpo del cerchio
        # Distanza dal centro al punto del mouse
        distance = math.sqrt((mouse_x - self.cx)**2 + (mouse_y - self.cy)**2)
        if distance <= self.radius:
            self.active_handle_index = -1
            return "body"
            
        self.active_handle_index = -1
        return None

    def update_coords(self, new_cx, new_cy, new_radius):
        """
        Aggiorna le coordinate del centro e il raggio del cerchio.
        """
        self.cx = new_cx
        self.cy = new_cy
        self.radius = max(new_radius, HANDLE_SIZE // 2) # Raggio minimo

# --- Classe per l'Ovale Interattivo ---
class InteractiveEllipse:
    """
    Rappresenta un ovale disegnabile e ridimensionabile su un canvas Tkinter.
    """
    def __init__(self, canvas, x1, y1, x2, y2, color=COLOR_ELLIPSE_BORDER, border_width=2, fill_color=""):
        self.canvas = canvas
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.color = color
        self.border_width = border_width
        self.fill_color = fill_color # Nuovo attributo per il colore di riempimento
        
        self.oval_id = None # ID dell'ovale disegnato sul canvas
        self.handle_ids = [] # Lista di ID delle maniglie
        self.active_handle_index = -1 # Indice della maniglia attiva

        self.start_drag_x = 0
        self.start_drag_y = 0

    def draw(self):
        """
        Disegna l'ovale e le sue maniglie sul canvas Tkinter.
        Rimuove le forme precedenti prima di ridisegnare.
        """
        self.delete_shapes()

        self.oval_id = self.canvas.create_oval(
            self.x1, self.y1, self.x2, self.y2,
            outline=self.color, width=self.border_width, fill=self.fill_color # Usa self.fill_color qui
        )

        # Disegna le maniglie
        self.handle_ids = []
        handles = self._get_handles_coords()
        for i, (hx, hy) in enumerate(handles):
            handle_color = COLOR_HANDLE_ACTIVE if i == self.active_handle_index else COLOR_HANDLE_NORMAL
            handle_id = self.canvas.create_rectangle(
                hx - HANDLE_SIZE // 2, hy - HANDLE_SIZE // 2,
                hx + HANDLE_SIZE // 2, hy + HANDLE_SIZE // 2,
                fill=handle_color, outline=handle_color
            )
            self.handle_ids.append(handle_id)

    def delete_shapes(self):
        """
        Rimuove l'ovale e tutte le sue maniglie dal canvas Tkinter.
        """
        if self.oval_id:
            self.canvas.delete(self.oval_id)
            self.oval_id = None
        for handle_id in self.handle_ids:
            self.canvas.delete(handle_id)
        self.handle_ids = []

    def _get_handles_coords(self):
        """
        Calcola e restituisce le coordinate centrali delle 8 maniglie per l'ovale (bounding box).
        """
        x1, y1, x2, y2 = self.x1, self.y1, self.x2, self.y2
        xm, ym = (x1 + x2) // 2, (y1 + y2) // 2
        
        return [
            (x1, y1), (xm, y1), (x2, y1), # Top-left, Top-mid, Top-right
            (x1, ym),                     # Mid-left
            (x2, ym),                     # Mid-right
            (x1, y2), (xm, y2), (x2, y2)  # Bottom-left, Bottom-mid, Bottom-right
        ]

    def check_hit(self, mouse_x, mouse_y):
        """
        Controlla se le coordinate del mouse colpiscono una maniglia o il corpo dell'ovale.
        Restituisce "handle" (con indice), "body" o None.
        """
        # Controlla le maniglie
        handles = self._get_handles_coords()
        for i, (hx, hy) in enumerate(handles):
            if hx - HANDLE_SIZE // 2 <= mouse_x <= hx + HANDLE_SIZE // 2 and \
               hy - HANDLE_SIZE // 2 <= mouse_y <= hy + HANDLE_SIZE // 2:
                self.active_handle_index = i
                return "handle"
        
        # Controlla il corpo dell'ovale (usando l'ID dell'ovale per hit detection)
        if self.oval_id:
            overlapping_objects = self.canvas.find_overlapping(mouse_x, mouse_y, mouse_x, mouse_y)
            if self.oval_id in overlapping_objects:
                self.active_handle_index = -1
                return "body"
            
        self.active_handle_index = -1
        return None

    def update_coords(self, new_x1, new_y1, new_x2, new_y2):
        """
        Aggiorna le coordinate del bounding box dell'ovale, assicurandosi che x1 <= x2 e y1 <= y2.
        """
        self.x1 = min(new_x1, new_x2)
        self.y1 = min(new_y1, new_y2)
        self.x2 = max(new_x1, new_x2)
        self.y2 = max(new_y1, new_y2)

# --- Classe per il Poligono Interattivo ---
class InteractivePolygon:
    """
    Rappresenta un poligono disegnabile e modificabile su un canvas Tkinter.
    """
    def __init__(self, canvas, points=None, color=COLOR_POLYGON_BORDER, border_width=2, fill_color=""):
        self.canvas = canvas
        # I punti sono una lista di tuple (x, y)
        self.points = points if points is not None else [] 
        self.color = color
        self.border_width = border_width
        self.fill_color = fill_color
        
        self.polygon_id = None # ID del poligono disegnato sul canvas
        self.handle_ids = [] # Lista di ID delle maniglie per i vertici
        self.active_handle_index = -1 # Indice del vertice attivo

        self.start_drag_x = 0
        self.start_drag_y = 0
        self.is_closed = False # Indica se il poligono è stato chiuso (es. con doppio clic)

    def add_point(self, x, y):
        """Aggiunge un punto al poligono."""
        self.points.append((x, y))

    def draw(self):
        """
        Disegna il poligono e le maniglie dei suoi vertici sul canvas Tkinter.
        Rimuove le forme precedenti prima di ridisegnare.
        """
        self.delete_shapes()

        if len(self.points) > 1:
            # Converte la lista di tuple (x,y) in una lista piatta [x1, y1, x2, y2, ...]
            flat_points = [coord for point in self.points for coord in point]
            
            self.polygon_id = self.canvas.create_polygon(
                *flat_points,
                outline=self.color, width=self.border_width, fill=self.fill_color
            )
            # Se il poligono è chiuso, assicurati che il riempimento sia applicato.
            # Altrimenti, non riempire (per visualizzare solo i segmenti durante il disegno).
            if self.is_closed and len(self.points) > 2:
                self.canvas.itemconfigure(self.polygon_id, fill=self.fill_color)
            else:
                self.canvas.itemconfigure(self.polygon_id, fill="") # Non riempire se non chiuso

        # Disegna le maniglie per ogni vertice
        self.handle_ids = []
        for i, (px, py) in enumerate(self.points):
            handle_color = COLOR_HANDLE_ACTIVE if i == self.active_handle_index else COLOR_POLYGON_VERTEX_HANDLE
            handle_id = self.canvas.create_rectangle(
                px - HANDLE_SIZE // 2, py - HANDLE_SIZE // 2,
                px + HANDLE_SIZE // 2, py + HANDLE_SIZE // 2,
                fill=handle_color, outline=handle_color
            )
            self.handle_ids.append(handle_id)

    def delete_shapes(self):
        """
        Rimuove il poligono e tutte le sue maniglie dal canvas Tkinter.
        """
        if self.polygon_id:
            self.canvas.delete(self.polygon_id)
            self.polygon_id = None
        for handle_id in self.handle_ids:
            self.canvas.delete(handle_id)
        self.handle_ids = []

    def check_hit(self, mouse_x, mouse_y):
        """
        Controlla se le coordinate del mouse colpiscono una maniglia (vertice) o il corpo del poligono.
        Restituisce "handle" (con indice), "body" o None.
        """
        # Controlla prima le maniglie (vertici)
        for i, (px, py) in enumerate(self.points):
            if px - HANDLE_SIZE // 2 <= mouse_x <= px + HANDLE_SIZE // 2 and \
               py - HANDLE_SIZE // 2 <= mouse_y <= py + HANDLE_SIZE // 2:
                self.active_handle_index = i
                return "handle" # Colpito un vertice
        
        # Controlla il corpo del poligono (solo se è chiuso e riempito)
        if self.polygon_id and self.is_closed and self.fill_color != "":
            overlapping_objects = self.canvas.find_overlapping(mouse_x, mouse_y, mouse_x, mouse_y)
            if self.polygon_id in overlapping_objects:
                self.active_handle_index = -1 # Nessun vertice attivo se clicco sul corpo
                return "body" # Colpito il corpo del poligono
            
        self.active_handle_index = -1
        return None # Nessun hit

    def update_point(self, index, new_x, new_y):
        """Aggiorna le coordinate di un vertice specifico."""
        if 0 <= index < len(self.points):
            self.points[index] = (new_x, new_y)

    def move_polygon(self, dx, dy):
        """Sposta l'intero poligono di dx, dy."""
        new_points = []
        for px, py in self.points:
            new_points.append((px + dx, py + dy))
        self.points = new_points

    def close_polygon(self):
        """Marca il poligono come chiuso."""
        if len(self.points) > 2:
            self.is_closed = True
            # Non aggiungiamo il primo punto alla fine qui, Tkinter lo chiude automaticamente
            # quando fill è specificato e i punti sono forniti.

# --- Classe per la Polilinea Interattiva (Linea Aperta) ---
class InteractivePolyline:
    """
    Rappresenta una polilinea disegnabile e modificabile su un canvas Tkinter.
    Non è una forma chiusa e non ha riempimento.
    """
    def __init__(self, canvas, points=None, color=COLOR_POLYLINE_BORDER, border_width=2):
        self.canvas = canvas
        self.points = points if points is not None else []
        self.color = color
        self.border_width = border_width
        
        self.line_id = None # ID della linea disegnata sul canvas
        self.handle_ids = [] # Lista di ID delle maniglie per i vertici
        self.active_handle_index = -1 # Indice del vertice attivo

        self.start_drag_x = 0
        self.start_drag_y = 0

    def add_point(self, x, y):
        """Aggiunge un punto alla polilinea."""
        self.points.append((x, y))

    def draw(self):
        """
        Disegna la polilinea e le maniglie dei suoi vertici sul canvas Tkinter.
        Rimuove le forme precedenti prima di ridisegnare.
        """
        self.delete_shapes()

        if len(self.points) > 1:
            flat_points = [coord for point in self.points for coord in point]
            self.line_id = self.canvas.create_line(
                *flat_points,
                fill=self.color, # Corretto da 'outline' a 'fill'
                width=self.border_width,
                smooth=False # smooth=False per segmenti dritti
            )

        # Disegna le maniglie per ogni vertice
        self.handle_ids = []
        for i, (px, py) in enumerate(self.points):
            handle_color = COLOR_HANDLE_ACTIVE if i == self.active_handle_index else COLOR_POLYLINE_VERTEX_HANDLE
            handle_id = self.canvas.create_rectangle(
                px - HANDLE_SIZE // 2, py - HANDLE_SIZE // 2,
                px + HANDLE_SIZE // 2, py + HANDLE_SIZE // 2,
                fill=handle_color, outline=handle_color
            )
            self.handle_ids.append(handle_id)

    def delete_shapes(self):
        """
        Rimuove la polilinea e tutte le sue maniglie dal canvas Tkinter.
        """
        if self.line_id:
            self.canvas.delete(self.line_id)
            self.line_id = None
        for handle_id in self.handle_ids:
            self.canvas.delete(handle_id)
        self.handle_ids = []

    def check_hit(self, mouse_x, mouse_y):
        """
        Controlla se le coordinate del mouse colpiscono una maniglia (vertice) o la linea della polilinea.
        Restituisce "handle" (con indice), "body" (se cliccato sulla linea) o None.
        """
        # Controlla prima le maniglie (vertici)
        for i, (px, py) in enumerate(self.points):
            if px - HANDLE_SIZE // 2 <= mouse_x <= px + HANDLE_SIZE // 2 and \
               py - HANDLE_SIZE // 2 <= mouse_y <= py + HANDLE_SIZE // 2:
                self.active_handle_index = i
                return "handle" # Colpito un vertice
        
        # Controlla se il clic è vicino alla linea (più complesso per le linee)
        # Per semplicità, useremo find_overlapping sul line_id, che funziona sul contorno.
        if self.line_id:
            overlapping_objects = self.canvas.find_overlapping(mouse_x, mouse_y, mouse_x, mouse_y)
            if self.line_id in overlapping_objects:
                self.active_handle_index = -1
                return "body" # Colpito il corpo della linea
            
        self.active_handle_index = -1
        return None

    def update_point(self, index, new_x, new_y):
        """Aggiorna le coordinate di un vertice specifico."""
        if 0 <= index < len(self.points):
            self.points[index] = (new_x, new_y)

    def move_polyline(self, dx, dy):
        """Sposta l'intera polilinea di dx, dy."""
        new_points = []
        for px, py in self.points:
            new_points.append((px + dx, py + dy))
        self.points = new_points

# --- Funzione Utility per convertire immagini OpenCV in PhotoImage per Tkinter ---
def cv2_to_tk_image(cv_image):
    """
    Converte un'immagine OpenCV (NumPy array BGR) in un oggetto PhotoImage di Tkinter.
    """
    # Converti da BGR a RGB (Pillow lavora con RGB)
    rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
    # Converti in immagine PIL (Pillow Image)
    pil_image = Image.fromarray(rgb_image)
    # Converti in PhotoImage per Tkinter
    tk_image = ImageTk.PhotoImage(pil_image)
    return tk_image

