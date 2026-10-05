/* =====================================================================
 * Vistas: tablero, evaluaciones, cuestionario, resultados y planes
 * ===================================================================== */
const cabecera = (titulo, desc = '', acciones = '') => `<div class="page-head"><div><h1>${esc(titulo)}</h1>${desc ? `<p>${desc}</p>` : ''}</div><div class="row no-print">${acciones}</div></div>`;
const sinEval = () => `<div class="card empty"><p>No hay una evaluación activa.</p>${can('eval.gestionar') ? '<a class="btn primary" href="#/evaluacion">Crear evaluación</a>' : '<p class="muted">Solicite al Contralor interno o al Auditor interno que cree una evaluación.</p>'}</div>`;
const tile = (lbl, val, sub = '', extra = '') => `<div class="tile"><div class="lbl">${esc(lbl)}</div><div class="val num">${val}</div>${sub ? `<div class="sub">${sub}</div>` : ''}${extra}</div>`;

/* Evaluaciones --------------------------------------------------------- */
function nuevaEvaluacion(nombre, ejercicio, copiarDe = null) {
  const base = copiarDe ? DB.evals.find((e) => e.id === copiarDe) : null;
  const ev = {
    id: uid('e'), nombre, ejercicio, estado: 'Borrador', creada: ahora(), creadaPor: SES ? SES.usuario : '',
    banco: B.version,
    datos: base ? JSON.parse(JSON.stringify(base.datos)) : {
      empresa: DB.config.institucion, nombreComercial: DB.config.nombreComercial, director: '', contralorNombre: '', contralorCargo: 'Contralor Interno',
      presidenteCA: '', presidenteCargo: 'Presidente del Comité de Auditoría', revisadoPor: 'Presidente, Secretario y Vocales del Consejo de Administración',
      fechaInicio: hoy(), fechaFin: new Date(Date.now() + 30 * 864e5).toISOString().slice(0, 10), proximaEvaluacion: '',
      procesos: 'Gobierno\nCrédito y cobranza\nTalento humano\nTecnologías de la información\nContabilidad y finanzas', evaluadores: '', conclusiones: '', explicacion: '', notas: '',
    },
    resp: {},
  };
  if (base) {
    ev.datos.fechaInicio = hoy();
    // Se copian respuestas y evidencias; la validación de auditoría inicia de nuevo.
    for (const [k, r] of Object.entries(base.resp)) if (PREG[k]) { const c = JSON.parse(JSON.stringify(r)); delete c.val; ev.resp[k] = c; }
  }
  DB.evals.push(ev);
  DB.evalActiva = ev.id;
  bitacora('Alta de evaluación', nombre + (base ? ' (copia de ' + base.nombre + ')' : ''));
  return ev;
}
function cargarDemo(ev) {
  for (const [k, d] of Object.entries(B.demo)) {
    if (!PREG[k]) continue;
    const r = JSON.parse(JSON.stringify(d));
    if (r.a) r.a = r.a.map((x) => (x === 1 ? 1 : 0));
    if (r.matriz) r.matriz = /^s/i.test(r.matriz) ? 'Sí' : 'No';
    r.upd = { por: 'demo', fecha: ahora() };
    ev.resp[k] = r;
  }
  ev.datos.empresa = ev.datos.empresa || 'Institución de demostración';
  bitacora('Carga de demostración', ev.nombre);
}

VISTAS.tablero = () => {
  const ev = evalActiva();
  const st = ev ? stats(ev) : null;
  const abiertos = DB.hallazgos.filter((h) => !['Solventado', 'Cerrado'].includes(h.estatus));
  const krisFuera = DB.kris.filter((k) => { const v = ultimoValor(k); return v && estadoKRI(k, v.valor).c !== 'b-good'; });
  const riesgosAltos = DB.riesgos.filter((r) => sev(r.probR || r.prob, r.impR || r.imp) >= 10);
  const pend = [];
  if (st) {
    if (SES.rol === 'contralor' && st.pendientes) pend.push(`<a href="#/cuestionario/${B.components[0].code}?f=pend">${st.pendientes} puntos de interés por contestar</a>`);
    if (SES.rol === 'contralor' && st.sinPlan.length) pend.push(`<a href="#/planes">${st.sinPlan.length} deficiencias de prioridad alta/media sin plan de solución</a>`);
    if (SES.rol === 'auditor' && st.porValidar) pend.push(`<a href="#/auditoria/validacion">${st.porValidar} respuestas por validar</a>`);
    if (st.errores.length) pend.push(`<a href="#/resultados">${st.errores.length} inconsistencias en la evaluación</a>`);
  }
  if (SES.rol === 'riesgos') {
    const sinEval = DB.riesgos.filter((r) => !r.prob || !r.imp).length;
    if (sinEval) pend.push(`<a href="#/riesgos">${sinEval} riesgos sin evaluar</a>`);
    const sinDato = DB.kris.filter((k) => !(k.valores || []).some((v) => v.periodo === periodoActual())).length;
    if (sinDato) pend.push(`<a href="#/riesgos/kri">${sinDato} KRI sin valor en ${periodoActual()}</a>`);
  }
  if (SES.rol === 'sistemas') {
    const dias = DB.meta.ultimoRespaldo ? Math.floor((Date.now() - new Date(DB.meta.ultimoRespaldo)) / 864e5) : null;
    pend.push(`<a href="#/admin/respaldos">${dias == null ? 'No se ha generado ningún respaldo' : 'Último respaldo hace ' + dias + ' día(s)'}</a>`);
  }
  if (abiertos.some(hallazgoVencido) && ['auditor', 'contralor'].includes(SES.rol)) pend.push(`<a href="#/auditoria">${abiertos.filter(hallazgoVencido).length} hallazgos con fecha compromiso vencida</a>`);

  return `${cabecera('Tablero', ev ? `${esc(ev.nombre)} · ${esc(ev.datos.empresa || DB.config.institucion)}` : 'Resumen del sistema de control interno')}
  ${pend.length ? `<div class="callout info" style="margin-bottom:1rem"><b>Pendientes de ${esc(ROLES[SES.rol].n)}:</b> ${pend.join(' · ')}</div>` : ''}
  ${!ev ? sinEval() : `
  <div class="grid g4">
    ${tile('Madurez del SCI (ponderada)', st.global == null ? '—' : fmtN(st.global), badgeMadurez(st.global) + ` <span class="muted">de 5.00</span>`)}
    ${tile('Avance de la evaluación', fmtPct(st.contestadas / st.total, 0), `${st.contestadas} de ${st.total} puntos de interés`, progreso(st.contestadas, st.total))}
    ${tile('Inconsistencias', st.errores.length, `${st.sinEvidencia.length} con evidencia faltante`)}
    ${tile('Planes de solución', st.planes.total, `<span class="badge ${st.planes.Vencido ? 'b-crit' : 'b-good'}">${st.planes.Vencido} vencidos</span> ${st.planes.Concluido} concluidos`)}
  </div>
  <div class="grid g2" style="margin-top:1rem">
    <div class="card"><div class="card-head"><h3>Madurez por componente</h3><a class="btn sm" href="#/resultados">Ver detalle</a></div>
      ${barras(st.comps.map((c) => ({ etiqueta: c.name, valor: c.score, tip: `${c.name}: ${c.score == null ? 'sin datos' : fmtN(c.score) + ' · ' + madurez(c.score)} (${c.contestadas}/${c.total} contestadas)` })))}
      <p class="muted" style="font-size:.78rem;margin:.5rem 0 0">Escala 0–5. Líneas punteadas: límites de los niveles de madurez.</p>
    </div>
    <div class="card"><h3>Nivel de riesgo de los puntos de interés</h3>
      ${apilada([{ n: 'Riesgo bajo', v: st.riesgo.Bajo, color: 'var(--good)' }, { n: 'Riesgo moderado', v: st.riesgo.Moderado, color: 'var(--warn)' }, { n: 'Riesgo alto', v: st.riesgo.Alto, color: 'var(--crit)' }])}
      <h3 style="margin-top:1.25rem">¿Los componentes operan de manera integrada?</h3>
      <p><span class="badge ${st.integrado ? 'b-good' : 'b-crit'}">${st.integrado ? 'Sí' : 'No'}</span>
      <span class="muted">Criterio: todos los puntos contestados, madurez ≥ 3 y al menos ${fmtPct(DB.config.umbralIntegracion, 0)} presentes y funcionando en cada componente.</span></p>
    </div>
  </div>`}
  <div class="grid g4" style="margin-top:1rem">
    ${tile('Hallazgos abiertos', abiertos.length, `<span class="badge ${abiertos.some(hallazgoVencido) ? 'b-crit' : 'b-good'}">${abiertos.filter(hallazgoVencido).length} vencidos</span>`)}
    ${tile('Riesgos residuales alto/crítico', riesgosAltos.length, `de ${DB.riesgos.length} en la matriz`)}
    ${tile('KRI fuera de apetito', krisFuera.length, `de ${DB.kris.length} indicadores`)}
    ${tile('Expedientes revisados (mesa)', DB.mesa.revisiones.length, `${DB.mesa.revisiones.filter((r) => estadoRevision(r) === 'Detenido').length} detenidos`)}
  </div>
  ${krisFuera.length ? `<div class="card" style="margin-top:1rem"><h3>Indicadores clave de riesgo fuera de apetito</h3><div class="tbl-wrap"><table class="tbl"><tr><th>Indicador</th><th class="r">Último valor</th><th>Periodo</th><th>Estado</th></tr>
    ${krisFuera.map((k) => { const v = ultimoValor(k); const s = estadoKRI(k, v.valor); return `<tr><td>${esc(k.nombre)}</td><td class="r num">${fmtN(v.valor)} ${esc(k.unidad)}</td><td>${esc(v.periodo)}</td><td><span class="badge ${s.c}">${esc(s.n)}</span></td></tr>`; }).join('')}</table></div></div>` : ''}`;
};

VISTAS.evaluacion = () => {
  const ev = evalActiva();
  const puedeDatos = can('eval.datos') && ev && !evalBloqueada(ev);
  const d = ev ? ev.datos : {};
  return `${cabecera('Evaluaciones y datos generales', 'Cada evaluación corresponde a un cierre de ejercicio. Puede crear una nueva copiando las respuestas de la anterior para dar seguimiento a la mejora.',
    can('eval.gestionar') ? `<button class="btn primary" data-act="eval-nueva">${ico('mas')} Nueva evaluación</button>` : '')}
  <div class="card"><div class="tbl-wrap"><table class="tbl">
    <tr><th>Evaluación</th><th>Ejercicio</th><th>Estado</th><th>Avance</th><th class="r">Madurez</th><th>Creada</th><th class="no-print">Acciones</th></tr>
    ${DB.evals.length ? DB.evals.map((e) => {
      const s = stats(e);
      return `<tr class="${e.id === DB.evalActiva ? 'sel' : ''}"><td><b>${esc(e.nombre)}</b>${e.banco !== B.version ? `<br><small>Banco ${esc(e.banco)}</small>` : ''}</td><td>${esc(e.ejercicio)}</td>
      <td><span class="badge ${e.estado === 'Cerrada' ? 'b-neutral' : e.estado === 'En revisión' ? 'b-warn' : 'b-info'}">${esc(e.estado)}</span></td>
      <td style="min-width:120px">${progreso(s.contestadas, s.total)}<small>${s.contestadas}/${s.total}</small></td>
      <td class="r">${s.global == null ? '—' : fmtN(s.global)} ${badgeMadurez(s.global)}</td><td>${fmtFecha(e.creada)}<br><small>${esc(e.creadaPor)}</small></td>
      <td class="no-print"><div class="row">
        ${e.id !== DB.evalActiva ? `<button class="btn sm" data-act="eval-activar" data-id="${e.id}">Activar</button>` : ''}
        ${can('eval.responder') && e.estado === 'Borrador' ? `<button class="btn sm" data-act="eval-estado" data-id="${e.id}" data-e="En revisión">Enviar a revisión</button>` : ''}
        ${can('eval.validar') && e.estado === 'En revisión' ? `<button class="btn sm" data-act="eval-estado" data-id="${e.id}" data-e="Borrador">Devolver</button>` : ''}
        ${can('eval.cerrar') && e.estado !== 'Cerrada' ? `<button class="btn sm" data-act="eval-estado" data-id="${e.id}" data-e="Cerrada">Cerrar</button>` : ''}
        ${can('eval.cerrar') && e.estado === 'Cerrada' ? `<button class="btn sm" data-act="eval-estado" data-id="${e.id}" data-e="En revisión">Reabrir</button>` : ''}
        ${(can('admin') || (can('eval.gestionar') && e.estado === 'Borrador')) ? `<button class="btn sm danger" data-act="eval-borrar" data-id="${e.id}">Eliminar</button>` : ''}
      </div></td></tr>`;
    }).join('') : '<tr><td colspan="7" class="empty">Sin evaluaciones.</td></tr>'}
  </table></div></div>
  ${ev ? `<div class="card"><div class="card-head"><h2>Datos generales — ${esc(ev.nombre)}</h2>${evalBloqueada(ev) ? '<span class="badge b-neutral">Evaluación cerrada: solo lectura</span>' : ''}</div>
  <form data-submit="eval-datos">
    <h3>Datos de la institución</h3>
    <div class="grid g3">
      ${campo('nombre', 'Nombre de la evaluación', ev.nombre, { dis: !puedeDatos })}
      ${campo('ejercicio', 'Al cierre del ejercicio', ev.ejercicio, { dis: !puedeDatos })}
      ${campo('empresa', 'Empresa', d.empresa, { dis: !puedeDatos })}
      ${campo('nombreComercial', 'Nombre comercial', d.nombreComercial, { dis: !puedeDatos })}
      ${campo('director', 'Director o Gerente General', d.director, { dis: !puedeDatos })}
      ${campo('proximaEvaluacion', 'Próxima evaluación', d.proximaEvaluacion, { dis: !puedeDatos, ph: 'Cierre del ejercicio ' + (Number(ev.ejercicio) + 1 || '') })}
    </div>
    <h3>Responsable de Contraloría Interna</h3>
    <div class="grid g4">
      ${campo('contralorNombre', 'Nombre', d.contralorNombre, { dis: !puedeDatos })}
      ${campo('contralorCargo', 'Cargo o puesto', d.contralorCargo, { dis: !puedeDatos })}
      ${campo('fechaInicio', 'Fecha de inicio', d.fechaInicio, { tipo: 'date', dis: !puedeDatos })}
      ${campo('fechaFin', 'Fecha de fin', d.fechaFin, { tipo: 'date', dis: !puedeDatos })}
    </div>
    <h3>Comité de Auditoría</h3>
    <div class="grid g3">
      ${campo('presidenteCA', 'Presidente del Comité de Auditoría', d.presidenteCA, { dis: !puedeDatos })}
      ${campo('presidenteCargo', 'Cargo o puesto', d.presidenteCargo, { dis: !puedeDatos })}
      ${campo('revisadoPor', 'Revisado por (nombre y cargo)', d.revisadoPor, { dis: !puedeDatos })}
    </div>
    <div class="grid g2">
      ${campo('procesos', 'Procesos seleccionados (uno por renglón)', d.procesos, { tipo: 'textarea', dis: !puedeDatos })}
      ${campo('evaluadores', 'Equipo evaluador', d.evaluadores, { tipo: 'textarea', dis: !puedeDatos, ph: 'Nombre — cargo' })}
    </div>
    <div class="callout" style="margin-bottom:.75rem">El proceso de evaluación y la aplicación del presente instrumento es responsabilidad del Comité de Auditoría, en conjunto con las unidades relacionadas. Los resultados se revisan con la Gerencia y las áreas propietarias de cada punto de interés.</div>
    ${puedeDatos ? '<div class="row end"><button class="btn primary" type="submit">Guardar datos generales</button></div>' : ''}
  </form></div>` : ''}`;
};
ACT['eval-nueva'] = async () => {
  const anio = new Date().getFullYear();
  const r = await formModal({
    titulo: 'Nueva evaluación', chico: true,
    cuerpo: `${campo('nombre', 'Nombre', 'Evaluación COSO ERM ' + anio, { req: true })}
      ${campo('ejercicio', 'Ejercicio (cierre)', String(anio), { req: true })}
      ${campo('copiar', 'Copiar respuestas y evidencias de', '', { opciones: [['', '— Iniciar en blanco —'], ...DB.evals.map((e) => [e.id, e.nombre])] })}
      ${campo('demo', 'Cargar respuestas de ejemplo del Excel (capacitación)', false, { tipo: 'checkbox' })}`,
    botones: [{ id: 'cancel', t: 'Cancelar' }, { id: 'ok', t: 'Crear', primary: true }],
  }, (d) => (!d.nombre.trim() ? 'Indique el nombre.' : null));
  if (!r) return;
  const ev = nuevaEvaluacion(r.datos.nombre.trim(), r.datos.ejercicio.trim(), r.datos.copiar || null);
  if (r.datos.demo) cargarDemo(ev);
  guardar(); render(); toast('Evaluación creada y activada.');
};
ACT['eval-activar'] = (t) => { DB.evalActiva = t.dataset.id; guardar(); render(); };
ACT['eval-estado'] = async (t) => {
  const ev = DB.evals.find((e) => e.id === t.dataset.id);
  const nuevo = t.dataset.e;
  if (nuevo === 'Cerrada') {
    const s = stats(ev);
    const avisos = [];
    if (s.pendientes) avisos.push(`${s.pendientes} puntos de interés sin contestar`);
    if (s.errores.length) avisos.push(`${s.errores.length} inconsistencias`);
    if (s.porValidar) avisos.push(`${s.porValidar} respuestas sin validar`);
    if (!await confirmar('Cerrar evaluación', `Al cerrar, la evaluación queda en solo lectura.${avisos.length ? '<br><br><b>Atención:</b> ' + esc(avisos.join(', ')) + '.' : ''}`, { ok: 'Cerrar evaluación' })) return;
    ev.cerrada = ahora(); ev.cerradaPor = SES.usuario;
  }
  ev.estado = nuevo;
  bitacora('Cambio de estado de evaluación', ev.nombre + ' → ' + nuevo);
  guardar(); render();
};
ACT['eval-borrar'] = async (t) => {
  const ev = DB.evals.find((e) => e.id === t.dataset.id);
  if (!await confirmar('Eliminar evaluación', `Se eliminará <b>${esc(ev.nombre)}</b> con todas sus respuestas. Esta acción no se puede deshacer.`, { ok: 'Eliminar', peligro: true })) return;
  DB.evals = DB.evals.filter((e) => e !== ev);
  if (DB.evalActiva === ev.id) DB.evalActiva = DB.evals.length ? DB.evals[DB.evals.length - 1].id : null;
  bitacora('Baja de evaluación', ev.nombre);
  guardar(); render();
};
ACT['eval-datos'] = (f) => {
  const ev = evalActiva();
  const d = leerForm(f);
  ev.nombre = d.nombre.trim() || ev.nombre; ev.ejercicio = d.ejercicio.trim();
  delete d.nombre; delete d.ejercicio;
  Object.assign(ev.datos, d);
  bitacora('Datos generales', ev.nombre);
  guardar(); render(); toast('Datos generales guardados.');
};

/* Cuestionario --------------------------------------------------------- */
const FILTROS = [['', 'Todos'], ['pend', 'Sin contestar'], ['err', 'Con inconsistencia'], ['alto', 'Riesgo alto'], ['plan', 'Requieren plan'], ['val', 'Por validar'], ['obs', 'Con observaciones de auditoría'], ['nuevo', 'Nuevos 2026']];
let CUES = { q: '', f: '', tema: '' };
function filtraPregunta(q, r) {
  if (CUES.tema && q.tema !== CUES.tema) return false;
  if (CUES.q) {
    const t = norm(q.id + ' ' + q.t + ' ' + (q.orig || ''));
    if (!norm(CUES.q).split('_').every((w) => t.includes(w))) return false;
  }
  const a = r && r.a;
  switch (CUES.f) {
    case 'pend': return !a;
    case 'err': return noAcumulativo(a);
    case 'alto': return riesgoQ(a) === 'Alto';
    case 'plan': return requierePlan(r || {}) && !(r && r.plan);
    case 'val': return !!a && !(r.val && r.val.estado);
    case 'obs': return !!(r && r.val && r.val.estado === 'Con observaciones');
    case 'nuevo': return !!q.nuevo;
    default: return true;
  }
}
function htmlPregunta(q, r, editable) {
  const a = r && r.a;
  const lv = nivel(a);
  const v = r && r.val && r.val.estado;
  return `<div class="q" id="q-${q.id.replace(/\./g, '-')}">
    <div class="qid">${esc(q.id)}</div>
    <div>
      <div class="qt">${esc(q.t)}</div>
      <div class="qmeta">
        ${q.nuevo ? '<span class="badge b-info plain">Nuevo 2026</span>' : ''}
        ${q.actualizado ? '<span class="badge b-info plain">Actualizado 2026</span>' : ''}
        ${q.tema ? `<span class="badge b-neutral plain">${esc(q.tema)}</span>` : ''}
        ${q.orig && q.orig !== q.id ? `<span class="badge b-neutral plain" title="Identificador en el Excel original">Excel ${esc(q.orig)}</span>` : ''}
        ${noAcumulativo(a) ? '<span class="badge b-crit">Atributos no acumulativos</span>' : ''}
        ${v ? `<span class="badge ${v === 'Validado' ? 'b-good' : 'b-serious'}">${esc(v)}</span>` : ''}
        ${r && r.prio ? `<span class="badge b-neutral">Prioridad ${esc(r.prio)}</span>` : ''}
        ${r && (r.plan || r.defi) ? `<span class="badge ${planEstado(r) === 'Vencido' ? 'b-crit' : 'b-neutral'}">Plan: ${esc(planEstado(r))}</span>` : ''}
      </div>
    </div>
    <div class="q-side">
      <div class="attr-legend">${ATR.map((x) => `<span title="${esc(x.n)}">${x.k}</span>`).join('')}</div>
      <div class="attrs" role="group" aria-label="Atributos de ${esc(q.id)}">${ATR.map((x, i) => `<button class="attr ${a && a[i] ? 'on' : ''}" ${editable ? '' : 'disabled'} data-act="attr" data-q="${q.id}" data-i="${i}" aria-pressed="${a && a[i] ? 'true' : 'false'}" title="${esc(x.k + ') ' + x.n)}">${a ? (a[i] ? '1' : '0') : ''}</button>`).join('')}</div>
      <div class="row">
        ${a ? `<span class="lvl" title="Nivel de cumplimiento según la tabla de criterios">Nivel ${lv}</span>
          <span class="badge ${presente(a) ? 'b-good' : 'b-neutral'} plain" title="a+b+c+d ≥ 3">${presente(a) ? 'Presente' : 'No presente'}</span>
          <span class="badge ${funcionando(a) ? 'b-good' : 'b-neutral'} plain" title="e+f+g+h ≥ 3">${funcionando(a) ? 'Funcionando' : 'No funcionando'}</span>
          ${badgeRiesgo(riesgoQ(a))}` : `<span class="muted">Sin contestar</span>${editable ? `<button class="btn sm" data-act="attr-cero" data-q="${q.id}" title="Registrar que no existe ningún atributo">Evaluar en 0</button>` : ''}`}
        <button class="btn sm" data-act="detalle" data-q="${q.id}">Detalle</button>
      </div>
    </div>
  </div>`;
}
function htmlPrincipio(p, ev) {
  const st = stats(ev).comps.flatMap((c) => c.principles).find((x) => x.n === p.n);
  return `<header id="ph-${p.n}"><h3>Principio ${p.n}: ${esc(p.t)}</h3>
    <span class="muted num">${st.contestadas}/${st.total}</span>
    <span class="num"><b>${st.score == null ? '—' : fmtN(st.score)}</b></span>${badgeMadurez(st.score)}</header>`;
}
VISTAS.cuestionario = (args) => {
  const ev = evalActiva();
  if (!ev) return cabecera('Cuestionario') + sinEval();
  const qs = new URLSearchParams(location.hash.split('?')[1] || '');
  if (qs.get('f') != null) CUES.f = qs.get('f');
  const code = (args[0] || B.components[0].code).split('?')[0];
  const comp = COMP[code] || B.components[0];
  const editable = can('eval.responder') && !evalBloqueada(ev);
  const st = stats(ev);
  let total = 0;
  const cuerpo = comp.principles.map((p) => {
    const filas = p.q.filter((q) => filtraPregunta(q, ev.resp[q.id]));
    total += filas.length;
    if (!filas.length) return '';
    return `<section class="principle" data-p="${p.n}">${htmlPrincipio(p, ev)}${filas.map((q) => htmlPregunta(q, ev.resp[q.id], editable)).join('')}</section>`;
  }).join('');
  return `${cabecera('Cuestionario COSO ERM', `Marque los atributos que cumple cada punto de interés. El nivel (0–5) se obtiene de la tabla de criterios: <b>a</b> Existe · <b>b</b> Diseñada · <b>c</b> Aprobado · <b>d</b> Difundido · <b>e</b> Implementado · <b>f</b> Responsable · <b>g</b> Funcionamiento · <b>h</b> Mejora continua.`,
    `<a class="btn" href="#/catalogos/criterios">Criterios</a>`)}
  ${!editable ? `<div class="callout ${evalBloqueada(ev) ? 'warn' : ''}" style="margin-bottom:1rem">${evalBloqueada(ev) ? 'La evaluación está cerrada: solo lectura.' : `Su perfil (${esc(ROLES[SES.rol].n)}) consulta las respuestas; el Contralor interno las captura.${can('eval.validar') ? ' Use «Detalle» para validar u observar cada respuesta.' : ''}`}</div>` : ''}
  <div class="tabs" role="tablist">${st.comps.map((c) => `<a href="#/cuestionario/${c.code}" class="${c.code === comp.code ? 'on' : ''}">${esc(c.name)} <small class="num">${c.contestadas}/${c.total}</small></a>`).join('')}</div>
  <div class="row no-print" style="margin-bottom:1rem">
    <input type="search" placeholder="Buscar por texto o ID…" value="${esc(CUES.q)}" data-chg="cues-q" style="max-width:300px">
    <select data-chg="cues-f" style="max-width:240px">${FILTROS.map(([v, t]) => `<option value="${v}" ${CUES.f === v ? 'selected' : ''}>${esc(t)}</option>`).join('')}</select>
    <select data-chg="cues-tema" style="max-width:220px"><option value="">Todos los temas</option>${TEMAS.map((t) => `<option ${CUES.tema === t ? 'selected' : ''}>${esc(t)}</option>`).join('')}</select>
    <span class="muted">${total} punto(s) mostrados</span>
  </div>
  ${cuerpo || '<div class="card empty">Ningún punto de interés coincide con el filtro.</div>'}`;
};
CHG['cues-q'] = (t) => { CUES.q = t.value; render(); };
CHG['cues-f'] = (t) => { CUES.f = t.value; history.replaceState(null, '', location.hash.split('?')[0]); render(); };
CHG['cues-tema'] = (t) => { CUES.tema = t.value; render(); };

function refrescarPregunta(qid) {
  const ev = evalActiva();
  const q = PREG[qid];
  const el = document.getElementById('q-' + qid.replace(/\./g, '-'));
  if (el) el.outerHTML = htmlPregunta(q, ev.resp[qid], can('eval.responder') && !evalBloqueada(ev));
  const ph = document.getElementById('ph-' + q.p);
  if (ph) ph.outerHTML = htmlPrincipio(PRINCIPIOS.find((p) => p.n === q.p), ev);
}
function marcarCambio(r) { r.upd = { por: SES.usuario, fecha: ahora() }; if (r.val && r.val.estado === 'Validado') r.val = { ...r.val, estado: '', obs: (r.val.obs || '') + ' [Respuesta modificada después de validar]' }; }
ACT.attr = (t) => {
  const ev = evalActiva();
  if (!can('eval.responder') || evalBloqueada(ev)) return;
  const qid = t.dataset.q, i = Number(t.dataset.i);
  const r = ev.resp[qid] || (ev.resp[qid] = {});
  if (!r.a) r.a = [0, 0, 0, 0, 0, 0, 0, 0];
  const nuevo = r.a[i] ? 0 : 1;
  // Atajo acumulativo: al marcar un atributo se marcan los anteriores; al desmarcar, los posteriores.
  if (nuevo) for (let k = 0; k <= i; k++) r.a[k] = 1; else for (let k = i; k < 8; k++) r.a[k] = 0;
  marcarCambio(r);
  bitacora('Respuesta', `${qid}: ${r.a.join('')} (nivel ${nivel(r.a)})`);
  guardar();
  refrescarPregunta(qid);
  const b = document.querySelector(`[data-act="attr"][data-q="${qid}"][data-i="${i}"]`);
  if (b) b.focus();
};
ACT['attr-cero'] = (t) => {
  const ev = evalActiva();
  const qid = t.dataset.q;
  const r = ev.resp[qid] || (ev.resp[qid] = {});
  r.a = [0, 0, 0, 0, 0, 0, 0, 0];
  marcarCambio(r);
  bitacora('Respuesta', `${qid}: 00000000 (nivel 0)`);
  guardar();
  refrescarPregunta(qid);
};

/* Detalle de un punto de interés: evidencias, análisis, plan y validación */
ACT.detalle = async (t) => {
  const ev = evalActiva();
  const qid = t.dataset.q;
  const q = PREG[qid];
  const r = ev.resp[qid] || {};
  const bloq = evalBloqueada(ev);
  const eR = can('eval.responder') && !bloq;
  const eM = (can('eval.riesgo') || can('eval.responder')) && !bloq;
  const eV = can('eval.validar') && !bloq;
  const evs = r.ev || [];
  const riesgosVinc = DB.riesgos.filter((x) => (x.qids || []).includes(qid));
  const hall = DB.hallazgos.filter((h) => h.qid === qid);
  const res = await formModal({
    titulo: `Punto de interés ${qid}`,
    cuerpo: `<p><b>${esc(q.t)}</b></p>
    <p class="muted">Componente: ${esc(COMP[q.comp].name)} · Principio ${q.p}${q.orig ? ' · ID Excel ' + esc(q.orig) : ''}${r.upd ? ' · Última modificación: ' + esc(r.upd.por) + ', ' + fmtFechaHora(r.upd.fecha) : ''}</p>
    ${r.a ? `<p>Atributos: <code>${r.a.map((x, i) => ATR[i].k + '=' + x).join(' ')}</code> → <b>Nivel ${nivel(r.a)}</b> ${badgeRiesgo(riesgoQ(r.a))}</p>` : '<div class="callout warn" style="margin-bottom:.75rem">Aún no se capturan los atributos de este punto de interés.</div>'}
    <h3>Responsables</h3>
    <div class="grid g2">
      ${campo('area', 'Gerencia / área / comité', r.area, { dis: !eR, lista: 'dl-areas' })}
      ${campo('cargo', 'Cargo responsable', r.cargo, { dis: !eR, lista: 'dl-cargos' })}
    </div>
    ${datalist('dl-areas', DB.responsables.areas)}${datalist('dl-cargos', DB.responsables.cargos)}
    <h3>Sustentos para su cumplimiento</h3>
    <div class="grid g2">
      ${campo('ev0', 'a y b · Nombre del documento (política, procedimiento, actividad)', evs[0], { tipo: 'textarea', dis: !eR })}
      ${ATR.slice(2).map((x, i) => campo('ev' + (i + 1), `${x.k} · ${x.n}`, evs[i + 1], { tipo: 'textarea', dis: !eR, ph: x.ev })).join('')}
      ${campo('ubic', 'Ubicación electrónica de las evidencias', r.ubic, { dis: !eR, ph: 'Servidor, carpeta compartida, intranet, URL…' })}
    </div>
    <h3>Análisis</h3>
    <div class="grid g3">
      ${campo('matriz', '¿Integrado en la matriz de riesgos?', r.matriz || '', { opciones: [['', '—'], 'Sí', 'No'], dis: !eM })}
      ${campo('prio', 'Prioridad', r.prio || '', { opciones: [['', '—'], 'Alta', 'Media', 'Baja'], dis: !eM })}
      <div class="field"><label class="f">Riesgos vinculados</label>${riesgosVinc.length ? riesgosVinc.map((x) => `<span class="badge b-neutral plain">${esc(x.clave)}</span>`).join(' ') : '<span class="muted">Ninguno (vincúlelos desde Gestión de riesgos)</span>'}</div>
    </div>
    ${campo('coment', 'Comentario', r.coment, { tipo: 'textarea', dis: !eR })}
    ${campo('defi', 'Descripción de la deficiencia', r.defi, { tipo: 'textarea', dis: !eR })}
    <h3>Plan de solución ${requierePlan(r) && !r.plan ? '<span class="badge b-crit">Requerido por prioridad</span>' : ''}</h3>
    ${campo('plan', 'Descripción del plan de solución', r.plan, { tipo: 'textarea', dis: !eR })}
    <div class="grid g3">
      ${campo('resp', 'Responsable (nombre completo — cargo)', r.resp, { dis: !eR })}
      ${campo('fi', 'Fecha de inicio', r.fi, { tipo: 'date', dis: !eR })}
      ${campo('ff', 'Fecha de fin', r.ff, { tipo: 'date', dis: !eR })}
      ${campo('presup', 'Presupuesto', r.presup, { dis: !eR })}
      ${campo('entreg', 'Entregable', r.entreg, { dis: !eR })}
      ${campo('avance', 'Avance (%)', r.avance ?? '', { tipo: 'number', dis: !eR, attrs: 'min="0" max="100" step="5"' })}
    </div>
    <h3>Validación de Auditoría Interna</h3>
    <div class="grid g3">
      ${campo('valEstado', 'Estado', (r.val && r.val.estado) || '', { opciones: [['', 'Pendiente'], 'Validado', 'Con observaciones'], dis: !eV })}
      <div style="grid-column:span 2">${campo('valObs', 'Observación del auditor', r.val && r.val.obs, { tipo: 'textarea', dis: !eV })}</div>
    </div>
    ${r.val && r.val.por ? `<p class="muted">Validado por ${esc(r.val.por)} el ${fmtFechaHora(r.val.fecha)}</p>` : ''}
    ${hall.length ? `<h3>Hallazgos relacionados</h3><ul>${hall.map((h) => `<li>${esc(h.folio)} — ${esc(h.titulo)} <span class="badge b-neutral">${esc(h.estatus)}</span></li>`).join('')}</ul>` : ''}`,
    botones: [
      ...(can('hallazgos') ? [{ id: 'hallazgo', t: 'Registrar hallazgo' }] : []),
      { id: 'cancel', t: 'Cerrar' },
      ...((eR || eM || eV) ? [{ id: 'ok', t: 'Guardar', primary: true }] : []),
    ],
  }, (d) => {
    if (d.avance !== '' && (Number(d.avance) < 0 || Number(d.avance) > 100)) return 'El avance debe estar entre 0 y 100.';
    if (d.fi && d.ff && d.ff < d.fi) return 'La fecha de fin no puede ser anterior a la de inicio.';
    if (d.valEstado === 'Con observaciones' && !d.valObs.trim()) return 'Describa la observación de auditoría.';
    return null;
  });
  if (!res) return;
  const d = res.datos;
  if (res.boton === 'ok' || res.boton === 'hallazgo') {
    const rr = ev.resp[qid] || (ev.resp[qid] = {});
    const antes = JSON.stringify([rr.area, rr.cargo, rr.ubic, rr.coment, rr.defi, rr.plan, rr.resp, rr.fi, rr.ff, rr.presup, rr.entreg, rr.avance, rr.ev]);
    if (eR) {
      Object.assign(rr, { area: d.area, cargo: d.cargo, ubic: d.ubic, coment: d.coment, defi: d.defi, plan: d.plan, resp: d.resp, fi: d.fi, ff: d.ff, presup: d.presup, entreg: d.entreg, avance: d.avance === '' ? null : Number(d.avance) });
      rr.ev = [0, 1, 2, 3, 4, 5, 6].map((i) => d['ev' + i] || '');
      if (JSON.stringify([rr.area, rr.cargo, rr.ubic, rr.coment, rr.defi, rr.plan, rr.resp, rr.fi, rr.ff, rr.presup, rr.entreg, rr.avance, rr.ev]) !== antes) marcarCambio(rr);
    }
    if (eM) Object.assign(rr, { matriz: d.matriz, prio: d.prio });
    if (eV && (d.valEstado || '') !== ((rr.val && rr.val.estado) || '') || (eV && d.valObs !== ((rr.val && rr.val.obs) || ''))) {
      rr.val = { estado: d.valEstado, obs: d.valObs, por: SES.usuario, fecha: ahora() };
      bitacora('Validación de auditoría', `${qid}: ${d.valEstado || 'Pendiente'}`);
    }
    bitacora('Detalle de punto de interés', qid);
    guardar();
  }
  if (res.boton === 'hallazgo') return editarHallazgo(null, { qid, titulo: 'Deficiencia en ' + qid, condicion: d.defi || '', criterio: q.t, origen: SES.rol === 'contralor' ? 'Contraloría interna' : 'Auditoría interna' });
  if (location.hash.startsWith('#/cuestionario')) refrescarPregunta(qid); else render();
};

/* Resultados ----------------------------------------------------------- */
VISTAS.resultados = (args) => {
  const ev = evalActiva();
  if (!ev) return cabecera('Resultados') + sinEval();
  const st = stats(ev);
  const otras = DB.evals.filter((e) => e.id !== ev.id);
  const compId = args[0] && otras.some((e) => e.id === args[0]) ? args[0] : (otras.length ? otras[otras.length - 1].id : '');
  const compEv = otras.find((e) => e.id === compId);
  const st2 = compEv ? stats(compEv) : null;
  const editC = can('conclusiones') && !evalBloqueada(ev);
  return `${cabecera('Resultados de la evaluación', `Madurez y cumplimiento del sistema de control interno — ${esc(ev.nombre)}`, `<a class="btn" href="#/reportes/ejecutivo">${ico('reporte')} Informe ejecutivo</a>`)}
  <div class="grid g4">
    ${tile('Madurez ponderada', st.global == null ? '—' : fmtN(st.global), badgeMadurez(st.global))}
    ${tile('Promedio simple de componentes', st.promedioSimple == null ? '—' : fmtN(st.promedioSimple), badgeMadurez(st.promedioSimple))}
    ${tile('Cumplimiento respecto al máximo', st.global == null ? '—' : fmtPct(st.global / 5, 0), 'Puntaje / 5')}
    ${tile('Preguntas por contestar', st.pendientes, `${st.errores.length} errores en la evaluación`)}
  </div>
  <div class="card" style="margin-top:1rem"><h2>I. Resumen por componente</h2>
    <div class="tbl-wrap"><table class="tbl">
      <tr><th>Componente</th><th class="r">Ponderación</th><th class="r">Puntaje máximo</th><th class="r">Puntaje</th><th>Nivel de madurez</th><th class="r">% Cumplimiento</th><th class="r">Contestadas</th></tr>
      ${st.comps.map((c) => `<tr><td>${esc(c.name)}</td><td class="r num">${fmtPct(c.peso, 0)}</td><td class="r num">5</td><td class="r num"><b>${c.score == null ? '—' : fmtN(c.score)}</b></td><td>${badgeMadurez(c.score)}</td><td class="r num">${c.score == null ? '—' : fmtPct(c.score / 5, 0)}</td><td class="r num">${c.contestadas}/${c.total}</td></tr>`).join('')}
      <tr class="grp"><td>Sistema de control interno (ponderado)</td><td class="r num">${fmtPct(sum(st.comps.map((c) => c.peso)), 0)}</td><td class="r">5</td><td class="r num">${st.global == null ? '—' : fmtN(st.global)}</td><td>${badgeMadurez(st.global)}</td><td class="r num">${st.global == null ? '—' : fmtPct(st.global / 5, 0)}</td><td class="r num">${st.contestadas}/${st.total}</td></tr>
    </table></div>
  </div>
  <div class="card"><h2>II. Detalle por principio</h2>
    ${st.comps.map((c) => `<h3 style="margin-top:1rem">${esc(c.name)} ${badgeMadurez(c.score)}</h3>${barras(c.principles.map((p) => ({ etiqueta: `P${p.n}. ${p.t}`, valor: p.score, tip: `Principio ${p.n}: ${p.score == null ? 'sin datos' : fmtN(p.score) + ' · ' + madurez(p.score)} — ${p.contestadas}/${p.total} contestadas, ${p.presente} presentes, ${p.funcionando} funcionando` })))}`).join('')}
  </div>
  <div class="grid g2">
    <div class="card"><h2>III. ¿Están presentes y funcionando?</h2>
      <div class="tbl-wrap"><table class="tbl"><tr><th>Componente</th><th class="r">Está presente</th><th class="r">Está funcionando</th></tr>
      ${st.comps.map((c) => `<tr><td>${esc(c.name)}</td><td class="r num">${fmtPct(c.pctPresente, 0)}</td><td class="r num">${fmtPct(c.pctFuncionando, 0)}</td></tr>`).join('')}
      <tr class="grp"><td>SCI</td><td class="r num">${fmtPct(avg(st.comps.map((c) => c.pctPresente)), 0)}</td><td class="r num">${fmtPct(avg(st.comps.map((c) => c.pctFuncionando)), 0)}</td></tr></table></div>
      <p style="margin-top:.75rem">¿Operan todos los componentes juntos y de manera integrada? <span class="badge ${st.integrado ? 'b-good' : 'b-crit'}">${st.integrado ? 'Sí' : 'No'}</span></p>
    </div>
    <div class="card"><h2>IV. Riesgo de los puntos de interés</h2>
      <div class="tbl-wrap"><table class="tbl"><tr><th>Componente</th><th class="r">Bajo</th><th class="r">Moderado</th><th class="r">Alto</th></tr>
      ${st.comps.map((c) => `<tr><td>${esc(c.name)}</td><td class="r num">${c.riesgo.Bajo}</td><td class="r num">${c.riesgo.Moderado}</td><td class="r num">${c.riesgo.Alto}</td></tr>`).join('')}
      <tr class="grp"><td>Total</td>${['Bajo', 'Moderado', 'Alto'].map((k) => `<td class="r num">${st.riesgo[k]} <small>(${st.contestadas ? fmtPct(st.riesgo[k] / st.contestadas, 0) : '—'})</small></td>`).join('')}</tr></table></div>
      <p class="muted" style="font-size:.8rem;margin-top:.5rem">Suma de atributos: &gt; 6 riesgo bajo; 5–6 moderado; ≤ 4 alto.</p>
    </div>
  </div>
  <div class="card"><div class="card-head"><h2>V. Comparativo entre evaluaciones</h2>
    ${otras.length ? `<select data-chg="res-comp" style="max-width:320px">${otras.map((e) => `<option value="${e.id}" ${e.id === compId ? 'selected' : ''}>${esc(e.nombre)}</option>`).join('')}</select>` : ''}</div>
    ${!compEv ? '<p class="muted">Aplicable a partir de la segunda evaluación.</p>' : `
    <div class="grid g2"><div class="tbl-wrap"><table class="tbl"><tr><th>Componente</th><th class="r">${esc(compEv.ejercicio || compEv.nombre)}</th><th class="r">${esc(ev.ejercicio || ev.nombre)}</th><th class="r">Variación</th><th>Situación</th></tr>
      ${st.comps.map((c, i) => { const a = st2.comps[i].score, b = c.score; const v = a != null && b != null ? b - a : null; const s = v == null ? '—' : v > 0.005 ? 'Mejoró' : v < -0.005 ? 'Empeoró' : 'Sin cambio';
        return `<tr><td>${esc(c.name)}</td><td class="r num">${a == null ? '—' : fmtN(a)}</td><td class="r num">${b == null ? '—' : fmtN(b)}</td><td class="r num">${v == null ? '—' : (v > 0 ? '+' : '') + fmtN(v)}</td><td><span class="badge ${s === 'Mejoró' ? 'b-good' : s === 'Empeoró' ? 'b-crit' : 'b-neutral'}">${s}</span></td></tr>`; }).join('')}
    </table></div>
    <div>${barrasDobles(st.comps.map((c, i) => ({ etiqueta: c.name, valores: [st2.comps[i].score, c.score] })), [compEv.nombre, ev.nombre])}</div></div>`}
  </div>
  <div class="card"><h2>VI. Conclusiones</h2>
    <form data-submit="conclusiones">
      ${campo('conclusiones', 'Conclusiones sobre la madurez, operación y efectividad del SCI', ev.datos.conclusiones, { tipo: 'textarea', dis: !editC, attrs: 'rows="5"' })}
      ${campo('explicacion', 'Explicación de los componentes que empeoraron', ev.datos.explicacion, { tipo: 'textarea', dis: !editC })}
      ${campo('notas', 'Notas (deficiencias mayores a nivel principio o componente)', ev.datos.notas, { tipo: 'textarea', dis: !editC })}
      ${editC ? '<div class="row end"><button class="btn primary" type="submit">Guardar conclusiones</button></div>' : ''}
    </form>
  </div>
  ${st.errores.length || st.sinEvidencia.length ? `<div class="card"><h2>VII. Errores y evidencias faltantes</h2>
    <div class="tbl-wrap"><table class="tbl"><tr><th>Punto</th><th>Observación</th></tr>
    ${st.errores.map((e) => `<tr><td><a href="#" data-act="detalle" data-q="${e.id}">${e.id}</a></td><td><span class="badge b-crit">Error</span> ${esc(e.motivo)}</td></tr>`).join('')}
    ${st.sinEvidencia.map((e) => `<tr><td><a href="#" data-act="detalle" data-q="${e.id}">${e.id}</a></td><td><span class="badge b-warn">Evidencia</span> Atributos marcados sin sustento: ${esc(e.faltan.join(', '))}</td></tr>`).join('')}
    </table></div></div>` : ''}`;
};
CHG['res-comp'] = (t) => ir('resultados/' + t.value);
ACT.conclusiones = (f) => {
  const ev = evalActiva();
  Object.assign(ev.datos, leerForm(f));
  bitacora('Conclusiones', ev.nombre);
  guardar(); toast('Conclusiones guardadas.');
};

/* Planes de solución --------------------------------------------------- */
let PLAN_F = '';
function filasPlanes(ev) {
  return PREGUNTAS.map((q) => ({ q, r: ev.resp[q.id] || {} }))
    .filter(({ r }) => r.plan || r.defi || requierePlan(r))
    .map(({ q, r }) => ({ q, r, estado: planEstado(r) || 'Sin plan' }));
}
VISTAS.planes = () => {
  const ev = evalActiva();
  if (!ev) return cabecera('Planes de solución') + sinEval();
  const todas = filasPlanes(ev);
  const filas = todas.filter((x) => !PLAN_F || x.estado === PLAN_F);
  const cls = { Vencido: 'b-crit', Concluido: 'b-good', 'En proceso': 'b-info', Pendiente: 'b-warn', 'Sin plan': 'b-serious' };
  const cuenta = (e) => todas.filter((x) => x.estado === e).length;
  return `${cabecera('Planes de solución', 'Deficiencias identificadas y planes de solución (PS) para los puntos de interés con prioridad alta y media.', `<button class="btn" data-act="planes-csv">${ico('descarga')} CSV</button>`)}
  <div class="grid g4" style="margin-bottom:1rem">${['Sin plan', 'Pendiente', 'En proceso', 'Vencido'].map((e) => tile(e, cuenta(e))).join('')}</div>
  <div class="card">
    <div class="row" style="margin-bottom:.75rem"><select data-chg="plan-f" style="max-width:220px"><option value="">Todos los estados</option>${['Sin plan', 'Pendiente', 'En proceso', 'Vencido', 'Concluido'].map((e) => `<option ${PLAN_F === e ? 'selected' : ''}>${e}</option>`).join('')}</select><span class="muted">${filas.length} registro(s)</span></div>
    <div class="tbl-wrap"><table class="tbl">
      <tr><th>Punto</th><th>Nivel</th><th>Prioridad</th><th>Deficiencia</th><th>Plan de solución</th><th>Responsable</th><th>Fin</th><th style="min-width:110px">Avance</th><th>Estado</th></tr>
      ${filas.length ? filas.map(({ q, r, estado }) => `<tr>
        <td><a href="#" data-act="detalle" data-q="${q.id}"><b>${q.id}</b></a><br><small>${esc(trunc(q.t, 70))}</small></td>
        <td class="c">${nivel(r.a) ?? '—'}</td><td>${esc(r.prio || '—')}</td>
        <td>${esc(trunc(r.defi, 140))}</td><td>${esc(trunc(r.plan, 140)) || '<span class="muted">—</span>'}</td>
        <td>${esc(r.resp)}</td><td>${fmtFecha(r.ff)}</td>
        <td>${progreso(r.avance || 0, 100)}<small class="num">${r.avance || 0}%</small></td>
        <td><span class="badge ${cls[estado]}">${esc(estado)}</span></td></tr>`).join('') : '<tr><td colspan="9" class="empty">Sin deficiencias registradas.</td></tr>'}
    </table></div>
  </div>`;
};
CHG['plan-f'] = (t) => { PLAN_F = t.value; render(); };
ACT['planes-csv'] = () => {
  const ev = evalActiva();
  descargar(`SECI_planes_${sello()}.csv`, aCSV(filasPlanes(ev), COLS.planes), 'text/csv');
  bitacora('Exportación', 'Planes de solución CSV');
  guardar();
};
