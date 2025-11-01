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
        this.inicializarTablero();
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
        
        console.log('Actualizando tablero. Mi símbolo:', this.miSimbolo, 'Turno actual:', this.turnoActual, 'Es mi turno:', esMiTurno);
        
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
    }
    
    hacerMovimiento(posicion) {
        // Verificar condiciones antes de enviar el movimiento
        const esMiTurno = this.miSimbolo === this.turnoActual;
        const juegoEnProgreso = this.estadoActual === 'jugando';
        
        console.log('Intentando movimiento. Posición:', posicion, 'Es mi turno:', esMiTurno, 'Juego en progreso:', juegoEnProgreso);
        
        if (!esMiTurno) {
            console.log('No es tu turno. Tu símbolo:', this.miSimbolo, 'Turno actual:', this.turnoActual);
            alert('No es tu turno');
            return;
        }
        
        if (!juegoEnProgreso) {
            console.log('El juego no está en progreso. Estado:', this.estadoActual);
            alert('El juego no está en progreso');
            return;
        }
        
        // Verificar si la celda está ocupada
        const celdas = document.querySelectorAll('.celda');
        const celda = celdas[posicion];
        if (celda.textContent !== '') {
            console.log('Celda ocupada:', celda.textContent);
            alert('Esta celda ya está ocupada');
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
            alert('Error de conexión');
        }
    }
    
    // ... (el resto de los métodos se mantienen igual hasta procesarMensaje)
    
    procesarMensaje(mensaje) {
        console.log('Procesando mensaje:', mensaje);
        
        switch(mensaje.tipo) {
            case 'sala_creada':
                this.salaId = mensaje.sala_id;
                this.miSimbolo = 'X'; // El creador siempre es X
                console.log('Sala creada. Mi símbolo:', this.miSimbolo);
                this.mostrarPantallaJuego();
                this.actualizarInfoSala();
                this.mostrarMensajeEspera();
                break;
                
            case 'unido_exitoso':
                console.log('Unido exitosamente a la sala:', mensaje.sala);
                this.miSimbolo = mensaje.tu_simbolo;
                console.log('Unido a sala. Mi símbolo:', this.miSimbolo);
                this.mostrarPantallaJuego();
                this.actualizarPantallaConEstado(mensaje.sala);
                break;
                
            case 'estado_actualizado':
                console.log('Estado actualizado:', mensaje.sala);
                this.actualizarPantallaConEstado(mensaje.sala);
                break;
                
            case 'actualizar_tablero':
                console.log('Actualizando tablero. Turno:', mensaje.turno, 'Estado:', mensaje.estado);
                this.actualizarTablero(mensaje.tablero);
                this.actualizarTurno(mensaje.turno);
                this.actualizarEstado(mensaje.estado, mensaje.ganador);
                break;
                
            case 'estado_actual':
                this.miSimbolo = mensaje.tu_simbolo;
                console.log('Estado actual. Mi símbolo:', this.miSimbolo);
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
                console.error('Error del servidor:', mensaje.mensaje);
                alert('Error: ' + mensaje.mensaje);
                break;
        }
    }
    
    // ... (el resto de los métodos se mantienen igual)
    
    actualizarPantallaConEstado(sala) {
        console.log('Actualizando pantalla con estado:', sala);
        console.log('Mi símbolo actual:', this.miSimbolo);
        
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
    
    actualizarTurno(turno) {
        this.turnoActual = turno;
        
        const estado = document.getElementById('estado-turno');
        const jugadores = document.querySelectorAll('.jugador');
        
        console.log('Actualizando turno. Turno actual:', turno, 'Mi símbolo:', this.miSimbolo);
        
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
    }
    
    // ... (los demás métodos se mantienen igual)
}

const app = new TresEnRaya();
