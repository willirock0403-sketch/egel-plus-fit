"""Convierte una página-video (HTML) en MP4 con narración neuronal es_MX.
Uso: python3 render.py <config> [--probe]
"""
import sys, os, re, json, time, subprocess, asyncio, math
import numpy as np, soundfile as sf
from playwright.async_api import async_playwright

FPS = 30
INTRO = 2.8          # segundos de cortina al inicio
LEAD, GAP, TAIL = 0.8, 0.35, 1.3
SR = 24000

CONFIGS = {
  'ingreso': dict(src='/home/claude/ceneval/index.html', out='/home/claude/videos/Registro_EXANI-II_FIT.mp4',
                  hl_scene=1, marks=["En Institución", "Escribe tu matrícula", "Elige correctamente", "en Campus", "Después, acepta"],
                  boxes=[(414,122,394,36),(414,157,394,36),(414,193,394,36),(414,228,394,36),(514,262,192,38)]),
  'egel':    dict(src='/home/claude/egel/index.html', out='/home/claude/videos/EGEL_Plus_FIT_vozA.mp4',
                  hl_scene=9, marks=["En Institución", "Escriba su matrícula", "En Programa o Carrera", "En Campus", "dé clic en Aceptar"],
                  overrides=[(1, 'ul.list li:nth-child(1)', 'Para presentarlo'), (1, 'ul.list li:nth-child(2)', 'sin adeudar'),
                             (1, 'ul.list li:nth-child(3)', 'Si tiene alguna'),
                             (3, '.chk2 li.nota3', 'Al enviar este correo'),
                             (4, 'ul.list li:nth-child(2)', 'Imprima el recibo'), (4, '.tag2', 'Imprima el recibo'),
                             (4, 'ul.list li:nth-child(3)', 'verifique que'),
                             (5, 'figure.docimg', 'Ahí le darán'),
                             (6, '.hl-box', 'en cualquiera'), (6, '.stack > figure.docimg:nth-of-type(2)', 'Ahí le entregarán'),
                             (7, '.hl-box', 'en la esquina'),
                             (9, '.carov', 'En Programa o Carrera'),
                             (10, '.lnk-hl', 'Editar registro'), (10, '.warn', 'es su única'),
                             (11, '.cct', 'Cuando le pidan'),
                             (13, '.warn', 'Después, imprímalo')],
                  boxes=[(512,114,474,40),(512,156,474,40),(512,197,474,40),(512,239,474,40),(642,280,214,42)]),
}

SPEECH = [
  (r'EXANI-II', 'EXANI dos'),
  (r'EGEL Plus', 'Ejel Plus'),
  (r'\bISC\b', 'i, ese, ce'), (r'\bIIS\b', 'i, i, ese'), (r'\bIC\b', 'i, ce'),
  (r'cenevalfit@uat\.edu\.mx', 'ceneval fit, arroba, guat, punto edu, punto eme equis'),
  (r'28MSU0010B', 'dos, ocho, eme, ese, u, cero, cero, uno, cero, be'),
  (r'\bUAT\b', 'Guat'), (r'\bEDC\b', 'e, de, ce'), (r'\bPDF\b', 'pe de efe'),
  (r'\bPNG\b', 'pe ene ge'), (r'\bJPG\b', 'jota pe ge'), (r'CamScanner', 'Cam Scanner'),
]
def speech_text(s):
    for a, b in SPEECH: s = re.sub(a, b, s)
    return s

FONT_DIR = '/home/claude/tts/font/package/files'
def font_css():
    out = []
    for w in (400, 500, 600, 700, 800):
        for st in ('normal', 'italic'):
            out.append(f"@font-face{{font-family:'Montserrat';font-style:{st};font-weight:{w};"
                       f"src:url('file://{FONT_DIR}/montserrat-latin-{w}-{st}.woff2') format('woff2')}}")
    return '\n'.join(out)

RENDER_CSS = """
.sitehead,.hero,.sec,.sitefoot,#bar,.topbar{display:none!important}
main.page{padding:0!important;background:#fff!important}
#player{margin:0!important;max-width:none!important;border-radius:0!important;box-shadow:none!important}
html,body{margin:0!important;overflow:hidden!important;background:#fff!important}
"""

def prepare_html(cfg):
    s = open(cfg['src']).read()
    s = re.sub(r'<link[^>]+fonts\.(googleapis|gstatic)\.com[^>]*>\n?', '', s)
    s = s.replace('</style>', font_css() + RENDER_CSS + '\n</style>', 1)
    s = s.replace('setTimeout(finish, 3000);', '').replace("intro.addEventListener('click', finish);", '')
    p = cfg['out'].replace('.mp4', '.render.html')
    open(p, 'w').write(s)
    return p

# ---------- TTS ----------
OVR = []
_tts = None
def tts(text):
    global _tts
    import sherpa_onnx
    if _tts is None:
        d = '/home/claude/tts/kokoro-multi-lang-v1_0'
        _tts = sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
            kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(model=f'{d}/model.onnx', voices=f'{d}/voices.bin',
                tokens=f'{d}/tokens.txt', data_dir=f'{d}/espeak-ng-data', lang='es-419'),
            num_threads=2, provider='cpu'), max_num_sentences=1))
    a = _tts.generate(text, sid=28, speed=1.0)
    assert a.sample_rate == SR, a.sample_rate
    x = np.array(a.samples, dtype=np.float32)
    # recorta silencios de los extremos
    nz = np.where(np.abs(x) > 0.01)[0]
    if len(nz): x = x[max(0, nz[0]-200): nz[-1]+800]
    return x

async def page_info(html):
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={'width':1920,'height':1080})
        await pg.goto('file://' + html); await pg.wait_for_timeout(500)
        info = await pg.evaluate("""({dur: DUR, cues: CUES.map(c=>c.map(x=>x.s)),
            maxd: scenes.map(function(sc){ var m = 0; sc.querySelectorAll('[style*="--d"]').forEach(function(el){
                var v = parseFloat((el.getAttribute('style').match(/--d:\\s*([\\d.]+)s/)||[0,0])[1]); if (v > m) m = v; }); return m; })})""")
        await b.close()
        return info

def build_audio(cfg, info):
    scenes = []
    for k, cues in enumerate(info['cues']):
        parts, t, tl = [], LEAD, []
        for c in cues:
            x = tts(speech_text(c))
            tl.append((round(t, 3), c, len(x)/SR))
            parts.append((t, x)); t += len(x)/SR + GAP
        end = t - GAP
        dur = max(end + TAIL, info['maxd'][k] + 2.4, 6.0)
        scenes.append(dict(dur=dur, timeline=tl, parts=parts, end=end))
        print(f'escena {k}: voz {end:.1f}s  ult. aparición {info["maxd"][k]}s  dur {info["dur"][k]} -> {dur:.1f}', flush=True)
    # cuadros enteros por escena para no desfasar audio/video
    frames = [int(round(s['dur']*FPS)) for s in scenes]
    start = INTRO
    total = INTRO + sum(frames)/FPS
    track = np.zeros(int(math.ceil(total*SR)) + SR, dtype=np.float32)
    for s, n in zip(scenes, frames):
        for t, x in s['parts']:
            i0 = int(round((start + t)*SR)); track[i0:i0+len(x)] += x
        s['start'] = start; start += n/FPS
    return scenes, frames, track[:int(total*SR)]

def hl_css(cfg, scenes):
    k = cfg['hl_scene']; sc = scenes[k]
    def when(mark):
        for t, c, d in sc['timeline']:
            if mark in c:
                return t + d * c.index(mark)/max(1, len(c))
        raise ValueError(mark)
    ts = [when(m) for m in cfg['marks']]
    start = ts[0] - 0.5; L = sc['dur'] - start
    pct = lambda x: round(max(0, min(100, (x - start)/L*100)), 2)
    (l, t, w, h) = cfg['boxes'][0]
    fr = [f"0%{{opacity:0;top:{t}px;left:{l}px;width:{w}px;height:{h}px}}"]
    for j, (l, t, w, h) in enumerate(cfg['boxes']):
        a = pct(ts[j] - 0.25) if j else 2.5
        b = pct(ts[j+1] - 0.25) - 2 if j < len(cfg['boxes'])-1 else 100
        fr.append(f"{a}%,{b}%{{opacity:1;top:{t}px;left:{l}px;width:{w}px;height:{h}px}}")
    return (".scene.active .hl-move{animation:hlmoveR %.2fs ease-in-out %.2fs both !important}\n@keyframes hlmoveR{%s}"
            % (L, start, ''.join(fr)))

# ---------- render ----------
SET_FRAME = """([k,T]) => {
  if (i !== k) { go(k, true); }
  t = T;
  var line = cueAt(k, T); if (cc.textContent !== line) cc.textContent = line;
  document.getAnimations().forEach(function(a){ try{ a.pause(); a.currentTime = T*1000; }catch(e){} });
}"""

async def open_page(p, html, durs, cues, extra_css):
    b = await p.chromium.launch(args=['--disable-gpu'])
    pg = await b.new_page(viewport={'width':1920,'height':1080})
    await pg.goto('file://' + html)
    await pg.evaluate("document.fonts.ready")
    await pg.wait_for_timeout(400)
    await pg.add_style_tag(content=extra_css)
    await pg.evaluate("""([d,c]) => { pause(); DUR = d; CUES = c;
        TOTAL = DUR.reduce(function(a,b){return a+b;},0);
        fit(); }""", [durs, cues])
    if OVR:
        await pg.evaluate("""(ov) => { var sc = document.querySelectorAll('.scene');
            ov.forEach(function(o){ var el = sc[o[0]].querySelector(o[1]); if (el) el.style.setProperty('--d', o[2] + 's'); }); }""", OVR)
    return b, pg

def ff_writer(path):
    return subprocess.Popen(['ffmpeg','-loglevel','error','-y','-f','image2pipe','-framerate',str(FPS),'-c:v','mjpeg','-i','-',
                             '-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-r',str(FPS),path],
                            stdin=subprocess.PIPE)

async def render_intro(p, html, durs, cues, css, path):
    b, pg = await open_page(p, html, durs, cues, css)
    await pg.evaluate("document.getElementById('intro').classList.add('go')")
    w = ff_writer(path)
    for n in range(int(INTRO*FPS)):
        T = n/FPS
        await pg.evaluate("""(T) => { document.getAnimations().forEach(function(a){
            var el = a.effect && a.effect.target; if (el && el.closest && el.closest('#intro')) { a.pause(); a.currentTime = T*1000; } }); }""", T)
        w.stdin.write(await pg.screenshot(type='jpeg', quality=92, clip={'x':0,'y':0,'width':1920,'height':1080}))
    w.stdin.close(); w.wait(); await b.close()

async def render_scenes(p, html, durs, cues, css, frames, ks, segdir, tag):
    b, pg = await open_page(p, html, durs, cues, css)
    await pg.evaluate("var el=document.getElementById('intro'); if(el) el.style.display='none'; document.body.classList.remove('intro-on');")
    for k in ks:
        w = ff_writer(f'{segdir}/s{k:02d}.mp4'); t0 = time.time()
        for n in range(frames[k]):
            await pg.evaluate(SET_FRAME, [k, n/FPS])
            w.stdin.write(await pg.screenshot(type='jpeg', quality=92, clip={'x':0,'y':0,'width':1920,'height':1080}))
        w.stdin.close(); w.wait()
        print(f'[{tag}] escena {k}: {frames[k]} cuadros en {time.time()-t0:.0f}s', flush=True)
    await b.close()

async def main(name, probe=False):
    cfg = CONFIGS[name]
    os.makedirs('/home/claude/videos', exist_ok=True)
    html = prepare_html(cfg)
    info = await page_info(html)
    scenes, frames, track = build_audio(cfg, info)
    durs = [n/FPS for n in frames]
    cues = [[{'t': t, 's': c} for (t, c, d) in s['timeline']] for s in scenes]
    css = hl_css(cfg, scenes)
    global OVR
    OVR = []
    for k, sel, phrase in cfg.get('overrides', []):
        for t, c, d in scenes[k]['timeline']:
            if phrase.lower() in c.lower():
                OVR.append([k, sel, round(max(0.3, t + d * c.lower().index(phrase.lower()) / max(1, len(c)) - 0.15), 2)]); break
        else:
            raise ValueError(f'frase no encontrada: escena {k}: {phrase}')
    print('ajustes de aparición:', OVR, flush=True)
    base = cfg['out'][:-4]; segdir = base + '_seg'; os.makedirs(segdir, exist_ok=True)
    sf.write(base + '.wav', track, SR)
    json.dump(dict(durs=durs, cues=cues, starts=[s['start'] for s in scenes]), open(base + '.timeline.json', 'w'), ensure_ascii=False, indent=1)
    print('duración total %.1fs' % (INTRO + sum(durs)), flush=True)
    if probe:
        async with async_playwright() as p:
            b, pg = await open_page(p, html, durs, cues, css)
            await pg.evaluate("document.getElementById('intro').style.display='none'")
            t0 = time.time()
            for n in range(30):
                await pg.evaluate(SET_FRAME, [1, n/FPS]); await pg.screenshot(type='jpeg', quality=92, clip={'x':0,'y':0,'width':1920,'height':1080})
            print('30 cuadros en %.1fs' % (time.time()-t0))
            await b.close()
        return
    order = sorted(range(len(frames)), key=lambda k: -frames[k])
    A, B = [], []; sa = sb = 0
    for k in order:
        if sa <= sb: A.append(k); sa += frames[k]
        else: B.append(k); sb += frames[k]
    async with async_playwright() as p:
        await asyncio.gather(render_intro(p, html, durs, cues, css, f'{segdir}/intro.mp4'),
                             render_scenes(p, html, durs, cues, css, frames, sorted(A), segdir, 'A'),
                             render_scenes(p, html, durs, cues, css, frames, sorted(B), segdir, 'B'))
    with open(f'{segdir}/list.txt', 'w') as f:
        f.write(f"file '{segdir}/intro.mp4'\n")
        for k in range(len(frames)): f.write(f"file '{segdir}/s{k:02d}.mp4'\n")
    subprocess.run(['ffmpeg','-loglevel','error','-y','-f','concat','-safe','0','-i',f'{segdir}/list.txt','-c','copy',base + '.video.mp4'], check=True)
    subprocess.run(['ffmpeg','-loglevel','error','-y','-i',base + '.video.mp4','-i',base + '.wav',
                    '-map','0:v','-map','1:a','-c:v','copy','-af','loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000',
                    '-c:a','aac','-b:a','160k','-movflags','+faststart','-shortest', cfg['out']], check=True)
    print('LISTO', cfg['out'], flush=True)

if __name__ == '__main__':
    asyncio.run(main(sys.argv[1], '--probe' in sys.argv))
