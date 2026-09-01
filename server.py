import io
import os
import json
import base64
import importlib
import threading
httpServerModule = importlib.import_module("http.server")
urllibParseModule = importlib.import_module("urllib.parse")
whisperModule = importlib.import_module("whisper")
ollamaModule = importlib.import_module("ollama")
edgeModule = importlib.import_module("edge")
transcriberInstance = whisperModule.WhisperTranscriber()
tutorInstance = ollamaModule.OllamaTutor()
speakerInstance = edgeModule.EdgeSpeaker()
def initializeLocalModels():
  try:
    transcriberInstance.loadModel()
  except Exception:
    pass
  try:
    tutorInstance.ensureModelInstalled()
  except Exception:
    pass
class TutorRequestHandler(httpServerModule.BaseHTTPRequestHandler):
  def sendJsonResponse(self, statusCode, payloadDict):
    try:
      responseBody = json.dumps(payloadDict).encode("utf-8")
      self.send_response(statusCode)
      self.send_header("Content-Type", "application/json")
      self.send_header("Content-Length", str(len(responseBody)))
      self.send_header("Access-Control-Allow-Origin", "*")
      self.send_header("Access-Control-Allow-Headers", "Content-Type")
      self.end_headers()
      self.wfile.write(responseBody)
    except Exception:
      pass
  def sendAudioResponse(self, audioBytes):
    try:
      isMp3Audio = audioBytes.startswith(b"ID3") or audioBytes.startswith(b"\xff\xfb") or audioBytes.startswith(b"\xff\xf3")
      contentType = "audio/mpeg" if isMp3Audio else "audio/wav"
      self.send_response(200)
      self.send_header("Content-Type", contentType)
      self.send_header("Content-Length", str(len(audioBytes)))
      self.send_header("Access-Control-Allow-Origin", "*")
      self.end_headers()
      self.wfile.write(audioBytes)
    except Exception:
      pass
  def serveStaticFile(self, filePath, contentType):
    if os.path.exists(filePath):
      try:
        with open(filePath, "rb") as fileHandle:
          fileBytes = fileHandle.read()
        self.send_response(200)
        self.send_header("Content-Type", contentType)
        self.send_header("Content-Length", str(len(fileBytes)))
        self.end_headers()
        self.wfile.write(fileBytes)
      except Exception:
        pass
    else:
      self.sendJsonResponse(404, {"error": "File Not Found"})
  def handleGetRequest(self):
    parsedUrl = urllibParseModule.urlparse(self.path)
    requestPath = parsedUrl.path
    if requestPath == "/" or requestPath == "/vak.html":
      self.serveStaticFile("vak.html", "text/html; charset=utf-8")
    elif requestPath == "/vak.css":
      self.serveStaticFile("vak.css", "text/css; charset=utf-8")
    elif requestPath == "/vak.js":
      self.serveStaticFile("vak.js", "application/javascript; charset=utf-8")
    elif requestPath == "/api/status":
      self.sendJsonResponse(200, {
        "status": "Ready",
        "tutorReady": tutorInstance.isModelVerified,
        "transcriberLoaded": transcriberInstance.isLoaded,
        "message": "OK!"
      })
    else:
      self.sendJsonResponse(404, {"error": "Endpoint Not Found"})
  def handlePostRequest(self):
    parsedUrl = urllibParseModule.urlparse(self.path)
    requestPath = parsedUrl.path
    contentLengthHeader = self.headers.get("Content-Length", 0)
    contentLength = int(contentLengthHeader) if contentLengthHeader else 0
    requestBytes = self.rfile.read(contentLength) if contentLength > 0 else b""
    if requestPath == "/api/chat":
      try:
        requestJson = json.loads(requestBytes.decode("utf-8")) if requestBytes else {}
        userPrompt = requestJson.get("prompt", "")
        tutorLanguage = requestJson.get("tutorLanguage", "English")
        conversationHistory = requestJson.get("history", [])
        tutorResponse = tutorInstance.queryTutor(userPrompt, tutorLanguage, conversationHistory)
        self.sendJsonResponse(200, {"response": tutorResponse})
      except Exception as errorObject:
        self.sendJsonResponse(500, {"error": "Chat Processing Failed", "details": str(errorObject)})
    elif requestPath == "/api/transcribe":
      try:
        contentType = self.headers.get("Content-Type", "")
        if "application/json" in contentType:
          requestJson = json.loads(requestBytes.decode("utf-8"))
          audioBase64 = requestJson.get("audio", "")
          audioBinary = base64.b64decode(audioBase64)
          languageCode = requestJson.get("language", "en")
        else:
          audioBinary = requestBytes
          languageCode = "en"
        transcriptionText = transcriberInstance.transcribeAudio(audioBinary, languageCode)
        self.sendJsonResponse(200, {"transcript": transcriptionText})
      except Exception as errorObject:
        self.sendJsonResponse(500, {"error": "Transcription Failed", "details": str(errorObject)})
    elif requestPath == "/api/speak":
      try:
        requestJson = json.loads(requestBytes.decode("utf-8")) if requestBytes else {}
        textToSpeak = requestJson.get("text", "")
        languageCode = requestJson.get("language", "en")
        synthesizedAudio = speakerInstance.synthesizeToWave(textToSpeak, languageCode)
        self.sendAudioResponse(synthesizedAudio)
      except Exception as errorObject:
        self.sendJsonResponse(500, {"error": "Speech Synthesis Failed", "details": str(errorObject)})
    else:
      self.sendJsonResponse(404, {"error": "Endpoint Not Found"})
setattr(TutorRequestHandler, "do_GET", lambda self: self.handleGetRequest())
setattr(TutorRequestHandler, "do_POST", lambda self: self.handlePostRequest())
setattr(TutorRequestHandler, "do_OPTIONS", lambda self: (self.send_response(200), self.send_header("Access-Control-Allow-Origin", "*"), self.send_header("Access-Control-Allow-Headers", "Content-Type"), self.end_headers()))
def runServer(portNumber=8080):
  modelInitThread = threading.Thread(target=initializeLocalModels, daemon=True)
  modelInitThread.start()
  serverAddress = ("", portNumber)
  httpDaemon = httpServerModule.HTTPServer(serverAddress, TutorRequestHandler)
  print(f"Server Started On {portNumber}")
  httpDaemon.serve_forever()
if __name__ == "__main__":
  runServer(8080)