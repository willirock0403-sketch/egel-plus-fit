"""Página del EGEL Plus con el video MP4 (voz ElevenLabs) en lugar de la animación HTML."""
import re, json, base64, io, subprocess
from PIL import Image

s = open('/home/claude/egel/index.src.html').read()

def cut(start, end, new):
    global s
    i = s.index(start); j = s.index(end, i)
    s = s[:i] + new + s[j:]

VIDEO = '''<div id="player" class="vplayer">
  <video id="vid" controls controlsList="nodownload noplaybackrate" disablepictureinpicture playsinline preload="metadata" poster="poster.jpg" oncontextmenu="return false;"
         aria-label="Video tutorial: registro al EGEL Plus paso a paso">
    <source src="EGEL_Plus_FIT.mp4" type="video/mp4">
    Su navegador no puede reproducir este video.
  </video>
  <button class="bigplay" id="bigplay" aria-label="Reproducir video"></button>
</div>
<p class="vmeta">Duración 4:13 · Con voz y subtítulos</p>

'''
cut('<div id="player">', '<section class="sec" id="enlaces">', VIDEO)

SCRIPT = '''<script>
var IMG = __IMG__;
document.querySelectorAll('[data-img]').forEach(function(el){
  var k = el.getAttribute('data-img');
  if(IMG[k]) el.src = IMG[k];
});

// botón grande de reproducir
(function(){
  var v = document.getElementById('vid'), b = document.getElementById('bigplay');
  if(!v || !b) return;
  b.addEventListener('click', function(){ v.play(); });
  v.addEventListener('play', function(){ b.hidden = true; });
})();

// cortina de entrada: logos + departamento + contacto
(function(){
  var intro = document.getElementById('intro'), done = false;
  function finish(){
    if(done) return; done = true;
    intro.classList.add('out');
    document.body.classList.remove('intro-on');
    setTimeout(function(){ intro.style.display = 'none'; }, 1000);
  }
  if(!intro) return;
  requestAnimationFrame(function(){ intro.classList.add('go'); });
  setTimeout(finish, 3000);
  intro.addEventListener('click', finish);
})();
</script>
</body>
</html>
'''
i = s.index('<script>\nvar IMG = __IMG__;')
s = s[:i] + SCRIPT

CSS = '''
/* reproductor de video */
.vplayer{margin:26px auto 0;max-width:1280px;border-radius:10px;overflow:hidden;box-shadow:0 18px 50px rgba(0,0,0,.18);background:#000;line-height:0}
.vplayer{position:relative}
.vplayer video{display:block;width:100%;height:auto;aspect-ratio:16/9;background:#000}
.bigplay{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:112px;height:112px;border-radius:50%;border:0;cursor:pointer;
  background:rgba(237,28,36,.96);box-shadow:0 0 0 10px rgba(255,255,255,.55),0 16px 40px rgba(0,0,0,.35);transition:transform .15s ease}
.bigplay::after{content:"";position:absolute;left:43px;top:32px;border-left:38px solid #fff;border-top:24px solid transparent;border-bottom:24px solid transparent}
.bigplay:hover{transform:translate(-50%,-50%) scale(1.06)}
.bigplay:focus-visible{outline:4px solid var(--gris);outline-offset:6px}
.bigplay[hidden]{display:none}
@media(max-width:600px){.bigplay{width:76px;height:76px}.bigplay::after{left:29px;top:21px;border-left-width:26px;border-top-width:17px;border-bottom-width:17px}}
.vmeta{max-width:1280px;margin:14px auto 0;padding:0 24px;font-size:15px;color:var(--gris-med);text-align:center}
.vmeta a{color:var(--rojo);font-weight:700}
'''
s = s.replace('</style>', CSS + '</style>', 1)
s = s.replace('Siga el video paso a paso. Abajo encontrará', 'Reproduzca el video. Abajo encontrará')
a = '  <p class="h2sub">EGEL Plus · Examen General para el Egreso de la Licenciatura</p>\n'
assert s.count(a) == 1; s = s.replace(a, '')
open('/home/claude/egel/index.video.src.html', 'w').write(s)

used = sorted(set(re.findall(r'data-img="(\w+)"', s)))
print('imágenes usadas:', used)
def uri(p, maxw=None, q=86):
    im = Image.open(p); b = io.BytesIO()
    if maxw and im.width > maxw: im = im.resize((maxw, int(im.height*maxw/im.width)), Image.LANCZOS)
    if p.endswith('.png'): im.save(b, 'PNG', optimize=True); m = 'png'
    else: im.convert('RGB').save(b, 'JPEG', quality=q, optimize=True); m = 'jpeg'
    return f'data:image/{m};base64,' + base64.b64encode(b.getvalue()).decode()
I = '/home/claude/egel/img/'
SRC = {'lockup': (I+'lockup.png', 1400), 'mapa': (I+'m_mapa.jpg', 1400), 'ceneval': (I+'logo_ceneval.png', 900),
       'recibo': (I+'doc_recibo.jpg', 900, 82), 'ficha': (I+'doc_ficha.jpg', 900, 82), 'comprobante': (I+'doc_comprobante.jpg', 900, 82)}
IMG = {k: uri(*SRC[k]) for k in used}
REG = 'https://registroenlinea.ceneval.edu.mx/RegistroLinea/indexCerrado.php#institucion'
out = s.replace('__IMG__', json.dumps(IMG)).replace('__REG_URL__', REG)
open('/home/claude/egel/index.video.html', 'w').write(out)
print('KB', round(len(out)/1024))
