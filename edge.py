import io
import asyncio
import importlib
class EdgeSpeaker:
  def __init__(self):
    self.voiceMap = {
      "en": "en-US-AvaNeural",
      "ja": "ja-JP-NanamiNeural"
    }
  def synthesizeToWave(self, textContent, languageCode="en"):
    targetVoice = self.voiceMap.get(languageCode, "en-US-AvaNeural")
    try:
      edgeTtsModule = importlib.import_module("edge_tts")
      communicateClass = getattr(edgeTtsModule, "Communicate")
      async def generateAudioStream():
        communicator = communicateClass(textContent, targetVoice)
        audioBuffer = b""
        async for chunkItem in communicator.stream():
          if chunkItem.get("type") == "audio":
            audioBuffer += chunkItem.get("data", b"")
        return audioBuffer
      eventLoop = asyncio.new_event_loop()
      asyncio.set_event_loop(eventLoop)
      audioResult = eventLoop.run_until_complete(generateAudioStream())
      eventLoop.close()
      return audioResult if audioResult else b""
    except Exception:
      return b""