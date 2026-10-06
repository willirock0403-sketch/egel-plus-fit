"""Renderiza un video usando una narración externa (p. ej. ElevenLabs) ya cortada por escena.
Uso: python3 sync_render.py <config> <carpeta_segs> <salida.mp4>
Los subtítulos cambian en las pausas reales de la voz."""
import sys, os, re, json, math, asyncio
import numpy as np, soundfile as sf
sys.path.insert(0, '/home/claude/tts')
import render

name, segdir, out = sys.argv[1], sys.argv[2], sys.argv[3]
cfg = dict(render.CONFIGS[name]); cfg['out'] = out
meta = json.load(open(f'{segdir}/segs.json'))
SR = meta['sr']; render.SR = SR

import unicodedata
_rec = None
def _norm(t):
    t = unicodedata.normalize('NFD', t.lower())
    t = ''.join(ch for ch in t if unicodedata.category(ch) != 'Mn')
    return re.sub(r'[^a-z0-9 ]', ' ', t).split()
def _heard(x):
    global _rec
    if _rec is None:
        from asr import rec as r; _rec = r
    st = _rec.create_stream(); st.accept_waveform(SR, x); _rec.decode_stream(st)
    return _norm(st.result.text)

def boundaries(cues, seg, audio):
    """Inicio (s, relativo al segmento) de cada frase: la pausa tras la cual la voz dice las primeras palabras de esa frase."""
    if len(cues) == 1: return [0.0]
    lens = [len(render.speech_text(c)) for c in cues]
    tot = sum(lens); L = seg['len']; gaps = seg['gaps']
    res = [0.0]; acc = 0
    for j in range(1, len(cues)):
        acc += lens[j-1]; est = L * acc / tot
        want = _norm(cues[j])[:2]
        cand = [g for g in gaps if (g[0]+g[1])/2 > res[-1] + 0.3 and abs((g[0]+g[1])/2 - est) < 4.0]
        ok = []
        for g in cand:
            got = _heard(audio[int(g[1]*SR): int((g[1]+2.2)*SR)])[:2]
            if got[:1] == want[:1] and (len(want) < 2 or len(got) < 2 or got[1][:3] == want[1][:3]): ok.append(g)
        pool = ok or cand
        if pool:
            g = min(pool, key=lambda g: abs((g[0]+g[1])/2 - est))
            res.append(round(max(g[0], g[1] - 0.2), 3))
            if not ok: print(f'  aviso: frase {j} ({want}) sin coincidencia exacta; se usa la pausa más cercana', flush=True)
        else:
            res.append(round(est, 3)); print(f'  aviso: frase {j} sin pausa cercana', flush=True)
    return res

def build_audio(cfg_, info):
    scenes = []
    for k, cues in enumerate(info['cues']):
        seg = meta['segs'][k]
        x, sr = sf.read(f'{segdir}/seg{k:02d}.wav', dtype='float32'); assert sr == SR
        b = boundaries(cues, seg, x)
        ends = b[1:] + [seg['len']]
        tl = [(round(render.LEAD + b[j], 3), c, ends[j] - b[j]) for j, c in enumerate(cues)]
        dur = max(render.LEAD + seg['len'] + render.TAIL, info['maxd'][k] + 2.4, 6.0)
        scenes.append(dict(dur=dur, timeline=tl, parts=[(render.LEAD, x)], end=render.LEAD + seg['len']))
        print(f'escena {k}: voz {seg["len"]:.1f}s  frases {[t for t,_,_ in tl]}  dur {dur:.1f}', flush=True)
    frames = [int(round(s['dur']*render.FPS)) for s in scenes]
    start = render.INTRO; total = render.INTRO + sum(frames)/render.FPS
    track = np.zeros(int(math.ceil(total*SR)) + SR, dtype=np.float32)
    for s, n in zip(scenes, frames):
        for t, x in s['parts']:
            i0 = int(round((start + t)*SR)); track[i0:i0+len(x)] += x
        s['start'] = start; start += n/render.FPS
    return scenes, frames, track[:int(total*SR)]

render.build_audio = build_audio
render.CONFIGS[name] = cfg
asyncio.run(render.main(name, '--probe' in sys.argv))
