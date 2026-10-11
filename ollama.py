import os
import re
import json
import importlib
huggingfaceHubModule = importlib.import_module("huggingface_hub")
llamaCppModule = importlib.import_module("llama_cpp")
class OllamaTutor:
  def __init__(self, modelsDirectory="models/llm"):
    self.modelsDirectory = modelsDirectory
    self.repoId = "Qwen/Qwen3-4B-GGUF"
    self.fileName = "Qwen3-4B-Q4_K_M.gguf"
    self.llamaInstance = None
    self.isModelVerified = False
  def ensureModelInstalled(self):
    if not os.path.exists(self.modelsDirectory):
      os.makedirs(self.modelsDirectory, exist_ok=True)
    targetPath = os.path.join(self.modelsDirectory, self.fileName)
    if not os.path.exists(targetPath):
      huggingfaceHubModule.hf_hub_download(
        repo_id=self.repoId,
        filename=self.fileName,
        local_dir=self.modelsDirectory
      )
    if self.llamaInstance is None and os.path.exists(targetPath):
      llamaClass = getattr(llamaCppModule, "Llama")
      self.llamaInstance = llamaClass(
        model_path=targetPath,
        n_gpu_layers=-1,
        n_threads=8,
        n_batch=512,
        n_ctx=4096,
        verbose=False
      )
      self.isModelVerified = True
    return self.isModelVerified
  def getSystemPrompt(self, tutorLanguage="English"):
    if tutorLanguage == "Japanese":
      return "あなたの名前はノブナガです。親切で知識豊富な女性の日本語会話チューターです。相手の質問には直接詳しく正確に答え、自然な日本語で楽しく会話を広げてください。絵文字やマークダウン記号（アスタリスクや太字など）は絶対に使わず、純粋なテキストのみで話してください。思考プロセスやタグは出力せず、直接発話してください"
    return "Your Name Is Nobunaga. You Are A Friendly & Knowledgeable Female English Speaking Tutor. Always Answer The User Questions Directly With Rich & Engaging Information In Two To Four Conversational Sentences, Converse Naturally In English & Keep The Conversation Flowing. Speak In Pure Plain Text Only. Never Output Thinking Tags Or Internal Monologues. Never Use Emojis & Never Use Markdown Symbols Like Asterisks Or Bold Formatting"
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
    if not conversationHistory or conversationHistory[-1].get("content") != userPrompt:
      messagesList.append({"role": "user", "content": userPrompt})
    if self.llamaInstance is not None:
      try:
        completionResult = self.llamaInstance.create_chat_completion(
          messages=messagesList,
          max_tokens=2048,
          temperature=0.7
        )
        choiceItem = completionResult.get("choices", [{}])[0]
        rawResponse = choiceItem.get("message", {}).get("content", "").strip()
        if "</think>" in rawResponse:
          finalText = rawResponse.split("</think>")[-1].strip()
        elif "<think>" in rawResponse:
          finalText = re.sub(r"<think>.*?</think>", "", rawResponse, flags=re.DOTALL).strip()
        else:
          finalText = rawResponse
        cleanedText = re.sub(r"[*_#`~]", "", finalText)
        cleanedText = re.sub(r"[\U00010000-\U0010ffff]", "", cleanedText)
        cleanedText = re.sub(r"\s+", " ", cleanedText).strip()
        if cleanedText:
          return cleanedText
      except Exception:
        pass
    return "I Am Listening! Please Continue Speaking" if tutorLanguage == "English" else "お話を聞いています！続けて話してください"