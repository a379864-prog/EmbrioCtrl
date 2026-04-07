
import math
import cv2
import mediapipe as mp

class detectormanos():
    def __init__(self, mode=False, maxManos=2, Confdeteccion=0.5, Confsegui=0.5):
        self.mode = bool(mode)
        self.maxManos = int(maxManos)  # ← Asegura que sea entero
        self.Confdeteccion = float(Confdeteccion)  # ← Asegura que sea float
        self.Confsegui = float(Confsegui)          # ← Asegura que sea float

        self.mpmanos = mp.solutions.hands
        self.manos = self.mpmanos.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.maxManos,
            min_detection_confidence=self.Confdeteccion,
            min_tracking_confidence=self.Confsegui
        )
        self.dibujo = mp.solutions.drawing_utils
        self.tip = [4, 8, 12, 16, 20]
        self.lista = []

    def encontrarmanos(self, frame, dibujar=True):
        imgcolor = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.resultados = self.manos.process(imgcolor)

        if self.resultados.multi_hand_landmarks:
            for mano in self.resultados.multi_hand_landmarks:
                if dibujar:
                    self.dibujo.draw_landmarks(frame, mano, self.mpmanos.HAND_CONNECTIONS)
        return frame

    def encontrarposicion(self, frame, ManoNum=0, dibujar=True):
        xlista = []
        ylista = []
        bbox = []
        self.lista = []

        if self.resultados.multi_hand_landmarks:
            miMano = self.resultados.multi_hand_landmarks[ManoNum]
            for id, lm in enumerate(miMano.landmark):
                alto, ancho, _ = frame.shape
                cx, cy = int(lm.x * ancho), int(lm.y * alto)
                xlista.append(cx)
                ylista.append(cy)
                self.lista.append([id, cx, cy])
                if dibujar:
                    cv2.circle(frame, (cx, cy), 5, (0, 0, 0), cv2.FILLED)

            xmin, xmax = min(xlista), max(xlista)
            ymin, ymax = min(ylista), max(ylista)
            bbox = xmin, ymin, xmax, ymax
            if dibujar:
                cv2.rectangle(frame, (xmin - 20, ymin - 20), (xmax + 20, ymax + 20), (0, 255, 9), 2)
        return self.lista, bbox

    def dedosarriba(self):
        dedos = []
        if not self.lista:
            return dedos

        # --- LÓGICA AMBIDIESTRA ---
        # Detectamos si es mano Derecha o Izquierda para ajustar el pulgar
        etiqueta = "Right" # Default
        try:
            if self.resultados.multi_handedness:
                etiqueta = self.resultados.multi_handedness[0].classification[0].label
        except:
            pass

        # Pulgar (Eje X)
        # Para mano DERECHA: Pulgar abierto si Tip < Nudillo (está a la izquierda)
        # Para mano IZQUIERDA: Pulgar abierto si Tip > Nudillo (está a la derecha)
        tip_x = self.lista[self.tip[0]][1]
        nudillo_x = self.lista[self.tip[0] - 1][1]

        if etiqueta == "Right":
            if tip_x < nudillo_x:
                dedos.append(1)
            else:
                dedos.append(0)
        else: # Left
            if tip_x > nudillo_x:
                dedos.append(1)
            else:
                dedos.append(0)

        # Otros 4 dedos (Eje Y - Vertical)
        # Esto no cambia entre zurdos y diestros
        for id in range(1, 5):
            if self.lista[self.tip[id]][2] < self.lista[self.tip[id] - 2][2]:
                dedos.append(1)
            else:
                dedos.append(0)
        return dedos

    def distancia(self, p1, p2, frame, dibujar=True, r=15, t=3):
        x1, y1 = self.lista[p1][1:]
        x2, y2 = self.lista[p2][1:]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        if dibujar:
            cv2.line(frame, (x1, y1), (x2, y2), (0, 0, 255), t)
            cv2.circle(frame, (x1, y1), r, (0, 0, 255), cv2.FILLED)
            cv2.circle(frame, (cx, cy), r, (0, 0, 255), cv2.FILLED)

        length = math.hypot(x2 - x1, y2 - y1)
        return length, frame, [x1, y1, x2, y2, cx, cy]