import io
import av
import os
import wave
import importlib
fasterWhisperModule = None
try:
  fasterWhisperModule = importlib.import_module("faster_whisper")
except Exception:
  fasterWhisperModule = None
try:
  orgAV = av.open
  def pchAV(*posargs, **kwargs):
    kwargs.pop("metadata_errors", None)
    return orgAV(*posargs, **kwargs)
  av.open = pchAV
except Exception:
  pass
class WhisperTranscriber:
  def __init__(self, modelSize="turbo", downloadRoot="models/whisper"):
    self.modelSize = modelSize
    self.downloadRoot = downloadRoot
    self.modelInstance = None
    self.isLoaded = False
  def loadModel(self):
    if not os.path.exists(self.downloadRoot):
      os.makedirs(self.downloadRoot, exist_ok=True)
    if fasterWhisperModule is not None and self.modelInstance is None:
      try:
        whisperClass = getattr(fasterWhisperModule, "WhisperModel")
        self.modelInstance = whisperClass(
          self.modelSize,
          device="cpu",
          compute_type="int8",
          download_root=self.downloadRoot,
          cpu_threads=8
        )
        self.isLoaded = True
      except Exception:
        self.modelInstance = None
        self.isLoaded = False
    return self.isLoaded
  def transcribeAudio(self, audioBytes, languageCode="en"):
    if self.modelInstance is None:
      self.loadModel()
    if self.modelInstance is not None:
      try:
        audioStream = io.BytesIO(audioBytes)
        segments, info = self.modelInstance.transcribe(
          audioStream,
          language=languageCode,
          beam_size=5,
          vad_filter=True,
          condition_on_previous_text=False,
          temperature=0.0
        )
        transcriptList = [segment.text.strip() for segment in segments]
        transcriptionResult = " ".join(transcriptList)
        return transcriptionResult
      except Exception:
        return ""
    return ""
  def transcribeFile(self, filePath, languageCode="en"):
    if os.path.exists(filePath):
      with open(filePath, "rb") as audioFile:
        return self.transcribeAudio(audioFile.read(), languageCode)
    return ""