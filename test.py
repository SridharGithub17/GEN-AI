from langchain_community.llms import Ollama
import Configs

llm = Ollama(model="openhermes:latest", base_url=Configs.llm_URL)
a=llm.invoke('tell me about you')
print(a)

print('hello')