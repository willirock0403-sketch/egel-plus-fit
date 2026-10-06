import sherpa_onnx, soundfile as sf, sys, numpy as np
def make(voice):
    d=f'/home/claude/tts/{voice}'
    name=[x for x in __import__('os').listdir(d) if x.endswith('.onnx')][0]
    cfg=sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
        vits=sherpa_onnx.OfflineTtsVitsModelConfig(model=f'{d}/{name}',tokens=f'{d}/tokens.txt',data_dir=f'{d}/espeak-ng-data'),
        num_threads=2,provider='cpu'),max_num_sentences=1)
    return sherpa_onnx.OfflineTts(cfg)
if __name__=='__main__':
    txt="Bienvenido a la guía paso a paso para registrarte al EGEL Plus de CENEVAL, el Examen General para el Egreso de la Licenciatura. Cuando te pidan la clave del centro de trabajo, escribe: 2, 8, M, S, U, 0, 0, 1, 0, B."
    for v in ('vits-piper-es_MX-claude-high','vits-piper-es_MX-ald-medium'):
        t=make(v); a=t.generate(txt,sid=0,speed=1.0)
        sf.write(f'/home/claude/tts/test_{v}.wav',np.array(a.samples),a.sample_rate); print(v,a.sample_rate,len(a.samples)/a.sample_rate)
