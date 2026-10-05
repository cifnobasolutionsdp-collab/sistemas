/* =====================================================================
 * Reportes, integraciones, catálogos, administración e inicio
 * ===================================================================== */

/* Definición de columnas para exportar / importar ------------------------ */
const ATR_KEYS = ATR.map((a) => a.k);
const COLS = {
  hallazgos: [
    { key: 'folio', label: 'folio' }, { key: 'titulo', label: 'titulo' }, { key: 'origen', label: 'origen' }, { key: 'severidad', label: 'severidad' },
    { key: 'condicion', label: 'condicion' }, { key: 'criterio', label: 'criterio' }, { key: 'causa', label: 'causa' }, { key: 'efecto', label: 'efecto' },
    { key: 'recomendacion', label: 'recomendacion' }, { key: 'qid', label: 'punto_interes' }, { key: 'riesgo', label: 'riesgo' }, { key: 'area', label: 'area' },
    { key: 'responsable', label: 'responsable' }, { key: 'fechaCompromiso', label: 'fecha_compromiso' }, { key: 'estatus', label: 'estatus' },
  ],
  riesgos: [
    { key: 'clave', label: 'clave' }, { key: 'categoria', label: 'categoria' }, { key: 'proceso', label: 'proceso' }, { key: 'descripcion', label: 'descripcion' },
    { key: 'causa', label: 'causa' }, { key: 'consecuencia', label: 'consecuencia' }, { key: 'prob', label: 'probabilidad' }, { key: 'imp', label: 'impacto' },
    { key: 'controles', label: 'controles' }, { key: 'qids', label: 'puntos_interes' }, { key: 'probR', label: 'probabilidad_residual' }, { key: 'impR', label: 'impacto_residual' },
    { key: 'respuesta', label: 'respuesta' }, { key: 'dueno', label: 'dueno' },
    { key: 'sevI', label: 'severidad_inherente', get: (r) => sev(r.prob, r.imp), soloExport: true },
    { key: 'sevR', label: 'severidad_residual', get: (r) => sev(r.probR || r.prob, r.impR || r.imp), soloExport: true },
  ],
  auditorias: [
    { key: 'proceso', label: 'proceso' }, { key: 'area', label: 'area' }, { key: 'riesgo', label: 'riesgo' }, { key: 'periodo', label: 'periodo' },
    { key: 'responsable', label: 'responsable' }, { key: 'horas', label: 'horas' }, { key: 'estatus', label: 'estatus' }, { key: 'objetivo', label: 'objetivo' },
  ],
  kris: [
    { key: 'kri', label: 'kri' }, { key: 'periodo', label: 'periodo' }, { key: 'valor', label: 'valor' },
    { key: 'unidad', label: 'unidad', soloExport: true }, { key: 'estado', label: 'estado', soloExport: true },
  ],
  planes: [
    { key: 'id', label: 'punto_interes', get: (x) => x.q.id }, { key: 'texto', label: 'texto', get: (x) => x.q.t }, { key: 'nivel', label: 'nivel', get: (x) => nivel(x.r.a) },
    { key: 'prio', label: 'prioridad', get: (x) => x.r.prio }, { key: 'defi', label: 'deficiencia', get: (x) => x.r.defi }, { key: 'plan', label: 'plan_solucion', get: (x) => x.r.plan },
    { key: 'resp', label: 'responsable', get: (x) => x.r.resp }, { key: 'fi', label: 'fecha_inicio', get: (x) => x.r.fi }, { key: 'ff', label: 'fecha_fin', get: (x) => x.r.ff },
    { key: 'presup', label: 'presupuesto', get: (x) => x.r.presup }, { key: 'entreg', label: 'entregable', get: (x) => x.r.entreg }, { key: 'avance', label: 'avance', get: (x) => x.r.avance }, { key: 'estado', label: 'estado', get: (x) => x.estado },
  ],
  respuestas: [
    { key: 'id', label: 'punto_interes' }, { key: 'componente', label: 'componente', soloExport: true }, { key: 'principio', label: 'principio', soloExport: true }, { key: 'texto', label: 'texto', soloExport: true },
    ...ATR_KEYS.map((k) => ({ key: k, label: k })),
    { key: 'nivel', label: 'nivel', soloExport: true }, { key: 'presente', label: 'presente', soloExport: true }, { key: 'funcionando', label: 'funcionando', soloExport: true }, { key: 'riesgo', label: 'riesgo', soloExport: true },
    { key: 'area', label: 'area' }, { key: 'cargo', label: 'cargo' },
    ...['ev_ab', 'ev_c', 'ev_d', 'ev_e', 'ev_f', 'ev_g', 'ev_h'].map((k) => ({ key: k, label: 'evidencia_' + k.slice(3) })),
    { key: 'ubic', label: 'ubicacion' }, { key: 'matriz', label: 'matriz_riesgos' }, { key: 'prio', label: 'prioridad' }, { key: 'coment', label: 'comentario' },
    { key: 'defi', label: 'deficiencia' }, { key: 'plan', label: 'plan_solucion' }, { key: 'resp', label: 'responsable_plan' }, { key: 'fi', label: 'fecha_inicio' }, { key: 'ff', label: 'fecha_fin' },
    { key: 'presup', label: 'presupuesto' }, { key: 'entreg', label: 'entregable' }, { key: 'avance', label: 'avance' },
    { key: 'val', label: 'validacion_auditoria', soloExport: true }, { key: 'obs', label: 'observacion_auditoria', soloExport: true },
  ],
  bitacora: [
    { key: 'ts', label: 'fecha_hora' }, { key: 'usuario', label: 'usuario' }, { key: 'rol', label: 'rol' }, { key: 'accion', label: 'accion' }, { key: 'detalle', label: 'detalle' }, { key: 'prev', label: 'hash_anterior' }, { key: 'h', label: 'hash' },
  ],
};
COLS.mesa = () => [
  { key: 'folio', label: 'folio' }, { key: 'socio', label: 'socio' }, { key: 'producto', label: 'producto' }, { key: 'sucursal', label: 'sucursal' }, { key: 'monto', label: 'monto' },
  { key: 'fecha', label: 'fecha' }, { key: 'analista', label: 'analista' }, { key: 'nivel', label: 'nivel_autorizacion' }, { key: 'excepciones', label: 'excepciones' },
  { key: 'resultado', label: 'resultado', get: (r) => estadoRevision(r), soloExport: true },
  ...DB.mesa.checklist.map((c) => ({ key: 'it_' + c.id, label: c.id, get: (r) => (r.items || {})[c.id] || '' })),
];
function filasRespuestas(ev) {
  return PREGUNTAS.map((q) => {
    const r = ev.resp[q.id] || {};
    const o = { id: q.id, componente: COMP[q.comp].name, principio: q.p, texto: q.t };
    ATR_KEYS.forEach((k, i) => { o[k] = r.a ? r.a[i] : ''; });
    Object.assign(o, { nivel: nivel(r.a) ?? '', presente: r.a ? (presente(r.a) ? 'SI' : 'NO') : '', funcionando: r.a ? (funcionando(r.a) ? 'SI' : 'NO') : '', riesgo: riesgoQ(r.a) || '' });
    for (const k of ['area', 'cargo', 'ubic', 'matriz', 'prio', 'coment', 'defi', 'plan', 'resp', 'fi', 'ff', 'presup', 'entreg', 'avance']) o[k] = r[k] ?? '';
    ['ev_ab', 'ev_c', 'ev_d', 'ev_e', 'ev_f', 'ev_g', 'ev_h'].forEach((k, i) => { o[k] = (r.ev || [])[i] || ''; });
    o.val = (r.val && r.val.estado) || ''; o.obs = (r.val && r.val.obs) || '';
    return o;
  });
}
function filasKRI() {
  return DB.kris.flatMap((k) => (k.valores || []).map((v) => ({ kri: k.nombre, periodo: v.periodo, valor: v.valor, unidad: k.unidad, estado: estadoKRI(k, v.valor).n })));
}
function datosEntidad(e) {
  const ev = evalActiva();
  switch (e) {
    case 'hallazgos': return [DB.hallazgos, COLS.hallazgos];
    case 'riesgos': return [DB.riesgos, COLS.riesgos];
    case 'auditorias': return [DB.auditorias, COLS.auditorias];
    case 'kris': return [filasKRI(), COLS.kris];
    case 'mesa': return [DB.mesa.revisiones, COLS.mesa()];
    case 'planes': return [ev ? filasPlanes(ev) : [], COLS.planes];
    case 'respuestas': return [ev ? filasRespuestas(ev) : [], COLS.respuestas];
    case 'bitacora': return [DB.bitacora, COLS.bitacora];
    default: throw new Error('Entidad desconocida: ' + e);
  }
}
ACT['exp-csv'] = (t) => {
  const e = t.dataset.e;
  const [filas, cols] = datosEntidad(e);
  descargar(`SECI_${e}_${sello()}.csv`, aCSV(filas, cols), 'text/csv');
  bitacora('Exportación CSV', `${e} (${filas.length} registros)`);
  guardar();
};
ACT['plantilla-csv'] = (t) => {
  const e = t.dataset.e;
  if (e === 'cartera') {
    descargar('SECI_plantilla_cartera.csv', '﻿periodo,folio,socio,producto,sucursal,moneda,actividad,localidad,garantia,monto_original,saldo_vigente,saldo_vencido,dias_mora,plazo_meses,tasa_anual,fecha_otorgamiento,fecha_vencimiento\r\n', 'text/csv');
    return;
  }
  const cols = (typeof COLS[e] === 'function' ? COLS[e]() : COLS[e]).filter((c) => !c.soloExport);
  descargar(`SECI_plantilla_${e}.csv`, '﻿' + cols.map((c) => c.label).join(',') + '\r\n', 'text/csv');
};

/* Importación ----------------------------------------------------------- */
const IMPORTA = {
  hallazgos: { n: 'Hallazgos de auditoría', perm: 'hallazgos' },
  riesgos: { n: 'Matriz de riesgos', perm: 'riesgos' },
  kris: { n: 'Valores de KRI', perm: 'kris' },
  mesa: { n: 'Revisiones de mesa de control', perm: 'mesa' },
  auditorias: { n: 'Plan anual de auditoría', perm: 'auditplan' },
  respuestas: { n: 'Respuestas de la evaluación activa', perm: 'eval.responder' },
  cartera: { n: 'Cartera de crédito (lay out del sistema de riesgos de crédito)', perm: 'cartera' },
};
function mapearFila(f, cols) {
  const o = {};
  for (const c of cols) {
    if (c.soloExport) continue;
    const v = f[norm(c.label)] ?? f[norm(c.key)];
    if (v !== undefined) o[c.key] = v;
  }
  return o;
}
function aplicarImportacion(e, filas) {
  const r = { altas: 0, cambios: 0, errores: [] };
  const up = (lista, clave, obj, prefijo) => {
    const ex = lista.find((x) => x[clave] === obj[clave]);
    if (ex) { Object.assign(ex, obj); r.cambios++; return ex; }
    obj.id = uid(prefijo); lista.push(obj); r.altas++; return obj;
  };
  if (e === 'cartera') {
    const { cortes, errores } = agregarCartera(filas, 'importación');
    for (const c of cortes) { DB.cartera.cortes = DB.cartera.cortes.filter((x) => x.periodo !== c.periodo); DB.cartera.cortes.push(c); r.altas++; }
    r.errores = errores.map((n) => `Renglón ${n}: periodo o saldos inválidos`);
    return r;
  }
  filas.forEach((f, i) => {
    const lin = i + 2;
    try {
      if (e === 'hallazgos') {
        const o = mapearFila(f, COLS.hallazgos);
        if (!o.folio || !o.titulo) throw new Error('folio y titulo son obligatorios');
        if (o.qid && !PREG[o.qid]) throw new Error('punto_interes inexistente: ' + o.qid);
        if (o.severidad && !SEVERIDAD.includes(o.severidad)) o.severidad = 'Media';
        if (o.estatus && !ESTATUS_H.includes(o.estatus)) o.estatus = 'Abierto';
        const h = up(DB.hallazgos, 'folio', o, 'h');
        h.estatus = h.estatus || 'Abierto'; h.seguimiento = h.seguimiento || []; h.origen = h.origen || 'Auditoría externa';
      } else if (e === 'riesgos') {
        const o = mapearFila(f, COLS.riesgos);
        if (!o.clave || !o.descripcion) throw new Error('clave y descripcion son obligatorias');
        for (const k of ['prob', 'imp', 'probR', 'impR']) { if (o[k] !== undefined) { o[k] = num(o[k]); if (o[k] != null && (o[k] < 1 || o[k] > 5)) throw new Error(k + ' fuera de la escala 1-5'); } }
        if (o.qids !== undefined) o.qids = String(o.qids).split(/[|,;\s]+/).filter((q) => PREG[q]);
        up(DB.riesgos, 'clave', o, 'r');
      } else if (e === 'kris') {
        const o = mapearFila(f, COLS.kris);
        const k = DB.kris.find((x) => norm(x.nombre) === norm(o.kri) || x.id === o.kri);
        if (!k) throw new Error('KRI no registrado: ' + o.kri);
        if (!/^\d{4}-\d{2}$/.test(o.periodo || '') || num(o.valor) == null) throw new Error('periodo (AAAA-MM) o valor inválido');
        registrarValorKRI(k, o.periodo, num(o.valor), SES.usuario + ' (importación)');
        r.cambios++;
      } else if (e === 'mesa') {
        const o = mapearFila(f, COLS.mesa());
        if (!o.folio) throw new Error('folio obligatorio');
        o.monto = num(o.monto);
        o.items = {};
        for (const c of DB.mesa.checklist) {
          const v = String(o['it_' + c.id] || f[norm(c.id)] || 'C').toUpperCase();
          o.items[c.id] = ['C', 'NC', 'NA'].includes(v) ? v : 'C';
          delete o['it_' + c.id];
        }
        const rv = up(DB.mesa.revisiones, 'folio', o, 'm');
        rv.resultado = estadoRevision(rv);
      } else if (e === 'auditorias') {
        const o = mapearFila(f, COLS.auditorias);
        if (!o.proceso) throw new Error('proceso obligatorio');
        const ex = DB.auditorias.find((a) => norm(a.proceso) === norm(o.proceso) && (a.periodo || '') === (o.periodo || ''));
        if (ex) { Object.assign(ex, o); r.cambios++; } else { o.id = uid('a'); o.estatus = o.estatus || 'Programada'; o.riesgo = o.riesgo || 'Medio'; DB.auditorias.push(o); r.altas++; }
      } else if (e === 'respuestas') {
        const ev = evalActiva();
        if (!ev || evalBloqueada(ev)) throw new Error('No hay evaluación activa editable');
        const o = mapearFila(f, COLS.respuestas);
        if (!PREG[o.id]) throw new Error('punto_interes inexistente: ' + o.id);
        const rr = ev.resp[o.id] || (ev.resp[o.id] = {});
        const attrs = ATR_KEYS.map((k) => o[k]);
        if (attrs.some((x) => x !== undefined && x !== '')) {
          rr.a = attrs.map((x) => (/^(1|si|sí|x|true)$/i.test(String(x ?? '').trim()) ? 1 : 0));
        }
        for (const k of ['area', 'cargo', 'ubic', 'matriz', 'prio', 'coment', 'defi', 'plan', 'resp', 'fi', 'ff', 'presup', 'entreg']) if (o[k] !== undefined && o[k] !== '') rr[k] = o[k];
        if (o.avance !== undefined && o.avance !== '') rr.avance = clamp(num(o.avance) || 0, 0, 100);
        const evs = ['ev_ab', 'ev_c', 'ev_d', 'ev_e', 'ev_f', 'ev_g', 'ev_h'].map((k) => o[k]);
        if (evs.some((x) => x)) rr.ev = evs.map((x, i2) => x || (rr.ev || [])[i2] || '');
        marcarCambio(rr);
        r.cambios++;
      }
    } catch (err) { r.errores.push(`Renglón ${lin}: ${err.message}`); }
  });
  return r;
}
function aplicarPaquete(pq) {
  if (!pq || pq.formato !== 'seci.intercambio') throw new Error('El archivo no es un paquete de intercambio SECI (formato «seci.intercambio»).');
  const c = pq.contenido || {};
  const res = [];
  for (const [e, filas] of Object.entries(c)) {
    if (!IMPORTA[e]) { res.push(`${e}: entidad no reconocida, se omitió`); continue; }
    if (!can(IMPORTA[e].perm)) { res.push(`${IMPORTA[e].n}: su perfil no puede importar esta entidad, se omitió`); continue; }
    if (!Array.isArray(filas)) continue;
    // Los paquetes usan las mismas etiquetas que los CSV; se normalizan las llaves.
    const norm2 = filas.map((f) => Object.fromEntries(Object.entries(f).map(([k, v]) => [norm(k), Array.isArray(v) ? v.join('|') : v == null ? '' : String(v)])));
    const r = aplicarImportacion(e, norm2);
    res.push(`${IMPORTA[e].n}: ${r.altas} altas, ${r.cambios} actualizaciones${r.errores.length ? ', ' + r.errores.length + ' errores (' + r.errores.slice(0, 3).join('; ') + ')' : ''}`);
  }
  bitacora('Importación de paquete', (pq.origen && pq.origen.sistema || 'origen desconocido') + ': ' + res.join(' | '));
  guardar();
  return res;
}
function armarPaquete(area) {
  const ev = evalActiva();
  const ent = {
    auditoria: ['hallazgos', 'auditorias', 'respuestas', 'planes'],
    credito: ['mesa', 'kris', 'hallazgos'],
    riesgos: ['riesgos', 'kris', 'respuestas'],
    todo: ['hallazgos', 'auditorias', 'respuestas', 'planes', 'mesa', 'riesgos', 'kris'],
  }[area];
  const contenido = {};
  for (const e of ent) {
    const [filas, cols] = datosEntidad(e);
    contenido[e] = filas.map((f) => Object.fromEntries(cols.map((c) => [c.label, typeof c.get === 'function' ? c.get(f) : f[c.key]])));
  }
  const st = ev ? stats(ev) : null;
  return {
    formato: 'seci.intercambio', version: 1, generado: ahora(), area,
    origen: { sistema: 'SECI COSO ERM', version: APP_VERSION, banco: B.version, institucion: DB.config.institucion, usuario: SES.usuario },
    resumen: st ? { evaluacion: ev.nombre, ejercicio: ev.ejercicio, estado: ev.estado, madurez: st.global, nivel: madurez(st.global), componentes: st.comps.map((c) => ({ codigo: c.code, componente: c.name, puntaje: c.score, nivel: madurez(c.score), presente: c.pctPresente, funcionando: c.pctFuncionando })), cartera: DB.cartera.cortes.map((x) => ({ periodo: x.periodo, total: x.total, vencido: x.vencido, imor: x.total ? x.vencido / x.total : null })) } : null,
    contenido,
  };
}

/* Reportes --------------------------------------------------------------- */
const REPORTES = [['ejecutivo', 'Informe ejecutivo del SCI'], ['cedula', 'Cédula de evaluación detallada'], ['planes', 'Deficiencias y planes de solución'], ['hallazgos', 'Hallazgos de auditoría'], ['riesgos', 'Perfil de riesgos y KRI'], ['credito', 'Contraloría de crédito y mesa de control']];
VISTAS.reportes = (args) => {
  const tipo = REPORTES.some((r) => r[0] === args[0]) ? args[0] : 'ejecutivo';
  const ev = evalActiva();
  const enc = `<div class="print-only" style="margin-bottom:1rem"><b>${esc(DB.config.institucion)}</b> · SECI COSO ERM · ${esc(REPORTES.find((r) => r[0] === tipo)[1])}<br><small>Generado el ${fmtFechaHora(ahora())} por ${esc(SES.nombre)} (${esc(ROLES[SES.rol].n)})</small></div>`;
  let cuerpo = '';
  if (tipo === 'ejecutivo') cuerpo = ev ? repEjecutivo(ev) : sinEval();
  if (tipo === 'cedula') cuerpo = ev ? repCedula(ev) : sinEval();
  if (tipo === 'planes') cuerpo = ev ? VISTAS.planes().replace(/<div class="page-head">[\s\S]*?<\/div><\/div>/, '') : sinEval();
  if (tipo === 'hallazgos') cuerpo = repHallazgos();
  if (tipo === 'riesgos') cuerpo = VISTAS.riesgos([]).replace(/<div class="page-head">[\s\S]*?<\/div><\/div>/, '').replace(/<div class="tabs">[\s\S]*?<\/div>/, '') + `<h2 style="margin-top:1rem">Indicadores clave de riesgo</h2>` + vistaKRI() + vistaMapa().replace(/<div class="row" style="margin-bottom:1rem">[\s\S]*?<\/div><\/div>/, '');
  if (tipo === 'credito') cuerpo = vistaIndicadoresMesa() + '<h2 style="margin-top:1rem">Cartera</h2>' + vistaCartera();
  return `<div class="page-head no-print"><div><h1>Reportes</h1><p>Seleccione el reporte; use «Imprimir / PDF» para generar el documento.</p></div>
    <div class="row"><select data-chg="rep-tipo" style="max-width:320px">${REPORTES.map(([k, t]) => `<option value="${k}" ${k === tipo ? 'selected' : ''}>${t}</option>`).join('')}</select>
    <button class="btn primary" data-act="imprimir">${ico('imprimir')} Imprimir / PDF</button></div></div>${enc}${cuerpo}`;
};
CHG['rep-tipo'] = (t) => ir('reportes/' + t.value);
ACT.imprimir = () => { bitacora('Impresión de reporte', ruta().args[0] || 'ejecutivo'); guardar(); window.print(); };
function repEjecutivo(ev) {
  const st = stats(ev);
  const d = ev.datos;
  const prev = DB.evals.filter((e) => e.id !== ev.id && (e.ejercicio || '') < (ev.ejercicio || '')).sort((a, b) => (a.ejercicio || '').localeCompare(b.ejercicio || '')).pop();
  const sp = prev ? stats(prev) : null;
  const altos = PREGUNTAS.filter((q) => riesgoQ(ev.resp[q.id] && ev.resp[q.id].a) === 'Alto');
  const abiertos = DB.hallazgos.filter((h) => !['Solventado', 'Cerrado'].includes(h.estatus));
  return `<div class="card"><h1>Resumen ejecutivo — ${esc(ev.nombre)}</h1>
    <dl class="kv"><dt>Empresa</dt><dd>${esc(d.empresa)}</dd><dt>Al cierre del</dt><dd>${esc(ev.ejercicio)}</dd><dt>Director o Gerente General</dt><dd>${esc(d.director)}</dd>
    <dt>Procesos seleccionados</dt><dd>${esc(d.procesos).replace(/\n/g, '<br>')}</dd><dt>Elaborado por</dt><dd>${esc(d.contralorNombre)} — ${esc(d.contralorCargo)}</dd>
    <dt>Periodo de evaluación</dt><dd>${fmtFecha(d.fechaInicio)} a ${fmtFecha(d.fechaFin)}</dd><dt>Estado</dt><dd>${esc(ev.estado)}</dd></dl></div>
  <div class="grid g4" style="margin-top:1rem">${tile('Madurez del SCI', st.global == null ? '—' : fmtN(st.global), badgeMadurez(st.global))}${tile('Avance', fmtPct(st.contestadas / st.total, 0), `${st.pendientes} por contestar`)}${tile('Puntos con riesgo alto', st.riesgo.Alto)}${tile('Hallazgos abiertos', abiertos.length)}</div>
  <div class="card" style="margin-top:1rem"><h2>Nivel de madurez y cumplimiento por componente</h2>
    <div class="grid g2"><div class="tbl-wrap"><table class="tbl"><tr><th>Componente</th><th class="r">Puntaje</th><th>Madurez</th><th class="r">Presente</th><th class="r">Funcionando</th>${sp ? `<th class="r">${esc(prev.ejercicio)}</th><th>Situación</th>` : ''}</tr>
      ${st.comps.map((c, i) => { const v = sp && sp.comps[i].score != null && c.score != null ? c.score - sp.comps[i].score : null;
        return `<tr><td>${esc(c.name)}</td><td class="r num">${c.score == null ? '—' : fmtN(c.score)}</td><td>${badgeMadurez(c.score)}</td><td class="r num">${fmtPct(c.pctPresente, 0)}</td><td class="r num">${fmtPct(c.pctFuncionando, 0)}</td>${sp ? `<td class="r num">${sp.comps[i].score == null ? '—' : fmtN(sp.comps[i].score)}</td><td>${v == null ? '—' : v > 0.005 ? 'Mejoró' : v < -0.005 ? 'Empeoró' : 'Sin cambio'}</td>` : ''}</tr>`; }).join('')}
      <tr class="grp"><td>SCI (ponderado)</td><td class="r num">${st.global == null ? '—' : fmtN(st.global)}</td><td>${badgeMadurez(st.global)}</td><td></td><td></td>${sp ? `<td class="r num">${sp.global == null ? '—' : fmtN(sp.global)}</td><td></td>` : ''}</tr></table></div>
    <div>${barras(st.comps.map((c) => ({ etiqueta: c.name, valor: c.score })))}</div></div>
    <p style="margin-top:.75rem">¿Están todos los componentes operando juntos y de manera integrada? <b>${st.integrado ? 'Sí' : 'No'}</b></p></div>
  <div class="card"><h2>Riesgo de los puntos de interés</h2>${apilada([{ n: 'Riesgo bajo', v: st.riesgo.Bajo, color: 'var(--good)' }, { n: 'Riesgo moderado', v: st.riesgo.Moderado, color: 'var(--warn)' }, { n: 'Riesgo alto', v: st.riesgo.Alto, color: 'var(--crit)' }])}
    ${altos.length ? `<h3 style="margin-top:1rem">Puntos de interés con riesgo alto (${altos.length})</h3><div class="tbl-wrap"><table class="tbl"><tr><th>Punto</th><th>Descripción</th><th class="c">Nivel</th><th>Plan</th></tr>${altos.slice(0, 25).map((q) => { const r = ev.resp[q.id]; return `<tr><td>${q.id}</td><td>${esc(trunc(q.t, 150))}</td><td class="c">${nivel(r.a)}</td><td>${esc(planEstado(r) || 'Sin plan')}</td></tr>`; }).join('')}</table></div>${altos.length > 25 ? `<p class="muted">… y ${altos.length - 25} más (ver cédula detallada).</p>` : ''}` : ''}</div>
  <div class="grid g2">
    <div class="card"><h2>Líneas de control</h2><dl class="kv">
      <dt>Planes de solución</dt><dd>${st.planes.total} (${st.planes.Vencido} vencidos, ${st.planes.Concluido} concluidos)</dd>
      <dt>Hallazgos abiertos</dt><dd>${abiertos.length} (${abiertos.filter((h) => h.severidad === 'Alta').length} de severidad alta, ${abiertos.filter(hallazgoVencido).length} vencidos)</dd>
      <dt>Riesgos residuales alto/crítico</dt><dd>${DB.riesgos.filter((r) => sev(r.probR || r.prob, r.impR || r.imp) >= 10).length} de ${DB.riesgos.length}</dd>
      <dt>KRI fuera de apetito</dt><dd>${DB.kris.filter((k) => { const v = ultimoValor(k); return v && estadoKRI(k, v.valor).c !== 'b-good'; }).map((k) => esc(k.nombre)).join(', ') || 'Ninguno'}</dd>
      <dt>Mesa de control</dt><dd>${DB.mesa.revisiones.length} expedientes; ${DB.mesa.revisiones.filter((r) => estadoRevision(r) !== 'Liberado').length} con excepción</dd>
    </dl></div>
    <div class="card"><h2>Conclusiones</h2><p>${esc(d.conclusiones || 'Sin conclusiones capturadas.').replace(/\n/g, '<br>')}</p>${d.explicacion ? `<h3>Componentes que empeoraron</h3><p>${esc(d.explicacion).replace(/\n/g, '<br>')}</p>` : ''}</div>
  </div>
  <div class="card"><div class="grid g3" style="text-align:center;padding-top:2.5rem">
    <div style="border-top:1px solid var(--line-strong);padding-top:.4rem">${esc(d.contralorNombre || 'Contralor Interno')}<br><small>Elaboró</small></div>
    <div style="border-top:1px solid var(--line-strong);padding-top:.4rem">${esc(d.presidenteCA || 'Presidente del Comité de Auditoría')}<br><small>Revisó</small></div>
    <div style="border-top:1px solid var(--line-strong);padding-top:.4rem">${esc(d.revisadoPor || 'Consejo de Administración')}<br><small>Conoció</small></div>
  </div></div>`;
}
function repCedula(ev) {
  return B.components.map((c) => `<div class="card"><h2>${esc(c.name)}</h2>${c.principles.map((p) => `<h3 style="margin-top:.75rem">Principio ${p.n}: ${esc(p.t)}</h3>
    <div class="tbl-wrap"><table class="tbl"><tr><th>Punto</th><th>Pregunta</th>${ATR_KEYS.map((k) => `<th class="c">${k}</th>`).join('')}<th class="c">Nivel</th><th>Riesgo</th><th>Evidencia / ubicación</th><th>Validación</th></tr>
    ${p.q.map((q) => { const r = ev.resp[q.id] || {}; return `<tr><td>${q.id}</td><td>${esc(q.t)}</td>${ATR_KEYS.map((k, i) => `<td class="c num">${r.a ? r.a[i] : ''}</td>`).join('')}<td class="c"><b>${nivel(r.a) ?? '—'}</b></td><td>${esc(riesgoQ(r.a) || '')}</td><td>${esc(trunc((r.ev || []).filter(Boolean).join(' · '), 160))}${r.ubic ? `<br><small>${esc(r.ubic)}</small>` : ''}</td><td>${esc((r.val && r.val.estado) || '')}</td></tr>`; }).join('')}
    </table></div>`).join('')}</div>`).join('');
}
function repHallazgos() {
  if (!DB.hallazgos.length) return '<div class="card empty">Sin hallazgos registrados.</div>';
  return DB.hallazgos.map((h) => `<div class="card"><div class="card-head"><h3>${esc(h.folio)} — ${esc(h.titulo)}</h3><div class="row"><span class="badge ${clsSev(h.severidad)}">${esc(h.severidad)}</span><span class="badge ${clsEstH(h)}">${esc(hallazgoVencido(h) ? 'Vencido' : h.estatus)}</span></div></div>
    <dl class="kv"><dt>Origen</dt><dd>${esc(h.origen)}</dd><dt>Condición</dt><dd>${esc(h.condicion)}</dd><dt>Criterio</dt><dd>${esc(h.criterio)}</dd><dt>Causa</dt><dd>${esc(h.causa)}</dd><dt>Efecto</dt><dd>${esc(h.efecto)}</dd>
    <dt>Recomendación</dt><dd>${esc(h.recomendacion)}</dd><dt>Punto COSO / riesgo</dt><dd>${esc(h.qid || '—')} / ${esc(h.riesgo || '—')}</dd><dt>Responsable</dt><dd>${esc(h.responsable)} (${esc(h.area)})</dd><dt>Fecha compromiso</dt><dd>${fmtFecha(h.fechaCompromiso)}</dd></dl></div>`).join('');
}

/* Integraciones ---------------------------------------------------------- */
VISTAS.integraciones = (args) => {
  const tab = args[0] || '';
  const t = tabsDe('integraciones', tab, [['', 'Exportar'], ['importar', 'Importar'], ['conectores', 'Conectores REST'], ['formato', 'Formato de intercambio']]);
  const head = cabecera('Integraciones', 'Intercambio de información con herramientas de auditoría interna, contraloría de crédito / mesa de control y gestión de riesgos, mediante archivos CSV, paquetes JSON o servicios REST.');
  if (tab === 'importar') return head + t + vistaImportar();
  if (tab === 'conectores') return head + t + vistaConectores();
  if (tab === 'formato') return head + t + vistaFormato();
  const bloque = (titulo, desc, area, ents) => `<div class="card"><h3>${titulo}</h3><p class="muted">${desc}</p>
    <div class="row"><button class="btn primary" data-act="exp-paquete" data-a="${area}">${ico('descarga')} Paquete JSON</button>${ents.map(([e, n]) => `<button class="btn" data-act="exp-csv" data-e="${e}">${ico('descarga')} ${n} (CSV)</button>`).join('')}</div></div>`;
  return `${head}${t}
  ${bloque('Auditoría interna', 'Para software de papeles de trabajo y gestión de auditoría (TeamMate+, AuditBoard, ACL/Galvanize, IDEA, hojas de cálculo). Incluye la cédula de evaluación con validaciones, hallazgos y plan anual.', 'auditoria', [['respuestas', 'Cédula de evaluación'], ['hallazgos', 'Hallazgos'], ['auditorias', 'Plan anual'], ['planes', 'Planes de solución']])}
  ${bloque('Contraloría de crédito y mesa de control', 'Para el sistema núcleo (core) de crédito, la mesa de control y los tableros de contraloría.', 'credito', [['mesa', 'Revisiones de expedientes'], ['kris', 'Valores de KRI']])}
  ${bloque('Gestión de riesgos', 'Para el Sistema de Administración de Riesgos de Crédito y otras herramientas GRC: matriz de riesgos con los puntos de interés COSO que soportan cada control.', 'riesgos', [['riesgos', 'Matriz de riesgos'], ['kris', 'Valores de KRI']])}
  ${bloque('Paquete completo', 'Todas las entidades en un solo archivo JSON (no incluye usuarios ni bitácora; para eso use un respaldo).', 'todo', [['bitacora', 'Bitácora']])}`;
};
ACT['exp-paquete'] = (t) => {
  const pq = armarPaquete(t.dataset.a);
  descargar(`SECI_intercambio_${t.dataset.a}_${sello()}.json`, JSON.stringify(pq, null, 1));
  bitacora('Exportación de paquete', t.dataset.a);
  guardar();
};
function vistaImportar() {
  const disponibles = Object.entries(IMPORTA).filter(([, v]) => can(v.perm));
  return `<div class="grid g2">
    <div class="card"><h3>Importar CSV</h3>
      ${disponibles.length ? `<p class="muted">Use las plantillas para conocer las columnas. Se aceptan separadores coma, punto y coma o tabulador, en UTF-8. Los registros existentes se actualizan por su llave (folio, clave o punto de interés).</p>
      <form data-submit="importar-csv">
        ${campo('entidad', 'Información a importar', disponibles[0][0], { opciones: disponibles.map(([k, v]) => [k, v.n]) })}
        <div class="field"><label class="f">Archivo CSV</label><input type="file" name="archivo" accept=".csv,.txt,text/csv"></div>
        <div class="row"><button class="btn primary" type="submit">${ico('sube')} Importar</button><button class="btn" type="button" data-act="plantilla-sel">Descargar plantilla</button></div>
      </form>` : '<p class="muted">Su perfil no tiene permisos de importación.</p>'}
    </div>
    <div class="card"><h3>Importar paquete JSON</h3>
      <p class="muted">Paquete «seci.intercambio» generado por este sistema o por otra herramienta que siga el formato. Solo se aplican las entidades que su perfil puede modificar.</p>
      <input type="file" accept=".json,application/json" data-chg="importar-json">
    </div>
  </div>
  <div class="card"><h3>Sistema de Administración de Riesgos de Crédito</h3>
    <p>La cartera se importa con el mismo lay out CSV de carga del sistema de riesgos de crédito de este repositorio (<code>docs/layout_carga.md</code>). Con ella se calculan IMOR, concentración, antigüedad de mora y distribución por producto y sucursal, y se actualizan los KRI automáticos.</p>
    <div class="row"><a class="btn" href="#/credito/cartera">Ir a contraloría de cartera</a><button class="btn" data-act="plantilla-csv" data-e="cartera">Plantilla del lay out</button></div></div>`;
}
ACT['plantilla-sel'] = () => { const e = $('[name=entidad]').value; ACT['plantilla-csv']({ dataset: { e } }); };
ACT['importar-csv'] = async (f) => {
  const d = leerForm(f);
  const file = d.archivo && d.archivo[0];
  if (!file) return toast('Seleccione un archivo.', true);
  if (!can(IMPORTA[d.entidad].perm)) return toast('Sin permiso para importar esta información.', true);
  const { filas } = deCSV(await leerArchivo(file));
  if (!filas.length) return toast('El archivo no contiene renglones.', true);
  const r = aplicarImportacion(d.entidad, filas);
  bitacora('Importación CSV', `${IMPORTA[d.entidad].n} desde ${file.name}: ${r.altas} altas, ${r.cambios} cambios, ${r.errores.length} errores`);
  guardar();
  await modal({ titulo: 'Resultado de la importación', cuerpo: `<p><b>${r.altas}</b> altas · <b>${r.cambios}</b> actualizaciones · <b>${r.errores.length}</b> errores</p>${r.errores.length ? `<pre>${esc(r.errores.slice(0, 200).join('\n'))}</pre>` : ''}`, chico: true });
  cerrarModal(); render();
};
CHG['importar-json'] = async (t) => {
  const f = t.files[0];
  if (!f) return;
  const res = aplicarPaquete(JSON.parse(await leerArchivo(f)));
  await modal({ titulo: 'Paquete importado', cuerpo: `<ul>${res.map((x) => `<li>${esc(x)}</li>`).join('')}</ul>`, chico: true });
  cerrarModal(); render();
};
function vistaConectores() {
  const L = DB.integraciones.endpoints;
  const areas = { auditoria: 'Auditoría interna', credito: 'Contraloría de crédito / mesa de control', riesgos: 'Gestión de riesgos', todo: 'Todas' };
  return `<div class="callout info" style="margin-bottom:1rem">Los conectores envían (POST) o reciben (GET) paquetes «seci.intercambio» a un servicio REST de la institución. El servicio debe permitir CORS para el origen de este archivo y usar HTTPS. El token se guarda en este navegador: use credenciales de alcance limitado.</div>
  <div class="card"><div class="card-head"><h3>Conectores configurados</h3>${can('integra.config') ? `<button class="btn primary" data-act="con-editar">${ico('mas')} Nuevo conector</button>` : ''}</div>
  <div class="tbl-wrap"><table class="tbl"><tr><th>Nombre</th><th>Área</th><th>URL</th><th>Último envío / recepción</th><th></th></tr>
    ${L.length ? L.map((c) => `<tr><td><b>${esc(c.nombre)}</b></td><td>${esc(areas[c.area])}</td><td><code>${esc(c.url)}</code></td><td>${c.ultimo ? `${fmtFechaHora(c.ultimo.fecha)} · ${esc(c.ultimo.tipo)} · <span class="badge ${c.ultimo.ok ? 'b-good' : 'b-crit'}">${esc(c.ultimo.msg)}</span>` : '<span class="muted">—</span>'}</td>
      <td><div class="row">${puedeUsarConector(c) ? `<button class="btn sm" data-act="con-enviar" data-id="${c.id}">Enviar</button><button class="btn sm" data-act="con-recibir" data-id="${c.id}">Recibir</button>` : ''}${can('integra.config') ? `<button class="btn sm" data-act="con-editar" data-id="${c.id}">Editar</button>` : ''}</div></td></tr>`).join('') : '<tr><td colspan="5" class="empty">Sin conectores. Sistemas puede configurarlos.</td></tr>'}
  </table></div></div>`;
}
function puedeUsarConector(c) {
  if (can('integra.config')) return true;
  return { auditoria: ['auditor', 'contralor'], credito: ['contralor', 'riesgos'], riesgos: ['riesgos'], todo: [] }[c.area].includes(SES.rol);
}
ACT['con-editar'] = async (t) => {
  const id = t.dataset.id;
  const c = id ? DB.integraciones.endpoints.find((x) => x.id === id) : { area: 'auditoria' };
  const res = await formModal({ titulo: id ? 'Editar conector' : 'Nuevo conector', chico: true,
    cuerpo: `${campo('nombre', 'Nombre', c.nombre, { req: true, ph: 'p. ej. Herramienta de auditoría' })}
      ${campo('area', 'Área', c.area, { opciones: [['auditoria', 'Auditoría interna'], ['credito', 'Contraloría de crédito / mesa de control'], ['riesgos', 'Gestión de riesgos'], ['todo', 'Todas']] })}
      ${campo('url', 'URL del servicio', c.url, { tipo: 'url', req: true, ph: 'https://servidor/api/seci' })}
      ${campo('token', 'Token (Authorization: Bearer)', c.token, { tipo: 'password', ayuda: 'Opcional.' })}`,
    botones: [...(id ? [{ id: 'borrar', t: 'Eliminar', danger: true }] : []), { id: 'cancel', t: 'Cancelar' }, { id: 'ok', t: 'Guardar', primary: true }] },
  (d, b) => (b === 'borrar' ? null : !d.nombre.trim() ? 'Indique el nombre.' : !/^https?:\/\//i.test(d.url) ? 'La URL debe iniciar con https://' : null));
  if (!res) return;
  if (res.boton === 'borrar') DB.integraciones.endpoints = DB.integraciones.endpoints.filter((x) => x.id !== id);
  else { Object.assign(c, res.datos); if (!id) { c.id = uid('c'); DB.integraciones.endpoints.push(c); } }
  bitacora('Conector REST', (res.boton === 'borrar' ? 'Baja: ' : 'Configuración: ') + c.nombre + ' ' + c.url);
  guardar(); render();
};
async function llamarConector(c, metodo, cuerpo) {
  const headers = { Accept: 'application/json' };
  if (cuerpo) headers['Content-Type'] = 'application/json';
  if (c.token) headers.Authorization = 'Bearer ' + c.token;
  const resp = await fetch(c.url, { method: metodo, headers, body: cuerpo ? JSON.stringify(cuerpo) : undefined });
  if (!resp.ok) throw new Error('HTTP ' + resp.status);
  return metodo === 'GET' ? resp.json() : resp.text();
}
ACT['con-enviar'] = async (t) => {
  const c = DB.integraciones.endpoints.find((x) => x.id === t.dataset.id);
  try {
    await llamarConector(c, 'POST', armarPaquete(c.area));
    c.ultimo = { fecha: ahora(), tipo: 'envío', ok: true, msg: 'Correcto' };
    toast('Paquete enviado a ' + c.nombre);
  } catch (e) {
    c.ultimo = { fecha: ahora(), tipo: 'envío', ok: false, msg: e.message === 'Failed to fetch' ? 'Sin conexión o CORS' : e.message };
    toast('No fue posible enviar: ' + c.ultimo.msg, true);
  }
  bitacora('Envío por conector', `${c.nombre}: ${c.ultimo.msg}`);
  guardar(); render();
};
ACT['con-recibir'] = async (t) => {
  const c = DB.integraciones.endpoints.find((x) => x.id === t.dataset.id);
  try {
    const res = aplicarPaquete(await llamarConector(c, 'GET'));
    c.ultimo = { fecha: ahora(), tipo: 'recepción', ok: true, msg: 'Correcto' };
    guardar();
    await modal({ titulo: 'Información recibida', cuerpo: `<ul>${res.map((x) => `<li>${esc(x)}</li>`).join('')}</ul>`, chico: true });
    cerrarModal();
  } catch (e) {
    c.ultimo = { fecha: ahora(), tipo: 'recepción', ok: false, msg: e.message === 'Failed to fetch' ? 'Sin conexión o CORS' : e.message };
    toast('No fue posible recibir: ' + c.ultimo.msg, true);
  }
  bitacora('Recepción por conector', `${c.nombre}: ${c.ultimo.msg}`);
  guardar(); render();
};
function vistaFormato() {
  const ejemplo = { formato: 'seci.intercambio', version: 1, generado: '2026-10-05T12:00:00Z', area: 'auditoria', origen: { sistema: 'Herramienta externa', institucion: '…' }, contenido: { hallazgos: [{ folio: 'H-2026-001', titulo: '…', origen: 'Auditoría interna', severidad: 'Alta', punto_interes: '3.13.13', estatus: 'Abierto' }], kris: [{ kri: 'Índice de morosidad (IMOR)', periodo: '2026-09', valor: 4.8 }] } };
  const tabla = (e) => { const cols = (typeof COLS[e] === 'function' ? COLS[e]() : COLS[e]); return `<details class="box"><summary>${esc(IMPORTA[e] ? IMPORTA[e].n : e)} <small class="muted">(${e})</small></summary><p><code>${cols.map((c) => esc(c.label) + (c.soloExport ? '*' : '')).join(', ')}</code></p>${IMPORTA[e] ? `<button class="btn sm" data-act="plantilla-csv" data-e="${e}">Plantilla CSV</button>` : ''}</details>`; };
  return `<div class="card"><h3>Paquete «seci.intercambio» (JSON)</h3>
    <p>Las llaves de cada entidad dentro de <code>contenido</code> son las mismas columnas de los CSV. Para importar, las llaves se comparan sin acentos ni mayúsculas.</p><pre>${esc(JSON.stringify(ejemplo, null, 2))}</pre></div>
  <div class="card"><h3>Columnas por entidad</h3><p class="muted">* Solo exportación (se calculan; se ignoran al importar).</p>
    ${['respuestas', 'hallazgos', 'auditorias', 'riesgos', 'kris', 'mesa', 'planes', 'bitacora'].map(tabla).join('')}
    <details class="box"><summary>Cartera de crédito <small class="muted">(cartera)</small></summary><p>Lay out del Sistema de Administración de Riesgos de Crédito: <code>periodo, folio, socio, producto, sucursal, moneda, actividad, localidad, garantia, monto_original, saldo_vigente, saldo_vencido, dias_mora, plazo_meses, tasa_anual, fecha_otorgamiento, fecha_vencimiento</code>. Obligatorias para este sistema: periodo, folio, saldo_vigente y saldo_vencido.</p></details>
  </div>
  <div class="card"><h3>Valores aceptados</h3><dl class="kv">
    <dt>Atributos a–h</dt><dd>1/0, SI/NO, X o vacío</dd><dt>Severidad</dt><dd>${SEVERIDAD.join(', ')}</dd><dt>Estatus de hallazgo</dt><dd>${ESTATUS_H.join(', ')}</dd>
    <dt>Probabilidad / impacto</dt><dd>1 a 5</dd><dt>Mesa de control (por requisito)</dt><dd>C (cumple), NC (no cumple), NA (no aplica)</dd><dt>Fechas</dt><dd>AAAA-MM-DD; periodos AAAA-MM</dd></dl></div>`;
}

/* Catálogos -------------------------------------------------------------- */
VISTAS.catalogos = (args) => {
  const tab = args[0] || 'criterios';
  const t = tabsDe('catalogos', tab, [['criterios', 'Criterios de evaluación'], ['madurez', 'Niveles de madurez'], ['normativa', 'Normativa'], ['glosario', 'Glosario'], ['responsables', 'Responsables'], ['cambios', 'Actualizaciones 2026']]);
  const head = cabecera('Catálogos y normativa');
  if (tab === 'criterios') return head + t + `<div class="card"><h3>Nivel de cumplimiento</h3><div class="tbl-wrap"><table class="tbl"><tr><th>Valor</th><th>Criterio</th>${ATR.map((a) => `<th class="c">${a.k}<br><small>${esc(a.n)}</small></th>`).join('')}</tr>
    ${B.niveles.map((n) => `<tr><td><b>Nivel ${n.nivel}</b></td><td>${esc(n.t)}</td>${ATR.map((a, i) => `<td class="c">${i < n.requiere ? '1' : '0'}</td>`).join('')}</tr>`).join('')}</table></div>
    <p class="muted" style="margin-top:.5rem">Presente: a+b+c+d ≥ 3. Funcionando: e+f+g+h ≥ 3. Riesgo del punto de interés: suma de atributos &gt; 6 bajo, 5–6 moderado, ≤ 4 alto.</p></div>
    <div class="card"><h3>Característica de la evidencia</h3><div class="tbl-wrap"><table class="tbl"><tr><th>Ciclo</th><th>Parámetro</th><th>Evidencia esperada</th></tr>${ATR.map((a) => `<tr><td>${esc(a.ciclo)}</td><td>${a.k}. ${esc(a.n)}</td><td>${esc(a.ev)}</td></tr>`).join('')}</table></div></div>`;
  if (tab === 'madurez') return head + t + `<div class="card"><div class="tbl-wrap"><table class="tbl"><tr><th>Nivel</th><th>Intervalo</th><th>Estado del sistema de control interno</th></tr>
    ${B.madurez.map((m) => `<tr><td><b>${esc(m.n)}</b></td><td class="num">${esc(m.rango)}</td><td>${esc(m.t)}</td></tr>`).join('')}</table></div><p class="muted" style="margin-top:.5rem">Fuente: modelo de madurez de la herramienta SECI; ISO 31000.</p></div>`;
  if (tab === 'glosario') return head + t + `<div class="card"><dl class="kv" style="grid-template-columns:minmax(160px,max-content) 1fr;gap:.6rem 1.25rem">${B.glosario.map(([k, v]) => `<dt><b>${esc(k)}</b></dt><dd>${esc(v)}</dd>`).join('')}</dl></div>`;
  if (tab === 'cambios') return head + t + `<div class="card"><p>Banco de preguntas <b>${esc(B.version)}</b>: ${PREGUNTAS.length} puntos de interés en ${PRINCIPIOS.length} principios. Cambios respecto al Excel «Eval COSO ERM 2026»:</p><ol>${B.cambios.map((c) => `<li style="margin-bottom:.4rem">${esc(c)}</li>`).join('')}</ol>
    <p class="muted">Los puntos nuevos y actualizados se identifican en el cuestionario con las etiquetas «Nuevo 2026» y «Actualizado 2026».</p></div>`;
  if (tab === 'responsables') {
    const ed = can('catalogos');
    return head + t + `<form data-submit="resp-guardar"><div class="grid g2"><div class="card"><h3>Gerencias, áreas y comités</h3>${campo('areas', 'Uno por renglón', DB.responsables.areas.join('\n'), { tipo: 'textarea', dis: !ed, attrs: 'rows="14"' })}</div>
      <div class="card"><h3>Cargos</h3>${campo('cargos', 'Uno por renglón', DB.responsables.cargos.join('\n'), { tipo: 'textarea', dis: !ed, attrs: 'rows="14"' })}</div></div>
      ${ed ? '<div class="row end" style="margin-top:1rem"><button class="btn primary" type="submit">Guardar</button></div>' : ''}</form>`;
  }
  const ed = can('catalogos');
  return head + t + `<div class="card"><div class="card-head"><p class="muted" style="margin:0">Normativa interna y externa aplicable. Verifique la vigencia de cada ordenamiento con el área jurídica.</p>${ed ? `<button class="btn primary" data-act="norma-editar">${ico('mas')} Agregar</button>` : ''}</div>
    <div class="tbl-wrap"><table class="tbl"><tr><th>#</th><th>Normativa</th><th>Tipo</th><th>Ámbito</th><th>Documento / versión</th><th>Última actualización</th><th>Comentarios</th></tr>
    ${DB.normativa.map((n, i) => `<tr><td>${i + 1}</td><td>${ed ? `<a href="#" data-act="norma-editar" data-id="${n.id}">${esc(n.nombre)}</a>` : esc(n.nombre)}</td><td><span class="badge ${n.tipo === 'Externa' ? 'b-info' : 'b-neutral'} plain">${esc(n.tipo)}</span></td><td>${esc(n.ambito)}</td><td>${esc(n.documento)}</td><td>${fmtFecha(n.actualizacion)}</td><td>${esc(n.comentarios)}</td></tr>`).join('')}
    </table></div></div>`;
};
ACT['resp-guardar'] = (f) => {
  const d = leerForm(f);
  const lim = (s) => [...new Set(s.split('\n').map((x) => x.trim()).filter(Boolean))];
  DB.responsables = { areas: lim(d.areas), cargos: lim(d.cargos) };
  bitacora('Catálogo de responsables', `${DB.responsables.areas.length} áreas, ${DB.responsables.cargos.length} cargos`);
  guardar(); toast('Catálogo guardado.');
};
ACT['norma-editar'] = async (t) => {
  const id = t.dataset.id;
  const n = id ? DB.normativa.find((x) => x.id === id) : { tipo: 'Interna', ambito: 'Manual' };
  const res = await formModal({ titulo: id ? 'Editar normativa' : 'Agregar normativa', chico: true,
    cuerpo: `${campo('nombre', 'Nombre', n.nombre, { req: true })}<div class="grid g2">${campo('tipo', 'Tipo', n.tipo, { opciones: ['Externa', 'Interna'] })}${campo('ambito', 'Ámbito', n.ambito)}</div>
      ${campo('documento', 'Documento / versión / código', n.documento)}${campo('actualizacion', 'Fecha de última actualización', n.actualizacion, { tipo: 'date' })}${campo('comentarios', 'Comentarios y observaciones', n.comentarios, { tipo: 'textarea' })}`,
    botones: [...(id ? [{ id: 'borrar', t: 'Eliminar', danger: true }] : []), { id: 'cancel', t: 'Cancelar' }, { id: 'ok', t: 'Guardar', primary: true }] },
  (d, b) => (b !== 'borrar' && !d.nombre.trim() ? 'Indique el nombre.' : null));
  if (!res) return;
  if (res.boton === 'borrar') DB.normativa = DB.normativa.filter((x) => x.id !== id);
  else { Object.assign(n, res.datos); if (!id) { n.id = uid('n'); DB.normativa.push(n); } }
  bitacora('Catálogo de normativa', (res.boton === 'borrar' ? 'Baja: ' : 'Edición: ') + n.nombre);
  guardar(); render();
};

/* Mi cuenta -------------------------------------------------------------- */
VISTAS.perfil = () => {
  const u = usuarioActual();
  const mios = DB.bitacora.filter((b) => b.usuario === u.usuario).slice(-15).reverse();
  return `${cabecera('Mi cuenta')}
  <div class="grid g2"><div class="card"><h3>${esc(u.nombre)}</h3><dl class="kv"><dt>Usuario</dt><dd>${esc(u.usuario)}</dd><dt>Perfil</dt><dd>${esc(ROLES[u.rol].n)}</dd><dt>Funciones</dt><dd>${esc(ROLES[u.rol].d)}</dd><dt>Último acceso</dt><dd>${fmtFechaHora(u.ultimoAcceso)}</dd></dl></div>
  <div class="card"><h3>Cambiar contraseña</h3><form data-submit="cambio-pass">
    ${campo('actual', 'Contraseña actual', '', { tipo: 'password', req: true, attrs: 'autocomplete="current-password"' })}
    ${campo('nueva', 'Nueva contraseña', '', { tipo: 'password', req: true, attrs: 'autocomplete="new-password"' })}
    ${campo('nueva2', 'Confirmar', '', { tipo: 'password', req: true, attrs: 'autocomplete="new-password"' })}
    <div class="row end"><button class="btn primary" type="submit">Actualizar</button></div></form></div></div>
  <div class="card"><h3>Mi actividad reciente</h3><div class="tbl-wrap"><table class="tbl"><tr><th>Fecha</th><th>Acción</th><th>Detalle</th></tr>${mios.map((b) => `<tr><td>${fmtFechaHora(b.ts)}</td><td>${esc(b.accion)}</td><td>${esc(b.detalle)}</td></tr>`).join('')}</table></div></div>`;
};

/* Administración --------------------------------------------------------- */
let BIT_F = '';
VISTAS.admin = (args) => {
  if (!can('admin')) return cabecera('Administración') + '<div class="callout crit">Acceso exclusivo del perfil Sistemas.</div>';
  const tab = args[0] || '';
  const t = tabsDe('admin', tab, [['', 'Usuarios'], ['respaldos', 'Respaldos'], ['bitacora', 'Bitácora'], ['config', 'Configuración']]);
  if (tab === 'respaldos') return cabecera('Administración') + t + vistaRespaldos();
  if (tab === 'bitacora') return cabecera('Administración') + t + vistaBitacora();
  if (tab === 'config') return cabecera('Administración') + t + vistaConfig();
  return `${cabecera('Administración', '', `<button class="btn primary" data-act="usr-editar">${ico('mas')} Nuevo usuario</button>`)}${t}
  <div class="card"><div class="tbl-wrap"><table class="tbl"><tr><th>Usuario</th><th>Nombre</th><th>Perfil</th><th>Estado</th><th>Último acceso</th><th>Acciones</th></tr>
    ${DB.users.map((u) => `<tr><td><code>${esc(u.usuario)}</code></td><td>${esc(u.nombre)}</td><td>${esc(ROLES[u.rol].n)}</td>
      <td>${!u.activo ? '<span class="badge b-neutral">Inactivo</span>' : u.bloqueoHasta && new Date(u.bloqueoHasta) > new Date() ? '<span class="badge b-crit">Bloqueado</span>' : u.mustChange ? '<span class="badge b-warn">Contraseña temporal</span>' : '<span class="badge b-good">Activo</span>'}</td>
      <td>${fmtFechaHora(u.ultimoAcceso) || '<span class="muted">Nunca</span>'}</td>
      <td><div class="row"><button class="btn sm" data-act="usr-editar" data-id="${u.id}">Editar</button><button class="btn sm" data-act="usr-reset" data-id="${u.id}">Restablecer contraseña</button></div></td></tr>`).join('')}
  </table></div></div>
  <div class="card"><h3>Perfiles</h3><dl class="kv">${Object.values(ROLES).map((r) => `<dt><b>${esc(r.n)}</b></dt><dd>${esc(r.d)}</dd>`).join('')}</dl></div>`;
};
const sistemasActivos = (excepto) => DB.users.filter((u) => u.rol === 'sistemas' && u.activo && u.id !== excepto).length;
ACT['usr-editar'] = async (t) => {
  const id = t.dataset.id;
  const u = id ? DB.users.find((x) => x.id === id) : { rol: 'auditor', activo: true };
  const res = await formModal({ titulo: id ? 'Editar usuario' : 'Nuevo usuario', chico: true,
    cuerpo: `${campo('usuario', 'Usuario', u.usuario, { req: true, dis: !!id })}${campo('nombre', 'Nombre completo', u.nombre, { req: true })}
      ${campo('rol', 'Perfil', u.rol, { opciones: Object.entries(ROLES).map(([k, r]) => [k, r.n]) })}
      ${id ? campo('activo', 'Usuario activo', u.activo, { tipo: 'checkbox' }) : campo('pass', 'Contraseña temporal', passwordTemporal(), { ayuda: 'Se pedirá cambiarla en el primer acceso.' })}`,
    botones: [...(id && id !== SES.uid ? [{ id: 'borrar', t: 'Eliminar', danger: true }] : []), { id: 'cancel', t: 'Cancelar' }, { id: 'ok', t: 'Guardar', primary: true }] },
  (d, b) => {
    if (b === 'borrar') return sistemasActivos(id) < 1 ? 'Debe existir al menos un usuario de Sistemas activo.' : null;
    if (!id && !/^[a-z0-9._-]{3,30}$/i.test(d.usuario)) return 'Usuario: 3 a 30 caracteres (letras, números, punto, guion).';
    if (!id && DB.users.some((x) => x.usuario.toLowerCase() === d.usuario.toLowerCase())) return 'El usuario ya existe.';
    if (!d.nombre.trim()) return 'Indique el nombre.';
    if (!id) return politicaPassword(d.pass);
    if (u.rol === 'sistemas' && (d.rol !== 'sistemas' || !d.activo) && sistemasActivos(id) < 1) return 'Debe existir al menos un usuario de Sistemas activo.';
    return null;
  });
  if (!res) return;
  const d = res.datos;
  if (res.boton === 'borrar') {
    DB.users = DB.users.filter((x) => x.id !== id);
    bitacora('Baja de usuario', u.usuario);
  } else if (id) {
    const cambios = [u.nombre !== d.nombre ? 'nombre' : '', u.rol !== d.rol ? `perfil ${u.rol}→${d.rol}` : '', u.activo !== d.activo ? (d.activo ? 'activado' : 'desactivado') : ''].filter(Boolean).join(', ');
    Object.assign(u, { nombre: d.nombre.trim(), rol: d.rol, activo: d.activo });
    bitacora('Edición de usuario', `${u.usuario}: ${cambios || 'sin cambios'}`);
  } else {
    DB.users.push({ id: uid('u'), usuario: d.usuario.trim(), nombre: d.nombre.trim(), rol: d.rol, activo: true, mustChange: true, creado: ahora(), ...(await nuevaCredencial(d.pass)) });
    bitacora('Alta de usuario', `${d.usuario} (${ROLES[d.rol].n})`);
    await modal({ titulo: 'Usuario creado', chico: true, cuerpo: `<p>Entregue la contraseña temporal a <b>${esc(d.nombre)}</b>:</p><p><code style="font-size:1.1rem">${esc(d.pass)}</code></p>` });
    cerrarModal();
  }
  guardar(); render();
};
ACT['usr-reset'] = async (t) => {
  const u = DB.users.find((x) => x.id === t.dataset.id);
  if (!await confirmar('Restablecer contraseña', `Se generará una contraseña temporal para <b>${esc(u.usuario)}</b> y se desbloqueará la cuenta.`, { ok: 'Restablecer' })) return;
  const pass = passwordTemporal();
  Object.assign(u, await nuevaCredencial(pass), { mustChange: true, intentos: 0, bloqueoHasta: null });
  bitacora('Restablecimiento de contraseña', u.usuario);
  guardar(); render();
  await modal({ titulo: 'Contraseña temporal', chico: true, cuerpo: `<p>Nueva contraseña temporal para <b>${esc(u.usuario)}</b>:</p><p><code style="font-size:1.1rem">${esc(pass)}</code></p>` });
  cerrarModal();
};

function vistaRespaldos() {
  let tam = 0;
  try { tam = (localStorage.getItem(DB_KEY) || '').length * 2; } catch { /* sin acceso */ }
  return `<div class="grid g2">
    <div class="card"><h3>Descargar respaldo</h3>
      <p>Último respaldo: <b>${DB.meta.ultimoRespaldo ? fmtFechaHora(DB.meta.ultimoRespaldo) : 'nunca'}</b>. Tamaño de la información: <b>${fmtN(tam / 1024, 0)} KB</b>.</p>
      <p class="muted">El respaldo incluye evaluaciones, hallazgos, riesgos, KRI, mesa de control, cartera agregada, catálogos, usuarios (contraseñas cifradas con hash) y bitácora. Guárdelo en un medio seguro de la institución.</p>
      <div class="row"><button class="btn primary" data-act="resp-descargar">${ico('descarga')} Respaldo JSON</button>${hayCrypto() ? `<button class="btn" data-act="resp-cifrado">${ico('descarga')} Respaldo cifrado</button>` : ''}</div>
    </div>
    <div class="card"><h3>Restaurar respaldo</h3>
      <p class="muted">Reemplaza <b>toda</b> la información actual por la del respaldo. Antes de restaurar se descarga automáticamente un respaldo de la información actual.</p>
      <input type="file" accept=".json,application/json" data-chg="resp-restaurar">
    </div>
    <div class="card"><h3>Autoguardado en archivo local</h3>
      ${FS.estado === 'nosoportado' ? '<p class="muted">Este navegador no permite escribir archivos locales automáticamente (disponible en Chrome y Edge). Use los respaldos manuales.</p>'
        : `<p>Estado: <span class="badge ${FS.estado === 'activo' ? 'b-good' : FS.estado === 'permiso' ? 'b-warn' : 'b-neutral'}">${{ activo: 'Activo', permiso: 'Requiere permiso', no: 'No configurado' }[FS.estado]}</span> ${FS.handle ? `<code>${esc(FS.handle.name)}</code>` : ''}</p>
        <p class="muted">Cada cambio se escribe también en un archivo .json de su equipo o carpeta de red, que funciona como respaldo continuo.</p>
        <div class="row"><button class="btn" data-act="fs-vincular">Elegir archivo</button>${FS.estado === 'permiso' ? '<button class="btn" data-act="fs-reactivar">Conceder permiso</button>' : ''}${FS.handle ? '<button class="btn" data-act="fs-desvincular">Desvincular</button>' : ''}</div>`}
    </div>
    <div class="card"><h3>Eliminar información de este navegador</h3>
      <p class="muted">Borra todos los datos de este equipo (no afecta respaldos descargados). Útil al retirar un equipo.</p>
      <button class="btn danger" data-act="resp-borrar">Eliminar todo</button>
    </div>
  </div>`;
}
function respaldoDescargado(nombre) {
  DB.meta.ultimoRespaldo = ahora();
  bitacora('Respaldo', nombre);
  guardar();
}
ACT['resp-descargar'] = () => {
  const nombre = `SECI_respaldo_${sello()}.json`;
  respaldoDescargado(nombre);
  descargar(nombre, JSON.stringify(paqueteRespaldo()));
  render();
};
ACT['resp-cifrado'] = async () => {
  const res = await formModal({ titulo: 'Respaldo cifrado', chico: true,
    cuerpo: `<p class="muted">El archivo se cifra con AES-256-GCM. Sin la frase no es posible recuperarlo.</p>${campo('frase', 'Frase de cifrado', '', { tipo: 'password', req: true, ayuda: 'Mínimo 12 caracteres.' })}${campo('frase2', 'Confirmar frase', '', { tipo: 'password', req: true })}`,
    botones: [{ id: 'cancel', t: 'Cancelar' }, { id: 'ok', t: 'Descargar', primary: true }] },
  (d) => (d.frase.length < 12 ? 'La frase debe tener al menos 12 caracteres.' : d.frase !== d.frase2 ? 'Las frases no coinciden.' : null));
  if (!res) return;
  const nombre = `SECI_respaldo_cifrado_${sello()}.json`;
  respaldoDescargado(nombre);
  const cif = await cifrar(JSON.stringify(paqueteRespaldo()), res.datos.frase);
  descargar(nombre, JSON.stringify({ formato: 'seci-respaldo-cifrado', version: 1, generado: ahora(), institucion: DB.config.institucion, alg: 'AES-256-GCM/PBKDF2-SHA256-200000', ...cif }));
  render();
};
async function abrirRespaldo(file) {
  let obj = JSON.parse(await leerArchivo(file));
  if (obj.formato === 'seci-respaldo-cifrado') {
    if (!hayCrypto()) throw new Error('Este navegador no puede descifrar el respaldo.');
    const res = await formModal({ titulo: 'Respaldo cifrado', chico: true, cuerpo: campo('frase', 'Frase de cifrado', '', { tipo: 'password', req: true }), botones: [{ id: 'cancel', t: 'Cancelar' }, { id: 'ok', t: 'Descifrar', primary: true }] },
      async (d) => { try { obj._plano = await descifrar(obj, d.frase); return null; } catch { return 'Frase incorrecta o archivo dañado.'; } });
    if (!res) return null;
    obj = JSON.parse(obj._plano);
  }
  if (obj.formato !== 'seci-respaldo' || !obj.datos) throw new Error('El archivo no es un respaldo del SECI.');
  const integro = sha256(JSON.stringify(obj.datos)) === obj.integridad;
  const ok = await confirmar('Restaurar respaldo', `Respaldo de <b>${esc(obj.institucion || '—')}</b> generado el ${fmtFechaHora(obj.generado)} por ${esc(obj.por || '—')}.<br>
    ${obj.datos.users ? obj.datos.users.length : 0} usuarios · ${obj.datos.evals ? obj.datos.evals.length : 0} evaluaciones.<br><br>
    Integridad: ${integro ? '<span class="badge b-good">Verificada</span>' : '<span class="badge b-crit">El contenido no coincide con su huella; pudo haber sido modificado</span>'}<br><br>Se reemplazará toda la información actual.`, { ok: 'Restaurar', peligro: !integro });
  if (!ok) return null;
  const db = migrar(obj.datos);
  if (!db.users.some((u) => u.rol === 'sistemas' && u.activo)) throw new Error('El respaldo no contiene un usuario de Sistemas activo.');
  return db;
}
CHG['resp-restaurar'] = async (t) => {
  const f = t.files[0];
  if (!f) return;
  const nuevo = await abrirRespaldo(f);
  t.value = '';
  if (!nuevo) return;
  descargar(`SECI_respaldo_previo_${sello()}.json`, JSON.stringify(paqueteRespaldo()));
  const quien = SES.usuario;
  DB = nuevo;
  bitacora('Restauración de respaldo', `${f.name} (por ${quien})`);
  guardar();
  logout('Cierre de sesión por restauración');
  toast('Respaldo restaurado. Inicie sesión nuevamente.');
};
ACT['fs-vincular'] = async () => { await fsVincular(); render(); toast('Autoguardado activado.'); };
ACT['fs-desvincular'] = async () => { await fsDesvincular(); bitacora('Autoguardado', 'Desvinculado'); guardar(); render(); };
ACT['resp-borrar'] = async () => {
  const res = await formModal({ titulo: 'Eliminar toda la información', chico: true,
    cuerpo: `<div class="callout crit" style="margin-bottom:.75rem">Esta acción elimina definitivamente la información de este navegador.</div>${campo('conf', 'Escriba BORRAR para confirmar', '', { req: true })}`,
    botones: [{ id: 'cancel', t: 'Cancelar' }, { id: 'ok', t: 'Eliminar', danger: true }] }, (d) => (d.conf !== 'BORRAR' ? 'Escriba BORRAR en mayúsculas.' : null));
  if (!res) return;
  localStorage.removeItem(DB_KEY);
  sessionStorage.removeItem(SES_KEY);
  await fsDesvincular().catch(() => {});
  DB = null; SES = null;
  location.hash = '';
  render();
};
function vistaBitacora() {
  const L = DB.bitacora.filter((b) => !BIT_F || norm(b.usuario + ' ' + b.accion + ' ' + b.detalle).includes(norm(BIT_F))).slice(-500).reverse();
  return `<div class="card"><div class="row" style="margin-bottom:.75rem"><input type="search" placeholder="Filtrar por usuario, acción o detalle…" value="${esc(BIT_F)}" data-chg="bit-f" style="max-width:320px">
    <span class="muted">${DB.bitacora.length} eventos (se conservan los últimos ${MAX_BITACORA})</span><span class="spacer"></span>
    <button class="btn" data-act="bit-verificar">Verificar integridad</button><button class="btn" data-act="exp-csv" data-e="bitacora">${ico('descarga')} CSV</button></div>
  <div class="tbl-wrap" style="max-height:65vh"><table class="tbl"><tr><th>Fecha y hora</th><th>Usuario</th><th>Perfil</th><th>Acción</th><th>Detalle</th><th>Huella</th></tr>
    ${L.map((b) => `<tr><td class="num">${fmtFechaHora(b.ts)}</td><td>${esc(b.usuario)}</td><td>${esc(ROLES[b.rol] ? ROLES[b.rol].n : b.rol)}</td><td>${esc(b.accion)}</td><td>${esc(b.detalle)}</td><td><code title="${esc(b.h)}">${esc(b.h.slice(0, 10))}</code></td></tr>`).join('')}
  </table></div><p class="muted" style="font-size:.8rem;margin-top:.5rem">Cada evento incluye la huella SHA-256 del evento anterior; cualquier modificación o eliminación intermedia rompe la cadena y se detecta con «Verificar integridad».</p></div>`;
}
CHG['bit-f'] = (t) => { BIT_F = t.value; render(); };
ACT['bit-verificar'] = async () => {
  const r = verificarBitacora();
  bitacora('Verificación de bitácora', r.ok ? `Íntegra (${r.n} eventos)` : `Ruptura en el evento ${r.i + 1}`);
  guardar();
  await modal({ titulo: 'Integridad de la bitácora', chico: true, cuerpo: r.ok ? `<div class="callout info">La cadena de ${r.n} eventos es íntegra.</div>` : `<div class="callout crit">La cadena se rompe en el evento ${r.i + 1} (${esc(fmtFechaHora(r.e.ts))}, ${esc(r.e.usuario)}: ${esc(r.e.accion)}). La bitácora fue modificada fuera del sistema.</div>` });
  cerrarModal(); render();
};
function vistaConfig() {
  const c = DB.config;
  return `<form data-submit="config"><div class="grid g2">
    <div class="card"><h3>Institución</h3>${campo('institucion', 'Razón social', c.institucion, { req: true })}${campo('nombreComercial', 'Nombre comercial', c.nombreComercial)}${campo('tipo', 'Tipo de entidad', c.tipo, { opciones: ['SOCAP', 'SOFIPO', 'SOFOM', 'Caja de ahorro', 'Otra'] })}</div>
    <div class="card"><h3>Seguridad y respaldos</h3>${campo('sesionMin', 'Cierre de sesión por inactividad (minutos)', c.sesionMin, { tipo: 'number', attrs: 'min="5" max="240"' })}${campo('diasRespaldo', 'Recordar respaldo cada (días)', c.diasRespaldo, { tipo: 'number', attrs: 'min="1" max="90"' })}</div>
    <div class="card"><h3>Ponderación de componentes</h3><p class="muted">Deben sumar 100 %. Valores tomados de la hoja «Resultados» del Excel.</p>
      ${B.components.map((k) => campo('peso_' + k.code, k.name + ' (%)', Math.round((c.pesos[k.code] ?? k.peso) * 100), { tipo: 'number', attrs: 'min="0" max="100" step="1"' })).join('')}</div>
    <div class="card"><h3>Integración de componentes</h3>${campo('umbralIntegracion', 'Porcentaje mínimo de puntos presentes y funcionando por componente (%)', Math.round(c.umbralIntegracion * 100), { tipo: 'number', attrs: 'min="0" max="100"' })}</div>
  </div><div class="row end" style="margin-top:1rem"><button class="btn primary" type="submit">Guardar configuración</button></div></form>`;
}
ACT.config = (f) => {
  const d = leerForm(f);
  const pesos = Object.fromEntries(B.components.map((k) => [k.code, (num(d['peso_' + k.code]) || 0) / 100]));
  if (Math.abs(sum(Object.values(pesos)) - 1) > 0.001) return toast('Las ponderaciones deben sumar 100 %.', true);
  if (!d.institucion.trim()) return toast('Indique la institución.', true);
  Object.assign(DB.config, { institucion: d.institucion.trim(), nombreComercial: d.nombreComercial, tipo: d.tipo, sesionMin: clamp(num(d.sesionMin) || 20, 5, 240), diasRespaldo: clamp(num(d.diasRespaldo) || 7, 1, 90), umbralIntegracion: clamp((num(d.umbralIntegracion) || 70) / 100, 0, 1), pesos });
  bitacora('Configuración', 'Actualizó parámetros del sistema');
  guardar(); render(); toast('Configuración guardada.');
};

/* Inicio ----------------------------------------------------------------- */
window.addEventListener('storage', (e) => {
  if (e.key !== DB_KEY) return;
  DB = cargarDB();
  if (!DB) { SES = null; render(); return; }
  if (SES && !DB.users.some((u) => u.id === SES.uid && u.activo)) SES = null;
  render();
  toast('La información se actualizó desde otra pestaña.');
});
(async function iniciar() {
  aplicarTema();
  if (!B) { $('#app').innerHTML = '<div class="login-wrap"><div class="callout crit">El banco de preguntas no está incluido. Genere el sistema con <code>python coso_erm/herramientas/construir.py</code>.</div></div>'; return; }
  try { localStorage.setItem('seci.prueba', '1'); localStorage.removeItem('seci.prueba'); } catch {
    $('#app').innerHTML = '<div class="login-wrap"><div class="callout crit">El navegador bloquea el almacenamiento local (modo privado o política del equipo). El sistema no puede guardar información.</div></div>';
    return;
  }
  DB = cargarDB();
  if (DB) restaurarSesion();
  await fsIniciar();
  render();
})();
