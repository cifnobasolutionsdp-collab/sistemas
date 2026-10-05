/* =====================================================================
 * Interfaz: íconos, avisos, ventanas modales, gráficas y navegación
 * ===================================================================== */
const ICON = {
  tablero: '<path d="M3 13h8V3H3zM13 21h8V11h-8zM3 21h8v-6H3zM13 3v6h8V3z"/>',
  eval: '<path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>',
  lista: '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
  res: '<path d="M3 3v18h18"/><path d="M7 15l4-4 3 3 5-6"/>',
  plan: '<path d="M12 8v4l3 3"/><circle cx="12" cy="12" r="9"/>',
  audit: '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>',
  credito: '<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20"/>',
  riesgo: '<path d="M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/>',
  reporte: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h8"/>',
  integra: '<path d="M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.7 1.7"/><path d="M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.7-1.7"/>',
  catalogo: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V2H6.5A2.5 2.5 0 0 0 4 4.5z"/><path d="M4 19.5V22h16"/>',
  admin: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>',
  usuario: '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
  salir: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>',
  descarga: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>',
  sube: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12"/>',
  mas: '<path d="M12 5v14M5 12h14"/>',
  imprimir: '<path d="M6 9V2h12v7M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/>',
  menu: '<path d="M3 12h18M3 6h18M3 18h18"/>',
  tema: '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>',
  check: '<path d="M20 6L9 17l-5-5"/>',
  cerrar: '<path d="M18 6L6 18M6 6l12 12"/>',
};
const ico = (n) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICON[n] || ''}</svg>`;
const LOGO = '<div class="brand-mark"><svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 13l4 4L19 7"/></svg></div>';

function toast(msg, err = false) {
  const t = document.createElement('div');
  t.className = 'toast' + (err ? ' err' : '');
  t.textContent = msg;
  $('#toast-root').appendChild(t);
  setTimeout(() => t.remove(), err ? 7000 : 3500);
}

/* Modal: devuelve una promesa que resuelve con el botón presionado. */
let _modalResolve = null;
function modal({ titulo, cuerpo, botones = [{ id: 'ok', t: 'Aceptar', primary: true }], chico = false, alAbrir }) {
  cerrarModal();
  $('#modal-root').innerHTML = `
    <div class="modal-back" data-act="modal-fondo">
      <div class="modal ${chico ? 'sm' : ''}" role="dialog" aria-modal="true" aria-labelledby="modal-titulo">
        <header><h2 id="modal-titulo">${esc(titulo)}</h2><button class="btn ghost sm" data-modal="cancel" aria-label="Cerrar">${ico('cerrar')}</button></header>
        <div class="body">${cuerpo}</div>
        <footer>${botones.map((b) => `<button class="btn ${b.primary ? 'primary' : ''} ${b.danger ? 'danger' : ''}" data-modal="${esc(b.id)}">${esc(b.t)}</button>`).join('')}</footer>
      </div>
    </div>`;
  const m = $('.modal');
  const f = m.querySelector('input:not([type=hidden]):not([disabled]), select:not([disabled]), textarea:not([disabled])');
  (f || m.querySelector('[data-modal]')).focus();
  if (alAbrir) alAbrir(m);
  return new Promise((res) => { _modalResolve = res; });
}
function cerrarModal(valor = null) {
  if (_modalResolve) { const r = _modalResolve; _modalResolve = null; r(valor); }
  $('#modal-root').innerHTML = '';
}
document.addEventListener('click', (e) => {
  const b = e.target.closest('[data-modal]');
  if (b) {
    const id = b.dataset.modal;
    if (id === 'cancel') return cerrarModal('cancel');
    const res = _modalResolve;
    // El llamador decide si cierra (validaciones): resolvemos sin cerrar.
    if (res) { _modalResolve = null; res(id); }
  }
});
document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && $('.modal')) cerrarModal('cancel'); });
async function confirmar(titulo, texto, { ok = 'Confirmar', peligro = false } = {}) {
  const r = await modal({ titulo, cuerpo: `<p>${texto}</p>`, chico: true, botones: [{ id: 'cancel', t: 'Cancelar' }, { id: 'ok', t: ok, primary: !peligro, danger: peligro }] });
  cerrarModal();
  return r === 'ok';
}
/* Formulario modal con validación: `validar(datos)` devuelve mensaje de error o null. */
async function formModal(opts, validar) {
  let r = await modal(opts);
  while (r && r !== 'cancel') {
    const datos = leerForm($('.modal'));
    const err = validar ? await validar(datos, r) : null;
    if (!err) { cerrarModal(); return { boton: r, datos }; }
    let box = $('.modal .form-err');
    if (!box) { box = document.createElement('div'); box.className = 'callout crit form-err'; box.style.marginBottom = '.75rem'; $('.modal .body').prepend(box); }
    box.textContent = err;
    r = await new Promise((res) => { _modalResolve = res; });
  }
  cerrarModal();
  return null;
}
function leerForm(el) {
  const o = {};
  for (const x of $$('[name]', el)) {
    if (x.type === 'checkbox') o[x.name] = x.checked;
    else if (x.type === 'radio') { if (x.checked) o[x.name] = x.value; }
    else if (x.type === 'file') o[x.name] = x.files;
    else o[x.name] = x.value;
  }
  return o;
}

/* Campos de formulario ------------------------------------------------- */
function campo(nombre, etiqueta, valor = '', { tipo = 'text', opciones = null, dis = false, req = false, ph = '', ayuda = '', attrs = '', lista = '' } = {}) {
  const id = 'f_' + nombre + '_' + Math.random().toString(36).slice(2, 6);
  let input;
  if (opciones) {
    input = `<select id="${id}" name="${esc(nombre)}" ${dis ? 'disabled' : ''} ${attrs}>${opciones.map((o) => {
      const [v, t] = Array.isArray(o) ? o : [o, o];
      return `<option value="${esc(v)}" ${String(v) === String(valor ?? '') ? 'selected' : ''}>${esc(t)}</option>`;
    }).join('')}</select>`;
  } else if (tipo === 'textarea') {
    input = `<textarea id="${id}" name="${esc(nombre)}" ${dis ? 'disabled' : ''} placeholder="${esc(ph)}" ${attrs}>${esc(valor)}</textarea>`;
  } else if (tipo === 'checkbox') {
    return `<label class="row" style="margin-bottom:.6rem"><input type="checkbox" name="${esc(nombre)}" ${valor ? 'checked' : ''} ${dis ? 'disabled' : ''} ${attrs}> ${esc(etiqueta)}</label>`;
  } else {
    input = `<input id="${id}" type="${tipo}" name="${esc(nombre)}" value="${esc(valor)}" ${dis ? 'disabled' : ''} ${req ? 'required' : ''} placeholder="${esc(ph)}" ${lista ? `list="${esc(lista)}"` : ''} ${attrs}>`;
  }
  return `<div class="field"><label class="f" for="${id}">${esc(etiqueta)}${req ? ' *' : ''}</label>${input}${ayuda ? `<small>${esc(ayuda)}</small>` : ''}</div>`;
}
const datalist = (id, arr) => `<datalist id="${esc(id)}">${arr.map((x) => `<option value="${esc(x)}">`).join('')}</datalist>`;

/* Gráficas (HTML + CSS, con tooltip al pasar el cursor) ---------------- */
function barras(items, { max = 5, decimales = 2, sufijo = '', marcas = [1, 2, 3, 4, 5] } = {}) {
  if (!items.length) return '<div class="empty">Sin datos.</div>';
  return `<div class="chart-bars" style="display:grid;grid-template-columns:minmax(120px,32%) 1fr 56px;gap:.45rem .75rem;align-items:center">
    ${items.map((it) => {
      const v = it.valor;
      const pct = v == null ? 0 : clamp(v / max, 0, 1) * 100;
      return `<div style="font-size:.83rem;color:var(--text-2);line-height:1.25">${esc(it.etiqueta)}</div>
        <div style="position:relative;height:14px" data-tip="${esc(it.tip || (it.etiqueta + ': ' + (v == null ? 'sin datos' : fmtN(v, decimales) + sufijo)))}">
          ${marcas.map((m) => `<span style="position:absolute;left:${(m / max) * 100}%;top:-2px;bottom:-2px;border-left:1px dashed var(--line)"></span>`).join('')}
          <div style="position:absolute;inset:3px auto 3px 0;width:${pct}%;background:${it.color || 'var(--series-1)'};border-radius:0 4px 4px 0;min-width:${v ? 2 : 0}px"></div>
        </div>
        <div class="num" style="font-weight:650;text-align:right">${v == null ? '—' : fmtN(v, decimales) + sufijo}</div>`;
    }).join('')}
  </div>`;
}
function barrasDobles(items, series, { max = 5 } = {}) {
  const colores = ['var(--series-1)', 'var(--series-2)'];
  return `<div class="legend">${series.map((s, i) => `<span><i style="background:${colores[i]}"></i>${esc(s)}</span>`).join('')}</div>
  <div style="display:grid;grid-template-columns:minmax(120px,32%) 1fr;gap:.6rem .75rem;align-items:center">
    ${items.map((it) => `<div style="font-size:.83rem;color:var(--text-2)">${esc(it.etiqueta)}</div>
      <div style="display:grid;gap:3px">${it.valores.map((v, i) => `<div style="display:flex;align-items:center;gap:.5rem" data-tip="${esc(it.etiqueta + ' · ' + series[i] + ': ' + (v == null ? 'sin datos' : fmtN(v)))}">
        <div style="height:10px;width:${v == null ? 0 : clamp(v / max, 0, 1) * 85}%;background:${colores[i]};border-radius:0 4px 4px 0"></div>
        <span class="num" style="font-size:.78rem;color:var(--text-2)">${v == null ? '—' : fmtN(v)}</span></div>`).join('')}</div>`).join('')}
  </div>`;
}
function apilada(partes) {
  const total = sum(partes.map((p) => p.v));
  if (!total) return '<div class="empty">Sin puntos de interés evaluados.</div>';
  return `<div style="display:flex;height:22px;gap:2px;border-radius:5px;overflow:hidden">${partes.filter((p) => p.v).map((p) => `<div style="flex:${p.v};background:${p.color}" data-tip="${esc(p.n + ': ' + p.v + ' (' + fmtPct(p.v / total) + ')')}"></div>`).join('')}</div>
    <div class="legend" style="margin-top:.5rem">${partes.map((p) => `<span><i style="background:${p.color}"></i>${esc(p.n)}: <b class="num">${p.v}</b> (${fmtPct(p.v / total, 0)})</span>`).join('')}</div>`;
}
function progreso(v, max = 1) {
  const pct = max ? clamp(v / max, 0, 1) * 100 : 0;
  return `<div class="bar-track" title="${fmtN(pct, 0)}%"><div class="bar-fill" style="width:${pct}%"></div></div>`;
}
/* Tooltip global */
document.addEventListener('mouseover', (e) => {
  const t = e.target.closest('[data-tip]');
  const tip = $('#tip');
  if (!t) { tip.hidden = true; return; }
  tip.textContent = t.dataset.tip;
  tip.hidden = false;
});
document.addEventListener('mousemove', (e) => {
  const tip = $('#tip');
  if (tip.hidden) return;
  const x = Math.min(e.clientX + 14, window.innerWidth - tip.offsetWidth - 8);
  const y = e.clientY + 16 + tip.offsetHeight > window.innerHeight ? e.clientY - tip.offsetHeight - 10 : e.clientY + 16;
  tip.style.left = x + 'px'; tip.style.top = y + 'px';
});

/* Tema claro/oscuro */
function aplicarTema() {
  let t = null;
  try { t = localStorage.getItem(THEME_KEY); } catch { /* sin almacenamiento */ }
  if (t) document.documentElement.dataset.theme = t; else delete document.documentElement.dataset.theme;
}
function alternarTema() {
  const oscuro = document.documentElement.dataset.theme === 'dark' || (!document.documentElement.dataset.theme && matchMedia('(prefers-color-scheme: dark)').matches);
  try { localStorage.setItem(THEME_KEY, oscuro ? 'light' : 'dark'); } catch { /* sin almacenamiento */ }
  aplicarTema();
}

/* ---------------------------------------------------------------------
 * Navegación
 * ------------------------------------------------------------------- */
const MENU = [
  { g: 'Evaluación COSO ERM', items: [
    ['tablero', 'Tablero', 'tablero'],
    ['evaluacion', 'Evaluaciones y datos', 'eval'],
    ['cuestionario', 'Cuestionario', 'lista'],
    ['resultados', 'Resultados', 'res'],
    ['planes', 'Planes de solución', 'plan'],
  ] },
  { g: 'Líneas de control', items: [
    ['auditoria', 'Auditoría interna', 'audit'],
    ['credito', 'Contraloría de crédito y mesa de control', 'credito'],
    ['riesgos', 'Gestión de riesgos', 'riesgo'],
  ] },
  { g: 'Información', items: [
    ['reportes', 'Reportes', 'reporte'],
    ['integraciones', 'Integraciones', 'integra'],
    ['catalogos', 'Catálogos y normativa', 'catalogo'],
  ] },
  { g: 'Sistema', items: [
    ['admin', 'Administración', 'admin', 'admin'],
    ['perfil', 'Mi cuenta', 'usuario'],
  ] },
];
const VISTAS = {};
function ruta() {
  const h = location.hash.replace(/^#\/?/, '').split('?')[0];
  const [v, ...rest] = h.split('/');
  return { vista: v || 'tablero', args: rest.map(decodeURIComponent) };
}
const ir = (h) => { location.hash = '#/' + h; };
window.addEventListener('hashchange', () => { render(); window.scrollTo(0, 0); });

function render() {
  const app = $('#app');
  if (!DB) return renderInicio(app);
  if (!SES) return renderLogin(app);
  const u = usuarioActual();
  if (!u) { logout(); return; }
  if (u.mustChange) return renderCambioObligatorio(app);
  const { vista, args } = ruta();
  const fn = VISTAS[vista] || VISTAS.tablero;
  const ev = evalActiva();
  let contenido;
  try { contenido = fn(args); } catch (e) { console.error(e); contenido = `<div class="callout crit">Error al mostrar la vista: ${esc(e.message)}</div>`; }
  const dias = DB.meta.ultimoRespaldo ? Math.floor((Date.now() - new Date(DB.meta.ultimoRespaldo)) / 864e5) : null;
  const avisoRespaldo = can('respaldo') && (dias == null || dias >= DB.config.diasRespaldo);
  app.innerHTML = `
  <div class="shell">
    <nav class="nav" id="nav" aria-label="Menú principal">
      <div class="brand">${LOGO}<div><b>SECI · COSO ERM</b><span>${esc(DB.config.institucion || 'Control interno')}</span></div></div>
      ${MENU.map((g) => `<div class="nav-group"><div>${esc(g.g)}</div>${g.items.filter((i) => !i[3] || can(i[3])).map(([k, t, i]) => `<a href="#/${k}" class="${vista === k ? 'active' : ''}">${ico(i)}<span>${esc(t)}</span></a>`).join('')}</div>`).join('')}
      <div class="nav-foot">
        <div><b>${esc(SES.nombre)}</b></div>
        <div class="muted">${esc(ROLES[SES.rol].n)} · ${esc(SES.usuario)}</div>
        <div class="row" style="margin-top:.5rem">
          <button class="btn sm" data-act="tema" title="Cambiar tema">${ico('tema')}</button>
          <button class="btn sm" data-act="salir">${ico('salir')} Salir</button>
        </div>
        <div class="muted" style="margin-top:.5rem;font-size:.72rem">v${APP_VERSION} · banco ${esc(B.version)}</div>
      </div>
    </nav>
    <div class="main">
      <div class="topbar no-print">
        <button class="btn sm menu-btn" data-act="menu" aria-label="Abrir menú">${ico('menu')}</button>
        <label class="muted" for="sel-eval" style="font-size:.8rem">Evaluación activa</label>
        <select id="sel-eval" data-chg="eval-activa">
          ${DB.evals.length ? '' : '<option value="">— Sin evaluaciones —</option>'}
          ${DB.evals.map((e) => `<option value="${esc(e.id)}" ${e.id === DB.evalActiva ? 'selected' : ''}>${esc(e.nombre)} (${esc(e.estado)})</option>`).join('')}
        </select>
        ${ev ? `<span class="badge ${ev.estado === 'Cerrada' ? 'b-neutral' : ev.estado === 'En revisión' ? 'b-warn' : 'b-info'}">${esc(ev.estado)}</span>` : ''}
        <span class="grow"></span>
        ${FS.estado === 'activo' ? '<span class="badge b-good" title="Cada cambio se escribe también en el archivo local vinculado">Autoguardado en archivo</span>' : ''}
        ${FS.estado === 'permiso' && can('respaldo') ? '<button class="btn sm" data-act="fs-reactivar">Reactivar autoguardado</button>' : ''}
        ${avisoRespaldo ? `<a class="badge b-warn" href="#/admin/respaldos">${dias == null ? 'Sin respaldo' : 'Último respaldo hace ' + dias + ' días'}</a>` : ''}
      </div>
      <main class="content" id="contenido">${contenido}</main>
    </div>
  </div>`;
}

/* Delegación de eventos ------------------------------------------------ */
const ACT = {};
const CHG = {};
document.addEventListener('click', (e) => {
  const t = e.target.closest('[data-act]');
  if (!t) return;
  if (t.dataset.act === 'modal-fondo') { if (e.target === t) cerrarModal('cancel'); return; }
  const fn = ACT[t.dataset.act];
  if (fn) { e.preventDefault(); Promise.resolve(fn(t, e)).catch((err) => { console.error(err); toast(err.message || String(err), true); }); }
});
document.addEventListener('change', (e) => {
  const t = e.target.closest('[data-chg]');
  if (!t) return;
  const fn = CHG[t.dataset.chg];
  if (fn) Promise.resolve(fn(t, e)).catch((err) => { console.error(err); toast(err.message || String(err), true); });
});
document.addEventListener('submit', (e) => {
  const f = e.target.closest('form[data-submit]');
  if (!f) return;
  e.preventDefault();
  const fn = ACT[f.dataset.submit];
  if (fn) Promise.resolve(fn(f, e)).catch((err) => { console.error(err); toast(err.message || String(err), true); });
});
ACT.tema = () => alternarTema();
ACT.salir = () => logout();
ACT.menu = () => $('#nav').classList.toggle('open');
ACT['fs-reactivar'] = async () => { await fsReactivar(); render(); };
CHG['eval-activa'] = (t) => { DB.evalActiva = t.value; guardar(); render(); };

/* ---------------------------------------------------------------------
 * Primer uso, acceso y cambio de contraseña
 * ------------------------------------------------------------------- */
function renderInicio(app) {
  app.innerHTML = `
  <div class="login-wrap"><div class="login" style="width:min(560px,100%)">
    <div class="brand">${LOGO}<div><b>SECI · COSO ERM</b><span>Sistema de Evaluación de Control Interno</span></div></div>
    <div class="card">
      <h1>Configuración inicial</h1>
      <p class="muted">No hay información en este navegador. Configure la institución y la cuenta de <b>Sistemas</b>, o restaure un respaldo existente.</p>
      <form data-submit="setup" autocomplete="off">
        ${campo('institucion', 'Institución', '', { req: true, ph: 'Razón social de la entidad' })}
        ${campo('tipo', 'Tipo de entidad', 'SOCAP', { opciones: ['SOCAP', 'SOFIPO', 'SOFOM', 'Caja de ahorro', 'Otra'] })}
        <div class="grid g2">
          ${campo('nombre', 'Nombre del responsable de Sistemas', '', { req: true })}
          ${campo('usuario', 'Usuario de Sistemas', 'sistemas', { req: true })}
          ${campo('pass', 'Contraseña', '', { tipo: 'password', req: true, ayuda: 'Mínimo 8 caracteres, con letras y números.', attrs: 'autocomplete="new-password"' })}
          ${campo('pass2', 'Confirmar contraseña', '', { tipo: 'password', req: true, attrs: 'autocomplete="new-password"' })}
        </div>
        ${campo('crearRoles', 'Crear también las cuentas de Auditor interno, Contralor interno y Administrador de riesgos (con contraseña temporal)', true, { tipo: 'checkbox' })}
        ${campo('demo', 'Cargar la evaluación de ejemplo del Excel original (para capacitación)', false, { tipo: 'checkbox' })}
        <div class="row end"><button class="btn primary" type="submit">Crear sistema</button></div>
      </form>
    </div>
    <div class="card">
      <h3>¿Ya tiene un respaldo?</h3>
      <p class="muted">Restaure un archivo de respaldo <code>.json</code> (normal o cifrado) generado por este sistema.</p>
      <input type="file" accept=".json,application/json" data-chg="restaurar-inicio">
    </div>
    <p class="muted" style="font-size:.8rem;margin-top:1rem">La información se guarda únicamente en este equipo y navegador. Descargue respaldos periódicamente desde <i>Administración → Respaldos</i>.</p>
  </div></div>`;
}
ACT.setup = async (f) => {
  const d = leerForm(f);
  if (!d.institucion.trim() || !d.nombre.trim() || !d.usuario.trim()) return toast('Complete los campos obligatorios.', true);
  const err = politicaPassword(d.pass);
  if (err) return toast(err, true);
  if (d.pass !== d.pass2) return toast('Las contraseñas no coinciden.', true);
  DB = dbVacia();
  DB.config.institucion = d.institucion.trim();
  DB.config.tipo = d.tipo;
  const cred = await nuevaCredencial(d.pass);
  const admin = { id: uid('u'), usuario: d.usuario.trim(), nombre: d.nombre.trim(), rol: 'sistemas', activo: true, mustChange: false, creado: ahora(), ...cred };
  DB.users.push(admin);
  SES = { uid: admin.id, usuario: admin.usuario, rol: 'sistemas', nombre: admin.nombre, t: Date.now() };
  bitacora('Configuración inicial', 'Institución: ' + DB.config.institucion);
  const temporales = [];
  if (d.crearRoles) {
    for (const [usuario, rol, nombre] of [['auditor', 'auditor', 'Auditor interno'], ['contralor', 'contralor', 'Contralor interno'], ['riesgos', 'riesgos', 'Administrador de riesgos']]) {
      const pass = passwordTemporal();
      DB.users.push({ id: uid('u'), usuario, nombre, rol, activo: true, mustChange: true, creado: ahora(), ...(await nuevaCredencial(pass)) });
      temporales.push([usuario, ROLES[rol].n, pass]);
      bitacora('Alta de usuario', usuario + ' (' + ROLES[rol].n + ')');
    }
  }
  const ev = nuevaEvaluacion('Evaluación COSO ERM ' + new Date().getFullYear(), String(new Date().getFullYear()));
  if (d.demo) cargarDemo(ev);
  sessionStorage.setItem(SES_KEY, JSON.stringify(SES));
  guardar();
  render();
  if (temporales.length) {
    await modal({
      titulo: 'Contraseñas temporales',
      cuerpo: `<p>Entregue estas credenciales a cada responsable. Se solicitará cambiar la contraseña en el primer acceso. <b>No se volverán a mostrar.</b></p>
        <div class="tbl-wrap"><table class="tbl"><tr><th>Usuario</th><th>Rol</th><th>Contraseña temporal</th></tr>
        ${temporales.map((t) => `<tr><td><code>${esc(t[0])}</code></td><td>${esc(t[1])}</td><td><code>${esc(t[2])}</code></td></tr>`).join('')}</table></div>`,
      botones: [{ id: 'csv', t: 'Descargar lista' }, { id: 'ok', t: 'Entendido', primary: true }],
    }).then((r) => {
      if (r === 'csv') descargar('SECI_credenciales_temporales.csv', aCSV(temporales.map((t) => ({ usuario: t[0], rol: t[1], password: t[2] })), [{ key: 'usuario' }, { key: 'rol' }, { key: 'password' }]), 'text/csv');
      cerrarModal();
    });
  }
};
CHG['restaurar-inicio'] = async (t) => {
  const f = t.files[0];
  if (!f) return;
  const nuevo = await abrirRespaldo(f);
  if (!nuevo) return;
  DB = nuevo;
  SES = null;
  bitacora('Restauración de respaldo', 'Desde pantalla inicial: ' + f.name);
  guardar();
  toast('Respaldo restaurado. Inicie sesión con un usuario del respaldo.');
  render();
};

function renderLogin(app) {
  app.innerHTML = `
  <div class="login-wrap"><div class="login">
    <div class="brand">${LOGO}<div><b>SECI · COSO ERM</b><span>${esc(DB.config.institucion)}</span></div></div>
    <div class="card">
      <h1>Iniciar sesión</h1>
      <form data-submit="login">
        ${campo('usuario', 'Usuario', '', { req: true, attrs: 'autocomplete="username" autofocus' })}
        ${campo('pass', 'Contraseña', '', { tipo: 'password', req: true, attrs: 'autocomplete="current-password"' })}
        <div id="login-err"></div>
        <button class="btn primary" type="submit" style="width:100%;justify-content:center">Entrar</button>
      </form>
    </div>
    <p class="muted" style="font-size:.8rem;margin-top:1rem">Perfiles: Auditor interno · Contralor interno · Administrador de riesgos · Sistemas. Si olvidó su contraseña, solicite el restablecimiento al área de Sistemas.</p>
  </div></div>`;
  const u = $('[name=usuario]');
  if (u) u.focus();
}
ACT.login = async (f) => {
  const d = leerForm(f);
  const btn = f.querySelector('button[type=submit]');
  btn.disabled = true;
  try {
    await login(d.usuario, d.pass);
    if (!DB.evalActiva && DB.evals.length) DB.evalActiva = DB.evals[DB.evals.length - 1].id;
    render();
  } catch (e) {
    $('#login-err').innerHTML = `<div class="callout crit" style="margin-bottom:.75rem">${esc(e.message)}</div>`;
    btn.disabled = false;
  }
};
function renderCambioObligatorio(app) {
  app.innerHTML = `
  <div class="login-wrap"><div class="login">
    <div class="brand">${LOGO}<div><b>SECI · COSO ERM</b><span>${esc(DB.config.institucion)}</span></div></div>
    <div class="card">
      <h1>Cambie su contraseña</h1>
      <p class="muted">Por seguridad, defina una contraseña personal antes de continuar.</p>
      <form data-submit="cambio-pass">
        ${campo('actual', 'Contraseña actual (temporal)', '', { tipo: 'password', req: true })}
        ${campo('nueva', 'Nueva contraseña', '', { tipo: 'password', req: true, ayuda: 'Mínimo 8 caracteres, con letras y números.', attrs: 'autocomplete="new-password"' })}
        ${campo('nueva2', 'Confirmar nueva contraseña', '', { tipo: 'password', req: true, attrs: 'autocomplete="new-password"' })}
        <div class="row end"><button class="btn" type="button" data-act="salir">Salir</button><button class="btn primary" type="submit">Guardar</button></div>
      </form>
    </div>
  </div></div>`;
}
ACT['cambio-pass'] = async (f) => {
  const d = leerForm(f);
  const u = usuarioActual();
  if (await hashPassword(d.actual, u.salt, u.alg) !== u.hash) return toast('La contraseña actual no es correcta.', true);
  const err = politicaPassword(d.nueva);
  if (err) return toast(err, true);
  if (d.nueva !== d.nueva2) return toast('Las contraseñas no coinciden.', true);
  if (d.nueva === d.actual) return toast('La nueva contraseña debe ser distinta de la actual.', true);
  Object.assign(u, await nuevaCredencial(d.nueva), { mustChange: false, cambioPass: ahora() });
  bitacora('Cambio de contraseña', u.usuario);
  guardar();
  toast('Contraseña actualizada.');
  if (f.closest('.login')) render(); else f.reset();
};
