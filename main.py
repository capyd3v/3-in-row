from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import uuid
import json
from typing import Dict, List
import time
import random

app = FastAPI(title="3 en Raya Online")

# Almacenamiento en memoria de salas y conexiones
conexiones: Dict[str, WebSocket] = {}

class SalaManager:
    def __init__(self):
        self.salas: Dict[str, Dict] = {}
    
    def crear_sala(self, clave: str, creador: str) -> str:
        sala_id = str(uuid.uuid4())[:8]
        # Asignar X al creador inicialmente
        self.salas[sala_id] = {
            "id": sala_id,
            "clave": clave,
            "jugadores": [creador],
            "simbolos": {creador: "X"},  # Mapeo jugador -> símbolo
            "tablero": [""] * 9,
            "turno": "X",  # Empezará con X
            "estado": "esperando",
            "ganador": None,
            "creador": creador,
            "timestamp": time.time()
        }
        print(f"Sala creada: {sala_id} por {creador} como X")
        return sala_id
    
    def unir_sala(self, sala_id: str, clave: str, jugador: str) -> Dict:
        sala = self.salas.get(sala_id)
        if not sala:
            return {"exito": False, "mensaje": "Sala no encontrada"}
        if sala["clave"] != clave:
            return {"exito": False, "mensaje": "Clave incorrecta"}
        if len(sala["jugadores"]) >= 2:
            return {"exito": False, "mensaje": "Sala llena"}
        if jugador in sala["jugadores"]:
            return {"exito": False, "mensaje": "Ya estás en esta sala"}
            
        # Asignar O al segundo jugador
        sala["jugadores"].append(jugador)
        sala["simbolos"][jugador] = "O"
        
        # Cuando se une el segundo jugador, decidir aleatoriamente quién empieza
        if len(sala["jugadores"]) == 2:
            # Elegir aleatoriamente quién empieza (X u O)
            primer_turno = random.choice(["X", "O"])
            sala["turno"] = primer_turno
            sala["estado"] = "jugando"
            print(f"Segundo jugador {jugador} unido como O. Turno inicial: {primer_turno}")
        
        return {"exito": True, "sala": sala}
    
    def obtener_simbolo_jugador(self, sala_id: str, jugador: str) -> str:
        """Obtener el símbolo (X/O) de un jugador"""
        sala = self.salas.get(sala_id)
        return sala["simbolos"].get(jugador) if sala else None
    
    def hacer_movimiento(self, sala_id: str, posicion: int, jugador: str) -> bool:
        sala = self.salas.get(sala_id)
        if not sala or sala["estado"] != "jugando":
            print(f"No se puede mover: sala no encontrada o no en juego")
            return False
        
        # Obtener símbolo del jugador
        simbolo_jugador = self.obtener_simbolo_jugador(sala_id, jugador)
        if not simbolo_jugador:
            print(f"Jugador {jugador} no encontrado en sala")
            return False
        
        # Verificar que es el turno del jugador
        if sala["turno"] != simbolo_jugador:
            print(f"No es turno de {jugador}. Turno actual: {sala['turno']}")
            return False
        
        # Verificar posición válida
        if posicion < 0 or posicion > 8 or sala["tablero"][posicion] != "":
            print(f"Posición {posicion} inválida o ocupada")
            return False
        
        print(f"Jugador {jugador} ({simbolo_jugador}) mueve en posición {posicion}")
        
        # Hacer movimiento
        sala["tablero"][posicion] = simbolo_jugador
        
        # Verificar ganador
        if self.verificar_ganador(sala["tablero"], simbolo_jugador):
            sala["estado"] = "terminado"
            sala["ganador"] = jugador
            print(f"¡{jugador} gana la partida!")
        elif all(celda != "" for celda in sala["tablero"]):
            sala["estado"] = "empate"
            print("¡Empate!")
        else:
            # Cambiar turno
            sala["turno"] = "O" if sala["turno"] == "X" else "X"
            print(f"Turno cambiado a: {sala['turno']}")
        
        return True
    
    def verificar_ganador(self, tablero: List[str], jugador: str) -> bool:
        lineas_ganadoras = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],
            [0, 3, 6], [1, 4, 7], [2, 5, 8],
            [0, 4, 8], [2, 4, 6]
        ]
        
        for linea in lineas_ganadoras:
            if all(tablero[pos] == jugador for pos in linea):
                return True
        return False
    
    def obtener_info_sala(self, sala_id: str) -> Dict:
        return self.salas.get(sala_id)
    
    def obtener_salas_publicas(self) -> List[Dict]:
        ahora = time.time()
        salas_publicas = []
        
        for sala_id, sala in self.salas.items():
            es_valida = (
                ahora - sala["timestamp"] < 600 and
                len(sala["jugadores"]) < 2 and 
                sala["estado"] == "esperando"
            )
            
            if es_valida:
                salas_publicas.append({
                    "id": sala["id"],
                    "jugadores": sala["jugadores"],
                    "creador": sala["creador"],
                    "cantidad_jugadores": len(sala["jugadores"])
                })
        
        return salas_publicas
    
    def eliminar_sala_antigua(self):
        ahora = time.time()
        salas_a_eliminar = []
        
        for sala_id, sala in self.salas.items():
            if ahora - sala["timestamp"] > 1800:
                salas_a_eliminar.append(sala_id)
        
        for sala_id in salas_a_eliminar:
            del self.salas[sala_id]

sala_manager = SalaManager()

async def enviar_a_todos_en_sala(sala_id: str, mensaje: dict):
    """Envía un mensaje a todos los jugadores en una sala"""
    sala = sala_manager.obtener_info_sala(sala_id)
    if sala:
        for jugador in sala["jugadores"]:
            if jugador in conexiones:
                try:
                    await conexiones[jugador].send_text(json.dumps(mensaje))
                    print(f"Mensaje enviado a {jugador}: {mensaje['tipo']}")
                except Exception as e:
                    print(f"Error enviando a {jugador}: {e}")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/favicon.ico")
async def favicon():
    return FileResponse("static/favicon.ico")

@app.websocket("/ws/{sala_id}/{jugador}")
async def websocket_endpoint(websocket: WebSocket, sala_id: str, jugador: str):
    await websocket.accept()
    
    # Guardar conexión
    if jugador != "temp" and jugador != "salas":
        conexiones[jugador] = websocket
        print(f"Jugador {jugador} conectado a sala {sala_id}")
    
    try:
        while True:
            data = await websocket.receive_text()
            mensaje = json.loads(data)
            
            if mensaje["tipo"] == "crear_sala":
                clave = mensaje["clave"]
                jugador_nombre = mensaje.get("jugador", jugador)
                sala_id_nueva = sala_manager.crear_sala(clave, jugador_nombre)
                await websocket.send_text(json.dumps({
                    "tipo": "sala_creada",
                    "sala_id": sala_id_nueva
                }))
            
            elif mensaje["tipo"] == "unir_sala":
                clave = mensaje["clave"]
                jugador_nombre = mensaje.get("jugador", jugador)
                resultado = sala_manager.unir_sala(sala_id, clave, jugador_nombre)
                
                if resultado["exito"]:
                    sala = resultado["sala"]
                    # Enviar estado actual al jugador que se unió
                    await websocket.send_text(json.dumps({
                        "tipo": "unido_exitoso",
                        "sala": sala,
                        "tu_simbolo": sala["simbolos"][jugador_nombre]
                    }))
                    
                    # Notificar a TODOS en la sala (incluyendo al creador)
                    await enviar_a_todos_en_sala(sala_id, {
                        "tipo": "estado_actualizado",
                        "sala": sala
                    })
                else:
                    await websocket.send_text(json.dumps({
                        "tipo": "error",
                        "mensaje": resultado["mensaje"]
                    }))
            
            elif mensaje["tipo"] == "movimiento":
                posicion = mensaje["posicion"]
                print(f"Recibido movimiento de {jugador} en posición {posicion}")
                
                if sala_manager.hacer_movimiento(sala_id, posicion, jugador):
                    sala = sala_manager.obtener_info_sala(sala_id)
                    # Notificar a todos en la sala
                    await enviar_a_todos_en_sala(sala_id, {
                        "tipo": "actualizar_tablero",
                        "tablero": sala["tablero"],
                        "turno": sala["turno"],
                        "estado": sala["estado"],
                        "ganador": sala["ganador"]
                    })
                else:
                    # Enviar error solo al jugador que intentó mover
                    await websocket.send_text(json.dumps({
                        "tipo": "error",
                        "mensaje": "Movimiento inválido. Verifica que es tu turno y la posición está vacía."
                    }))
            
            elif mensaje["tipo"] == "obtener_estado":
                sala = sala_manager.obtener_info_sala(sala_id)
                if sala:
                    simbolo_jugador = sala_manager.obtener_simbolo_jugador(sala_id, jugador)
                    await websocket.send_text(json.dumps({
                        "tipo": "estado_actual",
                        "sala": sala,
                        "tu_simbolo": simbolo_jugador
                    }))
            
            elif mensaje["tipo"] == "obtener_salas":
                sala_manager.eliminar_sala_antigua()
                salas_publicas = sala_manager.obtener_salas_publicas()
                await websocket.send_text(json.dumps({
                    "tipo": "lista_salas",
                    "salas": salas_publicas
                }))
    
    except WebSocketDisconnect:
        print(f"Jugador {jugador} desconectado")
        if jugador in conexiones:
            del conexiones[jugador]
        # Limpiar sala si está vacía
        sala = sala_manager.obtener_info_sala(sala_id)
        if sala and jugador in sala["jugadores"]:
            sala["jugadores"].remove(jugador)
            if jugador in sala["simbolos"]:
                del sala["simbolos"][jugador]
            if not sala["jugadores"]:
                sala_manager.eliminar_sala(sala_id)
            else:
                # Notificar al otro jugador que se desconectó
                await enviar_a_todos_en_sala(sala_id, {
                    "tipo": "jugador_desconectado",
                    "mensaje": f"El jugador {jugador} se ha desconectado"
                })

app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
