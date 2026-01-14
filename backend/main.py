# main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect


from database import get_engine, get_session
# Base is now in models
from models import Base
import models

from services.nlp import nlp_service
from services.query import query_service

from routers import (
    user, 
    tenant, 
    auth, 
    data_source, 
    product, 
    category, 
    supplier, 
    warehouse, 
    warehouse, 
    stock_movement,
    dashboard
)

from sqlalchemy import text
# ... imports ...
# Ensure extensions exist
with get_engine().connect() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS ltree;"))
    conn.commit()

Base.metadata.create_all(bind=get_engine())

app = FastAPI(
    title="Assistant PME API",
    description="API for the AI Assistant for SME Stock Management Analysis",
    version="0.1.0",
    openapi_tags=[
        {"name": "Default", "description": "Endpoints par défaut / Santé"},
        {"name": "Authentication", "description": "Connexion utilisateur"},
        {"name": "Users", "description": "Opérations sur les utilisateurs"},
        {"name": "Tenants", "description": "Opérations sur les tenants (clients)"},
        {"name": "Data Sources", "description": "Gestion des sources de données"},
        {"name": "Products", "description": "Gestion des produits"},
        {"name": "Categories", "description": "Gestion des catégories"},
        {"name": "Stock Movements", "description": "Gestion des mouvements de stock"},
        {"name": "Suppliers", "description": "Gestion des fournisseurs"},
        {"name": "Warehouses", "description": "Gestion des entrepôts"},
    ]
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev/MVP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str): 
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/api/v1/chat/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket)
    print(f"Client #{client_id} connected via WebSocket.")
    
    # Time-aware greeting
    import datetime
    current_hour = datetime.datetime.now().hour
    greeting = "Bonjour" if 6 <= current_hour < 18 else "Bonsoir"
    
    await manager.send_personal_message(f"{greeting} ! Je m'appelle StockPilot, votre assistant sur l'analyse de votre Stock. Veuillez appuyer sur sources de données afin d'ajouter vos fichiers excel ou csv ou encore de connecter votre base de données.", websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Client #{client_id} sent: {data}")
            # Removed "Analyse de votre demande en cours..." to reduce noise
            
            analysis = nlp_service.analyze_query(data)
            print(f"   -> NLP Analysis: {analysis}")
            # Removed "AI: {analysis['summary']}" to keep it clean, or we can keep it if useful for debug but user asked to remove "le second message"
            # The user said: "pas le second message qui s'affiche là AI:.... non il faut enlever ça"
            # So I will comment it out or remove it.
            # await manager.send_personal_message(f"AI: {analysis['summary']}", websocket)

            db = get_session()
            try:
                # Use isolated session user/tenant
                user = auth.get_or_create_session_user(db, client_id)
                tenant_id = str(user.tenant_id)
                
                if tenant_id:
                    # Special handling for General Knowledge (chat)
                    if analysis.get("intent") == "GENERAL_KNOWLEDGE":
                         chat_response = nlp_service.generate_chat_response(data)
                         await manager.send_personal_message(f"{chat_response}", websocket)
                    else:
                        result = query_service.execute(db, tenant_id, analysis)
                        await manager.send_personal_message(f"{result['text']}", websocket)
                        
                        if result.get("chart"):
                            import json
                            chart_message = {
                                "type": "chart",
                                "data": result["chart"]
                            }
                            await websocket.send_text(json.dumps(chart_message))
                else:
                    await manager.send_personal_message("Erreur critique : Aucun tenant (entreprise) trouvé dans la base.", websocket)
            
            except Exception as e:
                print(f"Query Error: {e}")
                await manager.send_personal_message(f"Une erreur est survenue lors de l'interrogation des données : {str(e)}", websocket)
            finally:
                db.close() 

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"Client #{client_id} disconnected.")
    except Exception as e:
         print(f"WebSocket Error for client #{client_id}: {e}")
         try:
             await websocket.send_text(f"Une erreur critique est survenue: {e}")
         except Exception:
             pass 
         manager.disconnect(websocket)
         await websocket.close(code=1011) 

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(tenant.router)
app.include_router(data_source.router)
app.include_router(product.router)
app.include_router(category.router)
app.include_router(supplier.router)
app.include_router(warehouse.router)
app.include_router(stock_movement.router)
app.include_router(dashboard.router)

@app.get("/", tags=["Default"])
async def read_root():
    """
    Endpoint racine pour vérifier si l'API fonctionne.
    """
    return {"message": "Welcome to Assistant PME API!"}

@app.get("/health", tags=["Default"])
async def health_check():
    """
    Endpoint de vérification de santé.
    """
    return {"status": "ok"}