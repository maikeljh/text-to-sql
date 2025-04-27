import requests


class APIModel:
    def __init__(self, api_key: str, provider: str = "openai", model: str = "gpt-4"):
        """
        Initializes the API model for text generation.

        :param api_key: API key for the selected provider (OpenAI, DeepSeek, Gemini).
        :param provider: The provider name ('openai', 'deepseek', 'gemini').
        :param model: The model name to use (e.g., 'gpt-4' for OpenAI, 'deepseek-chat' for DeepSeek, 'gemini-pro' for Gemini).
        """
        self.api_key = api_key
        self.provider = provider.lower()
        self.model = model
        self._initialize_client()

    def _initialize_client(self):
        """Prints provider initialization (can be expanded for authentication setup)."""
        print(f"Initializing API client for {self.provider} using model {self.model}.")

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ):
        """
        Generates text using the specified API provider.

        :param system_prompt: The system message setting the context.
        :param user_prompt: The user input to generate a response.
        :param max_tokens: The maximum number of tokens to generate.
        :param temperature: Controls randomness (higher = more diverse responses).
        :return: Generated text response.
        """
        if self.provider == "openai":
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False,
            }

        elif self.provider == "deepseek":
            url = "https://api.deepseek.com/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False,
            }

        elif self.provider == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1/models/{self.model}:generateContent?key={self.api_key}"
            headers = {"Content-Type": "application/json"}

            full_prompt = f"{system_prompt}\n\nUser: {user_prompt}"

            payload = {
                "contents": [
                    {
                        "parts": [{"text": full_prompt}],
                    }
                ],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                },
            }

        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            if self.provider == "gemini":
                return response.json()["candidates"][0]["content"]["parts"][0]["text"]
            else:
                return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(
                f"API request failed: {response.status_code} - {response.text}"
            )
