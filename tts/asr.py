import sherpa_onnx, soundfile as sf, sys, numpy as np
d='/home/claude/tts/sherpa-onnx-whisper-small'
rec=sherpa_onnx.OfflineRecognizer.from_whisper(encoder=f'{d}/small-encoder.int8.onnx',decoder=f'{d}/small-decoder.int8.onnx',tokens=f'{d}/small-tokens.txt',language='es',task='transcribe',num_threads=2)
def tr(path):
    a,sr=sf.read(path,dtype='float32')
    if a.ndim>1: a=a.mean(1)
    s=rec.create_stream(); s.accept_waveform(sr,a); rec.decode_stream(s); return s.result.text.strip()
if __name__=='__main__':
    for p in sys.argv[1:]: print(p.split('/')[-1],'=>',tr(p))
