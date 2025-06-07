from typing import Literal, Optional
import ollama


class OllamaAgent:
    """
    A class to represent an Ollama agent that can use tools to solve problems.
    """

    def __init__(
        self,
        model: str,
        tools: list = [],
        system_prompt: str = "You are a helpful assistant who can use available tools to solve problems",
        chat_history: Optional[list[dict[Literal["role", "content"]]]] = [],
    ) -> None:
        self.model = model
        self.tools = tools
        self.chat_history = [{"role": "system", "content": system_prompt}]
        if chat_history:
            self.chat_history.extend(chat_history)

    async def chat(self, prompt_message: Optional[str] = None):
        self.chat_history.append(
            {
                "role": "user",
                "content": prompt_message,
            }
        )

        try:
            prompt_response = ollama.chat(
                model=self.model,
                messages=self.chat_history,
                tools=self.tools,
                stream=False,
                think=None,
                # format="json",
                format=None,
                options=None,
                keep_alive=None,
            )
        except ConnectionError as e:
            print(f"Connection error: {e}")
            return
        except Exception as e:
            print(f"An error occurred: {e}")
            return

        self.chat_history.append(
            {
                "role": "assistant",
                "content": prompt_response.message.content,
            }
        )
        return prompt_response
