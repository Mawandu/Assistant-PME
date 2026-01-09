# services/nlp.py
import os
import json
import logging
from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI
import google.generativeai as genai

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NLPService:
    def __init__(self):
        self.provider = os.getenv("DEFAULT_MODEL_PROVIDER", "groq").lower()
        self.api_key_groq = os.getenv("GROQ_API_KEY")
        self.api_key_openai = os.getenv("OPENAI_API_KEY")
        self.api_key_google = os.getenv("GOOGLE_API_KEY")
        self.groq_client = Groq(api_key=self.api_key_groq) if self.api_key_groq else None
        self.openai_client = OpenAI(api_key=self.api_key_openai) if self.api_key_openai else None
        if self.api_key_google:
            genai.configure(api_key=self.api_key_google)

    def analyze_query(self, user_message: str) -> dict:
        """
        Analyse la requête utilisateur via LLM (Groq par défaut) pour extraire l'intention et les entités.
        """
        system_prompt = """
        You are StockPilot, an expert inventory management assistant for SMEs.
        Your task is to analyze the user's request and return a structured JSON object.
        
        IMPORTANT: match the user's language in your summary and future responses. 
        If the user asks in English, the summary must be in English.
        If the user asks in French, the summary must be in French.
        
        POSSIBLE INTENTS:
        - LIST_PRODUCTS: User wants a LIST of products (filter by stock, category, supplier).
        - GET_STATS: User wants global stats or financial indicators (margin, profit).
        - PLOT_CHART: User explicitly wants a chart/visualization.
        - SEARCH_PRODUCT: User looks for A SINGLE specific product or "the most expensive/available" product.
        - LIST_SUPPLIERS: User wants a list of suppliers.
        - SUPPLIER_STATS: User wants stats about suppliers.
        - GENERAL_KNOWLEDGE: Theoretical or general questions (e.g., "What is FIFO?").
        - UNKNOWN: Off-topic requests.
        
        ENTITIES to extract:
        - filter_status: "OUT_OF_STOCK", "LOW_STOCK", "ACTIVE"
        - category: category name
        - product_name: product name or "most expensive product"
        - supplier_name: supplier name
        - stat_type: "by_category", "by_supplier", "global", "margin"
        - sort_order: "DESC", "ASC"
        - sort_field: "price", "quantity"
        - graph_type: "bar", "pie", "histogram"
        
        Expected JSON Format:
        {
            "intent": "CHOSEN_INTENT",
            "entities": {
                "filter_status": "...",
                "category": "...",
                "stat_type": "...",
                "sort_order": "...",
                "sort_field": "..."
            },
            "summary": "Concise summary of user request in USER'S LANGUAGE"
        }
        """

        try:
            if self.provider == "groq" and self.groq_client:
                return self._call_groq(system_prompt, user_message)
            elif self.provider == "openai" and self.openai_client:
                try:
                    response_text = self._call_openai(system_prompt, user_message)
                    # OpenAI might sometimes include text outside the JSON block
                    if isinstance(response_text, str) and "{" in response_text and "}" in response_text:
                        # Basic extraction if the LLM talks too much
                        start = response_text.find("{")
                        end = response_text.rfind("}") + 1
                        json_str = response_text[start:end]
                        return json.loads(json_str)
                    elif isinstance(response_text, dict): # If _call_openai already returned a dict
                        return response_text
                    else:
                        logger.warning(f"OpenAI response not strictly JSON: {response_text}")
                        return {"intent": "UNKNOWN", "entities": {}, "summary": "Réponse mal formatée par OpenAI"}
                except json.JSONDecodeError as e:
                    logger.error(f"Erreur de parsing JSON pour OpenAI: {e} - Response: {response_text}")
                    return {"intent": "UNKNOWN", "entities": {}, "error": str(e), "summary": "Erreur d'analyse JSON de la réponse OpenAI"}
            elif self.provider == "google" and self.api_key_google:
                return self._call_google(system_prompt, user_message)
            else:
                return {
                    "intent": "unknown",
                    "entities": {},
                    "summary": "Aucun fournisseur d'IA configuré. Vérifiez vos clés API."
                }
        except Exception as e:
            logger.error(f"Erreur NLP ({self.provider}): {e}")
            return {
                "entities": {},
                "summary": f"Erreur lors de l'analyse IA : {str(e)}"
            }

    def generate_chat_response(self, user_message: str) -> str:
        """
        Génère une réponse textuelle libre pour les questions générales / théoriques.
        """
        system_prompt = "You are StockPilot, an expert inventory assistant. Answer the user's question clearly and cleanly. IMPORTANT: Answer IN THE SAME LANGUAGE as the user's question (English or French)."
        
        try:
            if self.provider == "groq" and self.groq_client:
                logger.info("Appel à Groq (Chat)...")
                completion = self.groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.7,
                    max_tokens=800
                )
                return completion.choices[0].message.content
            
            # Fallback simple
            return "Désolé, je ne peux pas générer de réponse pour le moment."
            
        except Exception as e:
            logger.error(f"Erreur de génération chat: {e}")
            return "Une erreur technique m'empêche de répondre."

    def _call_groq(self, system_prompt, user_message):
        logger.info("Appel à Groq (Llama3-70b)...")
        chat_completion = self.groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            model="llama-3.3-70b-versatile", 
            temperature=0, 
            response_format={"type": "json_object"} 
        )
        response_content = chat_completion.choices[0].message.content
        return json.loads(response_content)

    def _call_openai(self, system_prompt, user_message):
        logger.info("Appel à OpenAI (GPT-4o)...")
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    def _call_google(self, system_prompt, user_message):
        logger.info("Appel à Google (Gemini)...")
        model = genai.GenerativeModel('gemini-pro')
        full_prompt = f"{system_prompt}\n\nUser Query: {user_message}\nAnswer in JSON:"
        response = model.generate_content(full_prompt)
        clean_response = response.text.replace('```json', '').replace('```', '')
        return json.loads(clean_response)

nlp_service = NLPService()