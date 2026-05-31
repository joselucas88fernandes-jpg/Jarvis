import os
import sys
import threading
import time
import queue
import numpy as np
import sounddevice as sd
import keyboard
from faster_whisper import WhisperModel
from pathlib import Path

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR = get_base_dir()
MODEL_ROOT = BASE_DIR / "models"

class AudioHandler:
    def __init__(self, model_size="base", device="cpu", compute_type="int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None
        self._model_lock = threading.Lock()

        self.samplerate = 16000
        self.channels = 1
        self.recording = False
        self.audio_queue = queue.Queue()

        # PTT keys
        self.ptt_keys = "ctrl+shift"
        self.is_ptt_active = False

        # Callbacks
        self.on_recording_start = None
        self.on_recording_stop = None
        self.on_transcription_ready = None

        self._keyboard_hooks = []

    def load_model(self):
        with self._model_lock:
            if self.model is None:
                print(f"[AudioHandler] 📦 Loading Whisper model '{self.model_size}'...")
                MODEL_ROOT.mkdir(parents=True, exist_ok=True)
                # download_root ensures it's saved in the project directory
                self.model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                    download_root=str(MODEL_ROOT)
                )
                print("[AudioHandler] ✅ Whisper model loaded.")

    def _record_callback(self, indata, frames, time_info, status):
        if status:
            print(f"[AudioHandler] ⚠️ sd callback status: {status}", file=sys.stderr)
        if self.recording:
            self.audio_queue.put(indata.copy())

    def start_ptt_listener(self):
        print(f"[AudioHandler] 🎧 Listening for PTT hotkey: {self.ptt_keys}")

        def on_press(e):
            try:
                if not self.is_ptt_active and keyboard.is_pressed("ctrl") and keyboard.is_pressed("shift"):
                    self.is_ptt_active = True
                    self._start_recording()
            except Exception as ex:
                print(f"[AudioHandler] ❌ Keyboard press error: {ex}")

        def on_release(e):
            try:
                if self.is_ptt_active:
                    if not (keyboard.is_pressed("ctrl") and keyboard.is_pressed("shift")):
                        self.is_ptt_active = False
                        self._stop_recording()
            except Exception as ex:
                print(f"[AudioHandler] ❌ Keyboard release error: {ex}")

        try:
            h1 = keyboard.on_press(on_press)
            h2 = keyboard.on_release(on_release)
            self._keyboard_hooks = [h1, h2]
        except ImportError:
            print("[AudioHandler] ❌ 'keyboard' library requires root/sudo on this OS.")
        except Exception as e:
            print(f"[AudioHandler] ❌ Failed to start PTT listener: {e}")

    def cleanup(self):
        """Clean up hooks and streams."""
        for hook in self._keyboard_hooks:
            try:
                keyboard.unhook(hook)
            except:
                pass
        self._keyboard_hooks = []
        if self.recording:
            self._stop_recording()

    def _start_recording(self):
        if self.recording:
            return

        self.recording = True
        self.audio_data = []
        while not self.audio_queue.empty():
            self.audio_queue.get()

        if self.on_recording_start:
            self.on_recording_start()

        try:
            self.stream = sd.InputStream(
                samplerate=self.samplerate,
                channels=self.channels,
                dtype='float32',
                callback=self._record_callback
            )
            self.stream.start()
            print("[AudioHandler] 🎤 Recording started...")
        except Exception as e:
            print(f"[AudioHandler] ❌ Failed to start audio stream: {e}")
            self.recording = False

    def _stop_recording(self):
        if not self.recording:
            return

        print("[AudioHandler] 🛑 Recording stopped.")
        self.recording = False
        try:
            self.stream.stop()
            self.stream.close()
        except:
            pass

        if self.on_recording_stop:
            self.on_recording_stop()

        # Collect all audio
        while not self.audio_queue.empty():
            self.audio_data.append(self.audio_queue.get())

        if self.audio_data:
            audio_np = np.concatenate(self.audio_data, axis=0).flatten()
            threading.Thread(target=self._transcribe, args=(audio_np,), daemon=True).start()

    def _transcribe(self, audio_np):
        try:
            if self.model is None:
                self.load_model()

            print("[AudioHandler] ⚙️ Transcribing...")
            segments, info = self.model.transcribe(audio_np, beam_size=5, language="pt")

            text = "".join(segment.text for segment in segments).strip()
            print(f"[AudioHandler] 📝 Transcript: {text}")

            if self.on_transcription_ready:
                self.on_transcription_ready(text)
        except Exception as e:
            print(f"[AudioHandler] ❌ Transcription error: {e}")
            if self.on_transcription_ready:
                self.on_transcription_ready("")

if __name__ == "__main__":
    handler = AudioHandler()
    handler.load_model()
    handler.start_ptt_listener()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        handler.cleanup()
