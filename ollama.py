import os
import json
import importlib
huggingfaceHubModule = importlib.import_module("huggingface_hub")
llamaCppModule = importlib.import_module("llama_cpp")
class OllamaTutor:
  def __init__(self, modelsDirectory="models/llm"):
    self.modelsDirectory = modelsDirectory
    self.repoId = "Qwen/Qwen2.5-0.5B-Instruct-GGUF"
    self.fileName = "qwen2.5-0.5b-instruct-q4_k_m.gguf"
    self.llamaInstance = None
    self.isModelVerified = False
  def ensureModelInstalled(self):
    if not os.path.exists(self.modelsDirectory):
      os.makedirs(self.modelsDirectory, exist_ok=True)
    localModelPath = os.path.join(self.modelsDirectory, self.fileName)
    if not os.path.exists(localModelPath):
      huggingfaceHubModule.hf_hub_download(
        repo_id=self.repoId,
        filename=self.fileName,
        local_dir=self.modelsDirectory
      )
    if self.llamaInstance is None and os.path.exists(localModelPath):
      llamaClass = getattr(llamaCppModule, "Llama")
      self.llamaInstance = llamaClass(model_path=localModelPath, n_ctx=2048, verbose=False)
      self.isModelVerified = True
    return self.isModelVerified
  def getSystemPrompt(self, tutorLanguage="English"):
    if tutorLanguage == "Japanese":
      return "あなたの名前はノブナガです。親切で魅力的な女性の日本語会話チューターです。自然な日本語で返答し、会話の文脈に合わせて楽しく話してください。文法の改善点があれば優しく伝えてください"
    return "Your Name Is Nobunaga. You Are A Friendly Female English Speaking Tutor. Converse Naturally In English, Reply To Whatever The User Says In A Helpful & Conversational Manner, Correct Grammar Gently & Keep The Flow Engaging"
  def queryTutor(self, userPrompt, tutorLanguage="English", conversationHistory=None):
    if self.llamaInstance is None:
      self.ensureModelInstalled()
    if conversationHistory is None:
      conversationHistory = []
    systemPrompt = self.getSystemPrompt(tutorLanguage)
    messagesList = [{"role": "system", "content": systemPrompt}]
    for historyItem in conversationHistory:
      roleName = "user" if historyItem.get("role") == "User" else "assistant"
      textContent = historyItem.get("content", "")
      messagesList.append({"role": roleName, "content": textContent})
    messagesList.append({"role": "user", "content": userPrompt})
    if self.llamaInstance is not None:
      try:
        completionResult = self.llamaInstance.create_chat_completion(
          messages=messagesList,
          max_tokens=150,
          temperature=0.7
        )
        choiceItem = completionResult.get("choices", [{}])[0]
        responseText = choiceItem.get("message", {}).get("content", "").strip()
        if responseText:
          return responseText
      except Exception:
        pass
    return "I Am Listening! Please Continue Speaking" if tutorLanguage == "English" else "お話を聞いています！続けて話してください"