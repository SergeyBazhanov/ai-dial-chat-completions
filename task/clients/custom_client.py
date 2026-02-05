import json
import aiohttp
import requests

from task.clients.base import BaseClient
from task.constants import DIAL_ENDPOINT
from task.models.message import Message
from task.models.role import Role


class DialClient(BaseClient):
    _endpoint: str

    def __init__(self, deployment_name: str):
        super().__init__(deployment_name)
        self._endpoint = DIAL_ENDPOINT + f"/openai/deployments/{deployment_name}/chat/completions"

    def get_completion(self, messages: list[Message]) -> Message:
        # 1. Create headers dict with api-key and Content-Type
        headers = {
            "api-key": self._api_key,
            "Content-Type": "application/json"
        }
        # 2. Create request_data dictionary with messages
        request_data = {
            "messages": [msg.to_dict() for msg in messages]
        }
        # 3. Make POST request
        response = requests.post(
            url=self._endpoint,
            headers=headers,
            json=request_data
        )
        # 5. If status code != 200 then raise Exception
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
        # 4. Get content from response, print it and return message
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        print(content)
        return Message(role=Role.AI, content=content)

    def _get_content_snippet(self, chunk: str) -> str | None:
        """
        Parse streaming data chunk and extract content snippet.
        
        Args:
            chunk: Raw chunk string starting with 'data: ' prefix
            
        Returns:
            Content snippet string or None if no content found
        """
        if not chunk or not chunk.startswith("data: "):
            return None
        # Check for final chunk
        if chunk == "data: [DONE]":
            return None
        # Remove "data: " prefix (6 characters)
        json_str = chunk[6:]
        try:
            data = json.loads(json_str)
            if data.get("choices") and data["choices"][0].get("delta"):
                return data["choices"][0]["delta"].get("content")
        except json.JSONDecodeError:
            return None
        return None

    async def stream_completion(self, messages: list[Message]) -> Message:
        # 1. Create headers dict with api-key and Content-Type
        headers = {
            "api-key": self._api_key,
            "Content-Type": "application/json"
        }
        # 2. Create request_data dictionary with stream=True and messages
        request_data = {
            "stream": True,
            "messages": [msg.to_dict() for msg in messages]
        }
        # 3. Create empty list called 'contents'
        contents = []
        # 4. Create aiohttp.ClientSession() using 'async with'
        async with aiohttp.ClientSession() as session:
            # 5. Make POST request using session.post()
            async with session.post(
                url=self._endpoint,
                json=request_data,
                headers=headers
            ) as response:
                # 6. Get content from chunks, print and collect them
                async for line in response.content:
                    chunk = line.decode("utf-8").strip()
                    if not chunk:
                        continue
                    # Check for final chunk
                    if chunk == "data: [DONE]":
                        break
                    # Use helper method to parse content snippet
                    content = self._get_content_snippet(chunk)
                    if content:
                        print(content, end="", flush=True)
                        contents.append(content)
        # Print empty row at the end
        print()
        return Message(role=Role.AI, content="".join(contents))

