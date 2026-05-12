"""
FreshMart — Suite de Tests Frontend (DOM/JS via jsdom + Node.js)
Cubre: localStorage tour, utilidades JS, lógica UI, flujos de formularios
Ejecutar: node test_frontend.js
"""

# Este archivo genera y ejecuta el test_frontend.js automáticamente
# Requiere: node.js instalado

import sys
import subprocess
import os
FRONTEND_TEST_JS = r"""
// ════════════════════════════════════════════════════════════════
// FreshMart — Tests Frontend
// Cubre la lógica JS del HTML sin necesidad de un navegador real
// Ejecutar: node test_frontend.js
// ════════════════════════════════════════════════════════════════

const { JSDOM } = require('jsdom');
const fs = require('fs');
const path = require('path');

// ── Colores para output ──────────────────────────────────────────
const GREEN = '\x1b[32m';
const RED   = '\x1b[31m';
const YELLOW = '\x1b[33m';
const CYAN  = '\x1b[36m';
const RESET = '\x1b[0m';
const BOLD  = '\x1b[1m';

// ── Runner de tests ──────────────────────────────────────────────
let passed = 0, failed = 0, skipped = 0;
const results = [];

function test(name, fn) {
  try {
    fn();
    passed++;
    results.push({ status: 'PASS', name });
    process.stdout.write(`  ${GREEN}✓${RESET} ${name}\n`);
  } catch (e) {
    failed++;
    results.push({ status: 'FAIL', name, error: e.message });
    process.stdout.write(`  ${RED}✗${RESET} ${name}\n`);
    process.stdout.write(`    ${RED}→ ${e.message}${RESET}\n`);
  }
}

function describe(suiteName, fn) {
  process.stdout.write(`\n${BOLD}${CYAN}▸ ${suiteName}${RESET}\n`);
  fn();
}

function expect(val) {
  return {
    toBe: (expected) => {
      if (val !== expected) throw new Error(`Esperado: ${JSON.stringify(expected)}, Recibido: ${JSON.stringify(val)}`);
    },
    toEqual: (expected) => {
      if (JSON.stringify(val) !== JSON.stringify(expected))
        throw new Error(`Esperado: ${JSON.stringify(expected)}, Recibido: ${JSON.stringify(val)}`);
    },
    toBeNull: () => {
      if (val !== null) throw new Error(`Esperado: null, Recibido: ${JSON.stringify(val)}`);
    },
    toBeTruthy: () => {
      if (!val) throw new Error(`Esperado valor truthy, Recibido: ${JSON.stringify(val)}`);
    },
    toBeFalsy: () => {
      if (val) throw new Error(`Esperado valor falsy, Recibido: ${JSON.stringify(val)}`);
    },
    toBeGreaterThan: (n) => {
      if (val <= n) throw new Error(`Esperado > ${n}, Recibido: ${val}`);
    },
    toBeGreaterThanOrEqual: (n) => {
      if (val < n) throw new Error(`Esperado >= ${n}, Recibido: ${val}`);
    },
    toBeLessThanOrEqual: (n) => {
      if (val > n) throw new Error(`Esperado <= ${n}, Recibido: ${val}`);
    },
    toContain: (str) => {
      if (!String(val).includes(str)) throw new Error(`"${val}" no contiene "${str}"`);
    },
    toMatch: (re) => {
      if (!re.test(String(val))) throw new Error(`"${val}" no coincide con ${re}`);
    },
    not: {
      toBe: (unexpected) => {
        if (val === unexpected) throw new Error(`No esperado: ${JSON.stringify(unexpected)}`);
      },
      toBeNull: () => {
        if (val === null) throw new Error(`No se esperaba null`);
      },
      toContain: (str) => {
        if (String(val).includes(str)) throw new Error(`"${val}" no debería contener "${str}"`);
      },
    }
  };
}

// ── Setup JSDOM con el HTML real ─────────────────────────────────
const htmlPath = path.join(__dirname, '/templates/index.html');
let dom, window, document;

function setupDOM() {
  const html = fs.readFileSync(htmlPath, 'utf8');
  dom = new JSDOM(html, {
    runScripts: 'dangerously',
    resources: 'usable',
    url: 'http://localhost:8000',
    beforeParse(win) {
      // Mock fetch global para no necesitar el backend
      win.fetch = async (url, opts) => {
        const body = opts?.body ? JSON.parse(opts.body) : {};
        // Simular respuestas básicas de la API
        if (url.includes('/api/auth/login')) {
          if (body.usuario === 'admin' && body.password === 'admin123') {
            return mockResponse(200, {
              token: 'mock.jwt.token',
              user: { id: 1, nombre: 'Admin Test', usuario: 'admin', rol: 'admin', activo: true }
            });
          }
          return mockResponse(401, { detail: 'Credenciales incorrectas' });
        }
        if (url.includes('/api/health')) return mockResponse(200, { status: 'ok' });
        if (url.includes('/api/dashboard')) return mockResponse(200, {
          ventas_hoy_total: 150000, ventas_hoy_count: 5,
          total_productos: 42, criticos: 2, bajos: 3,
          ordenes_pendientes: 1, ultimas_ventas: [], top_productos: []
        });
        if (url.includes('/api/productos')) return mockResponse(200, [
          { id: 'P001', nombre: 'Leche', categoria: 'Lácteos', precio: 1500, stock: 50, stock_min: 10, activo: 1 }
        ]);
        return mockResponse(200, {});
      };
    }
  });
  window = dom.window;
  document = window.document;
}

function mockResponse(status, data) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => data,
    text: async () => JSON.stringify(data)
  };
}

// ════════════════════════════════════════════════════════════════
//  TESTS: localStorage y Tour
// ════════════════════════════════════════════════════════════════

describe('Tour — localStorage', () => {
  test('localStorage está disponible en el contexto DOM', () => {
    setupDOM();
    expect(window.localStorage).toBeTruthy();
  });

  test('La clave fm_tour_seen no existe inicialmente', () => {
    window.localStorage.clear();
    expect(window.localStorage.getItem('fm_tour_seen')).toBeNull();
  });

  test('Se puede guardar y leer fm_tour_seen', () => {
    window.localStorage.setItem('fm_tour_seen', '1');
    expect(window.localStorage.getItem('fm_tour_seen')).toBe('1');
  });

  test('Se puede eliminar fm_tour_seen', () => {
    window.localStorage.setItem('fm_tour_seen', '1');
    window.localStorage.removeItem('fm_tour_seen');
    expect(window.localStorage.getItem('fm_tour_seen')).toBeNull();
  });

  test('El botón tour-topbar-btn existe en el DOM', () => {
    const btn = document.getElementById('tour-topbar-btn');
    expect(btn).not.toBeNull();
  });

  test('El FAB tour-fab NO existe en el DOM', () => {
    const fab = document.getElementById('tour-fab');
    expect(fab).toBeNull();
  });

  test('El botón tour-topbar-btn tiene display:none inicialmente', () => {
    const btn = document.getElementById('tour-topbar-btn');
    expect(btn.style.display).toBe('none');
  });

  test('El div tour-welcome existe en el DOM', () => {
    expect(document.getElementById('tour-welcome')).not.toBeNull();
  });

  test('El div tour-overlay existe en el DOM', () => {
    expect(document.getElementById('tour-overlay')).not.toBeNull();
  });

  test('TOUR_SEEN_KEY está definido como constante en el script', () => {
    // La constante debe estar definida en window
    expect(window.TOUR_SEEN_KEY).not.toBeNull();
    expect(window.TOUR_SEEN_KEY).toBe('fm_tour_seen');
  });
});

// ════════════════════════════════════════════════════════════════
//  TESTS: Estructura del DOM
// ════════════════════════════════════════════════════════════════

describe('Estructura del DOM', () => {
  test('Existe el contenedor #app', () => {
    expect(document.getElementById('app')).not.toBeNull();
  });

  test('Existe #login-screen', () => {
    expect(document.getElementById('login-screen')).not.toBeNull();
  });

  test('Existe #top-bar', () => {
    expect(document.getElementById('top-bar')).not.toBeNull();
  });

  test('Existe #top-nav con botones de navegación', () => {
    const nav = document.getElementById('top-nav');
    expect(nav).not.toBeNull();
    const btns = nav.querySelectorAll('.nav-btn');
    expect(btns.length).toBeGreaterThanOrEqual(3);
  });

  test('Existen las 4 vistas principales', () => {
    const views = ['view-dashboard', 'view-pos', 'view-inventario', 'view-proveedores'];
    views.forEach(id => {
      expect(document.getElementById(id)).not.toBeNull();
    });
  });

  test('Existe #toast para notificaciones', () => {
    expect(document.getElementById('toast')).not.toBeNull();
  });

  test('Existen los inputs de login', () => {
    expect(document.getElementById('inp-user')).not.toBeNull();
    expect(document.getElementById('inp-pass')).not.toBeNull();
    expect(document.getElementById('login-btn')).not.toBeNull();
  });

  test('Existe el botón de logout', () => {
    expect(document.getElementById('logout-btn')).not.toBeNull();
  });

  test('Existe el reloj en el topbar', () => {
    expect(document.getElementById('top-clock')).not.toBeNull();
  });

  test('Existe el pill de usuario', () => {
    expect(document.getElementById('user-pill')).not.toBeNull();
  });

  test('Los botones de navegación tienen data-view', () => {
    const btns = document.querySelectorAll('.nav-btn[data-view]');
    expect(btns.length).toBeGreaterThanOrEqual(3);
  });
});

// ════════════════════════════════════════════════════════════════
//  TESTS: Funciones utilitarias JS
// ════════════════════════════════════════════════════════════════

describe('Funciones utilitarias', () => {
  test('fmt() formatea moneda correctamente', () => {
    const fmt = window.fmt;
    expect(fmt).not.toBeNull();
    const result = fmt(1500);
    expect(result).toContain('$');
    expect(result).toContain('1.500');
  });

  test('initials() genera iniciales de nombre', () => {
    const initials = window.initials;
    expect(initials('Juan Pérez')).toBe('JP');
    expect(initials('Ana María López')).toBe('AM');
  });

  test('rolLabel() devuelve etiqueta correcta', () => {
    const rolLabel = window.rolLabel;
    expect(rolLabel('admin')).toBe('Administrador');
    expect(rolLabel('supervisor')).toBe('Supervisor');
    expect(rolLabel('cajero')).toBe('Cajero');
  });

  test('avatarClass() devuelve clase CSS según rol', () => {
    const avatarClass = window.avatarClass;
    expect(avatarClass('admin')).toBe('role-admin');
    expect(avatarClass('supervisor')).toBe('role-supervisor');
    expect(avatarClass('cajero')).toBe('role-cajero');
  });

  test('genUsuario() genera nombre de usuario desde nombre completo', () => {
    const genUsuario = window.genUsuario;
    const result = genUsuario('Juan Pérez');
    expect(result).toBeTruthy();
    expect(result.length).toBeGreaterThan(0);
    // No debe tener espacios
    expect(result).not.toContain(' ');
  });

  test('showToast() no lanza excepción', () => {
    let threw = false;
    try { window.showToast('Mensaje de prueba', 'ok'); } catch { threw = true; }
    expect(threw).toBeFalsy();
  });

  test('showToast() muestra el elemento #toast', () => {
    window.showToast('Test', 'ok');
    const toast = document.getElementById('toast');
    expect(toast.style.display).toBe('block');
    expect(toast.textContent).toBe('Test');
  });
});

// ════════════════════════════════════════════════════════════════
//  TESTS: Tour — funciones
// ════════════════════════════════════════════════════════════════

describe('Tour — funciones y comportamiento', () => {
  test('startTour() existe como función global', () => {
    expect(typeof window.startTour).toBe('function');
  });

  test('closeTourWelcome() existe como función global', () => {
    expect(typeof window.closeTourWelcome).toBe('function');
  });

  test('beginTourSteps() existe como función global', () => {
    expect(typeof window.beginTourSteps).toBe('function');
  });

  test('endTour() existe como función global', () => {
    expect(typeof window.endTour).toBe('function');
  });

  test('tourNext() existe como función global', () => {
    expect(typeof window.tourNext).toBe('function');
  });

  test('tourPrev() existe como función global', () => {
    expect(typeof window.tourPrev).toBe('function');
  });

  test('showTourAfterLogin() existe como función global', () => {
    expect(typeof window.showTourAfterLogin).toBe('function');
  });

  test('closeTourWelcome() guarda fm_tour_seen en localStorage', () => {
    window.localStorage.removeItem('fm_tour_seen');
    // Asegurarse que tour-welcome esté visible primero
    document.getElementById('tour-welcome').classList.add('show');
    window.closeTourWelcome();
    expect(window.localStorage.getItem('fm_tour_seen')).toBe('1');
  });

  test('closeTourWelcome() remueve clase "show" del welcome', () => {
    document.getElementById('tour-welcome').classList.add('show');
    window.closeTourWelcome();
    expect(document.getElementById('tour-welcome').classList.contains('show')).toBeFalsy();
  });

  test('endTour() guarda fm_tour_seen en localStorage', () => {
    window.localStorage.removeItem('fm_tour_seen');
    // Poner overlay activo para simular tour en progreso
    document.getElementById('tour-overlay').classList.add('active');
    window.tourActive = true;
    window.endTour();
    expect(window.localStorage.getItem('fm_tour_seen')).toBe('1');
  });

  test('endTour() desactiva tour-overlay', () => {
    document.getElementById('tour-overlay').classList.add('active');
    window.tourActive = true;
    window.endTour();
    expect(document.getElementById('tour-overlay').classList.contains('active')).toBeFalsy();
  });

  test('showTourAfterLogin() muestra tour-topbar-btn', () => {
    document.getElementById('tour-topbar-btn').style.display = 'none';
    window.localStorage.setItem('fm_tour_seen', '1'); // Que no auto-lance
    window.showTourAfterLogin();
    expect(document.getElementById('tour-topbar-btn').style.display).toBe('flex');
  });

  test('showTourAfterLogin() NO lanza startTour() si ya fue visto', () => {
    window.localStorage.setItem('fm_tour_seen', '1');
    let tourCalled = false;
    const origStart = window.startTour;
    window.startTour = () => { tourCalled = true; };
    window.showTourAfterLogin();
    window.startTour = origStart;
    expect(tourCalled).toBeFalsy();
  });

  test('startTour() muestra tour-welcome si #app es visible', () => {
    document.getElementById('app').classList.add('visible');
    document.getElementById('tour-welcome').classList.remove('show');
    window.startTour();
    expect(document.getElementById('tour-welcome').classList.contains('show')).toBeTruthy();
    document.getElementById('app').classList.remove('visible');
    document.getElementById('tour-welcome').classList.remove('show');
  });

  test('startTour() NO muestra tour-welcome si #app no es visible', () => {
    document.getElementById('app').classList.remove('visible');
    document.getElementById('tour-welcome').classList.remove('show');
    window.startTour();
    expect(document.getElementById('tour-welcome').classList.contains('show')).toBeFalsy();
  });

  test('TOUR_STEPS tiene pasos definidos', () => {
    expect(Array.isArray(window.TOUR_STEPS)).toBeTruthy();
    expect(window.TOUR_STEPS.length).toBeGreaterThan(0);
  });

  test('Cada paso del tour tiene title y desc', () => {
    window.TOUR_STEPS.forEach((step, i) => {
      if (!step.title) throw new Error(`Paso ${i} sin title`);
      if (!step.desc) throw new Error(`Paso ${i} sin desc`);
    });
  });
});

// ════════════════════════════════════════════════════════════════
//  TESTS: Navegación entre vistas
// ════════════════════════════════════════════════════════════════

describe('Navegación entre vistas', () => {
  test('switchView() existe como función global', () => {
    expect(typeof window.switchView).toBe('function');
  });

  test('La vista dashboard está activa por defecto', () => {
    const dash = document.getElementById('view-dashboard');
    expect(dash.classList.contains('active')).toBeTruthy();
  });

  test('PERMISOS está definido para los 3 roles', () => {
    const permisos = window.PERMISOS;
    expect(permisos).not.toBeNull();
    expect(Array.isArray(permisos.admin)).toBeTruthy();
    expect(Array.isArray(permisos.supervisor)).toBeTruthy();
    expect(Array.isArray(permisos.cajero)).toBeTruthy();
  });

  test('Admin tiene acceso a todas las vistas', () => {
    const permisos = window.PERMISOS;
    expect(permisos.admin).toContain('dashboard');
    expect(permisos.admin).toContain('pos');
    expect(permisos.admin).toContain('inventario');
    expect(permisos.admin).toContain('cajeros');
    expect(permisos.admin).toContain('proveedores');
  });

  test('Cajero solo accede a dashboard y pos', () => {
    const permisos = window.PERMISOS;
    expect(permisos.cajero).toContain('dashboard');
    expect(permisos.cajero).toContain('pos');
    expect(permisos.cajero).not.toContain('inventario');
    expect(permisos.cajero).not.toContain('cajeros');
    expect(permisos.cajero).not.toContain('proveedores');
  });

  test('Supervisor no tiene acceso a cajeros', () => {
    const permisos = window.PERMISOS;
    expect(permisos.supervisor).not.toContain('cajeros');
  });
});

// ════════════════════════════════════════════════════════════════
//  TESTS: Estado global y API
// ════════════════════════════════════════════════════════════════

describe('Estado global y configuración', () => {
  test('La constante API apunta a localhost:8000', () => {
    expect(window.API).toContain('localhost:8000');
    expect(window.API).toContain('/api');
  });

  test('authToken se inicializa desde localStorage', () => {
    // authToken debe existir como variable (puede ser '' si no hay token)
    expect(typeof window.authToken !== 'undefined').toBeTruthy();
  });

  test('currentUser se inicializa en null', () => {
    expect(window.currentUser).toBeNull();
  });

  test('posCart se inicializa como array vacío', () => {
    expect(Array.isArray(window.posCart)).toBeTruthy();
  });

  test('inventory se inicializa como array', () => {
    expect(Array.isArray(window.inventory)).toBeTruthy();
  });
});

// ════════════════════════════════════════════════════════════════
//  TESTS: Punto de Venta — lógica de carrito
// ════════════════════════════════════════════════════════════════

describe('Punto de Venta — lógica', () => {
  test('Funciones del POS están definidas', () => {
    const fns = ['renderCart', 'updateProcessBtn'];
    fns.forEach(fn => {
      expect(typeof window[fn]).toBe('function');
    });
  });

  test('Carrito vacío inicialmente', () => {
    expect(window.posCart.length).toBe(0);
  });

  test('#process-btn existe en el DOM', () => {
    expect(document.getElementById('process-btn')).not.toBeNull();
  });

  test('#process-btn está deshabilitado inicialmente', () => {
    const btn = document.getElementById('process-btn');
    expect(btn.disabled).toBeTruthy();
  });

  test('Existe el área de búsqueda de productos POS', () => {
    // El input de búsqueda del POS debe existir
    const posSearch = document.getElementById('pos-search');
    expect(posSearch).not.toBeNull();
  });
});

// ════════════════════════════════════════════════════════════════
//  TESTS: Formularios de Login
// ════════════════════════════════════════════════════════════════

describe('Formulario de Login', () => {
  test('doLogin() existe como función global', () => {
    expect(typeof window.doLogin).toBe('function');
  });

  test('doLogout() existe como función global', () => {
    expect(typeof window.doLogout).toBe('function');
  });

  test('El login-screen tiene display flex por defecto', () => {
    const ls = document.getElementById('login-screen');
    // Puede ser flex o inline flex
    const display = window.getComputedStyle(ls).display;
    expect(['flex', 'inline-flex', 'block'].includes(display) || ls.style.display !== 'none').toBeTruthy();
  });

  test('#login-error existe para mostrar errores', () => {
    expect(document.getElementById('login-error')).not.toBeNull();
  });

  test('#login-btn existe y llama doLogin', () => {
    const btn = document.getElementById('login-btn');
    expect(btn).not.toBeNull();
    expect(btn.getAttribute('onclick')).toContain('doLogin');
  });
});

// ════════════════════════════════════════════════════════════════
//  RESUMEN FINAL
// ════════════════════════════════════════════════════════════════

const total = passed + failed;
process.stdout.write('\n' + '─'.repeat(60) + '\n');
process.stdout.write(`${BOLD}Resultados: ${total} tests${RESET}\n`);
process.stdout.write(`  ${GREEN}✓ Pasados:  ${passed}${RESET}\n`);
if (failed > 0) {
  process.stdout.write(`  ${RED}✗ Fallidos: ${failed}${RESET}\n`);
  process.stdout.write('\n' + `${RED}${BOLD}Tests fallidos:${RESET}\n`);
  results.filter(r => r.status === 'FAIL').forEach(r => {
    process.stdout.write(`  ${RED}✗ ${r.name}${RESET}\n`);
    process.stdout.write(`    → ${r.error}\n`);
  });
  process.exit(1);
} else {
  process.stdout.write(`\n${GREEN}${BOLD}✅ Todos los tests pasaron (${passed}/${total})${RESET}\n`);
}
"""


def main():
    # Escribir el archivo JS
    js_path = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "__test__frontend.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(FRONTEND_TEST_JS)
    print(f"✓ test_frontend.js generado en {js_path}")
    print("Ejecutando tests frontend...\n")
    result = subprocess.run(["node", js_path], capture_output=False)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
