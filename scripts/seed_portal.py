"""Datos de demostración para el portal de suscripciones.

Crea organizaciones de ejemplo con usuarios, sesiones y suscripciones
en distintos planes para facilitar pruebas.

Uso:  python -m scripts.seed_portal
"""
from portal.database import Base, SessionLocal, engine
from portal.models import Organizacion, Suscripcion, UsuarioPortal
from portal.auth import hash_password

Base.metadata.create_all(bind=engine)
db = SessionLocal()

ORGS = [
    {
        "nombre": "Caja Popular del Sur",
        "rfc": "CPS010101AAA",
        "tipo": "socap",
        "telefono": "(961) 612-3456",
        "email": "rh@cajapopularsur.mx",
        "num_empleados": "51-200",
        "usuario_nombre": "Ana García López",
        "usuario_email": "ana.garcia@cajapopularsur.mx",
        "plan": "profesional",
        "estado": "activa",
    },
    {
        "nombre": "Financiera del Bajío Popular",
        "rfc": "FBP020202BBB",
        "tipo": "sofipo",
        "telefono": "(477) 713-9876",
        "email": "talento@finbajio.com",
        "num_empleados": "201-500",
        "usuario_nombre": "Carlos Mendoza Ruiz",
        "usuario_email": "carlos.mendoza@finbajio.com",
        "plan": "empresarial",
        "estado": "activa",
    },
    {
        "nombre": "Crédito Express MX",
        "rfc": "CEM030303CCC",
        "tipo": "sofome",
        "telefono": "(55) 5123-4567",
        "email": "rh@creditoexpress.mx",
        "num_empleados": "11-50",
        "usuario_nombre": "María Fernanda Torres",
        "usuario_email": "mftorres@creditoexpress.mx",
        "plan": "basico",
        "estado": "prueba",
    },
]

for datos in ORGS:
    if db.query(Organizacion).filter(Organizacion.rfc == datos["rfc"]).first():
        print(f"  Ya existe: {datos['nombre']}")
        continue

    org = Organizacion(
        nombre=datos["nombre"],
        rfc=datos["rfc"],
        tipo=datos["tipo"],
        telefono=datos["telefono"],
        email=datos["email"],
        num_empleados=datos["num_empleados"],
    )
    db.add(org)
    db.flush()

    usuario = UsuarioPortal(
        organizacion_id=org.id,
        nombre=datos["usuario_nombre"],
        email=datos["usuario_email"],
        password_hash=hash_password("demo1234"),
        rol="admin",
    )
    db.add(usuario)

    from portal.models import PLANES
    plan_info = PLANES[datos["plan"]]
    suscripcion = Suscripcion(
        organizacion_id=org.id,
        plan=datos["plan"],
        estado=datos["estado"],
        monto_mensual=plan_info["precio_mensual"],
        dias_prueba=14,
    )
    db.add(suscripcion)
    print(f"  + {datos['nombre']} ({datos['tipo'].upper()}) — Plan {plan_info['nombre']}")

db.commit()
db.close()
print("Seed del portal completado.")
