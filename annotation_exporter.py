import json
import math
from interactive_shapes import InteractiveRectangle, InteractiveCircle, InteractiveEllipse, InteractivePolygon, InteractivePolyline

def export_annotations_to_json(shapes, image_width, image_height, filename="annotations.json"):
    """
    Estrae le coordinate delle forme disegnate e le salva in un file JSON.
    Il formato JSON sarà strutturato per essere leggibile e potenzialmente convertibile
    in formati specifici per il training (es. YOLOv8).

    Args:
        shapes (list): Una lista di oggetti forma (InteractiveRectangle, InteractiveCircle, etc.).
        image_width (int): La larghezza dell'immagine su cui sono state disegnate le forme.
        image_height (int): L'altezza dell'immagine su cui sono state disegnate le forme.
        filename (str): Il nome del file JSON in cui salvare le annotazioni.
    """
    annotations_data = []

    for i, shape in enumerate(shapes):
        annotation = {
            "id": i,
            "type": "",
            "coordinates": {}
        }

        if isinstance(shape, InteractiveRectangle):
            annotation["type"] = "rectangle"
            annotation["coordinates"] = {
                "x1": int(shape.x1),
                "y1": int(shape.y1),
                "x2": int(shape.x2),
                "y2": int(shape.y2),
                "angle_rad": shape.angle, # Angolo in radianti
                "angle_deg": math.degrees(shape.angle) # Angolo in gradi per comodità
            }
            # Puoi anche aggiungere il centro normalizzato, larghezza e altezza per YOLO bounding box
            # cx_norm = ((shape.x1 + shape.x2) / 2) / image_width
            # cy_norm = ((shape.y1 + shape.y2) / 2) / image_height
            # w_norm = (shape.x2 - shape.x1) / image_width
            # h_norm = (shape.y2 - shape.y1) / image_height
            # annotation["yolo_bbox_normalized"] = [cx_norm, cy_norm, w_norm, h_norm]

        elif isinstance(shape, InteractiveCircle):
            annotation["type"] = "circle"
            annotation["coordinates"] = {
                "cx": int(shape.cx),
                "cy": int(shape.cy),
                "radius": int(shape.radius)
            }

        elif isinstance(shape, InteractiveEllipse):
            annotation["type"] = "ellipse"
            annotation["coordinates"] = {
                "x1": int(shape.x1),
                "y1": int(shape.y1),
                "x2": int(shape.x2),
                "y2": int(shape.y2)
            }

        elif isinstance(shape, InteractivePolygon):
            annotation["type"] = "polygon"
            # I poligoni per YOLOv8 segmentation sono spesso una lista piatta di coordinate normalizzate
            # Esempio: [x1_norm, y1_norm, x2_norm, y2_norm, ...]
            
            # Qui estraiamo i punti come lista di tuple (x, y)
            annotation["coordinates"] = [
                (int(p[0]), int(p[1])) for p in shape.points
            ]
            # Se il poligono è chiuso, puoi indicarlo
            annotation["is_closed"] = shape.is_closed

        elif isinstance(shape, InteractivePolyline):
            annotation["type"] = "polyline"
            annotation["coordinates"] = [
                (int(p[0]), int(p[1])) for p in shape.points
            ]
            # Le polilinee sono per definizione aperte, non hanno is_closed

        annotations_data.append(annotation)

    try:
        with open(filename, 'w') as f:
            json.dump(annotations_data, f, indent=4)
        print(f"Annotazioni esportate con successo in {filename}")
    except IOError as e:
        print(f"Errore durante l'esportazione delle annotazioni: {e}")

