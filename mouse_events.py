import tkinter as tk
# Importa le classi e le costanti necessarie dal modulo interactive_shapes
from interactive_shapes import InteractiveRectangle, InteractiveCircle, InteractiveEllipse, InteractivePolygon, InteractivePolyline, HANDLE_SIZE, ROTATION_HANDLE_OFFSET
import math # Necessario per calcoli di distanza/raggio per cerchi/ovali

class MouseEventHandler:
    """
    Gestisce gli eventi del mouse per l'applicazione di editing di immagini.
    Questa classe incapsula la logica di disegno, spostamento, ridimensionamento e rotazione delle forme.
    """
    def __init__(self, app_instance):
        """
        Inizializza il gestore eventi del mouse con un riferimento all'istanza dell'applicazione principale.
        Args:
            app_instance: L'istanza di ImageEditorApp a cui questo gestore eventi è collegato.
        """
        self.app = app_instance # Riferimento all'istanza di ImageEditorApp

    def on_mouse_down(self, event):
        """
        Gestisce l'evento di pressione del tasto del mouse.
        Inizia il disegno di una nuova forma, lo spostamento o il ridimensionamento/rotazione di una esistente.
        """
        self.app.start_x, self.app.start_y = event.x, event.y
        
        found_existing = False
        # Controlla se il clic è avvenuto su una forma esistente o una delle sue maniglie
        # Itera su tutte le forme, dal più recente al più vecchio (per selezionare quello in cima)
        # Questo è importante per la selezione di forme sovrapposte
        for shape in reversed(self.app.shapes): 
            hit_type = shape.check_hit(event.x, event.y)
            if hit_type == "handle":
                self.app.active_shape = shape 
                # La logica di trascinamento dipende dal tipo di forma e dalla maniglia
                if isinstance(shape, InteractiveRectangle) and shape.active_handle_index == 8:
                    self.app.drag_state = "rotate_rect"
                    self.app.active_shape.start_drag_x = event.x
                    self.app.active_shape.start_drag_y = event.y
                    self.app.active_shape.start_angle = self.app.active_shape.angle
                elif isinstance(shape, (InteractivePolygon, InteractivePolyline)):
                    self.app.drag_state = "move_vertex" # Spostamento di un vertice del poligono/polilinea
                else:
                    self.app.drag_state = "resize_shape" # Stato generico per ridimensionamento
                found_existing = True
                break
            elif hit_type == "body":
                self.app.active_shape = shape
                self.app.drag_state = "move_shape" # Stato generico per spostamento
                # Memorizza il punto di partenza relativo alla forma per il movimento
                if isinstance(shape, (InteractiveRectangle, InteractiveEllipse)):
                    self.app.active_shape.start_drag_x = event.x - shape.x1
                    self.app.active_shape.start_drag_y = event.y - shape.y1
                elif isinstance(shape, InteractiveCircle):
                    self.app.active_shape.start_drag_x = event.x - shape.cx
                    self.app.active_shape.start_drag_y = event.y - shape.cy
                elif isinstance(shape, (InteractivePolygon, InteractivePolyline)):
                    # Per poligoni/polilinee, start_drag_x/y sono usati per calcolare lo spostamento relativo
                    self.app.active_shape.start_drag_x = event.x
                    self.app.active_shape.start_drag_y = event.y
                found_existing = True
                break
        
        # Se non abbiamo cliccato su una forma esistente, creane una nuova in base alla modalità corrente
        if not found_existing:
            # Colore di riempimento per le nuove forme (leggermente visibile per cliccabilità)
            fill_color_for_new_shape = "#F0F0F0" # Un grigio molto chiaro
            
            if self.app.current_draw_mode == "rectangle":
                self.app.active_shape = InteractiveRectangle(self.app.canvas, event.x, event.y, event.x + 1, event.y + 1, fill_color=fill_color_for_new_shape)
                self.app.drag_state = "new_rect"
            elif self.app.current_draw_mode == "circle":
                self.app.active_shape = InteractiveCircle(self.app.canvas, event.x, event.y, 1, fill_color=fill_color_for_new_shape) # Inizia con raggio 1
                self.app.drag_state = "new_circle"
            elif self.app.current_draw_mode == "ellipse":
                self.app.active_shape = InteractiveEllipse(self.app.canvas, event.x, event.y, event.x + 1, event.y + 1, fill_color=fill_color_for_new_shape)
                self.app.drag_state = "new_ellipse"
            elif self.app.current_draw_mode == "polygon":
                # Se è la prima volta che clicchiamo per un poligono, creane uno nuovo
                if not isinstance(self.app.active_shape, InteractivePolygon) or self.app.active_shape.is_closed:
                    self.app.active_shape = InteractivePolygon(self.app.canvas, points=[(event.x, event.y)], fill_color=fill_color_for_new_shape)
                    self.app.shapes.append(self.app.active_shape)
                # Altrimenti, aggiungi un punto al poligono attivo (se non è chiuso)
                else:
                    self.app.active_shape.add_point(event.x, event.y)
                self.app.drag_state = "drawing_polygon" # Stato specifico per il disegno del poligono
            elif self.app.current_draw_mode == "polyline":
                # Se è la prima volta che clicchiamo per una polilinea, creane una nuova
                if not isinstance(self.app.active_shape, InteractivePolyline):
                    self.app.active_shape = InteractivePolyline(self.app.canvas, points=[(event.x, event.y)])
                    self.app.shapes.append(self.app.active_shape)
                # Altrimenti, aggiungi un punto alla polilinea attiva
                else:
                    self.app.active_shape.add_point(event.x, event.y)
                self.app.drag_state = "drawing_polyline" # Stato specifico per il disegno della polilinea
            
            # Solo aggiungi la forma alla lista se non è una forma multi-punto in fase di disegno continuo
            if self.app.active_shape and self.app.drag_state not in ["drawing_polygon", "drawing_polyline"]: 
                self.app.shapes.append(self.app.active_shape) 

        # Disegna immediatamente tutte le forme per mostrare lo stato attivo
        self.app.draw_all_shapes()


    def on_mouse_drag(self, event):
        """
        Gestisce l'evento di trascinamento del mouse (mouse mosso con tasto premuto).
        Aggiorna la posizione o le dimensioni della forma attiva.
        """
        if self.app.active_shape:
            current_x, current_y = event.x, event.y

            if self.app.drag_state == "new_rect":
                self.app.active_shape.update_coords(self.app.start_x, self.app.start_y, current_x, current_y)
            elif self.app.drag_state == "new_circle":
                # Calcola il raggio dal punto iniziale al punto corrente
                radius = int(math.sqrt((current_x - self.app.start_x)**2 + (current_y - self.app.start_y)**2))
                self.app.active_shape.update_coords(self.app.start_x, self.app.start_y, radius)
            elif self.app.drag_state == "new_ellipse":
                self.app.active_shape.update_coords(self.app.start_x, self.app.start_y, current_x, current_y)
            elif self.app.drag_state == "drawing_polygon":
                # Aggiorna l'ultimo punto del poligono mentre si trascina
                if self.app.active_shape.points:
                    self.app.active_shape.update_point(len(self.app.active_shape.points) - 1, current_x, current_y)
            elif self.app.drag_state == "drawing_polyline":
                # Aggiorna l'ultimo punto della polilinea mentre si trascina
                if self.app.active_shape.points:
                    self.app.active_shape.update_point(len(self.app.active_shape.points) - 1, current_x, current_y)
            
            elif self.app.drag_state == "move_shape":
                # Sposta la forma in base alla nuova posizione del mouse
                if isinstance(self.app.active_shape, (InteractiveRectangle, InteractiveEllipse)):
                    new_x1 = current_x - self.app.active_shape.start_drag_x
                    new_y1 = current_y - self.app.active_shape.start_drag_y
                    new_x2 = new_x1 + (self.app.active_shape.x2 - self.app.active_shape.x1)
                    new_y2 = new_y1 + (self.app.active_shape.y2 - self.app.active_shape.y1)
                    self.app.active_shape.update_coords(new_x1, new_y1, new_x2, new_y2)
                elif isinstance(self.app.active_shape, InteractiveCircle):
                    new_cx = current_x - self.app.active_shape.start_drag_x
                    new_cy = current_y - self.app.active_shape.start_drag_y
                    self.app.active_shape.update_coords(new_cx, new_cy, self.app.active_shape.radius)
                elif isinstance(self.app.active_shape, (InteractivePolygon, InteractivePolyline)):
                    dx = current_x - self.app.active_shape.start_drag_x
                    dy = current_y - self.app.active_shape.start_drag_y
                    self.app.active_shape.move_polygon(dx, dy) if isinstance(self.app.active_shape, InteractivePolygon) else self.app.active_shape.move_polyline(dx, dy)
                    self.app.active_shape.start_drag_x = current_x # Aggiorna il punto di partenza per il prossimo drag
                    self.app.active_shape.start_drag_y = current_y
            
            elif self.app.drag_state == "resize_shape":
                h_idx = self.app.active_shape.active_handle_index
                
                if isinstance(self.app.active_shape, (InteractiveRectangle, InteractiveEllipse)):
                    x1, y1, x2, y2 = self.app.active_shape.x1, self.app.active_shape.y1, \
                                     self.app.active_shape.x2, self.app.active_shape.y2
                    
                    # Calcola le nuove coordinate in base alla maniglia trascinata
                    if h_idx == 0: x1, y1 = current_x, current_y
                    elif h_idx == 1: y1 = current_y
                    elif h_idx == 2: x2, y1 = current_x, current_y
                    elif h_idx == 3: x1 = current_x
                    elif h_idx == 4: x2 = current_x
                    elif h_idx == 5: x1, y2 = current_x, current_y
                    elif h_idx == 6: y2 = current_y
                    elif h_idx == 7: x2, y2 = current_x, current_y
                    
                    self.app.active_shape.update_coords(x1, y1, x2, y2)
                    
                    # Assicurati che le dimensioni minime siano rispettate
                    if self.app.active_shape.x2 - self.app.active_shape.x1 < HANDLE_SIZE:
                        if h_idx in [0, 3, 5]: 
                            self.app.active_shape.x1 = self.app.active_shape.x2 - HANDLE_SIZE
                        else: 
                            self.app.active_shape.x2 = self.app.active_shape.x1 + HANDLE_SIZE
                    
                    if self.app.active_shape.y2 - self.app.active_shape.y1 < HANDLE_SIZE:
                        if h_idx in [0, 1, 2]: 
                            self.app.active_shape.y1 = self.app.active_shape.y2 - HANDLE_SIZE
                        else: 
                            self.app.active_shape.y2 = self.app.active_shape.y1 + HANDLE_SIZE
                
                elif isinstance(self.app.active_shape, InteractiveCircle):
                    # Per il cerchio, ridimensiona il raggio in base alla maniglia
                    # Calcola il raggio dal centro al punto corrente del mouse
                    cx, cy = self.app.active_shape.cx, self.app.active_shape.cy
                    new_radius = int(math.sqrt((current_x - cx)**2 + (current_y - cy)**2))
                    self.app.active_shape.update_coords(cx, cy, new_radius)

            elif self.app.drag_state == "move_vertex":
                # Sposta il vertice attivo del poligono/polilinea
                if isinstance(self.app.active_shape, (InteractivePolygon, InteractivePolyline)):
                    h_idx = self.app.active_shape.active_handle_index
                    self.app.active_shape.update_point(h_idx, current_x, current_y)

            elif self.app.drag_state == "rotate_rect":
                # Solo i rettangoli interattivi hanno il metodo rotate
                if isinstance(self.app.active_shape, InteractiveRectangle):
                    self.app.active_shape.rotate(current_x, current_y)

            self.app.draw_all_shapes() # Ridisegna per mostrare l'anteprima dinamica

    def on_mouse_up(self, event):
        """
        Gestisce l'evento di rilascio del tasto del mouse.
        Finalizza l'operazione di disegno, spostamento o ridimensionamento.
        """
        if self.app.active_shape:
            # Logica di finalizzazione per rettangolo/ovale (bounding box)
            if isinstance(self.app.active_shape, (InteractiveRectangle, InteractiveEllipse)):
                
                if self.app.active_shape.x2 - self.app.active_shape.x1 < HANDLE_SIZE:
                    if self.app.active_shape.x1 == self.app.start_x: 
                        self.app.active_shape.x2 = self.app.active_shape.x1 + HANDLE_SIZE
                    else: 
                        self.app.active_shape.x1 = self.app.active_shape.x2 - HANDLE_SIZE

                if self.app.active_shape.y2 - self.app.active_shape.y1 < HANDLE_SIZE:
                    if self.app.active_shape.y1 == self.app.start_y: 
                        self.app.active_shape.y2 = self.app.active_shape.y1 + HANDLE_SIZE
                    else: 
                        self.app.active_shape.y1 = self.app.active_shape.y2 - HANDLE_SIZE
            
            # Logica di finalizzazione per il cerchio
            elif isinstance(self.app.active_shape, InteractiveCircle):
                if self.app.active_shape.radius < HANDLE_SIZE // 2:
                    self.app.active_shape.radius = HANDLE_SIZE // 2 # Raggio minimo

            # Per i poligoni e polilinee, non resettiamo active_shape o drag_state su mouse_up
            # se siamo in modalità di disegno continuo.
            if self.app.drag_state in ["drawing_polygon", "drawing_polyline"]:
                # Non fare nulla qui, la forma rimane attiva per aggiungere altri punti
                pass
            else:
                self.app.active_shape.active_handle_index = -1 # Resetta l'indice della maniglia attiva
                self.app.draw_all_shapes() # Ridisegna la forma nella sua posizione/dimensione finale
                self.app.active_shape = None # Nessuna forma è più attiva
                self.app.drag_state = None       # Resetta lo stato di trascinamento

    def on_mouse_double_click(self, event):
        """
        Gestisce il doppio clic del mouse, usato per chiudere il poligono o finalizzare la polilinea.
        """
        if self.app.current_draw_mode == "polygon" and \
           isinstance(self.app.active_shape, InteractivePolygon) and \
           not self.app.active_shape.is_closed:
            
            self.app.active_shape.close_polygon()
            self.app.draw_all_shapes()
            self.app.active_shape = None # Il poligono è chiuso, non più attivo per il disegno
            self.app.drag_state = None
        elif self.app.current_draw_mode == "polyline" and \
             isinstance(self.app.active_shape, InteractivePolyline):
            # Finalizza la polilinea (non c'è un metodo 'close' formale, ma la si "termina")
            self.app.active_shape.active_handle_index = -1
            self.app.draw_all_shapes()
            self.app.active_shape = None # La polilinea è terminata
            self.app.drag_state = None
