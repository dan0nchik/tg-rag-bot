import litellm
import os
import config

# Для генерации ответов через Together.Litellm с моделью meta-llama
litellm.configure(api_key=os.getenv("TOGETHER_API_KEY"))
LLM_MODEL = config.LLM_MODEL


async def generate_response(prompt: str, system_prompt: str = "") -> str:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    # Используем LiteLLM как LLM-интегратор
    result = await litellm.chat_completion(model=LLM_MODEL, messages=messages)
    return result.choices[0].message.content
