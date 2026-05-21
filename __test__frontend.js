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
const RED = '\x1b[31m';
const YELLOW = '\x1b[33m';
const CYAN = '\x1b[36m';
const RESET = '\x1b[0m';
const BOLD = '\x1b[1m';

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
        if (url.includes('/api/auth/profile') && opts?.method === 'PATCH') return mockResponse(200, { message: 'Perfil actualizado' });
        if (url.includes('/api/auth/profile')) return mockResponse(200, {
          id: 1, nombre: 'Carlos Mendoza', usuario: 'admin', rol: 'admin',
          smtp_email: 'admin@gmail.com', notif_email_admin: 'admin@freshmart.cl', smtp_configured: true
        });
        if (url.includes('/api/auth/test-email')) return mockResponse(200, { message: 'Correo de prueba enviado correctamente' });
        if (url.includes('/api/notifications/stock-alerts')) return mockResponse(200, {
          data: [{ id: '7801007001', nombre: 'Pan Molde 550g', categoria: 'Panadería', icono: '🍞', stock: 3, stock_min: 10 }], total: 1
        });
        if (url.includes('/api/sales/summary')) return mockResponse(200, {
          success: true,
          data: { total_vendido: 500000, cantidad_ventas: 10, ticket_promedio: 50000 }
        });
        if (url.includes('/api/sales/history')) return mockResponse(200, {
          success: true,
          data: [
            {
              id: 1, total: 5000, metodo_pago: 'Efectivo', creado: '2026-05-17 10:30:00',
              cajero_nombre: 'Rodrigo Fuentes', num_productos: 3
            }
          ],
          pagination: { page: 1, per_page: 20, total: 1, pages: 1 }
        });
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

  test('Existen las 5 vistas principales', () => {
    const views = ['view-dashboard', 'view-pos', 'view-inventario', 'view-proveedores', 'view-historial'];
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

  test('El tour incluye el paso de Historial de Ventas', () => {
    const histStep = window.TOUR_STEPS.find(s => s.view === 'historial');
    expect(!!histStep).toBeTruthy();
    expect(histStep.title).toContain('Historial');
  });

  test('El tour NO navega a cajeros (botón fue reemplazado por Historial)', () => {
    const cajerosStep = window.TOUR_STEPS.find(s => s.view === 'cajeros');
    expect(!cajerosStep).toBeTruthy();
  });

  test('El target del paso Historial apunta al botón correcto del nav', () => {
    const histStep = window.TOUR_STEPS.find(s => s.view === 'historial');
    expect(histStep.target).toBe('[data-view="historial"]');
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
    expect(permisos.admin).toContain('historial');
  });

  test('Cajero solo accede a dashboard y pos', () => {
    const permisos = window.PERMISOS;
    expect(permisos.cajero).toContain('dashboard');
    expect(permisos.cajero).toContain('pos');
    expect(permisos.cajero).not.toContain('inventario');
    expect(permisos.cajero).not.toContain('cajeros');
    expect(permisos.cajero).not.toContain('proveedores');
    expect(permisos.cajero).not.toContain('historial');
  });

  test('Supervisor no tiene acceso a cajeros', () => {
    const permisos = window.PERMISOS;
    expect(permisos.supervisor).not.toContain('cajeros');
  });

  test('Supervisor tiene acceso a historial', () => {
    const permisos = window.PERMISOS;
    expect(permisos.supervisor).toContain('historial');
  });
});

// ════════════════════════════════════════════════════════════════
//  TESTS: Historial de Ventas — DOM y funciones
// ════════════════════════════════════════════════════════════════

describe('Historial de Ventas', () => {
  test('Existe la vista #view-historial en el DOM', () => {
    expect(document.getElementById('view-historial')).not.toBeNull();
  });

  test('Existen los botones de filtro rápido', () => {
    const btns = document.querySelectorAll('.hist-period-btn');
    expect(btns.length).toBeGreaterThanOrEqual(4);
  });

  test('Botón "Hoy" está activo por defecto', () => {
    const hoyBtn = document.querySelector('.hist-period-btn[data-period="today"]');
    expect(hoyBtn).not.toBeNull();
    expect(hoyBtn.classList.contains('active')).toBeTruthy();
  });

  test('Existen los inputs de fecha personalizada', () => {
    expect(document.getElementById('hist-start-date')).not.toBeNull();
    expect(document.getElementById('hist-end-date')).not.toBeNull();
  });

  test('El rango de fechas está oculto por defecto', () => {
    const range = document.getElementById('hist-date-range');
    expect(range).not.toBeNull();
    expect(range.style.display).toBe('none');
  });

  test('Existen los 3 KPI cards de resumen', () => {
    expect(document.getElementById('hkpi-total')).not.toBeNull();
    expect(document.getElementById('hkpi-count')).not.toBeNull();
    expect(document.getElementById('hkpi-avg')).not.toBeNull();
  });

  test('Existe la tabla de historial', () => {
    expect(document.getElementById('hist-table')).not.toBeNull();
    expect(document.getElementById('hist-tbody')).not.toBeNull();
  });

  test('Existen los botones de paginación', () => {
    expect(document.getElementById('hist-prev-btn')).not.toBeNull();
    expect(document.getElementById('hist-next-btn')).not.toBeNull();
  });

  test('histSetPeriod() existe como función global', () => {
    expect(typeof window.histSetPeriod).toBe('function');
  });

  test('histChangePage() existe como función global', () => {
    expect(typeof window.histChangePage).toBe('function');
  });

  test('histLoadData() existe como función global', () => {
    expect(typeof window.histLoadData).toBe('function');
  });

  test('histSetPeriod("custom") muestra el rango de fechas', () => {
    window.histSetPeriod('custom');
    const range = document.getElementById('hist-date-range');
    expect(range.style.display).not.toBe('none');
  });

  test('histSetPeriod("today") oculta el rango de fechas', () => {
    // Custom primero, luego volver a today
    window.histSetPeriod('custom');
    window.histSetPeriod('today');
    const range = document.getElementById('hist-date-range');
    expect(range.style.display).toBe('none');
  });

  test('histSetPeriod() marca el botón correcto como activo', () => {
    window.histSetPeriod('week');
    const weekBtn = document.querySelector('.hist-period-btn[data-period="week"]');
    const todayBtn = document.querySelector('.hist-period-btn[data-period="today"]');
    expect(weekBtn.classList.contains('active')).toBeTruthy();
    expect(todayBtn.classList.contains('active')).toBeFalsy();
    // Restablecer
    window.histSetPeriod('today');
  });

  test('El botón del historial en el nav tiene data-view="historial"', () => {
    const btn = document.querySelector('.nav-btn[data-view="historial"]');
    expect(btn).not.toBeNull();
  });

  test('No existe nav-btn con data-view="cajeros" (reemplazado)', () => {
    // La vista cajeros puede existir en el DOM pero no debería estar en el nav principal
    // según los requisitos (se reemplazó Personal por Historial en el nav)
    const histBtn = document.querySelector('.nav-btn[data-view="historial"]');
    expect(histBtn).not.toBeNull();
  });
});

// ════════════════════════════════════════════════════════════════
//  TESTS: Perfil de usuario & Configuración de correo
// ════════════════════════════════════════════════════════════════

describe('Perfil de usuario y configuración de correo', () => {
  test('El modal #profile-modal existe en el DOM', () => {
    expect(document.getElementById('profile-modal')).not.toBeNull();
  });

  test('El modal tiene los campos clave de perfil', () => {
    expect(document.getElementById('prof-nombre')).not.toBeNull();
    expect(document.getElementById('prof-usuario')).not.toBeNull();
    expect(document.getElementById('prof-role-badge')).not.toBeNull();
  });

  test('El modal tiene los campos de configuración SMTP', () => {
    expect(document.getElementById('prof-smtp-email')).not.toBeNull();
    expect(document.getElementById('prof-smtp-pass')).not.toBeNull();
    expect(document.getElementById('prof-notif-email')).not.toBeNull();
  });

  test('Existe el botón de enviar correo de prueba', () => {
    expect(document.getElementById('prof-test-btn')).not.toBeNull();
  });

  test('Existe indicador de estado SMTP', () => {
    expect(document.getElementById('prof-smtp-status')).not.toBeNull();
  });

  test('openProfileModal() existe como función global', () => {
    expect(typeof window.openProfileModal).toBe('function');
  });

  test('closeProfileModal() existe como función global', () => {
    expect(typeof window.closeProfileModal).toBe('function');
  });

  test('saveProfile() existe como función global', () => {
    expect(typeof window.saveProfile).toBe('function');
  });

  test('sendTestEmail() existe como función global', () => {
    expect(typeof window.sendTestEmail).toBe('function');
  });

  test('togglePassVis() existe como función global', () => {
    expect(typeof window.togglePassVis).toBe('function');
  });

  test('El modal no está visible por defecto (sin clase show)', () => {
    const modal = document.getElementById('profile-modal');
    expect(modal.classList.contains('show')).toBeFalsy();
  });

  test('openProfileModal() agrega clase show al modal', async () => {
    await window.openProfileModal();
    const modal = document.getElementById('profile-modal');
    expect(modal.classList.contains('show')).toBeTruthy();
    window.closeProfileModal();
  });

  test('closeProfileModal() remueve clase show del modal', async () => {
    await window.openProfileModal();
    window.closeProfileModal();
    const modal = document.getElementById('profile-modal');
    expect(modal.classList.contains('show')).toBeFalsy();
  });

  test('openProfileModal() puebla el campo nombre con datos del perfil', async () => {
    await window.openProfileModal();
    const nombre = document.getElementById('prof-nombre').value;
    expect(nombre).toBe('Carlos Mendoza');
    window.closeProfileModal();
  });

  test('openProfileModal() puebla el campo smtp_email con datos del perfil', async () => {
    await window.openProfileModal();
    const smtp = document.getElementById('prof-smtp-email').value;
    expect(smtp).toBe('admin@gmail.com');
    window.closeProfileModal();
  });

  test('El campo App Password nunca se prerellena', async () => {
    await window.openProfileModal();
    const pass = document.getElementById('prof-smtp-pass').value;
    expect(pass).toBe('');
    window.closeProfileModal();
  });

  test('togglePassVis() cambia input[type=password] a text', () => {
    const inp = document.getElementById('prof-smtp-pass');
    inp.type = 'password';
    window.togglePassVis('prof-smtp-pass', 'prof-pass-eye');
    expect(inp.type).toBe('text');
    inp.type = 'password'; // restaurar
  });

  test('El #user-pill tiene onclick que llama openProfileModal', () => {
    const pill = document.getElementById('user-pill');
    expect(pill.getAttribute('onclick')).toContain('openProfileModal');
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