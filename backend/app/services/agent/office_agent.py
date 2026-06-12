import json
import asyncio
from datetime import datetime
import google.generativeai as genai
from google.protobuf.json_format import MessageToDict
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.conversation import Conversation
from app.services.agent.tools import (
    current_client_id,
    search_knowledge_base,
    check_inventory,
    update_inventory,
    check_availability,
    book_appointment
)

# Configure the Gemini API
genai.configure(api_key=settings.GEMINI_API_KEY)

class OfficeAgent:
    def __init__(self, client_id: str, channel: str = "web", session_id: str = "default"):
        self.client_id = client_id
        self.channel = channel
        self.session_id = session_id
        
        # Define the system prompt for the Office Administrator
        self.system_prompt = (
            "You are a highly efficient, professional, and friendly Office Administrator in a Box.\n"
            "Your job is to assist clients, answer questions, update inventory, and book appointments.\n\n"
            "Rules:\n"
            "1. Use search_knowledge_base to answer questions about the business (hours, location, services, etc.).\n"
            "2. Use check_inventory and update_inventory for queries/changes regarding stock, products, and pricing.\n"
            "3. Use check_availability and book_appointment for scheduling. Always verify availability before booking.\n"
            "4. Do NOT make up information. If a query cannot be solved via tools, politely explain that you don't have that information.\n"
            "5. The current date is: " + datetime.now().strftime("%Y-%m-%d") + " (Use this for relative date requests like 'tomorrow' or 'next Monday').\n"
            "6. Always keep replies concise, professional, and appropriate for the channel (SMS/Voice needs shorter answers than Web)."
        )

    def _get_db_conversation(self, db):
        # Retrieve or create the conversation record
        conv = db.query(Conversation).filter(
            Conversation.channel == self.channel,
            Conversation.session_id == self.session_id
        ).first()
        
        if not conv:
            conv = Conversation(
                channel=self.channel,
                session_id=self.session_id,
                messages="[]"
            )
            db.add(conv)
            db.commit()
            db.refresh(conv)
        return conv

    def _load_history_for_gemini(self, json_history: str):
        try:
            turns = json.loads(json_history)
            gemini_history = []
            for turn in turns:
                role = turn.get("role", "user")
                text = turn.get("text", "")
                gemini_history.append({
                    "role": role,
                    "parts": [{"text": text}]
                })
            return gemini_history
        except Exception as e:
            print(f"Error loading conversation history: {e}")
            return []

    def _save_history(self, db, conv_record, history_list):
        # Convert the history list back into simple text list
        simplified_turns = []
        for turn in history_list:
            # turn can be a protobuf Content object or a dictionary
            if hasattr(turn, 'role'):
                role = turn.role
                parts = turn.parts
            elif isinstance(turn, dict):
                role = turn.get('role', 'user')
                parts = turn.get('parts', [])
            else:
                continue
                
            text_parts = []
            for p in parts:
                if hasattr(p, 'text'):
                    if p.text:
                        text_parts.append(p.text)
                elif isinstance(p, dict):
                    if 'text' in p:
                        text_parts.append(p['text'])
                        
            text = " ".join(text_parts).strip()
            if text:
                simplified_turns.append({
                    "role": role,
                    "text": text
                })
        
        # Keep only the last 20 messages for context window management
        simplified_turns = simplified_turns[-20:]
        
        conv_record.messages = json.dumps(simplified_turns)
        db.commit()

    def _content_to_dict(self, content):
        if not content:
            return None
        if isinstance(content, dict):
            return content
        if hasattr(content, "_pb"):
            return MessageToDict(content._pb, preserving_proto_field_name=True)
        return MessageToDict(content, preserving_proto_field_name=True)

    async def get_response(self, user_message: str) -> str:
        # Set context variables for tools
        current_client_id.set(self.client_id)
        
        db = SessionLocal()
        try:
            # 1. Load conversation record
            conv_record = self._get_db_conversation(db)
            
            # 2. Format history for Gemini
            turns = self._load_history_for_gemini(conv_record.messages)
            
            # 3. Append new user message (using dict format)
            turns.append({
                "role": "user",
                "parts": [{"text": user_message}]
            })
            
            # 4. Initialize Gemini Model with tools
            model = genai.GenerativeModel(
                model_name='gemini-3.5-flash',
                tools=[
                    search_knowledge_base,
                    check_inventory,
                    update_inventory,
                    check_availability,
                    book_appointment
                ],
                system_instruction=self.system_prompt
            )
            
            # 5. Execute conversational loops to resolve function calls
            max_loops = 5
            for loop in range(max_loops):
                print(f"[AGENT] Agent loop {loop + 1}...")
                
                # Retry wrapper for API rate limits and transient exhaustion errors
                response = None
                last_err = None
                for attempt in range(3):
                    try:
                        response = await model.generate_content_async(contents=turns)
                        break
                    except Exception as ex:
                        ex_class = type(ex).__name__
                        if "ResourceExhausted" in ex_class or "429" in str(ex) or "quota" in str(ex).lower():
                            last_err = ex
                            print(f"[AGENT] Quota/Rate limited (attempt {attempt+1}/3). Retrying in 2 seconds...")
                            await asyncio.sleep(2)
                        else:
                            raise ex
                
                if response is None:
                    if last_err:
                        raise last_err
                    raise Exception("Failed to generate content after retries")
                
                # Check for function calls
                candidate = response.candidates[0] if response.candidates else None
                parts = candidate.content.parts if candidate and candidate.content else []
                
                tool_calls = [p.function_call for p in parts if p.function_call]
                
                if tool_calls:
                    # Append assistant's request for tools to history as dict
                    turns.append(self._content_to_dict(candidate.content))
                    
                    # Execute tools and construct replies
                    response_parts = []
                    for call in tool_calls:
                        name = call.name
                        # Convert MapComposite args to standard dict
                        args_dict = {}
                        if call.args:
                            for k, v in call.args.items():
                                args_dict[k] = v
                        # Execute tool
                        result = await self._execute_tool(name, args_dict)
                        # Build function response part (using dict format)
                        resp_part = {
                            "function_response": {
                                "name": name,
                                "response": {"result": result}
                            }
                        }
                        response_parts.append(resp_part)
                    
                    # Append tool response turn (using dict format)
                    turns.append({
                        "role": "function",
                        "parts": response_parts
                    })
                    # Loop back to let the LLM evaluate tool results
                    continue
                else:
                    # Final text response received
                    final_text = response.text
                    
                    # Append assistant response to turns as dict
                    turns.append(self._content_to_dict(candidate.content))
                    
                    # 6. Save simplified history back to the database
                    self._save_history(db, conv_record, turns)
                    return final_text
            
            return "I apologize, but I timed out trying to resolve this request. Please try again."
            
        except Exception as e:
            print(f"Error in OfficeAgent execution: {e}")
            err_str = str(e)
            if "429" in err_str or "quota" in err_str.lower() or "limit" in err_str.lower():
                return "I encountered a Google Gemini API quota limit error (429 Resource Exhausted). Please check your API key billing details or wait a moment before trying again."
            return "I encountered a processing error. How else can I assist you today?"
        finally:
            db.close()

    async def _execute_tool(self, name: str, args: dict) -> str:
        print(f"[TOOL] Agent executing tool: {name} with args: {args}")
        try:
            if name == "search_knowledge_base":
                return await search_knowledge_base(query=args.get("query", ""))
            elif name == "check_inventory":
                return check_inventory(sku_or_name=args.get("sku_or_name", ""))
            elif name == "update_inventory":
                sku = args.get("sku", "")
                quantity_change = int(args.get("quantity_change", 0))
                return update_inventory(sku=sku, quantity_change=quantity_change)
            elif name == "check_availability":
                return check_availability(date_str=args.get("date_str", ""))
            elif name == "book_appointment":
                return book_appointment(
                    customer_name=args.get("customer_name", ""),
                    customer_phone=args.get("customer_phone", ""),
                    date_str=args.get("date_str", ""),
                    time_str=args.get("time_str", "")
                )
            else:
                return f"Error: Tool '{name}' not found."
        except Exception as e:
            return f"Error executing tool '{name}': {e}"
