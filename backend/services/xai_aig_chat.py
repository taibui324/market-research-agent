"""Wrapper around AIG's Chat Completions API with structured output support."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, TypeVar, Union

import openai
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.runnables import Runnable
from pydantic import BaseModel, ConfigDict, Field, SecretStr

from ..utils.settings import Settings, get_settings

if TYPE_CHECKING:
    from langchain_core.language_models.chat_models import (
        LangSmithParams,
        LanguageModelInput,
    )

_BM = TypeVar("_BM", bound=BaseModel)
_DictOrPydanticClass = Union[dict[str, Any], type[_BM], type]
_DictOrPydantic = Union[dict, _BM]


class XAIChatAIG(BaseChatModel):
    """XAI AIG chat model with structured output support.
    
    This is a custom implementation that uses the XAI AIG API through OpenAI client
    and provides structured output capabilities similar to LangChain's ChatXAI.
    
    Example:
        .. code-block:: python
        
            from backend.services.xai_aig_chat import XAIChatAIG
            
            llm = XAIChatAIG()
            response = await llm.ainvoke("Tell me about AI")
            
            # With structured output
            from pydantic import BaseModel
            
            class Joke(BaseModel):
                setup: str
                punchline: str
                
            structured_llm = llm.with_structured_output(Joke)
            joke = await structured_llm.ainvoke("Tell me a joke")
    """
    
    model_name: str = Field(default="x-ai:grok-4-0709", alias="model")
    """Model name to use."""
    
    search_parameters: Optional[Dict[str, Any]] = Field(default={"mode": "on"})
    """Parameters for search requests."""
    
    temperature: float = Field(default=0.7)
    """Sampling temperature."""
    
    max_tokens: Optional[int] = Field(default=None)
    """Maximum number of tokens to generate."""
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    aig_client: Optional[openai.AsyncOpenAI] = None
    settings: Optional[Settings] = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize AIG client using settings
        settings = get_settings()
        aig_config = settings.get_xai_settings()
        self.aig_client = openai.AsyncOpenAI(**aig_config)
        self.settings = settings
    
    @property
    def _llm_type(self) -> str:
        """Return type of chat model."""
        return "aig-chat"
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Get the identifying parameters."""
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
    
    def _convert_messages_to_openai_format(self, messages: List[BaseMessage]) -> List[Dict[str, str]]:
        """Convert LangChain messages to OpenAI format."""
        openai_messages = []
        
        for message in messages:
            if isinstance(message, SystemMessage):
                role = "system"
            elif isinstance(message, HumanMessage):
                role = "user"
            elif isinstance(message, AIMessage):
                role = "assistant"
            else:
                role = "user"  # Default fallback
            
            openai_messages.append({
                "role": role,
                "content": message.content
            })
        
        return openai_messages
    
    def _create_chat_result(self, response: Any) -> ChatResult:
        """Create ChatResult from OpenAI response."""
        if not response.choices:
            return ChatResult(generations=[])
        
        choice = response.choices[0]
        message = AIMessage(
            content=choice.message.content,
            response_metadata={
                "model_name": self.model_name,
                "finish_reason": choice.finish_reason,
                "usage": response.usage.model_dump() if response.usage else None,
            }
        )
        
        # Add citations if available
        if hasattr(response, 'citations') and response.citations:
            message.additional_kwargs["citations"] = response.citations
        
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])
    
    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate chat response asynchronously."""
        openai_messages = self._convert_messages_to_openai_format(messages)
        
        # Prepare request parameters
        request_params = {
            "model": self.model_name,
            "messages": openai_messages,
            "temperature": self.temperature,
        }
        
        if self.max_tokens:
            request_params["max_tokens"] = self.max_tokens
        
        if stop:
            request_params["stop"] = stop
        
        # Add search parameters if configured
        if self.search_parameters:
            request_params["extra_body"] = {
                "search_parameters": self.search_parameters
            }
        
        # Add any additional kwargs
        request_params.update(kwargs)
        
        # Make API call
        response = await self.aig_client.chat.completions.create(**request_params)
        
        return self._create_chat_result(response)
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate chat response synchronously."""
        # For simplicity, we'll raise an error for sync calls
        # In a full implementation, you'd create a sync client as well
        raise NotImplementedError(
            "Synchronous generation not implemented. Use ainvoke() instead of invoke()."
        )
    
    def with_structured_output(
        self,
        schema: Optional[_DictOrPydanticClass] = None,
        *,
        method: Literal["function_calling", "json_mode", "json_schema"] = "json_mode",
        include_raw: bool = False,
        **kwargs: Any,
    ) -> Runnable[LanguageModelInput, _DictOrPydantic]:
        """Model wrapper that returns outputs formatted to match the given schema.
        
        Args:
            schema: The output schema (Pydantic class or dict)
            method: The method for steering model generation
            include_raw: Whether to include raw response
            **kwargs: Additional arguments
            
        Returns:
            A Runnable that outputs structured data
        """
        return StructuredOutputRunnable(
            llm=self,
            schema=schema,
            method=method,
            include_raw=include_raw,
        )


class StructuredOutputRunnable(Runnable):
    """Runnable for structured output generation."""
    
    def __init__(
        self,
        llm: XAIChatAIG,
        schema: Optional[_DictOrPydanticClass] = None,
        method: str = "json_mode",
        include_raw: bool = False,
    ):
        self.llm = llm
        self.schema = schema
        self.method = method
        self.include_raw = include_raw
        self._is_pydantic = isinstance(schema, type) and issubclass(schema, BaseModel)
    
    def _create_structured_prompt(self, input_text: str) -> str:
        """Create a prompt that encourages structured output."""
        if self._is_pydantic:
            # Get schema from Pydantic model
            schema_dict = self.schema.model_json_schema()
            schema_str = json.dumps(schema_dict, indent=2)
            
            prompt = f"""Please respond with a JSON object that matches this exact schema:

{schema_str}

User request: {input_text}

Response (JSON only):"""
        else:
            prompt = f"""Please respond with a JSON object.

User request: {input_text}

Response (JSON only):"""
        
        return prompt
    
    def _parse_response(self, content: str) -> Any:
        """Parse the response content into structured format."""
        try:
            # Try to extract JSON from the response
            content = content.strip()
            
            # Handle cases where the response might have extra text
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            content = content.strip()
            
            # Parse JSON
            parsed_data = json.loads(content)
            
            # Convert to Pydantic model if schema is provided
            if self._is_pydantic:
                return self.schema(**parsed_data)
            
            return parsed_data
            
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            if self.include_raw:
                return {
                    "raw": content,
                    "parsed": None,
                    "parsing_error": e
                }
            raise ValueError(f"Failed to parse structured output: {e}")
    
    async def ainvoke(
        self,
        input: Union[str, List[BaseMessage], LanguageModelInput],
        config: Optional[Any] = None,
        **kwargs: Any,
    ) -> Any:
        """Invoke the structured output generation asynchronously."""
        # Convert input to string if needed
        if isinstance(input, str):
            prompt = self._create_structured_prompt(input)
            messages = [HumanMessage(content=prompt)]
        elif isinstance(input, list):
            # Assume it's a list of messages
            messages = input
        else:
            # Handle other input types
            messages = [HumanMessage(content=str(input))]
        
        # Generate response
        result = await self.llm._agenerate(messages, **kwargs)
        
        if not result.generations:
            raise ValueError("No response generated")
        
        content = result.generations[0].message.content
        
        if self.include_raw:
            try:
                parsed = self._parse_response(content)
                return {
                    "raw": result.generations[0].message,
                    "parsed": parsed,
                    "parsing_error": None
                }
            except Exception as e:
                return {
                    "raw": result.generations[0].message,
                    "parsed": None,
                    "parsing_error": e
                }
        else:
            return self._parse_response(content)
    
    def invoke(
        self,
        input: Union[str, List[BaseMessage], LanguageModelInput],
        config: Optional[Any] = None,
        **kwargs: Any,
    ) -> Any:
        """Invoke the structured output generation synchronously."""
        raise NotImplementedError(
            "Synchronous generation not implemented. Use ainvoke() instead."
        )
