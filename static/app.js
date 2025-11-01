class TresEnRaya {
    constructor() {
        this.ws = null;
        this.salaId = null;
        this.jugador = null;
        this.pantallas = {
            inicio: document.getElementById('pantalla-inicio'),
            crear: document.getElementById('pantalla-crear'),
            unir: document.getElementById('pantalla-unir'),
            juego: document.getElementById('pantalla-juego')
        };
        
        this.inicializarEventos();
    }
    
    inicializarEventos() {
        // Navegación
        document.getElementById('btn-crear-sala').addEventListener('click', () => this.mostrarPantalla('crear'));
        document.getElementById('btn-unir-sala').addEventListener('click', () => this.mostrarPantalla('unir'));
        document.getElementById('btn-volver-inicio').addEventListener('click', () => this.mostrarPantalla('inicio'));
        document.getElementById('btn-volver-inicio-2').addEventListener('click', () => this.mostrarPantalla('inicio'));
        document.getElementById('btn-volver-juego').addEventListener('click', () => this.volverAlInicio());
        
        // Formularios
        document.getElementById('form-crear-sala').addEventListener('submit', (e) => this.crearSala(e));
        document.getElementById('form-unir-sala').addEventListener('submit', (e) => this.unirSala(e));
        
        // Tablero
        this.inicializarTablero();
    }
    
    mostrarPantalla(pantalla) {
        Object.values(this.pantallas).forEach(p => p.classList.remove('activa'));
        this.pantallas[pantalla].classList.add('activa');
    }
    
    async conectarWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${this.salaId}/${this.jugador}`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('Conectado al servidor');
        };
        
        this.ws.onmessage = (event) => {
            const mensaje = JSON.parse(event.data);
            this.procesarMensaje(mensaje);
        };
        
        this.ws.onclose = () => {
            console.log('Conexión cerrada');
            setTimeout(() => this.conectarWebSocket(), 3000);
        };
        
        this.ws.onerror = (error) => {
            console.error('Error WebSocket:', error);
        };
    }
    
    procesarMensaje(mensaje) {
        switch(mensaje.tipo) {
            case 'sala_creada':
                this.salaId = mensaje.sala_id;
                this.mostrarPantallaJuego();
                this.actualizarInfoSala();
                break;
                
            case 'jugador_unido':
                this.actualizarJugadores(mensaje.jugadores);
                this.actualizarEstado(mensaje.estado);
                break;
                
            case 'actualizar_tablero':
                this.actualizarTablero(mensaje.tablero);
                this.actualizarTurno(mensaje.turno);
                this.actualizarEstado(mensaje.estado, mensaje.ganador);
                break;
                
            case 'estado_actual':
                this.actualizarPantallaConEstado(mensaje.sala);
                break;
                
            case 'error':
                alert(mensaje.mensaje);
                break;
        }
    }
    
    crearSala(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        this.jugador = formData.get('jugador').trim();
        const clave = formData.get('clave');
        
        if (!this.jugador) {
            alert('Por favor ingresa tu nombre');
            return;
        }
        
        this.conectarWebSocket().then(() => {
            this.ws.send(JSON.stringify({
                tipo: 'crear_sala',
                clave: clave
            }));
        });
    }
    
    unirSala(e) {
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
        this.conectarWebSocket().then(() => {
            this.ws.send(JSON.stringify({
                tipo: 'unir_sala',
                clave: clave
            }));
            this.mostrarPantallaJuego();
        });
    }
    
    mostrarPantallaJuego() {
        this.mostrarPantalla('juego');
        this.solicitarEstado();
    }
    
    solicitarEstado() {
        if (this.ws) {
            this.ws.send(JSON.stringify({
                tipo: 'obtener_estado'
            }));
        }
    }
    
    actualizarPantallaConEstado(sala) {
        this.actualizarInfoSala();
        this.actualizarJugadores(sala.jugadores);
        this.actualizarTablero(sala.tablero);
        this.actualizarTurno(sala.turno);
        this.actualizarEstado(sala.estado, sala.ganador);
    }
    
    actualizarInfoSala() {
        document.getElementById('sala-id').textContent = this.salaId;
    }
    
    actualizarJugadores(jugadores) {
        const contenedor = document.getElementById('jugadores');
        contenedor.innerHTML = '';
        
        jugadores.forEach((jugador, index) => {
            const div = document.createElement('div');
            div.className = 'jugador';
            div.textContent = `${jugador} (${index === 0 ? 'X' : 'O'})`;
            contenedor.appendChild(div);
        });
    }
    
    inicializarTablero() {
        const tablero = document.getElementById('tablero');
        tablero.innerHTML = '';
        
        for (let i = 0; i < 9; i++) {
            const celda = document.createElement('div');
            celda.className = 'celda';
            celda.dataset.posicion = i;
            celda.addEventListener('click', () => this.hacerMovimiento(i));
            tablero.appendChild(celda);
        }
    }
    
    hacerMovimiento(posicion) {
        if (this.ws) {
            this.ws.send(JSON.stringify({
                tipo: 'movimiento',
                posicion: posicion
            }));
        }
    }
    
    actualizarTablero(tablero) {
        const celdas = document.querySelectorAll('.celda');
        celdas.forEach((celda, index) => {
            celda.textContent = tablero[index];
            celda.className = 'celda';
            if (tablero[index] === 'X') {
                celda.classList.add('x');
            } else if (tablero[index] === 'O') {
                celda.classList.add('o');
            }
        });
    }
    
    actualizarTurno(turno) {
        const estado = document.getElementById('estado-turno');
        const jugadores = document.querySelectorAll('.jugador');
        
        estado.textContent = `Turno de: ${turno}`;
        
        jugadores.forEach((jugador, index) => {
            const simboloJugador = index === 0 ? 'X' : 'O';
            if (simboloJugador === turno) {
                jugador.classList.add('activo');
            } else {
                jugador.classList.remove('activo');
            }
        });
    }
    
    actualizarEstado(estado, ganador = null) {
        const estadoElemento = document.getElementById('estado-juego');
        
        switch(estado) {
            case 'esperando':
                estadoElemento.textContent = 'Esperando segundo jugador...';
                estadoElemento.className = 'estado-juego';
                break;
            case 'jugando':
                estadoElemento.textContent = '¡Juego en progreso!';
                estadoElemento.className = 'estado-juego';
                break;
            case 'terminado':
                estadoElemento.textContent = `¡Ganador: ${ganador}!`;
                estadoElemento.className = 'estado-juego ganador';
                break;
            case 'empate':
                estadoElemento.textContent = '¡Empate!';
                estadoElemento.className = 'estado-juego';
                break;
        }
    }
    
    volverAlInicio() {
        if (this.ws) {
            this.ws.close();
        }
        this.ws = null;
        this.salaId = null;
        this.jugador = null;
        this.mostrarPantalla('inicio');
        this.inicializarTablero();
    }
}

// Inicializar la aplicación cuando se carga la página
document.addEventListener('DOMContentLoaded', () => {
    new TresEnRaya();
});
