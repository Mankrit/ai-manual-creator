import inspect
import json
import logging
import time
from typing import Callable, Any, Dict, List, Union
import litellm
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("agent")

def function_to_schema(func: Callable) -> Dict[str, Any]:
    """
    Converts a Python function into an OpenAI-compatible JSON schema for tool calling.
    Uses docstrings and function signature reflection.
    """
    sig = inspect.signature(func)
    doc = inspect.getdoc(func) or ""
    
    # Parse docstring for parameter descriptions
    param_docs = {}
    lines = doc.split("\n")
    for line in lines:
        line = line.strip()
        if ":" in line:
            parts = line.split(":", 1)
            param_name = parts[0].strip().lstrip("-* ")
            param_desc = parts[1].strip()
            param_docs[param_name] = param_desc

    properties = {}
    required = []
    
    for name, param in sig.parameters.items():
        if name in ("self", "args", "kwargs"):
            continue
            
        # Infer type
        param_type = "string"
        if param.annotation == int:
            param_type = "integer"
        elif param.annotation == float:
            param_type = "number"
        elif param.annotation == bool:
            param_type = "boolean"
        elif param.annotation == list or getattr(param.annotation, "__origin__", None) is list:
            param_type = "array"
            
        param_desc = param_docs.get(name, f"The {name} parameter")
        
        properties[name] = {
            "type": param_type,
            "description": param_desc
        }
        
        if param_type == "array":
            properties[name]["items"] = {"type": "string"}
            
        if param.default == inspect.Parameter.empty:
            required.append(name)
            
    # Extract main function description (first non-empty lines)
    desc_lines = []
    for line in lines:
        if line.strip().startswith(":") or "returns" in line.lower():
            break
        desc_lines.append(line)
    description = "\n".join(desc_lines).strip()
    
    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": description or f"Execute {func.__name__}",
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    }

def run_agent(
    system_instruction: str,
    user_prompt: str,
    tools: Dict[str, Callable],
    model: str,
    max_turns: int = 20
) -> List[Dict[str, Any]]:
    """
    Runs a tool-use agent loop using LiteLLM.
    Returns the complete message history.
    """
    # 1. Generate schemas for the tools, forcing schema name to match the registration key
    tool_schemas = []
    if tools:
        for name, func in tools.items():
            schema = function_to_schema(func)
            schema["function"]["name"] = name
            tool_schemas.append(schema)
    else:
        tool_schemas = None
    
    # 2. Build initial message history
    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_prompt}
    ]
    
    turn = 0
    while turn < max_turns:
        turn += 1
        logger.info(f"--- Agent Turn {turn}/{max_turns} using model: {model} ---")
        
        # Add sleep to avoid rate limits on free models (e.g. OpenRouter 15 RPM limit)
        if "openrouter" in model.lower():
            time.sleep(4)
        
        try:
            # Call LiteLLM completion
            # litellm handles standard tool call routing for Gemini, Claude, OpenAI, etc.
            response = litellm.completion(
                model=model,
                messages=messages,
                tools=tool_schemas,
                tool_choice="auto" if tool_schemas else None,
                temperature=0.3
            )
        except Exception as e:
            logger.error(f"Error calling LLM: {str(e)}")
            messages.append({"role": "assistant", "content": f"Error communicating with LLM: {str(e)}"})
            break
            
        choice = response.choices[0]
        assistant_msg = choice.message
        
        # Log assistant text response if present
        if assistant_msg.content:
            logger.info(f"Agent response:\n{assistant_msg.content}")
            
        # Append assistant message to history (LiteLLM translates this to OpenAI format)
        messages.append(assistant_msg)
        
        # Check for tool calls
        if not assistant_msg.tool_calls:
            logger.info("No tool calls. Agent has finished its reply.")
            break
            
        logger.info(f"Agent requested {len(assistant_msg.tool_calls)} tool call(s).")
        
        for tool_call in assistant_msg.tool_calls:
            tool_name = tool_call.function.name
            tool_args_str = tool_call.function.arguments
            tool_id = tool_call.id
            
            logger.info(f"Executing tool '{tool_name}' with args: {tool_args_str}")
            
            # Find the registered function
            func = tools.get(tool_name)
            if not func:
                result = f"Error: Tool '{tool_name}' is not registered."
                logger.error(result)
            else:
                try:
                    # Parse arguments
                    args = json.loads(tool_args_str) if tool_args_str else {}
                    # Call function
                    result = func(**args)
                    logger.info(f"Tool '{tool_name}' execution completed successfully.")
                except Exception as e:
                    result = f"Error executing tool '{tool_name}': {str(e)}"
                    logger.error(result)
            
            # Format and append tool response
            messages.append({
                "role": "tool",
                "name": tool_name,
                "tool_call_id": tool_id,
                "content": str(result)
            })
            
    if turn >= max_turns:
        logger.warning("Reached maximum agent turns.")
        
    return messages
