# Riconoscimento vocale italiano offline (Windows 11, Python 3.15.2) — 2026-11-26
Fonte: rapporto del ricercatore-web (nulla installato né provato). "letto" = pagina aperta davvero.

## Raccomandazione
1. **sherpa-onnx + Parakeet-TDT 0.6b v3 int8** (prima scelta). PyPI sherpa-onnx 2.0.3 ha la wheel `cp315-win_amd64` (letto), licenza Apache. Modello: italiano tra 25 lingue, CC-BY-4.0 (uso commerciale ok), WER italiano 3,0% Fleurs / 10,1% MLS (letto, scheda del modello). Dimensione int8 non verificata.
   - Integrazione: `st.audio_input` → WAV → float32 mono 16 kHz → `OfflineRecognizer.from_transducer(...)` (nomi esatti dei parametri da verificare nella doc sherpa).
   - Modelli: https://k2-fsa.github.io/sherpa/onnx/pretrained_models/index.html
2. **whisper.cpp via subprocess** (piano B, nessun Python): binari Windows solo nella v1.8.2 (`whisper-bin-x64.zip`, letto); modello ggml `small-q5_1` 181 MiB da huggingface.co/ggerganov/whisper.cpp; comando `whisper-cli.exe -m ggml-small-q5_1.bin -l it -f file.wav -nt` (flag da verificare), WAV 16 kHz mono 16 bit. Licenza MIT.
3. **Vosk** (ripiego leggero): wheel `py3-none` (probabile ok su 3.15), Apache 2.0; `vosk-model-small-it-0.22` 48 MB ma WER ~17-26% (mediocre); modello grande 1,2 GB. Progetto fermo al 2022.
- **Windows System.Speech**: italiano non confermato, sconsigliato.
- **Web Speech API (Chrome)**: manda l'audio a Google (non offline, privacy): solo se il titolare lo accetta.

## Passi consigliati
1. `pip install sherpa-onnx` nel .venv della dashboard; verificare che prenda la wheel cp315.
2. Scaricare Parakeet-TDT v3 int8 dalla pagina dei modelli sherpa (fonte ufficiale) in una cartella fuori dal repo (es. ~/.claude/guardian/modelli/).
3. Nella dashboard: audio → 16 kHz mono float32 → trascrizione → mostrare il testo e chiedere conferma.
4. Comandi vocali: normalizzare (minuscole, senza punteggiatura) e confrontare con una lista di comandi (difflib), accettando varianti di "Guardian".
5. Se la wheel non si installa: whisper.cpp 1.8.2 + small-q5_1.

## Fonti lette
pypi.org/project/sherpa-onnx · pypi.org/pypi/sherpa-onnx/json · k2-fsa.github.io/sherpa/onnx/pretrained_models · huggingface.co/nvidia/parakeet-tdt-0.6b-v3 · huggingface.co/ggerganov/whisper.cpp · github.com/ggml-org/whisper.cpp releases v1.8.2 e v1.9.6 · pypi.org/project/vosk · alphacephei.com/vosk/models · learn.microsoft.com/en-ie/answers/questions/1688754 (non ufficiale)
