'use strict';
/* =====================================================================
 * SECI · Sistema de Evaluación de Control Interno con base en COSO ERM
 * Aplicación de un solo archivo: funciona sin servidor ni conexión.
 * Persistencia: localStorage del navegador + respaldos JSON exportables
 * + (opcional) autoguardado a un archivo local (File System Access API).
 * ===================================================================== */

const B = window.SECI_BANCO;
const APP_VERSION = '1.0.0';
const DB_KEY = 'seci.coso.db';
const SES_KEY = 'seci.coso.sesion';
const THEME_KEY = 'seci.coso.tema';
const ESQUEMA = 1;
const MAX_BITACORA = 5000;

/* ---------------------------------------------------------------------
 * Utilidades
 * ------------------------------------------------------------------- */
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const uid = (p = '') => p + Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
const hoy = () => new Date().toISOString().slice(0, 10);
const ahora = () => new Date().toISOString();
const periodoActual = () => new Date().toISOString().slice(0, 7);
const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
const fmtFecha = (iso) => {
  if (!iso) return '';
  const d = new Date(iso.length <= 10 ? iso + 'T12:00:00' : iso);
  if (isNaN(d)) return esc(iso);
  return d.toLocaleDateString('es-MX', { year: 'numeric', month: 'short', day: '2-digit' });
};
const fmtFechaHora = (iso) => iso ? new Date(iso).toLocaleString('es-MX', { dateStyle: 'short', timeStyle: 'short' }) : '';
const fmtN = (x, d = 2) => (x == null || isNaN(x)) ? '—' : Number(x).toLocaleString('es-MX', { minimumFractionDigits: d, maximumFractionDigits: d });
const fmtPct = (x, d = 1) => (x == null || isNaN(x)) ? '—' : fmtN(x * 100, d) + '%';
const fmtMon = (x) => (x == null || isNaN(x)) ? '—' : Number(x).toLocaleString('es-MX', { style: 'currency', currency: 'MXN', maximumFractionDigits: 0 });
const norm = (s) => String(s ?? '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
const num = (v) => { if (v == null || v === '') return null; const x = Number(String(v).replace(/[$,\s%]/g, '')); return isNaN(x) ? null : x; };
const sum = (arr) => arr.reduce((s, x) => s + (x || 0), 0);
const avg = (arr) => { const v = arr.filter((x) => x != null && !isNaN(x)); return v.length ? sum(v) / v.length : null; };
const trunc = (s, n) => { s = String(s ?? ''); return s.length > n ? s.slice(0, n - 1) + '…' : s; };
const sello = () => new Date().toISOString().replace(/[-:]/g, '').slice(0, 13).replace('T', '_');

function descargar(nombre, contenido, tipo = 'application/json') {
  const blob = contenido instanceof Blob ? contenido : new Blob([contenido], { type: tipo + ';charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = nombre;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500);
}
function leerArchivo(file) {
  return new Promise((res, rej) => {
    const r = new FileReader();
    r.onload = () => res(String(r.result));
    r.onerror = () => rej(r.error);
    r.readAsText(file, 'utf-8');
  });
}

/* CSV ---------------------------------------------------------------- */
function aCSV(filas, columnas) {
  const q = (v) => {
    const s = v == null ? '' : Array.isArray(v) ? v.join('|') : String(v);
    return /[",\n\r;]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  };
  const lineas = [columnas.map((c) => q(c.label || c.key)).join(',')];
  for (const f of filas) lineas.push(columnas.map((c) => q(typeof c.get === 'function' ? c.get(f) : f[c.key])).join(','));
  return '﻿' + lineas.join('\r\n');
}
function deCSV(texto) {
  texto = texto.replace(/^﻿/, '');
  const primera = texto.split(/\r?\n/, 1)[0] || '';
  const delim = (primera.match(/;/g) || []).length > (primera.match(/,/g) || []).length ? ';'
    : (primera.match(/\t/g) || []).length > (primera.match(/,/g) || []).length ? '\t' : ',';
  const filas = [];
  let fila = [], campo = '', comillas = false;
  for (let i = 0; i < texto.length; i++) {
    const c = texto[i];
    if (comillas) {
      if (c === '"') { if (texto[i + 1] === '"') { campo += '"'; i++; } else comillas = false; }
      else campo += c;
    } else if (c === '"') comillas = true;
    else if (c === delim) { fila.push(campo); campo = ''; }
    else if (c === '\n' || c === '\r') {
      if (c === '\r' && texto[i + 1] === '\n') i++;
      fila.push(campo); campo = '';
      if (fila.some((x) => x.trim() !== '')) filas.push(fila);
      fila = [];
    } else campo += c;
  }
  fila.push(campo);
  if (fila.some((x) => x.trim() !== '')) filas.push(fila);
  if (!filas.length) return { encabezados: [], filas: [] };
  const enc = filas[0].map((h) => norm(h));
  return { encabezados: enc, filas: filas.slice(1).map((f) => Object.fromEntries(enc.map((h, i) => [h, (f[i] ?? '').trim()]))) };
}

/* SHA-256 (síncrono, para la bitácora encadenada y como respaldo) ------ */
const K256 = new Uint32Array([0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2]);
function sha256(texto) {
  const msg = new TextEncoder().encode(texto);
  const l = msg.length;
  const nb = (l + 9 + 63) >> 6;
  const w = new Uint32Array(nb * 16);
  for (let i = 0; i < l; i++) w[i >> 2] |= msg[i] << (24 - (i & 3) * 8);
  w[l >> 2] |= 0x80 << (24 - (l & 3) * 8);
  w[nb * 16 - 2] = Math.floor(l / 0x20000000);
  w[nb * 16 - 1] = (l * 8) >>> 0;
  const H = new Uint32Array([0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]);
  const W = new Uint32Array(64);
  for (let blk = 0; blk < nb; blk++) {
    for (let t = 0; t < 16; t++) W[t] = w[blk * 16 + t];
    for (let t = 16; t < 64; t++) {
      const x = W[t - 15], y = W[t - 2];
      const s0 = ((x >>> 7) | (x << 25)) ^ ((x >>> 18) | (x << 14)) ^ (x >>> 3);
      const s1 = ((y >>> 17) | (y << 15)) ^ ((y >>> 19) | (y << 13)) ^ (y >>> 10);
      W[t] = (W[t - 16] + s0 + W[t - 7] + s1) | 0;
    }
    let [a, b, c, d, e, f, g, h] = H;
    for (let t = 0; t < 64; t++) {
      const S1 = ((e >>> 6) | (e << 26)) ^ ((e >>> 11) | (e << 21)) ^ ((e >>> 25) | (e << 7));
      const ch = (e & f) ^ (~e & g);
      const t1 = (h + S1 + ch + K256[t] + W[t]) | 0;
      const S0 = ((a >>> 2) | (a << 30)) ^ ((a >>> 13) | (a << 19)) ^ ((a >>> 22) | (a << 10));
      const mj = (a & b) ^ (a & c) ^ (b & c);
      const t2 = (S0 + mj) | 0;
      h = g; g = f; f = e; e = (d + t1) | 0; d = c; c = b; b = a; a = (t1 + t2) | 0;
    }
    H[0] += a; H[1] += b; H[2] += c; H[3] += d; H[4] += e; H[5] += f; H[6] += g; H[7] += h;
  }
  return [...H].map((x) => x.toString(16).padStart(8, '0')).join('');
}
const b64 = (buf) => btoa(String.fromCharCode(...new Uint8Array(buf)));
const deB64 = (s) => Uint8Array.from(atob(s), (c) => c.charCodeAt(0));
const aleatorio = (n = 16) => { const a = new Uint8Array(n); crypto.getRandomValues(a); return a; };
const hayCrypto = () => !!(window.crypto && crypto.subtle);

/* Contraseñas: PBKDF2-SHA256 (WebCrypto) o SHA-256 iterado si no existe. */
async function hashPassword(pass, saltB64, alg) {
  if (alg === 'pbkdf2') {
    if (!hayCrypto()) throw new Error('Este navegador no permite verificar la contraseña (WebCrypto no disponible). Abra el archivo directamente desde el disco o mediante https.');
    const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(pass), 'PBKDF2', false, ['deriveBits']);
    const bits = await crypto.subtle.deriveBits({ name: 'PBKDF2', salt: deB64(saltB64), iterations: 150000, hash: 'SHA-256' }, key, 256);
    return b64(bits);
  }
  let h = saltB64 + ':' + pass;
  for (let i = 0; i < 20000; i++) h = sha256(h + saltB64);
  return h;
}
async function nuevaCredencial(pass) {
  const salt = b64(aleatorio(16));
  const alg = hayCrypto() ? 'pbkdf2' : 'sha256i';
  return { salt, alg, hash: await hashPassword(pass, salt, alg) };
}
function politicaPassword(p) {
  if (!p || p.length < 8) return 'La contraseña debe tener al menos 8 caracteres.';
  if (!/[a-záéíóúñ]/i.test(p) || !/\d/.test(p)) return 'La contraseña debe combinar letras y números.';
  return null;
}
function passwordTemporal() {
  const abc = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789';
  const r = aleatorio(10);
  let s = [...r].map((x) => abc[x % abc.length]).join('');
  return s.slice(0, 5) + (r[0] % 10) + s.slice(5);
}

/* Cifrado de respaldos: AES-GCM con llave PBKDF2 a partir de una frase. */
async function llaveFrase(frase, salt) {
  const base = await crypto.subtle.importKey('raw', new TextEncoder().encode(frase), 'PBKDF2', false, ['deriveKey']);
  return crypto.subtle.deriveKey({ name: 'PBKDF2', salt, iterations: 200000, hash: 'SHA-256' }, base, { name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt']);
}
async function cifrar(texto, frase) {
  const salt = aleatorio(16), iv = aleatorio(12);
  const k = await llaveFrase(frase, salt);
  const ct = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, k, new TextEncoder().encode(texto));
  return { salt: b64(salt), iv: b64(iv), datos: b64(ct) };
}
async function descifrar(obj, frase) {
  const k = await llaveFrase(frase, deB64(obj.salt));
  const pt = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: deB64(obj.iv) }, k, deB64(obj.datos));
  return new TextDecoder().decode(pt);
}

/* ---------------------------------------------------------------------
 * Roles y permisos
 * ------------------------------------------------------------------- */
const ROLES = {
  sistemas: { n: 'Sistemas', d: 'Administra usuarios, respaldos, bitácora, configuración y conectores.' },
  contralor: { n: 'Contralor interno', d: 'Responde la evaluación COSO ERM, documenta evidencias y planes de solución; opera la mesa de control y la contraloría de crédito.' },
  auditor: { n: 'Auditor interno', d: 'Valida la evaluación, registra hallazgos, administra el plan anual de auditoría y cierra evaluaciones.' },
  riesgos: { n: 'Administrador de riesgos', d: 'Administra la matriz de riesgos, el apetito y los indicadores clave de riesgo (KRI); analiza la cartera.' },
};
const PERMISOS = {
  admin: ['sistemas'],
  respaldo: ['sistemas'],
  'integra.config': ['sistemas'],
  catalogos: ['sistemas', 'contralor'],
  'eval.responder': ['contralor'],
  'eval.datos': ['contralor'],
  'eval.gestionar': ['contralor', 'auditor'],
  'eval.validar': ['auditor'],
  'eval.cerrar': ['auditor'],
  'eval.riesgo': ['riesgos', 'contralor'],
  hallazgos: ['auditor', 'contralor'],
  'hallazgos.cerrar': ['auditor'],
  auditplan: ['auditor'],
  mesa: ['contralor'],
  cartera: ['contralor', 'riesgos'],
  riesgos: ['riesgos'],
  kris: ['riesgos'],
  conclusiones: ['contralor', 'auditor'],
};

/* ---------------------------------------------------------------------
 * Base de datos local
 * ------------------------------------------------------------------- */
let DB = null;
let SES = null; // { uid, usuario, rol, nombre }

const CHECKLIST_MESA = [
  ['Solicitud de crédito completa y firmada', true],
  ['Identificación oficial vigente, CURP y RFC', false],
  ['Comprobante de domicilio (no mayor a 3 meses)', false],
  ['Consulta a Sociedad de Información Crediticia autorizada y vigente', true],
  ['Análisis de capacidad de pago documentado', true],
  ['Autorización por el órgano o nivel facultado', true],
  ['Garantías y/o avales formalizados y valuados', true],
  ['Contrato y pagaré firmados conforme a las condiciones aprobadas', true],
  ['Expediente PLD/FT: conocimiento del socio, perfil transaccional y listas', true],
  ['Seguros contratados cuando aplique', false],
  ['Tasa, CAT y comisiones conforme a lo autorizado y publicado', false],
  ['Aviso de privacidad y consentimientos firmados', false],
];
const KRIS_BASE = [
  { nombre: 'Índice de morosidad (IMOR)', categoria: 'Crédito', unidad: '%', sentido: 'alto', apetito: 4, tolerancia: 6, capacidad: 8, auto: 'imor' },
  { nombre: 'Índice de cobertura de reservas (ICOR)', categoria: 'Crédito', unidad: '%', sentido: 'bajo', apetito: 120, tolerancia: 100, capacidad: 90, auto: '' },
  { nombre: 'Concentración de los 20 principales acreditados', categoria: 'Crédito', unidad: '%', sentido: 'alto', apetito: 15, tolerancia: 20, capacidad: 25, auto: 'conc20' },
  { nombre: 'Expedientes con excepción en mesa de control', categoria: 'Crédito', unidad: '%', sentido: 'alto', apetito: 5, tolerancia: 10, capacidad: 15, auto: 'excMesa' },
  { nombre: 'Coeficiente de liquidez', categoria: 'Liquidez', unidad: '%', sentido: 'bajo', apetito: 20, tolerancia: 15, capacidad: 10, auto: '' },
  { nombre: 'Nivel de capitalización (NICAP)', categoria: 'Solvencia', unidad: '%', sentido: 'bajo', apetito: 150, tolerancia: 125, capacidad: 100, auto: '' },
  { nombre: 'Planes de solución vencidos', categoria: 'Control interno', unidad: '#', sentido: 'alto', apetito: 0, tolerancia: 3, capacidad: 6, auto: 'planesVenc' },
  { nombre: 'Hallazgos de auditoría vencidos', categoria: 'Control interno', unidad: '#', sentido: 'alto', apetito: 0, tolerancia: 2, capacidad: 5, auto: 'hallVenc' },
];
const RESPONSABLES_BASE = {
  areas: ['Consejo de Administración', 'Consejo de Vigilancia', 'Comité de Auditoría', 'Comité de Riesgos', 'Comité de Crédito', 'Gerencia General', 'Contraloría Interna', 'Auditoría Interna', 'Administración de Riesgos', 'Contraloría de Crédito y Mesa de Control', 'Crédito y Cobranza', 'Captación', 'Contabilidad y Finanzas', 'Recursos Humanos', 'Sistemas', 'Cumplimiento PLD/FT', 'Jurídico'],
  cargos: ['Presidente del Consejo de Administración', 'Presidente del Comité de Auditoría', 'Director o Gerente General', 'Contralor Interno', 'Auditor Interno', 'Administrador de Riesgos', 'Contralor de Crédito', 'Analista de Mesa de Control', 'Gerente de Crédito', 'Oficial de Cumplimiento', 'Responsable de Sistemas', 'Contador General'],
};

function dbVacia() {
  return {
    meta: { esquema: ESQUEMA, creado: ahora(), banco: B.version, app: APP_VERSION, ultimoRespaldo: null, instancia: uid('i') },
    config: { institucion: '', nombreComercial: '', tipo: 'SOCAP', pesos: Object.fromEntries(B.components.map((c) => [c.code, c.peso])), umbralIntegracion: 0.7, sesionMin: 20, diasRespaldo: 7 },
    users: [],
    evals: [],
    evalActiva: null,
    hallazgos: [],
    auditorias: [],
    riesgos: [],
    kris: KRIS_BASE.map((k) => ({ id: uid('k'), ...k, valores: [] })),
    mesa: { checklist: CHECKLIST_MESA.map(([t, c], i) => ({ id: 'M' + String(i + 1).padStart(2, '0'), t, critico: c })), revisiones: [] },
    cartera: { cortes: [] },
    normativa: B.normativa.map((n) => ({ id: uid('n'), ...n, documento: '', actualizacion: '', comentarios: '' })),
    responsables: JSON.parse(JSON.stringify(RESPONSABLES_BASE)),
    integraciones: { endpoints: [] },
    bitacora: [],
  };
}
function cargarDB() {
  try {
    const raw = localStorage.getItem(DB_KEY);
    if (!raw) return null;
    return migrar(JSON.parse(raw));
  } catch (e) {
    console.error(e);
    return null;
  }
}
function migrar(db) {
  const base = dbVacia();
  for (const k of Object.keys(base)) if (db[k] == null) db[k] = base[k];
  db.meta = { ...base.meta, ...db.meta };
  db.config = { ...base.config, ...db.config, pesos: { ...base.config.pesos, ...(db.config || {}).pesos } };
  db.mesa = { ...base.mesa, ...db.mesa };
  db.meta.esquema = ESQUEMA;
  return db;
}
let _tGuardar = null;
function guardar() {
  try {
    localStorage.setItem(DB_KEY, JSON.stringify(DB));
  } catch (e) {
    toast('No fue posible guardar en el navegador (espacio insuficiente). Descargue un respaldo y depure la bitácora.', true);
    console.error(e);
  }
  clearTimeout(_tGuardar);
  _tGuardar = setTimeout(autoguardarArchivo, 1500);
}

/* Bitácora encadenada ------------------------------------------------- */
function bitacora(accion, detalle = '') {
  if (!DB) return;
  const prev = DB.bitacora.length ? DB.bitacora[DB.bitacora.length - 1].h : '0';
  const e = { ts: ahora(), usuario: SES ? SES.usuario : '—', rol: SES ? SES.rol : '—', accion, detalle: String(detalle).slice(0, 400), prev };
  e.h = sha256(prev + '|' + e.ts + '|' + e.usuario + '|' + e.rol + '|' + e.accion + '|' + e.detalle);
  DB.bitacora.push(e);
  if (DB.bitacora.length > MAX_BITACORA) DB.bitacora.splice(0, DB.bitacora.length - MAX_BITACORA);
}
function verificarBitacora() {
  const L = DB.bitacora;
  for (let i = 0; i < L.length; i++) {
    const e = L[i];
    if (i > 0 && e.prev !== L[i - 1].h) return { ok: false, i, e };
    const h = sha256(e.prev + '|' + e.ts + '|' + e.usuario + '|' + e.rol + '|' + e.accion + '|' + e.detalle);
    if (h !== e.h) return { ok: false, i, e };
  }
  return { ok: true, n: L.length };
}

/* Autoguardado a archivo local (Chrome/Edge) --------------------------- */
const FS = { handle: null, estado: 'no' }; // no | activo | permiso | nosoportado
const fsSoportado = () => 'showSaveFilePicker' in window;
function idb() {
  return new Promise((res, rej) => {
    const r = indexedDB.open('seci.coso.fs', 1);
    r.onupgradeneeded = () => r.result.createObjectStore('h');
    r.onsuccess = () => res(r.result);
    r.onerror = () => rej(r.error);
  });
}
async function idbSet(k, v) { const d = await idb(); return new Promise((res, rej) => { const t = d.transaction('h', 'readwrite'); v == null ? t.objectStore('h').delete(k) : t.objectStore('h').put(v, k); t.oncomplete = res; t.onerror = () => rej(t.error); }); }
async function idbGet(k) { const d = await idb(); return new Promise((res, rej) => { const t = d.transaction('h').objectStore('h').get(k); t.onsuccess = () => res(t.result); t.onerror = () => rej(t.error); }); }
async function fsIniciar() {
  if (!fsSoportado()) { FS.estado = 'nosoportado'; return; }
  try {
    FS.handle = await idbGet('archivo');
    if (!FS.handle) { FS.estado = 'no'; return; }
    const p = await FS.handle.queryPermission({ mode: 'readwrite' });
    FS.estado = p === 'granted' ? 'activo' : 'permiso';
  } catch { FS.estado = 'no'; }
}
async function fsVincular() {
  const h = await window.showSaveFilePicker({ suggestedName: 'SECI_datos.json', types: [{ description: 'Respaldo SECI', accept: { 'application/json': ['.json'] } }] });
  FS.handle = h;
  await idbSet('archivo', h);
  FS.estado = 'activo';
  await autoguardarArchivo();
  bitacora('Autoguardado', 'Vinculó archivo local ' + h.name);
  guardar();
}
async function fsReactivar() {
  if (!FS.handle) return;
  const p = await FS.handle.requestPermission({ mode: 'readwrite' });
  FS.estado = p === 'granted' ? 'activo' : 'permiso';
  if (FS.estado === 'activo') await autoguardarArchivo();
}
async function fsDesvincular() { FS.handle = null; FS.estado = 'no'; await idbSet('archivo', null); }
async function autoguardarArchivo() {
  if (FS.estado !== 'activo' || !FS.handle) return;
  try {
    const w = await FS.handle.createWritable();
    await w.write(JSON.stringify(paqueteRespaldo()));
    await w.close();
    FS.ultimo = ahora();
  } catch (e) {
    FS.estado = 'permiso';
    console.warn('Autoguardado', e);
  }
}
function paqueteRespaldo() {
  const datos = JSON.stringify(DB);
  return { formato: 'seci-respaldo', version: 1, app: APP_VERSION, banco: B.version, generado: ahora(), por: SES ? SES.usuario : '', institucion: DB.config.institucion, integridad: sha256(datos), datos: DB };
}

/* ---------------------------------------------------------------------
 * Sesión
 * ------------------------------------------------------------------- */
function can(p) { return !!SES && (PERMISOS[p] || []).includes(SES.rol); }
function usuarioActual() { return SES && DB.users.find((u) => u.id === SES.uid); }
async function login(usuario, pass) {
  const u = DB.users.find((x) => x.usuario.toLowerCase() === usuario.trim().toLowerCase());
  if (!u) { SES = null; bitacora('Acceso fallido', 'Usuario inexistente: ' + usuario); guardar(); throw new Error('Usuario o contraseña incorrectos.'); }
  if (!u.activo) throw new Error('El usuario está inactivo. Contacte al área de Sistemas.');
  if (u.bloqueoHasta && new Date(u.bloqueoHasta) > new Date()) {
    throw new Error('Usuario bloqueado temporalmente por intentos fallidos. Intente después de ' + new Date(u.bloqueoHasta).toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' }));
  }
  const h = await hashPassword(pass, u.salt, u.alg);
  if (h !== u.hash) {
    u.intentos = (u.intentos || 0) + 1;
    if (u.intentos >= 5) { u.bloqueoHasta = new Date(Date.now() + 10 * 60000).toISOString(); u.intentos = 0; }
    SES = null;
    bitacora('Acceso fallido', 'Contraseña incorrecta: ' + u.usuario);
    guardar();
    throw new Error('Usuario o contraseña incorrectos.');
  }
  u.intentos = 0; u.bloqueoHasta = null; u.ultimoAcceso = ahora();
  SES = { uid: u.id, usuario: u.usuario, rol: u.rol, nombre: u.nombre, t: Date.now() };
  sessionStorage.setItem(SES_KEY, JSON.stringify(SES));
  bitacora('Inicio de sesión', ROLES[u.rol].n);
  guardar();
}
function logout(motivo = 'Cierre de sesión') {
  if (SES) { bitacora(motivo, ''); guardar(); }
  SES = null;
  sessionStorage.removeItem(SES_KEY);
  location.hash = '';
  render();
}
function restaurarSesion() {
  try {
    const s = JSON.parse(sessionStorage.getItem(SES_KEY) || 'null');
    if (!s) return;
    const u = DB.users.find((x) => x.id === s.uid && x.activo);
    if (!u) return;
    if (Date.now() - s.t > DB.config.sesionMin * 60000) { sessionStorage.removeItem(SES_KEY); return; }
    SES = { uid: u.id, usuario: u.usuario, rol: u.rol, nombre: u.nombre, t: Date.now() };
  } catch { /* sesión inválida */ }
}
function tocarSesion() {
  if (!SES) return;
  SES.t = Date.now();
  sessionStorage.setItem(SES_KEY, JSON.stringify(SES));
}
setInterval(() => {
  if (SES && DB && Date.now() - SES.t > DB.config.sesionMin * 60000) {
    logout('Sesión expirada por inactividad');
    toast('La sesión se cerró por inactividad.');
  }
}, 30000);
['click', 'keydown'].forEach((ev) => document.addEventListener(ev, () => { if (SES && Date.now() - SES.t > 15000) tocarSesion(); }, true));

/* ---------------------------------------------------------------------
 * Banco de preguntas y cálculo
 * ------------------------------------------------------------------- */
const PREGUNTAS = [];
const PRINCIPIOS = [];
for (const c of B.components) for (const p of c.principles) {
  PRINCIPIOS.push({ ...p, comp: c.code });
  for (const q of p.q) PREGUNTAS.push({ ...q, comp: c.code, p: p.n });
}
const PREG = Object.fromEntries(PREGUNTAS.map((q) => [q.id, q]));
const COMP = Object.fromEntries(B.components.map((c) => [c.code, c]));
const TEMAS = [...new Set(PREGUNTAS.map((q) => q.tema).filter(Boolean))].sort();
const ATR = B.atributos;

const lead = (a) => { let n = 0; for (const x of a) { if (x === 1) n++; else break; } return n; };
function nivel(a) {
  if (!a) return null;
  const L = lead(a);
  return L >= 8 ? 5 : L >= 7 ? 4 : L >= 5 ? 3 : L >= 4 ? 2 : L >= 2 ? 1 : 0;
}
const noAcumulativo = (a) => !!a && a.slice(lead(a)).some((x) => x === 1);
const presente = (a) => !!a && (a[0] + a[1] + a[2] + a[3]) >= 3;
const funcionando = (a) => !!a && (a[4] + a[5] + a[6] + a[7]) >= 3;
function riesgoQ(a) {
  if (!a) return null;
  const s = sum(a);
  return s > 6 ? 'Bajo' : s > 4 ? 'Moderado' : 'Alto';
}
function madurez(score) {
  if (score == null) return '—';
  return score < 1 ? 'Inexistente' : score < 2 ? 'Inicial' : score < 3 ? 'Repetible' : score < 4 ? 'Definido' : score < 5 ? 'Gestionado' : 'Optimizado';
}
const clsMadurez = (s) => s == null ? 'b-neutral' : s < 2 ? 'b-crit' : s < 3 ? 'b-serious' : s < 4 ? 'b-warn' : 'b-good';
const clsRiesgo = (r) => ({ Bajo: 'b-good', Moderado: 'b-warn', Alto: 'b-crit' }[r] || 'b-neutral');
const badgeMadurez = (s) => s == null ? '<span class="muted">Sin datos</span>' : `<span class="badge ${clsMadurez(s)}">${esc(madurez(s))}</span>`;
const badgeRiesgo = (r) => r ? `<span class="badge ${clsRiesgo(r)}">Riesgo ${esc(r.toLowerCase())}</span>` : '';

function evalActiva() { return DB.evals.find((e) => e.id === DB.evalActiva) || null; }
const evalBloqueada = (ev) => !ev || ev.estado === 'Cerrada';

function planEstado(r) {
  if (!r || !(r.plan || r.defi)) return null;
  if ((r.avance || 0) >= 100 || r.estadoPlan === 'Concluido') return 'Concluido';
  if (r.ff && r.ff < hoy()) return 'Vencido';
  return r.estadoPlan || ((r.avance || 0) > 0 ? 'En proceso' : 'Pendiente');
}
function requierePlan(r) {
  const lv = nivel(r && r.a);
  return lv != null && lv < 4 && ['Alta', 'Media'].includes(r.prio);
}

function stats(ev) {
  const R = (ev && ev.resp) || {};
  const pesos = DB.config.pesos;
  const out = { comps: [], total: 0, contestadas: 0, errores: [], sinEvidencia: [], sinPlan: [], porValidar: 0, validadas: 0, observadas: 0, riesgo: { Bajo: 0, Moderado: 0, Alto: 0 }, presente: 0, funcionando: 0, planes: { total: 0, Vencido: 0, Concluido: 0, 'En proceso': 0, Pendiente: 0 } };
  for (const c of B.components) {
    const cs = { code: c.code, name: c.name, peso: pesos[c.code] ?? c.peso, principles: [], total: 0, contestadas: 0, presente: 0, funcionando: 0, riesgo: { Bajo: 0, Moderado: 0, Alto: 0 } };
    for (const p of c.principles) {
      const ps = { n: p.n, t: p.t, total: 0, contestadas: 0, suma: 0, presente: 0, funcionando: 0 };
      for (const q of p.q) {
        ps.total++;
        const r = R[q.id];
        if (r && r.a) {
          const lv = nivel(r.a);
          ps.contestadas++; ps.suma += lv;
          if (presente(r.a)) ps.presente++;
          if (funcionando(r.a)) ps.funcionando++;
          const rq = riesgoQ(r.a);
          cs.riesgo[rq]++; out.riesgo[rq]++;
          if (noAcumulativo(r.a)) out.errores.push({ id: q.id, motivo: 'Atributos no acumulativos: hay atributos marcados después de uno sin cumplir (el nivel se calcula hasta el primer atributo faltante).' });
          const ev2 = r.ev || [];
          const faltan = [];
          if (r.a[0] && r.a[1] && !ev2[0]) faltan.push('a-b');
          for (let k = 2; k < 8; k++) if (r.a[k] && !ev2[k - 1]) faltan.push(ATR[k].k);
          if (faltan.length) out.sinEvidencia.push({ id: q.id, faltan });
          if (requierePlan(r) && !r.plan) out.sinPlan.push(q.id);
          const v = r.val && r.val.estado;
          if (v === 'Validado') out.validadas++; else if (v === 'Con observaciones') out.observadas++; else out.porValidar++;
        }
        const pe = planEstado(r);
        if (pe) { out.planes.total++; out.planes[pe]++; }
      }
      ps.score = ps.contestadas ? ps.suma / ps.contestadas : null;
      cs.total += ps.total; cs.contestadas += ps.contestadas; cs.presente += ps.presente; cs.funcionando += ps.funcionando;
      cs.principles.push(ps);
    }
    cs.score = avg(cs.principles.map((p) => p.score));
    cs.pctPresente = cs.total ? cs.presente / cs.total : 0;
    cs.pctFuncionando = cs.total ? cs.funcionando / cs.total : 0;
    out.total += cs.total; out.contestadas += cs.contestadas; out.presente += cs.presente; out.funcionando += cs.funcionando;
    out.comps.push(cs);
  }
  const conScore = out.comps.filter((c) => c.score != null);
  const sp = sum(conScore.map((c) => c.peso));
  out.global = conScore.length && sp ? sum(conScore.map((c) => c.score * c.peso)) / sp : null;
  out.promedioSimple = avg(out.comps.map((c) => c.score));
  out.pendientes = out.total - out.contestadas;
  const u = DB.config.umbralIntegracion;
  out.integrado = out.pendientes === 0 && out.comps.every((c) => c.score >= 3 && c.pctPresente >= u && c.pctFuncionando >= u);
  return out;
}

/* Riesgos e indicadores ------------------------------------------------ */
const sev = (p, i) => (p || 0) * (i || 0);
function nivelSev(s) {
  if (!s) return { n: 'Sin evaluar', c: 'b-neutral' };
  return s >= 15 ? { n: 'Crítico', c: 'b-crit' } : s >= 10 ? { n: 'Alto', c: 'b-serious' } : s >= 5 ? { n: 'Medio', c: 'b-warn' } : { n: 'Bajo', c: 'b-good' };
}
function ultimoValor(k) {
  const v = [...(k.valores || [])].sort((a, b) => a.periodo.localeCompare(b.periodo));
  return v[v.length - 1] || null;
}
function estadoKRI(k, valor) {
  if (valor == null) return { n: 'Sin dato', c: 'b-neutral' };
  const peor = k.sentido === 'alto' ? (x, lim) => x > lim : (x, lim) => x < lim;
  if (!peor(valor, k.apetito)) return { n: 'Dentro del apetito', c: 'b-good' };
  if (!peor(valor, k.tolerancia)) return { n: 'En tolerancia', c: 'b-warn' };
  if (!peor(valor, k.capacidad)) return { n: 'Excede tolerancia', c: 'b-serious' };
  return { n: 'Excede capacidad', c: 'b-crit' };
}
function estadoRevision(r) {
  const items = r.items || {};
  const nc = DB.mesa.checklist.filter((c) => items[c.id] === 'NC');
  if (nc.some((c) => c.critico)) return 'Detenido';
  if (nc.length) return 'Liberado con excepción';
  return 'Liberado';
}
const clsRevision = (s) => ({ Liberado: 'b-good', 'Liberado con excepción': 'b-warn', Detenido: 'b-crit' }[s] || 'b-neutral');
function hallazgoVencido(h) { return !['Solventado', 'Cerrado'].includes(h.estatus) && h.fechaCompromiso && h.fechaCompromiso < hoy(); }
function valorAuto(tipo) {
  const ultimo = [...DB.cartera.cortes].sort((a, b) => a.periodo.localeCompare(b.periodo)).pop();
  if (tipo === 'imor') return ultimo && ultimo.total ? +(100 * ultimo.vencido / ultimo.total).toFixed(2) : null;
  if (tipo === 'conc20') return ultimo && ultimo.total ? +(100 * sum(ultimo.top.slice(0, 20).map((t) => t.saldo)) / ultimo.total).toFixed(2) : null;
  if (tipo === 'excMesa') {
    const per = periodoActual();
    let revs = DB.mesa.revisiones.filter((r) => (r.fecha || '').startsWith(per));
    if (!revs.length) revs = DB.mesa.revisiones;
    return revs.length ? +(100 * revs.filter((r) => estadoRevision(r) !== 'Liberado').length / revs.length).toFixed(2) : null;
  }
  if (tipo === 'planesVenc') { const ev = evalActiva(); return ev ? stats(ev).planes.Vencido : null; }
  if (tipo === 'hallVenc') return DB.hallazgos.filter(hallazgoVencido).length;
  return null;
}
