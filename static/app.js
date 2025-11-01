class TresEnRaya {
    constructor() {
        this.ws = null;
        this.salaId = null;
        this.jugador = null;
        this.miSimbolo = null;
        this.turnoActual = null;
        this.estadoActual = null;
        this.pantallas = {
            inicio: document.getElementById('pantalla-inicio'),
            crear: document.getElementById('pantalla-crear'),
            unir: document.getElementById('pantalla-unir'),
            juego: document.getElementById('pantalla-juego'),
            listar: document.getElementById('pantalla-listar')
        };
        
        this.inicializarEventos();
        this.inicializarTablero(); // Inicializar tablero una vez al inicio
    }
    
    inicializarEventos() {
        // Navegación
        document.getElementById('btn-crear-sala').addEventListener('click', () => this.mostrarPantalla('crear'));
        document.getElementById('btn-unir-sala').addEventListener('click', () => this.mostrarPantalla('listar'));
        document.getElementById('btn-volver-inicio').addEventListener('click', () => this.mostrarPantalla('inicio'));
        document.getElementById('btn-volver-inicio-2').addEventListener('click', () => this.mostrarPantalla('inicio'));
        document.getElementById('btn-volver-listar').addEventListener('click', () => this.mostrarPantalla('inicio'));
        document.getElementById('btn-volver-juego').addEventListener('click', () => this.volverAlInicio());
        document.getElementById('btn-actualizar-lista').addEventListener('click', () => this.obtenerSalasDisponibles());
        
        // Formularios
        document.getElementById('form-crear-sala').addEventListener('submit', (e) => this.crearSala(e));
        document.getElementById('form-unir-sala').addEventListener('submit', (e) => this.unirSala(e));
        
        // Cargar salas disponibles al mostrar la pantalla
        document.getElementById('btn-unir-sala').addEventListener('click', () => {
            setTimeout(() => this.obtenerSalasDisponibles(), 100);
        });
    }
    
    inicializarTablero() {
        const tablero = document.getElementById('tablero');
        if (!tablero) return;
        
        tablero.innerHTML = '';
        
        for (let i = 0; i < 9; i++) {
            const celda = document.createElement('div');
            celda.className = 'celda';
            celda.dataset.posicion = i;
            celda.addEventListener('click', () => this.hacerMovimiento(i));
            tablero.appendChild(celda);
        }
    }
    
    actualizarTablero(tablero) {
        const celdas = document.querySelectorAll('.celda');
        const esMiTurno = this.miSimbolo === this.turnoActual;
        const juegoEnProgreso = this.estadoActual === 'jugando';
        
        celdas.forEach((celda, index) => {
            // Limpiar la celda primero
            celda.textContent = '';
            celda.className = 'celda';
            
            // Actualizar con el valor del tablero
            if (tablero[index]) {
                celda.textContent = tablero[index];
                if (tablero[index] === 'X') {
                    celda.classList.add('x');
                } else if (tablero[index] === 'O') {
                    celda.classList.add('o');
                }
            }
            
            // Configurar interactividad
            const celdaOcupada = !!tablero[index];
            const puedeJugar = esMiTurno && juegoEnProgreso && !celdaOcupada;
            
            if (puedeJugar) {
                celda.style.cursor = 'pointer';
                celda.style.opacity = '1';
                celda.classList.add('jugable');
            } else {
                celda.style.cursor = 'not-allowed';
                celda.style.opacity = celdaOcupada ? '1' : '0.6';
                celda.classList.remove('jugable');
            }
        });
        
        console.log('Tablero actualizado. Mi turno:', esMiTurno, 'Estado:', this.estadoActual);
    }
    
    hacerMovimiento(posicion) {
        // Verificar condiciones antes de enviar el movimiento
        const esMiTurno = this.miSimbolo === this.turnoActual;
        const juegoEnProgreso = this.estadoActual === 'jugando';
        
        if (!esMiTurno) {
            console.log('No es tu turno');
            return;
        }
        
        if (!juegoEnProgreso) {
            console.log('El juego no está en progreso');
            return;
        }
        
        // Verificar si la celda está ocupada
        const celdas = document.querySelectorAll('.celda');
        const celda = celdas[posicion];
        if (celda.textContent !== '') {
            console.log('Celda ocupada');
            return;
        }
        
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            console.log('Enviando movimiento en posición:', posicion);
            this.ws.send(JSON.stringify({
                tipo: 'movimiento',
                posicion: posicion
            }));
        } else {
            console.log('WebSocket no está conectado');
        }
    }
    
    // ... (el resto de los métodos se mantienen igual)
    mostrarPantalla(pantalla) {
        Object.values(this.pantallas).forEach(p => {
            if (p) p.classList.remove('activa');
        });
        if (this.pantallas[pantalla]) {
            this.pantallas[pantalla].classList.add('activa');
        }
        
        if (pantalla === 'listar') {
            setTimeout(() => this.obtenerSalasDisponibles(), 100);
        }
    }
    
    async conectarWebSocket(salaId = 'temp', jugador = 'temp') {
        return new Promise((resolve, reject) => {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/${salaId}/${jugador}`;
            
            console.log('Conectando a:', wsUrl);
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('Conectado al servidor');
                resolve();
            };
            
            this.ws.onmessage = (event) => {
                console.log('Mensaje recibido:', event.data);
                const mensaje = JSON.parse(event.data);
                this.procesarMensaje(mensaje);
            };
            
            this.ws.onclose = () => {
                console.log('Conexión cerrada');
            };
            
            this.ws.onerror = (error) => {
                console.error('Error WebSocket:', error);
                reject(error);
            };
        });
    }
    
    procesarMensaje(mensaje) {
        console.log('Procesando mensaje:', mensaje);
        
        switch(mensaje.tipo) {
            case 'sala_creada':
                this.salaId = mensaje.sala_id;
                this.miSimbolo = 'X';
                this.mostrarPantallaJuego();
                this.actualizarInfoSala();
                this.mostrarMensajeEspera();
                break;
                
            case 'unido_exitoso':
                console.log('Unido exitosamente a la sala:', mensaje.sala);
                this.miSimbolo = mensaje.tu_simbolo;
                this.mostrarPantallaJuego();
                this.actualizarPantallaConEstado(mensaje.sala);
                break;
                
            case 'estado_actualizado':
                this.actualizarPantallaConEstado(mensaje.sala);
                break;
                
            case 'actualizar_tablero':
                console.log('Actualizando tablero:', mensaje.tablero);
                this.actualizarTablero(mensaje.tablero);
                this.actualizarTurno(mensaje.turno);
                this.actualizarEstado(mensaje.estado, mensaje.ganador);
                break;
                
            case 'estado_actual':
                this.miSimbolo = mensaje.tu_simbolo;
                this.actualizarPantallaConEstado(mensaje.sala);
                break;
                
            case 'lista_salas':
                this.mostrarSalasDisponibles(mensaje.salas);
                break;
                
            case 'jugador_desconectado':
                alert(mensaje.mensaje);
                this.volverAlInicio();
                break;
                
            case 'error':
                alert(mensaje.mensaje);
                break;
        }
    }
    
    async crearSala(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        this.jugador = formData.get('jugador').trim();
        const clave = formData.get('clave');
        
        if (!this.jugador) {
            alert('Por favor ingresa tu nombre');
            return;
        }
        
        try {
            await this.conectarWebSocket('temp', this.jugador);
            
            await new Promise(resolve => {
                if (this.ws.readyState === WebSocket.OPEN) {
                    resolve();
                } else {
                    this.ws.addEventListener('open', resolve);
                }
            });
            
            this.ws.send(JSON.stringify({
                tipo: 'crear_sala',
                clave: clave,
                jugador: this.jugador
            }));
        } catch (error) {
            console.error('Error:', error);
            alert('Error al conectar con el servidor');
        }
    }
    
    async obtenerSalasDisponibles() {
        try {
            console.log('Obteniendo salas disponibles...');
            
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/lista/salas`;
            
            const tempWs = new WebSocket(wsUrl);
            
            tempWs.onopen = () => {
                console.log('Conexión temporal abierta para obtener salas');
                tempWs.send(JSON.stringify({
                    tipo: 'obtener_salas'
                }));
            };
            
            tempWs.onmessage = (event) => {
                console.log('Respuesta de salas:', event.data);
                const mensaje = JSON.parse(event.data);
                if (mensaje.tipo === 'lista_salas') {
                    this.mostrarSalasDisponibles(mensaje.salas);
                }
                tempWs.close();
            };
            
            tempWs.onerror = (error) => {
                console.error('Error en conexión temporal:', error);
            };
            
        } catch (error) {
            console.error('Error al obtener salas:', error);
        }
    }
    
    mostrarSalasDisponibles(salas) {
        const lista = document.getElementById('lista-salas');
        if (!lista) return;
        
        console.log('Mostrando salas:', salas);
        lista.innerHTML = '';
        
        if (!salas || salas.length === 0) {
            lista.innerHTML = '<div class="no-salas">No hay salas disponibles. Crea una nueva sala!</div>';
            return;
        }
        
        salas.forEach(sala => {
            const div = document.createElement('div');
            div.className = 'sala-item';
            div.innerHTML = `
                <div class="sala-info">
                    <strong>Sala: ${sala.id}</strong>
                    <span>Jugadores: ${sala.jugadores.length}/2</span>
                    <span>Creada por: ${sala.creador}</span>
                </div>
                <div class="sala-acciones">
                    <input type="password" class="clave-input" placeholder="Clave" id="clave-${sala.id}">
                    <input type="text" class="nombre-input" placeholder="Tu nombre" id="nombre-${sala.id}">
                    <button onclick="app.unirseASalaDesdeLista('${sala.id}')">Unirse</button>
                </div>
            `;
            lista.appendChild(div);
        });
    }
    
    async unirseASalaDesdeLista(salaId) {
        const claveInput = document.getElementById(`clave-${salaId}`);
        const nombreInput = document.getElementById(`nombre-${salaId}`);
        
        if (!claveInput || !nombreInput) {
            alert('Error: No se encontraron los campos de entrada');
            return;
        }
        
        const clave = claveInput.value;
        const nombre = nombreInput.value.trim();
        
        if (!nombre) {
            alert('Por favor ingresa tu nombre');
            return;
        }
        
        if (!clave) {
            alert('Por favor ingresa la clave de la sala');
            return;
        }
        
        this.jugador = nombre;
        this.salaId = salaId;
        
        try {
            await this.conectarWebSocket(salaId, nombre);
            
            await new Promise(resolve => {
                if (this.ws.readyState === WebSocket.OPEN) {
                    resolve();
                } else {
                    this.ws.addEventListener('open', resolve);
                }
            });
            
            console.log('Enviando solicitud de unión...');
            this.ws.send(JSON.stringify({
                tipo: 'unir_sala',
                clave: clave,
                jugador: nombre
            }));
            
        } catch (error) {
            console.error('Error al unirse:', error);
            alert('Error al unirse a la sala');
        }
    }
    
    async unirSala(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        this.jugador = formData.get('jugador').trim();
        const salaId = formData.get('sala_id');
        const clave = formData.get('clave');
        
        if (!this.jugador) {
            alert('Por favor ingresa tu nombre');
            return;
        }
        
        this.salaId = salaId;
        
        try {
            await this.conectarWebSocket(salaId, this.jugador);
            
            await new Promise(resolve => {
                if (this.ws.readyState === WebSocket.OPEN) {
                    resolve();
                } else {
                    this.ws.addEventListener('open', resolve);
                }
            });
            
            this.ws.send(JSON.stringify({
                tipo: 'unir_sala',
                clave: clave,
                jugador: this.jugador
            }));
            
        } catch (error) {
            alert('Error al unirse a la sala');
        }
    }
    
    mostrarPantallaJuego() {
        this.mostrarPantalla('juego');
    }
    
    mostrarMensajeEspera() {
        const estadoElemento = document.getElementById('estado-juego');
        if (estadoElemento) {
            estadoElemento.textContent = '🕐 Esperando a que se una otro jugador...';
            estadoElemento.className = 'estado-juego esperando';
        }
    }
    
    actualizarPantallaConEstado(sala) {
        console.log('Actualizando pantalla con estado:', sala);
        
        this.actualizarInfoSala();
        this.actualizarJugadores(sala.jugadores, sala.simbolos);
        this.actualizarTablero(sala.tablero);
        this.actualizarTurno(sala.turno);
        this.actualizarEstado(sala.estado, sala.ganador);
        
        if (sala.estado === 'esperando' && sala.jugadores.length === 1) {
            this.mostrarMensajeEspera();
        } else if (sala.estado === 'jugando') {
            this.ocultarMensajeEspera();
        }
    }
    
    actualizarInfoSala() {
        const elemento = document.getElementById('sala-id');
        if (elemento) {
            elemento.textContent = this.salaId;
        }
    }
    
    actualizarJugadores(jugadores, simbolos) {
        const contenedor = document.getElementById('jugadores');
        if (!contenedor) return;
        
        contenedor.innerHTML = '';
        
        jugadores.forEach((jugador) => {
            const simbolo = simbolos[jugador];
            const div = document.createElement('div');
            div.className = 'jugador';
            div.textContent = `${jugador} (${simbolo})`;
            
            if (jugador === this.jugador) {
                div.style.fontWeight = 'bold';
                div.style.color = '#667eea';
            }
            
            contenedor.appendChild(div);
        });
    }
    
    actualizarTurno(turno) {
        this.turnoActual = turno;
        
        const estado = document.getElementById('estado-turno');
        const jugadores = document.querySelectorAll('.jugador');
        
        if (estado) {
            const esMiTurno = this.miSimbolo === turno;
            
            if (esMiTurno) {
                estado.textContent = `🎯 ¡Es tu turno! (${turno})`;
                estado.style.color = '#28a745';
                estado.style.fontWeight = 'bold';
            } else {
                estado.textContent = `⏳ Turno del oponente (${turno})`;
                estado.style.color = '#666';
                estado.style.fontWeight = 'normal';
            }
        }
        
        jugadores.forEach((jugador) => {
            const texto = jugador.textContent;
            const simboloJugador = texto.includes('(X)') ? 'X' : 'O';
            
            if (simboloJugador === turno) {
                jugador.classList.add('activo');
            } else {
                jugador.classList.remove('activo');
            }
        });
        
        // Actualizar interactividad del tablero
        this.actualizarInteractividadTablero();
    }
    
    actualizarInteractividadTablero() {
        const celdas = document.querySelectorAll('.celda');
        const esMiTurno = this.miSimbolo === this.turnoActual;
        const juegoEnProgreso = this.estadoActual === 'jugando';
        
        celdas.forEach((celda) => {
            const celdaOcupada = celda.textContent !== '';
            const puedeJugar = esMiTurno && juegoEnProgreso && !celdaOcupada;
            
            if (puedeJugar) {
                celda.style.cursor = 'pointer';
                celda.style.opacity = '1';
            } else {
                celda.style.cursor = 'not-allowed';
                celda.style.opacity = celdaOcupada ? '1' : '0.6';
            }
        });
    }
    
    actualizarEstado(estado, ganador = null) {
        this.estadoActual = estado;
        
        const estadoElemento = document.getElementById('estado-juego');
        if (!estadoElemento) return;
        
        switch(estado) {
            case 'esperando':
                this.mostrarMensajeEspera();
                break;
            case 'jugando':
                estadoElemento.textContent = '¡Juego en progreso!';
                estadoElemento.className = 'estado-juego';
                break;
            case 'terminado':
                const esGanador = ganador === this.jugador;
                estadoElemento.textContent = esGanador ? 
                    '🎉 ¡Has ganado!' : 
                    `🏆 Ganador: ${ganador}`;
                estadoElemento.className = 'estado-juego ganador';
                break;
            case 'empate':
                estadoElemento.textContent = '🤝 ¡Empate!';
                estadoElemento.className = 'estado-juego';
                break;
        }
        
        // Actualizar interactividad del tablero cuando cambia el estado
        this.actualizarInteractividadTablero();
    }
    
    ocultarMensajeEspera() {
        const estadoElemento = document.getElementById('estado-juego');
        if (estadoElemento) {
            estadoElemento.textContent = '¡Juego en progreso!';
            estadoElemento.className = 'estado-juego';
        }
    }
    
    volverAlInicio() {
        if (this.ws) {
            this.ws.close();
        }
        this.ws = null;
        this.salaId = null;
        this.jugador = null;
        this.miSimbolo = null;
        this.turnoActual = null;
        this.estadoActual = null;
        this.mostrarPantalla('inicio');
        this.inicializarTablero(); // Reiniciar tablero
    }
}

const app = new TresEnRaya();
