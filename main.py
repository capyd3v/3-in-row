from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uuid
import json
from typing import Dict, List

app = FastAPI(title="3 en Raya Online")

# Almacenamiento en memoria de salas y conexiones
salas: Dict[str, Dict] = {}
conexiones: Dict[str, WebSocket] = {}

class SalaManager:
    def __init__(self):
        self.salas: Dict[str, Dict] = {}
    
    def crear_sala(self, clave: str, creador: str) -> str:
        sala_id = str(uuid.uuid4())[:8]
        self.salas[sala_id] = {
            "id": sala_id,
            "clave": clave,
            "jugadores": [creador],
            "tablero": [""] * 9,
            "turno": "X",
            "estado": "esperando",
            "ganador": None,
            "creador": creador
        }
        return sala_id
    
    def unir_sala(self, sala_id: str, clave: str, jugador: str) -> bool:
        sala = self.salas.get(sala_id)
        if not sala:
            return False
        if sala["clave"] != clave:
            return False
        if len(sala["jugadores"]) >= 2:
            return False
        if jugador in sala["jugadores"]:
            return False
            
        sala["jugadores"].append(jugador)
        if len(sala["jugadores"]) == 2:
            sala["estado"] = "jugando"
        return True
    
    def hacer_movimiento(self, sala_id: str, posicion: int, jugador: str) -> bool:
        sala = self.salas.get(sala_id)
        if not sala or sala["estado"] != "jugando":
            return False
        
        # Verificar turno
        jugador_index = sala["jugadores"].index(jugador)
        simbolo_actual = "X" if jugador_index == 0 else "O"
        
        if sala["turno"] != simbolo_actual:
            return False
        
        # Verificar posición válida
        if posicion < 0 or posicion > 8 or sala["tablero"][posicion] != "":
            return False
        
        # Hacer movimiento
        sala["tablero"][posicion] = sala["turno"]
        
        # Verificar ganador
        if self.verificar_ganador(sala["tablero"], sala["turno"]):
            sala["estado"] = "terminado"
            sala["ganador"] = jugador
        elif all(celda != "" for celda in sala["tablero"]):
            sala["estado"] = "empate"
        else:
            # Cambiar turno
            sala["turno"] = "O" if sala["turno"] == "X" else "X"
        
        return True
    
    def verificar_ganador(self, tablero: List[str], jugador: str) -> bool:
        # Combinaciones ganadoras
        lineas_ganadoras = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Horizontales
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Verticales
            [0, 4, 8], [2, 4, 6]              # Diagonales
        ]
        
        for linea in lineas_ganadoras:
            if all(tablero[pos] == jugador for pos in linea):
                return True
        return False
    
    def obtener_info_sala(self, sala_id: str) -> Dict:
        return self.salas.get(sala_id)
    
    def eliminar_sala(self, sala_id: str):
        if sala_id in self.salas:
            del self.salas[sala_id]

sala_manager = SalaManager()

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.websocket("/ws/{sala_id}/{jugador}")
async def websocket_endpoint(websocket: WebSocket, sala_id: str, jugador: str):
    await websocket.accept()
    conexiones[jugador] = websocket
    
    try:
        while True:
            data = await websocket.receive_text()
            mensaje = json.loads(data)
            
            if mensaje["tipo"] == "crear_sala":
                clave = mensaje["clave"]
                sala_id = sala_manager.crear_sala(clave, jugador)
                await websocket.send_text(json.dumps({
                    "tipo": "sala_creada",
                    "sala_id": sala_id
                }))
            
            elif mensaje["tipo"] == "unir_sala":
                clave = mensaje["clave"]
                if sala_manager.unir_sala(sala_id, clave, jugador):
                    # Notificar a todos en la sala
                    sala = sala_manager.obtener_info_sala(sala_id)
                    for j in sala["jugadores"]:
                        if j in conexiones:
                            await conexiones[j].send_text(json.dumps({
                                "tipo": "jugador_unido",
                                "jugadores": sala["jugadores"],
                                "estado": sala["estado"]
                            }))
                else:
                    await websocket.send_text(json.dumps({
                        "tipo": "error",
                        "mensaje": "No se pudo unir a la sala"
                    }))
            
            elif mensaje["tipo"] == "movimiento":
                posicion = mensaje["posicion"]
                if sala_manager.hacer_movimiento(sala_id, posicion, jugador):
                    sala = sala_manager.obtener_info_sala(sala_id)
                    # Notificar a todos en la sala
                    for j in sala["jugadores"]:
                        if j in conexiones:
                            await conexiones[j].send_text(json.dumps({
                                "tipo": "actualizar_tablero",
                                "tablero": sala["tablero"],
                                "turno": sala["turno"],
                                "estado": sala["estado"],
                                "ganador": sala["ganador"]
                            }))
            
            elif mensaje["tipo"] == "obtener_estado":
                sala = sala_manager.obtener_info_sala(sala_id)
                if sala:
                    await websocket.send_text(json.dumps({
                        "tipo": "estado_actual",
                        "sala": sala
                    }))
    
    except WebSocketDisconnect:
        del conexiones[jugador]
        # Limpiar sala si está vacía
        sala = sala_manager.obtener_info_sala(sala_id)
        if sala and jugador in sala["jugadores"]:
            sala["jugadores"].remove(jugador)
            if not sala["jugadores"]:
                sala_manager.eliminar_sala(sala_id)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
