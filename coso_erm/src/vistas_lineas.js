/* =====================================================================
 * Vistas: auditoría interna, contraloría de crédito / mesa de control
 * y gestión de riesgos
 * ===================================================================== */
const tabsDe = (base, actual, lista) => `<div class="tabs">${lista.map(([k, t]) => `<a href="#/${base}${k ? '/' + k : ''}" class="${actual === k ? 'on' : ''}">${esc(t)}</a>`).join('')}</div>`;
const ORIGENES = ['Auditoría interna', 'Contraloría interna', 'Contraloría de crédito', 'Mesa de control', 'Administración de riesgos', 'Auditoría externa', 'Autoridad supervisora'];
const ESTATUS_H = ['Abierto', 'En atención', 'Atendido (por verificar)', 'Solventado', 'Cerrado'];
const SEVERIDAD = ['Alta', 'Media', 'Baja'];
const clsSev = (s) => ({ Alta: 'b-crit', Media: 'b-warn', Baja: 'b-good' }[s] || 'b-neutral');
const clsEstH = (h) => hallazgoVencido(h) ? 'b-crit' : ({ Solventado: 'b-good', Cerrado: 'b-neutral', 'Atendido (por verificar)': 'b-info' }[h.estatus] || 'b-warn');

/* Auditoría interna ---------------------------------------------------- */
let HALL_F = { estatus: 'abiertos', origen: '' };
VISTAS.auditoria = (args) => {
  const tab = args[0] || '';
  const t = tabsDe('auditoria', tab, [['', 'Hallazgos'], ['plan', 'Plan anual de auditoría'], ['validacion', 'Validación del cuestionario']]);
  if (tab === 'plan') return cabecera('Auditoría interna', 'Universo auditable y plan anual basado en riesgos (Normas Globales de Auditoría Interna, IIA 2024).', can('auditplan') ? `<button class="btn primary" data-act="aud-nueva">${ico('mas')} Agregar auditoría</button>` : '') + t + vistaPlanAuditoria();
  if (tab === 'validacion') return cabecera('Auditoría interna', 'Validación independiente de las respuestas capturadas por la Contraloría interna.') + t + vistaValidacion();
  const lista = DB.hallazgos.filter((h) => (HALL_F.estatus === 'abiertos' ? !['Solventado', 'Cerrado'].includes(h.estatus) : HALL_F.estatus === 'vencidos' ? hallazgoVencido(h) : true) && (!HALL_F.origen || h.origen === HALL_F.origen));
  return `${cabecera('Auditoría interna', 'Registro y seguimiento de hallazgos: condición, criterio, causa, efecto y recomendación.',
    `<button class="btn" data-act="exp-csv" data-e="hallazgos">${ico('descarga')} CSV</button>${can('hallazgos') ? `<button class="btn primary" data-act="hall-nuevo">${ico('mas')} Nuevo hallazgo</button>` : ''}`)}
  ${t}
  <div class="row" style="margin-bottom:.75rem">
    <select data-chg="hall-est" style="max-width:200px">${[['abiertos', 'Abiertos'], ['vencidos', 'Vencidos'], ['todos', 'Todos']].map(([v, x]) => `<option value="${v}" ${HALL_F.estatus === v ? 'selected' : ''}>${x}</option>`).join('')}</select>
    <select data-chg="hall-org" style="max-width:240px"><option value="">Todos los orígenes</option>${ORIGENES.map((o) => `<option ${HALL_F.origen === o ? 'selected' : ''}>${o}</option>`).join('')}</select>
    <span class="muted">${lista.length} hallazgo(s)</span>
  </div>
  <div class="card"><div class="tbl-wrap"><table class="tbl">
    <tr><th>Folio</th><th>Hallazgo</th><th>Origen</th><th>Severidad</th><th>Punto / riesgo</th><th>Responsable</th><th>Compromiso</th><th>Estatus</th></tr>
    ${lista.length ? lista.map((h) => `<tr><td><a href="#" data-act="hall-editar" data-id="${h.id}"><b>${esc(h.folio)}</b></a></td>
      <td>${esc(h.titulo)}<br><small>${esc(trunc(h.condicion, 120))}</small></td><td>${esc(h.origen)}</td>
      <td><span class="badge ${clsSev(h.severidad)}">${esc(h.severidad)}</span></td>
      <td>${h.qid ? `<a href="#" data-act="detalle" data-q="${esc(h.qid)}">${esc(h.qid)}</a>` : ''} ${h.riesgo ? `<span class="badge b-neutral plain">${esc(h.riesgo)}</span>` : ''}</td>
      <td>${esc(h.responsable)}<br><small>${esc(h.area)}</small></td><td>${fmtFecha(h.fechaCompromiso)}</td>
      <td><span class="badge ${clsEstH(h)}">${esc(hallazgoVencido(h) ? 'Vencido' : h.estatus)}</span></td></tr>`).join('') : '<tr><td colspan="8" class="empty">Sin hallazgos.</td></tr>'}
  </table></div></div>`;
};
CHG['hall-est'] = (t) => { HALL_F.estatus = t.value; render(); };
CHG['hall-org'] = (t) => { HALL_F.origen = t.value; render(); };
ACT['hall-nuevo'] = () => editarHallazgo(null, {});
ACT['hall-editar'] = (t) => editarHallazgo(t.dataset.id);
function siguienteFolio(pref, lista, campoF = 'folio') {
  const anio = new Date().getFullYear();
  const n = lista.filter((x) => String(x[campoF] || '').startsWith(`${pref}-${anio}-`)).length + 1;
  return `${pref}-${anio}-${String(n).padStart(3, '0')}`;
}
async function editarHallazgo(id, pre = {}) {
  const h = id ? DB.hallazgos.find((x) => x.id === id) : { folio: siguienteFolio('H', DB.hallazgos), estatus: 'Abierto', severidad: 'Media', origen: 'Auditoría interna', seguimiento: [], ...pre };
  const ed = can('hallazgos');
  const res = await formModal({
    titulo: id ? `Hallazgo ${h.folio}` : 'Nuevo hallazgo',
    cuerpo: `<div class="grid g3">
      ${campo('folio', 'Folio', h.folio, { dis: !ed, req: true })}
      ${campo('origen', 'Origen', h.origen, { opciones: ORIGENES, dis: !ed })}
      ${campo('severidad', 'Severidad', h.severidad, { opciones: SEVERIDAD, dis: !ed })}
    </div>
    ${campo('titulo', 'Título', h.titulo, { dis: !ed, req: true })}
    <div class="grid g2">
      ${campo('condicion', 'Condición (lo que se encontró)', h.condicion, { tipo: 'textarea', dis: !ed })}
      ${campo('criterio', 'Criterio (norma, política o punto de interés incumplido)', h.criterio, { tipo: 'textarea', dis: !ed })}
      ${campo('causa', 'Causa', h.causa, { tipo: 'textarea', dis: !ed })}
      ${campo('efecto', 'Efecto / riesgo', h.efecto, { tipo: 'textarea', dis: !ed })}
    </div>
    ${campo('recomendacion', 'Recomendación', h.recomendacion, { tipo: 'textarea', dis: !ed })}
    <div class="grid g3">
      ${campo('qid', 'Punto de interés COSO vinculado', h.qid, { dis: !ed, ph: 'p. ej. 3.13.13', lista: 'dl-q' })}
      ${campo('riesgo', 'Riesgo vinculado (clave)', h.riesgo, { dis: !ed, lista: 'dl-r' })}
      ${campo('area', 'Área responsable', h.area, { dis: !ed, lista: 'dl-areas' })}
      ${campo('responsable', 'Responsable de atención', h.responsable, { dis: !ed })}
      ${campo('fechaCompromiso', 'Fecha compromiso', h.fechaCompromiso, { tipo: 'date', dis: !ed })}
      ${campo('estatus', 'Estatus', h.estatus, { opciones: ESTATUS_H.filter((s) => can('hallazgos.cerrar') || !['Solventado', 'Cerrado'].includes(s) || s === h.estatus), dis: !ed })}
    </div>
    ${datalist('dl-q', PREGUNTAS.map((q) => q.id))}${datalist('dl-r', DB.riesgos.map((r) => r.clave))}${datalist('dl-areas', DB.responsables.areas)}
    <h3>Seguimiento</h3>
    ${(h.seguimiento || []).length ? `<ul>${h.seguimiento.map((s) => `<li><small>${fmtFechaHora(s.fecha)} · ${esc(s.por)}</small><br>${esc(s.nota)}</li>`).join('')}</ul>` : '<p class="muted">Sin notas de seguimiento.</p>'}
    ${ed ? campo('nota', 'Agregar nota de seguimiento', '', { tipo: 'textarea' }) : ''}`,
    botones: [...(id && can('hallazgos.cerrar') ? [{ id: 'borrar', t: 'Eliminar', danger: true }] : []), { id: 'cancel', t: 'Cerrar' }, ...(ed ? [{ id: 'ok', t: 'Guardar', primary: true }] : [])],
  }, (d, b) => {
    if (b === 'borrar') return null;
    if (!d.titulo.trim()) return 'Indique el título del hallazgo.';
    if (d.qid && !PREG[d.qid.trim()]) return 'El punto de interés no existe en el banco de preguntas.';
    if (DB.hallazgos.some((x) => x.folio === d.folio.trim() && x.id !== id)) return 'El folio ya existe.';
    return null;
  });
  if (!res) return;
  if (res.boton === 'borrar') {
    if (!await confirmar('Eliminar hallazgo', `¿Eliminar el hallazgo ${esc(h.folio)}?`, { ok: 'Eliminar', peligro: true })) return;
    DB.hallazgos = DB.hallazgos.filter((x) => x.id !== id);
    bitacora('Baja de hallazgo', h.folio); guardar(); render(); return;
  }
  const d = res.datos;
  const nota = d.nota; delete d.nota;
  d.folio = d.folio.trim(); d.qid = d.qid.trim();
  const cambioEstatus = id && d.estatus !== h.estatus;
  Object.assign(h, d);
  h.seguimiento = h.seguimiento || [];
  if (cambioEstatus) h.seguimiento.push({ fecha: ahora(), por: SES.usuario, nota: 'Cambio de estatus a: ' + d.estatus });
  if (nota && nota.trim()) h.seguimiento.push({ fecha: ahora(), por: SES.usuario, nota: nota.trim() });
  if (!id) { h.id = uid('h'); h.creado = ahora(); h.por = SES.usuario; DB.hallazgos.push(h); }
  bitacora(id ? 'Edición de hallazgo' : 'Alta de hallazgo', h.folio + ' · ' + h.estatus);
  guardar(); render(); toast('Hallazgo guardado.');
}

function vistaPlanAuditoria() {
  const L = DB.auditorias;
  return `<div class="card"><div class="tbl-wrap"><table class="tbl">
    <tr><th>Proceso / área auditable</th><th>Riesgo</th><th>Periodo</th><th>Responsable</th><th class="r">Horas</th><th>Estatus</th><th>Hallazgos</th></tr>
    ${L.length ? [...L].sort((a, b) => ['Alto', 'Medio', 'Bajo'].indexOf(a.riesgo) - ['Alto', 'Medio', 'Bajo'].indexOf(b.riesgo)).map((a) => `<tr>
      <td>${can('auditplan') ? `<a href="#" data-act="aud-editar" data-id="${a.id}"><b>${esc(a.proceso)}</b></a>` : `<b>${esc(a.proceso)}</b>`}<br><small>${esc(a.area)}</small></td>
      <td><span class="badge ${{ Alto: 'b-crit', Medio: 'b-warn', Bajo: 'b-good' }[a.riesgo] || 'b-neutral'}">${esc(a.riesgo)}</span></td>
      <td>${esc(a.periodo)}</td><td>${esc(a.responsable)}</td><td class="r num">${esc(a.horas)}</td>
      <td><span class="badge ${a.estatus === 'Concluida' ? 'b-good' : a.estatus === 'En ejecución' ? 'b-info' : 'b-neutral'}">${esc(a.estatus)}</span></td>
      <td class="num">${DB.hallazgos.filter((h) => h.auditoria === a.id).length}</td></tr>`).join('') : '<tr><td colspan="7" class="empty">Sin auditorías programadas.</td></tr>'}
  </table></div>
  <p class="muted" style="margin-top:.5rem;font-size:.8rem">Sugerencia: priorice los procesos con riesgos residuales altos de la matriz y los componentes COSO con menor madurez.</p></div>`;
}
ACT['aud-nueva'] = () => editarAuditoria(null);
ACT['aud-editar'] = (t) => editarAuditoria(t.dataset.id);
async function editarAuditoria(id) {
  const a = id ? DB.auditorias.find((x) => x.id === id) : { riesgo: 'Medio', estatus: 'Programada', periodo: new Date().getFullYear() + '-T1' };
  const res = await formModal({
    titulo: id ? 'Editar auditoría' : 'Agregar auditoría al plan', chico: true,
    cuerpo: `${campo('proceso', 'Proceso / área auditable', a.proceso, { req: true })}
      ${campo('area', 'Área', a.area, { lista: 'dl-areas' })}${datalist('dl-areas', DB.responsables.areas)}
      <div class="grid g2">${campo('riesgo', 'Nivel de riesgo', a.riesgo, { opciones: ['Alto', 'Medio', 'Bajo'] })}
      ${campo('periodo', 'Periodo (AAAA-T#)', a.periodo)}
      ${campo('responsable', 'Auditor responsable', a.responsable)}
      ${campo('horas', 'Horas estimadas', a.horas, { tipo: 'number' })}</div>
      ${campo('estatus', 'Estatus', a.estatus, { opciones: ['Programada', 'En ejecución', 'Concluida', 'Diferida', 'Cancelada'] })}
      ${campo('objetivo', 'Objetivo y alcance', a.objetivo, { tipo: 'textarea' })}`,
    botones: [...(id ? [{ id: 'borrar', t: 'Eliminar', danger: true }] : []), { id: 'cancel', t: 'Cancelar' }, { id: 'ok', t: 'Guardar', primary: true }],
  }, (d, b) => (b !== 'borrar' && !d.proceso.trim() ? 'Indique el proceso.' : null));
  if (!res) return;
  if (res.boton === 'borrar') { DB.auditorias = DB.auditorias.filter((x) => x.id !== id); bitacora('Baja de auditoría', a.proceso); }
  else {
    Object.assign(a, res.datos);
    if (!id) { a.id = uid('a'); DB.auditorias.push(a); }
    bitacora(id ? 'Edición de auditoría' : 'Alta de auditoría', a.proceso);
  }
  guardar(); render();
}
function vistaValidacion() {
  const ev = evalActiva();
  if (!ev) return sinEval();
  const st = stats(ev);
  const filas = PREGUNTAS.filter((q) => ev.resp[q.id] && ev.resp[q.id].a);
  return `<div class="grid g3" style="margin-bottom:1rem">${tile('Por validar', st.porValidar)}${tile('Validadas', st.validadas)}${tile('Con observaciones', st.observadas)}</div>
  <div class="card"><div class="tbl-wrap"><table class="tbl">
    <tr><th>Punto</th><th>Nivel</th><th>Evidencia</th><th>Validación</th><th>Observación</th>${can('eval.validar') && !evalBloqueada(ev) ? '<th class="no-print">Acción rápida</th>' : ''}</tr>
    ${filas.length ? filas.map((q) => { const r = ev.resp[q.id]; const v = r.val && r.val.estado; const faltan = st.sinEvidencia.find((x) => x.id === q.id);
      return `<tr><td><a href="#" data-act="detalle" data-q="${q.id}"><b>${q.id}</b></a><br><small>${esc(trunc(q.t, 90))}</small></td><td class="c">${nivel(r.a)}</td>
      <td>${faltan ? `<span class="badge b-warn">Falta ${esc(faltan.faltan.join(', '))}</span>` : '<span class="badge b-good">Completa</span>'}</td>
      <td><span class="badge ${v === 'Validado' ? 'b-good' : v ? 'b-serious' : 'b-neutral'}">${esc(v || 'Pendiente')}</span></td><td>${esc(trunc(r.val && r.val.obs, 120))}</td>
      ${can('eval.validar') && !evalBloqueada(ev) ? `<td class="no-print">${v !== 'Validado' ? `<button class="btn sm" data-act="validar-rapido" data-q="${q.id}">${ico('check')} Validar</button>` : ''}</td>` : ''}</tr>`; }).join('') : '<tr><td colspan="6" class="empty">Aún no hay respuestas capturadas.</td></tr>'}
  </table></div></div>`;
}
ACT['validar-rapido'] = (t) => {
  const ev = evalActiva();
  const r = ev.resp[t.dataset.q];
  r.val = { estado: 'Validado', obs: (r.val && r.val.obs) || '', por: SES.usuario, fecha: ahora() };
  bitacora('Validación de auditoría', t.dataset.q + ': Validado');
  guardar(); render();
};

/* Contraloría de crédito y mesa de control ----------------------------- */
VISTAS.credito = (args) => {
  const tab = args[0] || '';
  const t = tabsDe('credito', tab, [['', 'Mesa de control'], ['indicadores', 'Indicadores de mesa'], ['cartera', 'Contraloría de cartera'], ['checklist', 'Lista de verificación']]);
  const head = cabecera('Contraloría de crédito y mesa de control', 'Verificación de expedientes previa a la disposición, seguimiento de excepciones e indicadores de la cartera.',
    tab === '' ? `<button class="btn" data-act="exp-csv" data-e="mesa">${ico('descarga')} CSV</button>${can('mesa') ? `<button class="btn primary" data-act="mesa-nueva">${ico('mas')} Revisar expediente</button>` : ''}`
      : tab === 'cartera' && can('cartera') ? `<label class="btn primary">${ico('sube')} Cargar cartera (lay out CSV)<input type="file" accept=".csv,text/csv" data-chg="cartera-csv" hidden></label>` : '');
  if (tab === 'indicadores') return head + t + vistaIndicadoresMesa();
  if (tab === 'cartera') return head + t + vistaCartera();
  if (tab === 'checklist') return head + t + vistaChecklist();
  const L = [...DB.mesa.revisiones].sort((a, b) => (b.fecha || '').localeCompare(a.fecha || ''));
  return `${head}${t}<div class="card"><div class="tbl-wrap"><table class="tbl">
    <tr><th>Folio crédito</th><th>Socio / acreditado</th><th>Producto</th><th>Sucursal</th><th class="r">Monto</th><th>Fecha</th><th>Analista</th><th>Incumplimientos</th><th>Resultado</th></tr>
    ${L.length ? L.map((r) => { const nc = DB.mesa.checklist.filter((c) => (r.items || {})[c.id] === 'NC'); const est = estadoRevision(r);
      return `<tr><td><a href="#" data-act="mesa-editar" data-id="${r.id}"><b>${esc(r.folio)}</b></a></td><td>${esc(r.socio)}</td><td>${esc(r.producto)}</td><td>${esc(r.sucursal)}</td>
      <td class="r num">${fmtMon(r.monto)}</td><td>${fmtFecha(r.fecha)}</td><td>${esc(r.analista)}</td>
      <td>${nc.length ? nc.map((c) => `<span class="badge ${c.critico ? 'b-crit' : 'b-warn'} plain" title="${esc(c.t)}">${esc(c.id)}</span>`).join(' ') : '<span class="muted">—</span>'}</td>
      <td><span class="badge ${clsRevision(est)}">${esc(est)}</span></td></tr>`; }).join('') : '<tr><td colspan="9" class="empty">Sin expedientes revisados. También puede importarlos desde Integraciones (CSV o conector).</td></tr>'}
  </table></div></div>`;
};
ACT['mesa-nueva'] = () => editarRevision(null);
ACT['mesa-editar'] = (t) => editarRevision(t.dataset.id);
async function editarRevision(id) {
  const r = id ? DB.mesa.revisiones.find((x) => x.id === id) : { fecha: hoy(), analista: SES.nombre, items: {} };
  const ed = can('mesa');
  const res = await formModal({
    titulo: id ? `Expediente ${r.folio}` : 'Revisión de expediente de crédito',
    cuerpo: `<div class="grid g3">
      ${campo('folio', 'Folio del crédito', r.folio, { req: true, dis: !ed })}
      ${campo('socio', 'Socio / acreditado', r.socio, { dis: !ed })}
      ${campo('producto', 'Producto', r.producto, { dis: !ed })}
      ${campo('sucursal', 'Sucursal', r.sucursal, { dis: !ed })}
      ${campo('monto', 'Monto autorizado', r.monto, { tipo: 'number', dis: !ed })}
      ${campo('fecha', 'Fecha de revisión', r.fecha, { tipo: 'date', dis: !ed })}
      ${campo('analista', 'Analista de mesa de control', r.analista, { dis: !ed })}
      ${campo('nivel', 'Órgano / nivel que autorizó', r.nivel, { dis: !ed, ph: 'Comité de crédito, gerente…' })}
    </div>
    <h3>Lista de verificación</h3>
    <div class="tbl-wrap"><table class="tbl"><tr><th>Requisito</th><th class="c">Cumple</th><th class="c">No cumple</th><th class="c">No aplica</th></tr>
    ${DB.mesa.checklist.map((c) => { const v = (r.items || {})[c.id] || 'C'; return `<tr><td>${esc(c.id)} · ${esc(c.t)} ${c.critico ? '<span class="badge b-crit plain">Crítico</span>' : ''}</td>
      ${['C', 'NC', 'NA'].map((o) => `<td class="c"><input type="radio" name="it_${esc(c.id)}" value="${o}" ${v === o ? 'checked' : ''} ${ed ? '' : 'disabled'} aria-label="${esc(c.t)}: ${o}"></td>`).join('')}</tr>`; }).join('')}
    </table></div>
    ${campo('excepciones', 'Excepciones autorizadas / observaciones', r.excepciones, { tipo: 'textarea', dis: !ed })}
    <p class="muted" style="font-size:.8rem">Resultado automático: cualquier requisito crítico incumplido detiene la disposición; otros incumplimientos la liberan con excepción.</p>`,
    botones: [...(id && ed ? [{ id: 'borrar', t: 'Eliminar', danger: true }, { id: 'hallazgo', t: 'Registrar hallazgo' }] : []), { id: 'cancel', t: 'Cerrar' }, ...(ed ? [{ id: 'ok', t: 'Guardar', primary: true }] : [])],
  }, (d, b) => (b === 'ok' && !d.folio.trim() ? 'Indique el folio del crédito.' : null));
  if (!res) return;
  if (res.boton === 'borrar') {
    DB.mesa.revisiones = DB.mesa.revisiones.filter((x) => x.id !== id);
    bitacora('Baja de revisión de mesa', r.folio); guardar(); render(); return;
  }
  if (res.boton === 'ok') {
    const items = {};
    for (const c of DB.mesa.checklist) items[c.id] = res.datos['it_' + c.id] || 'C';
    const d = res.datos;
    Object.assign(r, { folio: d.folio.trim(), socio: d.socio, producto: d.producto, sucursal: d.sucursal, monto: num(d.monto), fecha: d.fecha, analista: d.analista, nivel: d.nivel, excepciones: d.excepciones, items });
    r.resultado = estadoRevision(r);
    if (!id) { r.id = uid('m'); r.por = SES.usuario; DB.mesa.revisiones.push(r); }
    bitacora(id ? 'Edición de revisión de mesa' : 'Revisión de mesa de control', `${r.folio}: ${r.resultado}`);
    guardar(); render(); toast('Revisión guardada: ' + r.resultado);
  }
  if (res.boton === 'hallazgo') {
    const nc = DB.mesa.checklist.filter((c) => (r.items || {})[c.id] === 'NC');
    editarHallazgo(null, { origen: 'Mesa de control', titulo: `Excepciones en expediente ${r.folio}`, condicion: nc.map((c) => c.t).join('; ') + (r.excepciones ? '. ' + r.excepciones : ''), criterio: 'Manual de Contraloría de Crédito y Mesa de Control', qid: PREGUNTAS.find((q) => q.tema === 'Mesa de control')?.id || '', area: 'Crédito y Cobranza', severidad: nc.some((c) => c.critico) ? 'Alta' : 'Media' });
  }
}
function vistaIndicadoresMesa() {
  const L = DB.mesa.revisiones;
  if (!L.length) return '<div class="card empty">Sin revisiones de mesa de control.</div>';
  const est = (s) => L.filter((r) => estadoRevision(r) === s).length;
  const porSuc = {};
  for (const r of L) { const k = r.sucursal || 'Sin sucursal'; porSuc[k] = porSuc[k] || { n: 0, exc: 0, det: 0 }; porSuc[k].n++; const s = estadoRevision(r); if (s !== 'Liberado') porSuc[k].exc++; if (s === 'Detenido') porSuc[k].det++; }
  const porReq = DB.mesa.checklist.map((c) => ({ c, n: L.filter((r) => (r.items || {})[c.id] === 'NC').length })).filter((x) => x.n).sort((a, b) => b.n - a.n);
  return `<div class="grid g4">${tile('Expedientes revisados', L.length)}${tile('Liberados sin excepción', est('Liberado'), fmtPct(est('Liberado') / L.length, 0))}${tile('Liberados con excepción', est('Liberado con excepción'), fmtPct(est('Liberado con excepción') / L.length, 0))}${tile('Detenidos', est('Detenido'), fmtPct(est('Detenido') / L.length, 0))}</div>
  <div class="grid g2" style="margin-top:1rem">
    <div class="card"><h3>Requisitos con más incumplimientos</h3>${porReq.length ? barras(porReq.map((x) => ({ etiqueta: `${x.c.id} ${trunc(x.c.t, 50)}`, valor: x.n, tip: `${x.c.t}: ${x.n} expediente(s)` })), { max: Math.max(...porReq.map((x) => x.n)), decimales: 0, marcas: [] }) : '<p class="muted">Sin incumplimientos.</p>'}</div>
    <div class="card"><h3>Excepciones por sucursal</h3><div class="tbl-wrap"><table class="tbl"><tr><th>Sucursal</th><th class="r">Revisados</th><th class="r">Con excepción</th><th class="r">Detenidos</th><th class="r">% excepción</th></tr>
      ${Object.entries(porSuc).sort((a, b) => b[1].exc / b[1].n - a[1].exc / a[1].n).map(([k, v]) => `<tr><td>${esc(k)}</td><td class="r num">${v.n}</td><td class="r num">${v.exc}</td><td class="r num">${v.det}</td><td class="r num">${fmtPct(v.exc / v.n, 0)}</td></tr>`).join('')}</table></div></div>
  </div>`;
}
function vistaChecklist() {
  const ed = can('mesa');
  return `<div class="card"><p class="muted">Requisitos que verifica la mesa de control antes de la disposición. Los requisitos críticos detienen la operación si no se cumplen.</p>
  <div class="tbl-wrap"><table class="tbl"><tr><th>Clave</th><th>Requisito</th><th>Crítico</th>${ed ? '<th></th>' : ''}</tr>
  ${DB.mesa.checklist.map((c) => `<tr><td>${esc(c.id)}</td><td>${esc(c.t)}</td><td>${c.critico ? '<span class="badge b-crit">Sí</span>' : 'No'}</td>${ed ? `<td><button class="btn sm" data-act="chk-editar" data-id="${esc(c.id)}">Editar</button></td>` : ''}</tr>`).join('')}
  </table></div>${ed ? `<div class="row end" style="margin-top:.75rem"><button class="btn" data-act="chk-editar">${ico('mas')} Agregar requisito</button></div>` : ''}</div>`;
}
ACT['chk-editar'] = async (t) => {
  const id = t.dataset.id;
  const c = id ? DB.mesa.checklist.find((x) => x.id === id) : { id: 'M' + String(DB.mesa.checklist.length + 1).padStart(2, '0'), t: '', critico: false };
  const res = await formModal({ titulo: id ? 'Editar requisito' : 'Nuevo requisito', chico: true,
    cuerpo: `${campo('t', 'Requisito', c.t, { req: true })}${campo('critico', 'Es crítico (detiene la disposición)', c.critico, { tipo: 'checkbox' })}`,
    botones: [...(id ? [{ id: 'borrar', t: 'Eliminar', danger: true }] : []), { id: 'cancel', t: 'Cancelar' }, { id: 'ok', t: 'Guardar', primary: true }] }, (d, b) => (b !== 'borrar' && !d.t.trim() ? 'Indique el requisito.' : null));
  if (!res) return;
  if (res.boton === 'borrar') DB.mesa.checklist = DB.mesa.checklist.filter((x) => x.id !== id);
  else { c.t = res.datos.t.trim(); c.critico = res.datos.critico; if (!id) DB.mesa.checklist.push(c); }
  bitacora('Lista de verificación de mesa', (res.boton === 'borrar' ? 'Baja ' : 'Edición ') + c.id);
  guardar(); render();
};

/* Cartera: se importa con el lay out del Sistema de Administración de
   Riesgos de Crédito (docs/layout_carga.md) y se guardan solo agregados. */
function agregarCartera(filas, fuente) {
  const req = ['periodo', 'folio', 'saldo_vigente', 'saldo_vencido'];
  const faltan = req.filter((k) => !(k in (filas[0] || {})));
  if (faltan.length) throw new Error('Faltan columnas obligatorias del lay out: ' + faltan.join(', '));
  const porPer = {};
  const errores = [];
  filas.forEach((f, i) => {
    const vig = num(f.saldo_vigente), ven = num(f.saldo_vencido);
    if (!/^\d{4}-\d{2}$/.test(f.periodo || '') || vig == null || ven == null) { errores.push(i + 2); return; }
    const P = porPer[f.periodo] || (porPer[f.periodo] = { periodo: f.periodo, creditos: 0, vigente: 0, vencido: 0, porProducto: {}, porSucursal: {}, mora: { 'Al corriente': 0, '1-30': 0, '31-90': 0, '91-180': 0, '>180': 0 }, socios: {} });
    P.creditos++; P.vigente += vig; P.vencido += ven;
    const tot = vig + ven;
    for (const [k, campoD] of [['porProducto', 'producto'], ['porSucursal', 'sucursal']]) {
      const key = f[campoD] || 'N/D';
      const o = P[k][key] || (P[k][key] = { vigente: 0, vencido: 0, n: 0 });
      o.vigente += vig; o.vencido += ven; o.n++;
    }
    const dm = num(f.dias_mora) || 0;
    P.mora[dm <= 0 ? 'Al corriente' : dm <= 30 ? '1-30' : dm <= 90 ? '31-90' : dm <= 180 ? '91-180' : '>180'] += tot;
    const s = f.socio || f.folio;
    P.socios[s] = (P.socios[s] || 0) + tot;
  });
  const cortes = Object.values(porPer).map((P) => {
    P.total = P.vigente + P.vencido;
    P.top = Object.entries(P.socios).sort((a, b) => b[1] - a[1]).slice(0, 20).map(([socio, saldo]) => ({ socio, saldo }));
    P.acreditados = Object.keys(P.socios).length;
    delete P.socios;
    P.fuente = fuente; P.cargado = ahora(); P.por = SES.usuario;
    return P;
  });
  return { cortes, errores };
}
CHG['cartera-csv'] = async (t) => {
  const f = t.files[0];
  if (!f) return;
  const { filas } = deCSV(await leerArchivo(f));
  const { cortes, errores } = agregarCartera(filas, f.name);
  for (const c of cortes) {
    DB.cartera.cortes = DB.cartera.cortes.filter((x) => x.periodo !== c.periodo);
    DB.cartera.cortes.push(c);
  }
  bitacora('Carga de cartera', `${f.name}: ${cortes.map((c) => c.periodo).join(', ')} (${filas.length - errores.length} créditos, ${errores.length} rechazados)`);
  guardar(); render();
  toast(`Cartera cargada: ${cortes.length} periodo(s). ${errores.length ? errores.length + ' renglones rechazados (' + errores.slice(0, 8).join(', ') + (errores.length > 8 ? '…' : '') + ').' : ''}`, !!errores.length);
};
let CORTE_SEL = '';
function vistaCartera() {
  const cortes = [...DB.cartera.cortes].sort((a, b) => a.periodo.localeCompare(b.periodo));
  if (!cortes.length) return `<div class="card empty"><p>No se ha cargado información de cartera.</p><p class="muted">Use el lay out CSV del Sistema de Administración de Riesgos de Crédito (<code>periodo, folio, socio, producto, sucursal, …, saldo_vigente, saldo_vencido, dias_mora</code>). Solo se guardan cifras agregadas y los 20 principales acreditados.</p></div>`;
  const c = cortes.find((x) => x.periodo === CORTE_SEL) || cortes[cortes.length - 1];
  const imor = c.total ? c.vencido / c.total : null;
  const conc = c.total ? sum(c.top.map((t) => t.saldo)) / c.total : null;
  const kImor = DB.kris.find((k) => k.auto === 'imor');
  const kConc = DB.kris.find((k) => k.auto === 'conc20');
  const dist = (obj) => Object.entries(obj).map(([k, v]) => ({ k, ...v, total: v.vigente + v.vencido })).sort((a, b) => b.total - a.total);
  const tabla = (titulo, filas) => `<div class="card"><h3>${esc(titulo)}</h3><div class="tbl-wrap"><table class="tbl"><tr><th></th><th class="r">Créditos</th><th class="r">Saldo vigente</th><th class="r">Saldo vencido</th><th class="r">% cartera</th><th class="r">IMOR</th></tr>
    ${filas.map((f) => `<tr><td>${esc(f.k)}</td><td class="r num">${f.n}</td><td class="r num">${fmtMon(f.vigente)}</td><td class="r num">${fmtMon(f.vencido)}</td><td class="r num">${fmtPct(f.total / c.total)}</td><td class="r num">${fmtPct(f.total ? f.vencido / f.total : null)}</td></tr>`).join('')}</table></div></div>`;
  return `<div class="row" style="margin-bottom:1rem"><label class="muted">Corte</label><select data-chg="corte" style="max-width:160px">${cortes.map((x) => `<option ${x.periodo === c.periodo ? 'selected' : ''}>${esc(x.periodo)}</option>`).join('')}</select><span class="muted">Fuente: ${esc(c.fuente)} · ${fmtFechaHora(c.cargado)} · ${esc(c.por)}</span>
    ${can('kris') ? '<button class="btn sm" data-act="kri-auto">Actualizar KRI automáticos</button>' : ''}</div>
  <div class="grid g4">
    ${tile('Cartera total', fmtMon(c.total), `${c.creditos} créditos · ${c.acreditados} acreditados`)}
    ${tile('Cartera vencida', fmtMon(c.vencido), `Vigente ${fmtMon(c.vigente)}`)}
    ${tile('IMOR', fmtPct(imor, 2), kImor ? `<span class="badge ${estadoKRI(kImor, imor * 100).c}">${estadoKRI(kImor, imor * 100).n}</span>` : '')}
    ${tile('Concentración 20 principales', fmtPct(conc, 1), kConc ? `<span class="badge ${estadoKRI(kConc, conc * 100).c}">${estadoKRI(kConc, conc * 100).n}</span>` : '')}
  </div>
  <div class="grid g2" style="margin-top:1rem">
    <div class="card"><h3>Evolución del IMOR</h3>${barras(cortes.map((x) => ({ etiqueta: x.periodo, valor: x.total ? 100 * x.vencido / x.total : null })), { max: Math.max(10, ...cortes.map((x) => x.total ? 100 * x.vencido / x.total : 0)) * 1.1, sufijo: '%', marcas: kImor ? [kImor.apetito, kImor.tolerancia] : [] })}
      ${kImor ? `<p class="muted" style="font-size:.78rem">Líneas: apetito ${kImor.apetito}% y tolerancia ${kImor.tolerancia}%.</p>` : ''}</div>
    <div class="card"><h3>Saldo por antigüedad de mora</h3>${barras(Object.entries(c.mora).map(([k, v]) => ({ etiqueta: k === 'Al corriente' ? k : k + ' días', valor: c.total ? 100 * v / c.total : 0, tip: `${k}: ${fmtMon(v)}` })), { max: 100, sufijo: '%', decimales: 1, marcas: [25, 50, 75] })}</div>
  </div>
  <div class="grid g2" style="margin-top:1rem">${tabla('Por producto', dist(c.porProducto))}${tabla('Por sucursal', dist(c.porSucursal))}</div>
  <div class="card"><h3>20 principales acreditados</h3><div class="tbl-wrap"><table class="tbl"><tr><th>#</th><th>Acreditado</th><th class="r">Saldo</th><th class="r">% cartera</th></tr>
    ${c.top.map((t, i) => `<tr><td>${i + 1}</td><td>${esc(t.socio)}</td><td class="r num">${fmtMon(t.saldo)}</td><td class="r num">${fmtPct(t.saldo / c.total, 2)}</td></tr>`).join('')}</table></div></div>`;
}
CHG.corte = (t) => { CORTE_SEL = t.value; render(); };

/* Gestión de riesgos --------------------------------------------------- */
const CATEGORIAS_R = ['Crédito', 'Liquidez', 'Mercado', 'Operacional', 'Tecnológico', 'Ciberseguridad', 'Legal', 'Reputacional', 'PLD/FT', 'Estratégico', 'Terceros', 'ASG', 'Fraude', 'Cumplimiento'];
const RESPUESTAS_R = ['Reducir', 'Aceptar', 'Evitar', 'Compartir / transferir'];
let MAPA = 'residual';
VISTAS.riesgos = (args) => {
  const tab = args[0] || '';
  const t = tabsDe('riesgos', tab, [['', 'Matriz de riesgos'], ['mapa', 'Mapa de calor'], ['kri', 'Apetito e indicadores (KRI)']]);
  if (tab === 'mapa') return cabecera('Gestión de riesgos', 'Probabilidad × impacto (escala 1–5).') + t + vistaMapa();
  if (tab === 'kri') return cabecera('Gestión de riesgos', 'Apetito, tolerancia y capacidad de riesgo aprobados por el Consejo; semáforo de indicadores clave.',
    `${can('kris') ? `<button class="btn" data-act="kri-auto">Actualizar automáticos</button><button class="btn primary" data-act="kri-editar">${ico('mas')} Nuevo KRI</button>` : ''}`) + t + vistaKRI();
  const L = [...DB.riesgos].sort((a, b) => sev(b.probR || b.prob, b.impR || b.imp) - sev(a.probR || a.prob, a.impR || a.imp));
  const ev = evalActiva();
  return `${cabecera('Gestión de riesgos', 'Matriz de riesgos: riesgo inherente, controles vinculados a los puntos de interés COSO y riesgo residual.',
    `<button class="btn" data-act="exp-csv" data-e="riesgos">${ico('descarga')} CSV</button>${can('riesgos') ? `<button class="btn primary" data-act="riesgo-editar">${ico('mas')} Nuevo riesgo</button>` : ''}`)}
  ${t}<div class="card"><div class="tbl-wrap"><table class="tbl">
    <tr><th>Clave</th><th>Riesgo</th><th>Categoría</th><th class="c">Inherente</th><th>Controles (puntos COSO)</th><th class="c">Residual</th><th>Respuesta</th><th>Dueño</th></tr>
    ${L.length ? L.map((r) => { const si = sev(r.prob, r.imp), sr = sev(r.probR || r.prob, r.impR || r.imp), ni = nivelSev(si), nr = nivelSev(sr);
      const madC = ev ? avg((r.qids || []).map((q) => nivel(ev.resp[q] && ev.resp[q].a))) : null;
      return `<tr><td><a href="#" data-act="riesgo-editar" data-id="${r.id}"><b>${esc(r.clave)}</b></a></td><td>${esc(r.descripcion)}<br><small>${esc(r.proceso)}</small></td><td>${esc(r.categoria)}</td>
      <td class="c"><span class="badge ${ni.c}">${si || '—'} ${esc(ni.n)}</span></td>
      <td>${(r.qids || []).map((q) => `<a href="#" data-act="detalle" data-q="${esc(q)}">${esc(q)}</a>`).join(', ') || '<span class="muted">—</span>'}${madC != null ? `<br><small>Madurez de controles: ${fmtN(madC)}</small>` : ''}</td>
      <td class="c"><span class="badge ${nr.c}">${sr || '—'} ${esc(nr.n)}</span></td><td>${esc(r.respuesta)}</td><td>${esc(r.dueno)}</td></tr>`; }).join('') : '<tr><td colspan="8" class="empty">Matriz de riesgos vacía.</td></tr>'}
  </table></div></div>`;
};
ACT['riesgo-editar'] = async (t) => {
  const id = t.dataset.id;
  const r = id ? DB.riesgos.find((x) => x.id === id) : { clave: 'R-' + String(DB.riesgos.length + 1).padStart(3, '0'), categoria: 'Crédito', respuesta: 'Reducir', qids: [], estatus: 'Vigente' };
  const ed = can('riesgos');
  const ev = evalActiva();
  const esc5 = [['', '—'], [1, '1 · Muy bajo'], [2, '2 · Bajo'], [3, '3 · Medio'], [4, '4 · Alto'], [5, '5 · Muy alto']];
  const res = await formModal({
    titulo: id ? `Riesgo ${r.clave}` : 'Nuevo riesgo',
    cuerpo: `<div class="grid g3">${campo('clave', 'Clave', r.clave, { req: true, dis: !ed })}${campo('categoria', 'Categoría', r.categoria, { opciones: CATEGORIAS_R, dis: !ed })}${campo('proceso', 'Proceso', r.proceso, { dis: !ed })}</div>
      ${campo('descripcion', 'Descripción del riesgo', r.descripcion, { req: true, dis: !ed })}
      <div class="grid g2">${campo('causa', 'Causas', r.causa, { tipo: 'textarea', dis: !ed })}${campo('consecuencia', 'Consecuencias', r.consecuencia, { tipo: 'textarea', dis: !ed })}</div>
      <h3>Riesgo inherente</h3><div class="grid g2">${campo('prob', 'Probabilidad', r.prob || '', { opciones: esc5, dis: !ed })}${campo('imp', 'Impacto', r.imp || '', { opciones: esc5, dis: !ed })}</div>
      <h3>Controles</h3>
      ${campo('controles', 'Descripción de controles', r.controles, { tipo: 'textarea', dis: !ed })}
      ${campo('qids', 'Puntos de interés COSO que soportan el control (separados por coma)', (r.qids || []).join(', '), { dis: !ed, ph: '1.1.2, 3.13.13' })}
      ${ev && (r.qids || []).length ? `<p class="muted">Nivel actual de esos puntos en «${esc(ev.nombre)}»: ${(r.qids || []).map((q) => `${esc(q)}=${nivel(ev.resp[q] && ev.resp[q].a) ?? 's/c'}`).join(' · ')}</p>` : ''}
      <h3>Riesgo residual</h3><div class="grid g2">${campo('probR', 'Probabilidad residual', r.probR || '', { opciones: esc5, dis: !ed })}${campo('impR', 'Impacto residual', r.impR || '', { opciones: esc5, dis: !ed })}</div>
      <div class="grid g3">${campo('respuesta', 'Respuesta al riesgo', r.respuesta, { opciones: RESPUESTAS_R, dis: !ed })}${campo('dueno', 'Dueño del riesgo', r.dueno, { dis: !ed, lista: 'dl-areas' })}${campo('kri', 'KRI asociado', r.kri || '', { opciones: [['', '—'], ...DB.kris.map((k) => [k.id, k.nombre])], dis: !ed })}</div>
      ${datalist('dl-areas', DB.responsables.areas)}`,
    botones: [...(id && ed ? [{ id: 'borrar', t: 'Eliminar', danger: true }] : []), { id: 'cancel', t: 'Cerrar' }, ...(ed ? [{ id: 'ok', t: 'Guardar', primary: true }] : [])],
  }, (d, b) => {
    if (b === 'borrar') return null;
    if (!d.clave.trim() || !d.descripcion.trim()) return 'Clave y descripción son obligatorias.';
    if (DB.riesgos.some((x) => x.clave === d.clave.trim() && x.id !== id)) return 'La clave ya existe.';
    const malos = d.qids.split(/[,;\s]+/).filter(Boolean).filter((q) => !PREG[q]);
    if (malos.length) return 'Puntos de interés inexistentes: ' + malos.join(', ');
    return null;
  });
  if (!res) return;
  if (res.boton === 'borrar') {
    if (!await confirmar('Eliminar riesgo', `¿Eliminar ${esc(r.clave)}?`, { ok: 'Eliminar', peligro: true })) return;
    DB.riesgos = DB.riesgos.filter((x) => x.id !== id); bitacora('Baja de riesgo', r.clave);
  } else {
    const d = res.datos;
    Object.assign(r, d, { clave: d.clave.trim(), prob: num(d.prob), imp: num(d.imp), probR: num(d.probR), impR: num(d.impR), qids: d.qids.split(/[,;\s]+/).filter(Boolean), actualizado: ahora() });
    if (!id) { r.id = uid('r'); DB.riesgos.push(r); }
    // Marca «integrado en la matriz» en la evaluación activa.
    if (ev && !evalBloqueada(ev)) for (const q of r.qids) { const rr = ev.resp[q] || (ev.resp[q] = {}); rr.matriz = 'Sí'; }
    bitacora(id ? 'Edición de riesgo' : 'Alta de riesgo', `${r.clave} (inherente ${sev(r.prob, r.imp)}, residual ${sev(r.probR || r.prob, r.impR || r.imp)})`);
  }
  guardar(); render();
};
function vistaMapa() {
  const cel = {};
  for (const r of DB.riesgos) {
    const p = MAPA === 'residual' ? (r.probR || r.prob) : r.prob, i = MAPA === 'residual' ? (r.impR || r.imp) : r.imp;
    if (!p || !i) continue;
    (cel[p + '-' + i] = cel[p + '-' + i] || []).push(r.clave);
  }
  const color = (s) => s >= 15 ? 'var(--crit-soft)' : s >= 10 ? 'var(--serious-soft)' : s >= 5 ? 'var(--warn-soft)' : 'var(--good-soft)';
  let g = '';
  for (let p = 5; p >= 1; p--) {
    g += `<div class="ax">${p}</div>`;
    for (let i = 1; i <= 5; i++) { const L = cel[p + '-' + i] || []; g += `<div class="cell" style="background:${color(p * i)}" data-tip="${esc(`Probabilidad ${p} × impacto ${i} = ${p * i} (${nivelSev(p * i).n})${L.length ? ': ' + L.join(', ') : ''}`)}">${L.length || ''}</div>`; }
  }
  g += '<div></div>' + [1, 2, 3, 4, 5].map((i) => `<div class="ax">${i}</div>`).join('');
  return `<div class="card"><div class="row" style="margin-bottom:1rem"><div class="tabs" style="margin:0;border:none">${['inherente', 'residual'].map((m) => `<button class="${MAPA === m ? 'on' : ''}" data-act="mapa" data-m="${m}">Riesgo ${m}</button>`).join('')}</div></div>
    <div style="display:grid;grid-template-columns:auto 1fr;gap:.5rem;align-items:center;max-width:620px">
      <div style="writing-mode:vertical-rl;transform:rotate(180deg);color:var(--text-3);font-size:.8rem">Probabilidad</div>
      <div><div class="heat">${g}</div><div style="text-align:center;color:var(--text-3);font-size:.8rem;margin-top:.25rem">Impacto</div></div>
    </div>
    <div class="legend" style="margin-top:1rem">${[['Bajo (1–4)', 'var(--good-soft)'], ['Medio (5–9)', 'var(--warn-soft)'], ['Alto (10–14)', 'var(--serious-soft)'], ['Crítico (15–25)', 'var(--crit-soft)']].map(([t, c]) => `<span><i style="background:${c};border:1px solid var(--line-strong)"></i>${t}</span>`).join('')}</div>
    <p class="muted" style="font-size:.8rem">El número en cada celda es la cantidad de riesgos; pase el cursor para ver las claves.</p></div>`;
}
ACT.mapa = (t) => { MAPA = t.dataset.m; render(); };
function vistaKRI() {
  return `<div class="card"><div class="tbl-wrap"><table class="tbl">
    <tr><th>Indicador</th><th>Categoría</th><th class="r">Apetito</th><th class="r">Tolerancia</th><th class="r">Capacidad</th><th class="r">Último valor</th><th>Periodo</th><th>Estado</th><th>Tendencia</th>${can('kris') ? '<th class="no-print"></th>' : ''}</tr>
    ${DB.kris.map((k) => { const vs = [...(k.valores || [])].sort((a, b) => a.periodo.localeCompare(b.periodo)); const u = vs[vs.length - 1]; const s = estadoKRI(k, u && u.valor);
      const ult = vs.slice(-6); const mx = Math.max(k.capacidad, ...ult.map((v) => v.valor)) || 1;
      const spark = ult.length > 1 ? `<svg viewBox="0 0 100 24" width="90" height="24" aria-hidden="true"><polyline fill="none" stroke="var(--series-1)" stroke-width="2" points="${ult.map((v, i) => `${(i / (ult.length - 1)) * 96 + 2},${22 - (v.valor / mx) * 20}`).join(' ')}"/></svg>` : '';
      return `<tr><td><b>${esc(k.nombre)}</b><br><small>${k.sentido === 'alto' ? 'Mayor valor = mayor riesgo' : 'Menor valor = mayor riesgo'}${k.auto ? ' · automático' : ''}</small></td><td>${esc(k.categoria)}</td>
      <td class="r num">${fmtN(k.apetito)}</td><td class="r num">${fmtN(k.tolerancia)}</td><td class="r num">${fmtN(k.capacidad)}</td>
      <td class="r num"><b>${u ? fmtN(u.valor) + ' ' + esc(k.unidad) : '—'}</b></td><td>${esc(u ? u.periodo : '')}</td><td><span class="badge ${s.c}">${esc(s.n)}</span></td><td>${spark}</td>
      ${can('kris') ? `<td class="no-print"><div class="row"><button class="btn sm" data-act="kri-valor" data-id="${k.id}">Registrar valor</button><button class="btn sm" data-act="kri-editar" data-id="${k.id}">Editar</button></div></td>` : ''}</tr>`; }).join('')}
  </table></div><p class="muted" style="font-size:.8rem;margin-top:.5rem">Umbrales de referencia: ajústelos a lo aprobado por el Consejo de Administración y a la regulación vigente aplicable.</p></div>`;
}
ACT['kri-editar'] = async (t) => {
  const id = t.dataset.id;
  const k = id ? DB.kris.find((x) => x.id === id) : { categoria: 'Crédito', unidad: '%', sentido: 'alto', valores: [], auto: '' };
  const res = await formModal({ titulo: id ? 'Editar KRI' : 'Nuevo KRI', chico: true,
    cuerpo: `${campo('nombre', 'Nombre', k.nombre, { req: true })}
      <div class="grid g2">${campo('categoria', 'Categoría', k.categoria, { opciones: [...new Set([...CATEGORIAS_R, 'Liquidez', 'Solvencia', 'Control interno'])] })}${campo('unidad', 'Unidad', k.unidad, { opciones: ['%', '#', '$', 'días', 'veces'] })}</div>
      ${campo('sentido', 'Dirección', k.sentido, { opciones: [['alto', 'Mayor valor = mayor riesgo'], ['bajo', 'Menor valor = mayor riesgo']] })}
      <div class="grid g3">${campo('apetito', 'Apetito', k.apetito, { tipo: 'number', attrs: 'step="any"' })}${campo('tolerancia', 'Tolerancia', k.tolerancia, { tipo: 'number', attrs: 'step="any"' })}${campo('capacidad', 'Capacidad', k.capacidad, { tipo: 'number', attrs: 'step="any"' })}</div>
      ${campo('auto', 'Cálculo automático', k.auto, { opciones: [['', 'Manual'], ['imor', 'IMOR del último corte de cartera'], ['conc20', 'Concentración 20 principales'], ['excMesa', '% expedientes con excepción'], ['planesVenc', 'Planes de solución vencidos'], ['hallVenc', 'Hallazgos vencidos']] })}`,
    botones: [...(id ? [{ id: 'borrar', t: 'Eliminar', danger: true }] : []), { id: 'cancel', t: 'Cancelar' }, { id: 'ok', t: 'Guardar', primary: true }] },
  (d, b) => {
    if (b === 'borrar') return null;
    if (!d.nombre.trim()) return 'Indique el nombre.';
    const [a, tol, c] = [num(d.apetito), num(d.tolerancia), num(d.capacidad)];
    if ([a, tol, c].some((x) => x == null)) return 'Capture apetito, tolerancia y capacidad.';
    if (d.sentido === 'alto' ? !(a <= tol && tol <= c) : !(a >= tol && tol >= c)) return d.sentido === 'alto' ? 'Debe cumplirse apetito ≤ tolerancia ≤ capacidad.' : 'Debe cumplirse apetito ≥ tolerancia ≥ capacidad.';
    return null;
  });
  if (!res) return;
  if (res.boton === 'borrar') { DB.kris = DB.kris.filter((x) => x.id !== id); bitacora('Baja de KRI', k.nombre); }
  else {
    const d = res.datos;
    Object.assign(k, { nombre: d.nombre.trim(), categoria: d.categoria, unidad: d.unidad, sentido: d.sentido, apetito: num(d.apetito), tolerancia: num(d.tolerancia), capacidad: num(d.capacidad), auto: d.auto });
    if (!id) { k.id = uid('k'); DB.kris.push(k); }
    bitacora(id ? 'Edición de KRI' : 'Alta de KRI', k.nombre);
  }
  guardar(); render();
};
ACT['kri-valor'] = async (t) => {
  const k = DB.kris.find((x) => x.id === t.dataset.id);
  const res = await formModal({ titulo: 'Registrar valor — ' + k.nombre, chico: true,
    cuerpo: `${campo('periodo', 'Periodo', periodoActual(), { tipo: 'month', req: true })}${campo('valor', 'Valor (' + k.unidad + ')', '', { tipo: 'number', req: true, attrs: 'step="any"' })}
      ${(k.valores || []).length ? `<h3>Historial</h3><div class="tbl-wrap"><table class="tbl"><tr><th>Periodo</th><th class="r">Valor</th></tr>${[...k.valores].sort((a, b) => b.periodo.localeCompare(a.periodo)).slice(0, 12).map((v) => `<tr><td>${esc(v.periodo)}</td><td class="r num">${fmtN(v.valor)}</td></tr>`).join('')}</table></div>` : ''}`,
    botones: [{ id: 'cancel', t: 'Cancelar' }, { id: 'ok', t: 'Guardar', primary: true }] },
  (d) => (!/^\d{4}-\d{2}$/.test(d.periodo) ? 'Periodo inválido (AAAA-MM).' : num(d.valor) == null ? 'Valor inválido.' : null));
  if (!res) return;
  registrarValorKRI(k, res.datos.periodo, num(res.datos.valor), SES.usuario);
  bitacora('Valor de KRI', `${k.nombre} ${res.datos.periodo}: ${res.datos.valor}`);
  guardar(); render();
};
function registrarValorKRI(k, periodo, valor, por) {
  k.valores = (k.valores || []).filter((v) => v.periodo !== periodo);
  k.valores.push({ periodo, valor, por, fecha: ahora() });
}
ACT['kri-auto'] = () => {
  let n = 0;
  const cortes = [...DB.cartera.cortes].sort((a, b) => a.periodo.localeCompare(b.periodo));
  for (const k of DB.kris.filter((x) => x.auto)) {
    const v = valorAuto(k.auto);
    if (v == null) continue;
    const per = ['imor', 'conc20'].includes(k.auto) && cortes.length ? cortes[cortes.length - 1].periodo : periodoActual();
    registrarValorKRI(k, per, v, 'automático');
    n++;
  }
  bitacora('KRI automáticos', n + ' indicadores actualizados');
  guardar(); render(); toast(n + ' indicador(es) actualizado(s).');
};
