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
# Mapeo de jugador a sala actual
jugador_sala: Dict[str, str] = {}

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
            "timestamp": time.time(),
            # Nuevos campos para reinicio y marcador
            "reinicio_pendiente": [],
            "marcador": {creador: 0},  # Victorias por jugador
            "partidas_jugadas": 0
        }
        print(f"Sala creada: {sala_id} por {creador} como X")
        print(f"Simbolos en sala: {self.salas[sala_id]['simbolos']}")
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
        # Inicializar marcador para el nuevo jugador
        sala["marcador"][jugador] = 0
        
        # Cuando se une el segundo jugador, decidir aleatoriamente quién empieza
        if len(sala["jugadores"]) == 2:
            # Elegir aleatoriamente quién empieza (X u O)
            primer_turno = random.choice(["X", "O"])
            sala["turno"] = primer_turno
            sala["estado"] = "jugando"
            print(f"Segundo jugador {jugador} unido como O. Turno inicial: {primer_turno}")
            print(f"Simbolos actualizados: {sala['simbolos']}")
        
        return {"exito": True, "sala": sala}
    
    def obtener_simbolo_jugador(self, sala_id: str, jugador: str) -> str:
        """Obtener el símbolo (X/O) de un jugador"""
        sala = self.salas.get(sala_id)
        if not sala:
            print(f"Sala {sala_id} no encontrada para jugador {jugador}")
            return None
        
        simbolo = sala["simbolos"].get(jugador)
        print(f"Obteniendo símbolo para {jugador} en sala {sala_id}: {simbolo}")
        print(f"Simbolos disponibles: {sala['simbolos']}")
        return simbolo
    
    def hacer_movimiento(self, sala_id: str, posicion: int, jugador: str) -> bool:
        sala = self.salas.get(sala_id)
        if not sala:
            print(f"Sala {sala_id} no encontrada")
            return False
        
        if sala["estado"] != "jugando":
            print(f"Sala no está en estado 'jugando'. Estado actual: {sala['estado']}")
            return False
        
        # Obtener símbolo del jugador
        simbolo_jugador = self.obtener_simbolo_jugador(sala_id, jugador)
        if not simbolo_jugador:
            print(f"Jugador {jugador} no tiene símbolo asignado en sala {sala_id}")
            return False
        
        print(f"Intentando movimiento: Jugador {jugador} ({simbolo_jugador}) en posición {posicion}")
        print(f"Turno actual: {sala['turno']}")
        print(f"Tablero actual: {sala['tablero']}")
        
        # Verificar que es el turno del jugador
        if sala["turno"] != simbolo_jugador:
            print(f"No es turno de {jugador}. Turno actual: {sala['turno']}, Símbolo jugador: {simbolo_jugador}")
            return False
        
        # Verificar posición válida
        if posicion < 0 or posicion > 8:
            print(f"Posición {posicion} fuera de rango")
            return False
        
        if sala["tablero"][posicion] != "":
            print(f"Posición {posicion} ya ocupada por: {sala['tablero'][posicion]}")
            return False
        
        print(f"Movimiento válido. Jugador {jugador} ({simbolo_jugador}) mueve en posición {posicion}")
        
        # Hacer movimiento
        sala["tablero"][posicion] = simbolo_jugador
        print(f"Tablero después del movimiento: {sala['tablero']}")
        
        # Verificar ganador
        if self.verificar_ganador(sala["tablero"], simbolo_jugador):
            sala["estado"] = "terminado"
            sala["ganador"] = jugador
            # Incrementar marcador del ganador - CORRECCIÓN: usar el nombre del jugador directamente
            if jugador in sala["marcador"]:
                sala["marcador"][jugador] += 1
            else:
                sala["marcador"][jugador] = 1
            sala["partidas_jugadas"] += 1
            print(f"¡{jugador} gana la partida! Marcador: {sala['marcador']}")
        elif all(celda != "" for celda in sala["tablero"]):
            sala["estado"] = "empate"
            sala["partidas_jugadas"] += 1
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
    
    def solicitar_reinicio(self, sala_id: str, jugador: str) -> Dict:
        """Solicitar reinicio de partida"""
        sala = self.salas.get(sala_id)
        if not sala:
            return {"exito": False, "mensaje": "Sala no encontrada"}
        
        if sala["estado"] not in ["terminado", "empate"]:
            return {"exito": False, "mensaje": "La partida no ha terminado"}
        
        if jugador not in sala["reinicio_pendiente"]:
            sala["reinicio_pendiente"].append(jugador)
            print(f"Jugador {jugador} solicita reinicio. Pendientes: {sala['reinicio_pendiente']}")
        
        # Verificar si ambos jugadores han aceptado el reinicio
        if len(sala["reinicio_pendiente"]) == 2:
            # Reiniciar partida
            self.reiniciar_partida(sala_id)
            return {"exito": True, "reiniciado": True, "sala": sala}
        else:
            # Encontrar quién falta por aceptar
            jugadores_faltantes = [j for j in sala["jugadores"] if j not in sala["reinicio_pendiente"]]
            return {"exito": True, "reiniciado": False, "faltante": jugadores_faltantes[0] if jugadores_faltantes else None}
    
    def reiniciar_partida(self, sala_id: str):
        """Reiniciar completamente la partida"""
        sala = self.salas.get(sala_id)
        if not sala:
            return
        
        # Limpiar tablero
        sala["tablero"] = [""] * 9
        
        # Reiniciar estado de reinicio
        sala["reinicio_pendiente"] = []
        
        # Intercambiar símbolos para dar ventaja al que perdió
        if sala["ganador"] and len(sala["jugadores"]) == 2:
            # El ganador anterior ahora será O, el perdedor será X
            ganador_anterior = sala["ganador"]
            perdedor = [j for j in sala["jugadores"] if j != ganador_anterior][0]
            
            sala["simbolos"][ganador_anterior] = "O"
            sala["simbolos"][perdedor] = "X"
            # El que perdió empieza (el que ahora tiene X)
            sala["turno"] = "X"
        else:
            # En caso de empate o primera partida, alternar aleatoriamente
            simbolos = ["X", "O"]
            random.shuffle(simbolos)
            for i, jugador in enumerate(sala["jugadores"]):
                sala["simbolos"][jugador] = simbolos[i]
            # El que tiene X empieza
            sala["turno"] = "X"
        
        sala["estado"] = "jugando"
        sala["ganador"] = None
        
        print(f"Partida reiniciada en sala {sala_id}. Nuevos símbolos: {sala['simbolos']}, Turno: {sala['turno']}")
    
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
    
    def eliminar_sala(self, sala_id: str):
        """Eliminar una sala específica"""
        if sala_id in self.salas:
            del self.salas[sala_id]
            print(f"Sala {sala_id} eliminada")

sala_manager = SalaManager()

async def enviar_a_todos_en_sala(sala_id: str, mensaje: dict):
    """Envía un mensaje a todos los jugadores en una sala"""
    sala = sala_manager.obtener_info_sala(sala_id)
    if sala:
        for jugador in sala["jugadores"]:
            if jugador in conexiones:
                try:
                    await conexiones[jugador].send_text(json.dumps(mensaje))
                    print(f"Mensaje {mensaje['tipo']} enviado a {jugador}")
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
        jugador_sala[jugador] = sala_id  # Registrar la sala actual del jugador
        print(f"Jugador {jugador} conectado a sala {sala_id}")
    
    try:
        while True:
            data = await websocket.receive_text()
            mensaje = json.loads(data)
            
            if mensaje["tipo"] == "crear_sala":
                clave = mensaje["clave"]
                jugador_nombre = mensaje.get("jugador", jugador)
                sala_id_nueva = sala_manager.crear_sala(clave, jugador_nombre)
                
                # Actualizar la sala del jugador
                jugador_sala[jugador_nombre] = sala_id_nueva
                
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
                    simbolo_jugador = sala_manager.obtener_simbolo_jugador(sala_id, jugador_nombre)
                    
                    # Actualizar la sala del jugador
                    jugador_sala[jugador_nombre] = sala_id
                    
                    # Enviar estado actual al jugador que se unió
                    await websocket.send_text(json.dumps({
                        "tipo": "unido_exitoso",
                        "sala": sala,
                        "tu_simbolo": simbolo_jugador
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
                
                # Obtener la sala REAL del jugador (no la del WebSocket)
                sala_id_real = jugador_sala.get(jugador)
                if not sala_id_real:
                    await websocket.send_text(json.dumps({
                        "tipo": "error",
                        "mensaje": "No estás en ninguna sala"
                    }))
                    continue
                
                print(f"Jugador {jugador} está en sala real: {sala_id_real}")
                
                # Verificar que la sala existe
                sala = sala_manager.obtener_info_sala(sala_id_real)
                if not sala:
                    await websocket.send_text(json.dumps({
                        "tipo": "error",
                        "mensaje": "Sala no encontrada"
                    }))
                    continue
                
                # Verificar que el jugador está en la sala
                if jugador not in sala["jugadores"]:
                    await websocket.send_text(json.dumps({
                        "tipo": "error", 
                        "mensaje": "No estás en esta sala"
                    }))
                    continue
                
                if sala_manager.hacer_movimiento(sala_id_real, posicion, jugador):
                    sala = sala_manager.obtener_info_sala(sala_id_real)
                    # Notificar a todos en la sala
                    await enviar_a_todos_en_sala(sala_id_real, {
                        "tipo": "actualizar_tablero",
                        "tablero": sala["tablero"],
                        "turno": sala["turno"],
                        "estado": sala["estado"],
                        "ganador": sala["ganador"],
                        "marcador": sala["marcador"],
                        "partidas_jugadas": sala["partidas_jugadas"]
                    })
                else:
                    # Obtener información de debug para el error
                    sala = sala_manager.obtener_info_sala(sala_id_real)
                    simbolo_jugador = sala_manager.obtener_simbolo_jugador(sala_id_real, jugador)
                    
                    error_msg = f"Movimiento inválido. Turno actual: {sala['turno']}, Tu símbolo: {simbolo_jugador}"
                    print(f"Error: {error_msg}")
                    
                    # Enviar error solo al jugador que intentó mover
                    await websocket.send_text(json.dumps({
                        "tipo": "error",
                        "mensaje": error_msg
                    }))
            
            elif mensaje["tipo"] == "solicitar_reinicio":
                # Obtener la sala REAL del jugador
                sala_id_real = jugador_sala.get(jugador)
                if not sala_id_real:
                    await websocket.send_text(json.dumps({
                        "tipo": "error",
                        "mensaje": "No estás en ninguna sala"
                    }))
                    continue
                
                resultado = sala_manager.solicitar_reinicio(sala_id_real, jugador)
                
                if resultado["exito"]:
                    if resultado.get("reiniciado"):
                        # Partida reiniciada, enviar nuevo estado a todos
                        sala = sala_manager.obtener_info_sala(sala_id_real)
                        await enviar_a_todos_en_sala(sala_id_real, {
                            "tipo": "partida_reiniciada",
                            "sala": sala,
                            "marcador": sala["marcador"]
                        })
                    else:
                        # Solo un jugador ha aceptado, notificar a todos
                        sala = sala_manager.obtener_info_sala(sala_id_real)
                        await enviar_a_todos_en_sala(sala_id_real, {
                            "tipo": "reinicio_pendiente",
                            "solicitado_por": jugador,
                            "esperando_a": resultado["faltante"],
                            "reinicio_pendiente": sala["reinicio_pendiente"]
                        })
                else:
                    await websocket.send_text(json.dumps({
                        "tipo": "error",
                        "mensaje": resultado["mensaje"]
                    }))
            
            elif mensaje["tipo"] == "obtener_estado":
                # Obtener la sala REAL del jugador
                sala_id_real = jugador_sala.get(jugador)
                if sala_id_real:
                    sala = sala_manager.obtener_info_sala(sala_id_real)
                    if sala:
                        simbolo_jugador = sala_manager.obtener_simbolo_jugador(sala_id_real, jugador)
                        await websocket.send_text(json.dumps({
                            "tipo": "estado_actual",
                            "sala": sala,
                            "tu_simbolo": simbolo_jugador,
                            "marcador": sala["marcador"],
                            "partidas_jugadas": sala["partidas_jugadas"]
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
        sala_id_real = jugador_sala.get(jugador)
        if sala_id_real and jugador in jugador_sala:
            del jugador_sala[jugador]
            
            sala = sala_manager.obtener_info_sala(sala_id_real)
            if sala and jugador in sala["jugadores"]:
                sala["jugadores"].remove(jugador)
                if jugador in sala["simbolos"]:
                    del sala["simbolos"][jugador]
                if jugador in sala["marcador"]:
                    del sala["marcador"][jugador]
                if jugador in sala["reinicio_pendiente"]:
                    sala["reinicio_pendiente"].remove(jugador)
                
                # Si la sala queda vacía, eliminarla
                if not sala["jugadores"]:
                    sala_manager.eliminar_sala(sala_id_real)
                    print(f"Sala {sala_id_real} eliminada por estar vacía")
                else:
                    # Notificar al otro jugador que se desconectó
                    await enviar_a_todos_en_sala(sala_id_real, {
                        "tipo": "jugador_desconectado",
                        "mensaje": f"El jugador {jugador} se ha desconectado"
                    })

app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
