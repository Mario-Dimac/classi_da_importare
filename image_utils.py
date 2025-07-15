import cv2
import numpy as np

def create_blank_cv_image(width, height, color=(0, 0, 0)):
    """
    Crea un'immagine vuota (NumPy array) con le dimensioni e il colore di sfondo specificati.
    Args:
        width (int): Larghezza dell'immagine in pixel.
        height (int): Altezza dell'immagine in pixel.
        color (tuple): Colore di sfondo in formato BGR (es. (0,0,0) per nero, (255,255,255) per bianco).
    Returns:
        numpy.ndarray: L'immagine OpenCV creata.
    """
    # Crea un'immagine nera di base
    image = np.zeros((height, width, 3), dtype=np.uint8)
    # Riempie l'immagine con il colore specificato
    image[:] = color
    return image

def load_cv_image(path):
    """
    Carica un'immagine da un percorso specificato usando OpenCV.
    Args:
        path (str): Percorso del file immagine.
    Returns:
        numpy.ndarray or None: L'immagine OpenCV caricata, o None se il caricamento fallisce.
    """
    image = cv2.imread(path)
    if image is None:
        print(f"Errore: Impossibile caricare l'immagine da {path}")
    return image

