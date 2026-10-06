import re, json, base64, io
from PIL import Image

BASE = '/home/claude/ceneval/index.src.html'   # mismo motor y estilo del video de ingreso
s = open(BASE).read()

def R(a, b, count=1):
    global s
    n = s.count(a)
    assert n == count, (n, a[:100])
    s = s.replace(a, b)

def cut(start, end, new, keep_end=True):
    """Reemplaza desde `start` hasta antes de `end`."""
    global s
    i = s.index(start); j = s.index(end, i)
    s = s[:i] + new + (s[j:] if keep_end else s[j+len(end):])

NARR = [
 "Bienvenido a la guía paso a paso para registrarse al EGEL Plus de CENEVAL, el Examen General para el Egreso de la Licenciatura.",
 "El EGEL Plus evalúa de forma integral los conocimientos de su carrera y sus habilidades transversales como egresado. Para presentarlo debe tener acreditado el cien por ciento de sus créditos: sin adeudar materias y sin estar inscrito. Si tiene alguna materia en curso, no tiene derecho a presentar el examen.",
 "Primero, entre al portal de alumnos de la UAT y descargue su Kardex Histórico en formato PDF.",
 "Envíelo al correo cenevalfit@uat.edu.mx, junto con su nombre completo, carrera, matrícula, teléfono, correo, el periodo escolar en el que concluyó sus estudios y una copia en PDF de su identificación oficial, ya sea INE o pasaporte vigente. Al enviar este correo, se le añadirá a una lista para enviarle posteriormente su carta de terminación de estudios. Esta carta se envía por separado y no es necesaria para obtener su pase.",
 "Le enviaremos por correo su recibo de tesorería. Imprima el recibo y verifique que sus datos sean correctos, para estar a tiempo de hacer cualquier modificación.",
 "Con su recibo impreso, acuda a la ventanilla de Cobros del Edificio Administrativo 2, el edificio central de la universidad. Ahí le darán la ficha de pago de su examen. Verifique de nuevo que sus datos sean correctos.",
 "Con su ficha de pago, realice el pago de su examen en cualquiera de los bancos o tiendas que aparecen en ella, como OXXO. Ahí le entregarán un comprobante de pago: consérvelo.",
 "Después, coloque el comprobante de pago en la esquina superior izquierda de su ficha, escanee ambos en un solo archivo PDF y envíelo al correo cenevalfit@uat.edu.mx. No se aceptan imágenes PNG ni JPG. Puede usar una aplicación de escaneo como CamScanner.",
 "Con su comprobante recibido, CENEVAL FIT hará su pre-registro en el sistema y le avisará por correo cuando esté listo.",
 "Cuando reciba ese aviso, entre al registro en línea de CENEVAL. En Institución, elija Universidad Autónoma de Tamaulipas. Escriba su matrícula solo con números. En Programa o Carrera, elija su carrera escrita exactamente como aparece en pantalla: Ingeniero Civil, Ingeniero en Sistemas Computacionales o Ingeniero Industrial y de Sistemas. En Campus, elija Universidad Autónoma de Tamaulipas, Facultad de Ingeniería Tampico. Revise que todo esté correcto y, después, dé clic en Aceptar.",
 "Ya dentro del portal, dé clic en Editar registro y verifique que sus datos sean correctos: es su única oportunidad para hacer cualquier modificación.",
 "Llene correctamente cada apartado y conteste todas las encuestas del portal. Cuando le pidan la clave del centro de trabajo, escriba: 28MSU0010B.",
 "Cuando complete todos los apartados y las encuestas, en la parte inferior de la página podrá generar su Pase de Ingreso al Examen.",
 "Guarde su pase en formato PDF: dé clic en Impresión de este talón de registro, elija Guardar como PDF y guárdelo. Después, imprímalo: su pase impreso es requisito indispensable para presentar el examen.",
 "Una vez que tenga su Pase de Ingreso al Examen, habrá finalizado su registro correctamente.",
 "El día del examen, preséntese en la explanada de la Facultad de Ingeniería a partir de las ocho de la mañana. Llegue diez minutos antes, con su Pase de Ingreso impreso y su credencial de elector o pasaporte vigente, en físico.",
 "Importante: si no llega hasta generar su Pase de Ingreso al Examen, su registro no estará completo. Perderá su pago y, aún más importante, el derecho a presentar su examen.",
 "Si tiene dudas, comuníquese con la Maestra Paulina Fernández Izaguirre, Coordinadora de Exámenes Estandarizados. ¡Mucho éxito en su examen CENEVAL EGEL Plus!"
]

def t_at(txt):
    w = len(txt.split()); p = len(re.findall(r'[.:!?]\s', txt))
    return 0.7 + w/2.45 + p*0.35

DUR = [max(8, round(t_at(n) + 1.3)) for n in NARR]
DUR[0] = max(DUR[0], 11); DUR[-1] = max(DUR[-1], 12)

# ---- cabecera del documento ----
R('<title>Registro en línea al EXANI-II — Facultad de Ingeniería Tampico, UAT</title>',
  '<title>Registro al EGEL Plus — Facultad de Ingeniería Tampico, UAT</title>')
s = re.sub(r'<meta name="description" content="[^"]*">',
  '<meta name="description" content="Video tutorial paso a paso para el registro al EGEL Plus de CENEVAL (egresados). Coordinación de Exámenes Estandarizados, Facultad de Ingeniería Tampico, UAT.">', s, count=1)

# ---- resaltador del Paso 6: tiempos calculados desde la narración ----
n9 = NARR[9]
marks = ["En Institución", "Escriba su matrícula", "En Programa o Carrera", "En Campus", "dé clic en Aceptar"]
ts = [t_at(n9[:n9.index(m)]) for m in marks]
start = ts[0] - 0.5; L = DUR[9] - start
pct = lambda x: round((x - start) / L * 100, 1)
tr = 2.0
boxes = [(512,114,474,40),(512,156,474,40),(512,197,474,40),(512,239,474,40),(642,280,214,42)]
frames = ["  0%{opacity:0;top:114px;left:512px;width:474px;height:40px}"]
for k,(l,t,w,h) in enumerate(boxes):
    a = pct(ts[k]-0.3) if k else 2.5
    b = pct(ts[k+1]-0.3) - tr if k < len(boxes)-1 else 100
    frames.append(f"  {a}%,{round(b,1)}%{{opacity:1;top:{t}px;left:{l}px;width:{w}px;height:{h}px}}")
kf = "@keyframes hlmove{\n" + "\n".join(frames) + "\n}"
s = re.sub(r'\.scene\.active \.hl-move\{animation:hlmove [^}]*\}\n@keyframes hlmove\{.*?\n\}',
           f'.scene.active .hl-move{{animation:hlmove {round(L,1)}s ease-in-out {round(start,1)}s both}}\n' + kf, s, count=1, flags=re.S)
s = s.replace('.hl-move{position:absolute;left:414px;top:122px;width:394px;height:36px;',
              '.hl-move{position:absolute;left:512px;top:114px;width:474px;height:40px;')

# ---- CSS nuevo ----
CSS = open('/home/claude/egel/extra.css').read()
R('/* pilas de capturas */', CSS + '\n/* pilas de capturas */')

# ---- encabezado del video ----
R('<p class="mid">Registro en línea · <b>EXANI-II</b></p>', '<p class="mid">Registro · <b>EGEL Plus</b></p>')

# ---- página: encabezado y hero ----
R('<p class="t">Registro en línea al EXANI-II<span>Coordinación de Exámenes Estandarizados</span></p>',
  '<p class="t">Registro al EGEL Plus<span>Coordinación de Exámenes Estandarizados</span></p>')
R('<p class="k">Video tutorial · Guía paso a paso</p>', '<p class="k">Video tutorial · Egresados</p>')
R('<h1>OBTÉN TU PASE DE EXAMEN</h1>', '<h1>OBTENGA SU PASE DE EXAMEN</h1>')
R('<p>Sigue el video paso a paso. Al final de esta página está el enlace oficial al registro en línea de CENEVAL y el contacto para dudas.</p>',
  '<p class="h2sub">EGEL Plus · Examen General para el Egreso de la Licenciatura</p>\n  <p>Siga el video paso a paso. Abajo encontrará los enlaces, los datos importantes y el contacto para dudas.</p>')

# ---- escenas ----
sc = open('/home/claude/egel/scenes.html').read()
for k, d in enumerate(DUR):
    sc = sc.replace(f'data-dur="@{k}"', f'data-dur="{d}"')
def at(k, phrase):
    n = NARR[k]; return round(t_at(n[:n.index(phrase)]), 1)
for key, k, ph in (('T3', 3, 'Al enviar este correo'), ('T5', 5, 'Ahí le darán'), ('T6a', 6, 'en cualquiera'), ('T6b', 6, 'Ahí le entregarán'), ('T7', 7, 'en la esquina'), ('T9c', 9, 'En Programa o Carrera')):
    sc = sc.replace(f'--d:@{key};', f'--d:{at(k, ph)}s;')
assert '@' not in re.sub(r'[\w.]+@uat\.edu\.mx', '', sc), 'duración sin asignar'
cut('    <!-- 0 · Portada -->', '    <div id="cc"></div>', sc)

# ---- página: secciones y pie ----
pg = open('/home/claude/egel/page.html').read()
cut('<section class="sec" id="registro">', '<script>', pg + '\n')

# ---- narración ----
s = re.sub(r'var NARR = \[\n.*?\n\];', 'var NARR = ' + json.dumps(NARR, ensure_ascii=False, indent=0) + ';', s, count=1, flags=re.S)

# ---- subtítulos: cortar solo en signos seguidos de espacio (no parte el correo) ----
R("  var parts = txt.match(/[^.!?:]+[.!?:]+|[^.!?:]+$/g).map(function(s){return s.trim();}).filter(Boolean);",
  "  var parts = txt.replace(/([.!?:])\\s+/g, '$1\\u0001').split('\\u0001').map(function(s){return s.trim();}).filter(Boolean);")

# ---- pronunciación de la CCT y del correo en la voz (los subtítulos quedan igual) ----
R("    var u = new SpeechSynthesisUtterance(p);",
  "    var u = new SpeechSynthesisUtterance(p.replace(/28MSU0010B/g, '2, 8, M, S, U, 0, 0, 1, 0, B').replace(/cenevalfit@uat\\.edu\\.mx/g, 'ceneval fit, arroba, u a t, punto, e d u, punto, m x'));")

open('/home/claude/egel/index.src.html', 'w').write(s)
print('DUR', DUR, 'total', sum(DUR))

# ---- imágenes incrustadas ----
def uri(p, maxw=None, q=86):
    im = Image.open(p)
    b = io.BytesIO()
    if p.endswith('.png'):
        if maxw and im.width > maxw:
            im = im.resize((maxw, int(im.height*maxw/im.width)), Image.LANCZOS)
        im.save(b, 'PNG', optimize=True); mime = 'png'
    else:
        im = im.convert('RGB')
        if maxw and im.width > maxw:
            im = im.resize((maxw, int(im.height*maxw/im.width)), Image.LANCZOS)
        im.save(b, 'JPEG', quality=q, optimize=True); mime = 'jpeg'
    return f'data:image/{mime};base64,' + base64.b64encode(b.getvalue()).decode()
I = '/home/claude/egel/img/'
IMG = {'uat': uri(I+'logo_uat.png', 700), 'fit': uri(I+'logo_fit.png', 900), 'lockup': uri(I+'lockup.png', 1400),
       'ceneval': uri(I+'logo_ceneval.png', 900),
       'kardex': uri(I+'k_kardex.jpg'), 'mapa': uri(I+'m_mapa.jpg', q=84), 'registro': uri(I+'r_registro.jpg', q=90),
       'datos': uri(I+'d_datos.jpg', 1200), 'menu1': uri(I+'e_menu_incompleto.jpg', 1400), 'seccion': uri(I+'e_seccion1.jpg', 1200),
       'menu2': uri(I+'e_menu_completo.jpg', 1400), 'pase': uri(I+'p_pase_egel.jpg', q=90), 'imprimir': uri(I+'i_imprimir.jpg'),
       'recibo': uri(I+'doc_recibo.jpg', 1200, 84), 'ficha': uri(I+'doc_ficha.jpg', 1400, 84), 'ticket': uri(I+'doc_ticket.jpg', 600, 84), 'comprobante': uri(I+'doc_comprobante.jpg', 1400, 84)}
REG = 'https://registroenlinea.ceneval.edu.mx/RegistroLinea/indexCerrado.php#institucion'
out = s.replace('__IMG__', json.dumps(IMG)).replace('__REG_URL__', REG)
open('/home/claude/egel/index.html', 'w').write(out)
print('MB', round(len(out)/1e6, 2))
