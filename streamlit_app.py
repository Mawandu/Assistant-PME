import streamlit as st
import os
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

# --- PATH HACK FOR LOCAL MODULES ---
# We need to add 'backend' to sys.path so we can import services
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# FIX: Import from 'database' directly because sys.path includes 'backend'.
# This matches how models.py imports it, preventing "split-brain" where we have two Base classes.
# FIX: Import from 'database' directly because sys.path includes 'backend'.
# This matches how models.py imports it, preventing "split-brain" where we have two Base classes.
from database import DATABASE_URL
import models
# Base is now in models to prevent reloading desync
Base = models.Base
from services.nlp import nlp_service
from services.query import query_service
from routers import auth

# --- DATABASE CONNECTION CACHING ---
@st.cache_resource
def get_engine():
    """Create and cache the database engine."""
    # Use conservative pool settings to avoid "Cannot assign requested address"
    # pool_pre_ping=True checks liveness but can add overhead. Keeping it for stability.
    # pool_size=5 is default, but max_overflow=10 can spike connections.
    return create_engine(
        DATABASE_URL, 
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=0,
        pool_recycle=3600
    )

def get_session():
    """Create a new session using the cached engine."""
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

# Initialize DB (Cached to avoid repeated connections)
@st.cache_resource
def init_db():
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

init_db()

# --- CONFIG ---
st.set_page_config(
    page_title="StockPilot Analytics",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLES ---
st.markdown("""
<style>
    .stChatInputContainer {
        bottom: 20px !important;
    }
    .user-msg {
        background-color: #2563EB;
        color: white;
        padding: 10px 15px;
        border-radius: 15px 15px 0 15px;
        margin: 5px 0;
        max-width: 80%;
        float: right;
        clear: both;
    }
    .ai-msg {
        background-color: #F3F4F6;
        color: #1F2937;
        padding: 10px 15px;
        border-radius: 15px 15px 15px 0;
        margin: 5px 0;
        max-width: 80%;
        float: left;
        clear: both;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        text-align: center;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #1F2937;
    }
    .metric-label {
        font-size: 14px;
        color: #6B7280;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'client_id' not in st.session_state:
    st.session_state.client_id = f"user_{os.urandom(4).hex()}"
    
if 'messages' not in st.session_state:
    st.session_state.messages = []

# --- SIDEBAR ---
with st.sidebar:
    st.title("🤖 StockPilot")
    st.markdown("Votre assistant intelligent pour la gestion de stock PME.")
    
    st.divider()
    
    st.subheader("📁 Sources de Données")
    
    # File Uploader logic (Directly calling backend logic)
    uploaded_file = st.file_uploader("Ajouter un fichier (Excel/CSV)", type=['csv', 'xlsx', 'xls'])
    
    if uploaded_file:
        if st.button("Importer les données"):
            try:
                db = get_session()
                try:
                    # Get user (create if needed)
                    user = auth.get_or_create_session_user(db, st.session_state.client_id)
                    
                    # We need to adapt the upload logic from data_source.py here
                    # Or call a simplified service function. 
                    # For quick deploy, let's implement a simplified ingestor here using pandas directly.
                    
                    with st.spinner("Analyse et import en cours..."):
                        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
                        filename = uploaded_file.name
                        
                        # Create DataSource
                        ds = models.DataSource(
                            name=filename,
                            type=models.DataSourceType.FILE_UPLOAD,
                            tenant_id=user.tenant_id,
                            status=models.DataSourceStatus.ACTIVE,
                            last_sync_status="COMPLETED"
                        )
                        db.add(ds)
                        db.commit()
                        db.refresh(ds)
                        
                        df = None
                        if filename.endswith('.csv'):
                            df = pd.read_csv(uploaded_file)
                        else:
                            df = pd.read_excel(uploaded_file)
                            
                        # Standardize columns
                        column_mapping = {
                            'product': 'name', 'nom produit': 'name', 'nom': 'name', 'designation': 'name',
                            'sku': 'sku', 'ref': 'sku', 'reference': 'sku', 'code': 'sku',
                            'category': 'category', 'catégorie': 'category', 'famille': 'category',
                            'quantity': 'quantity', 'quantité': 'quantity', 'stock': 'quantity', 'qte': 'quantity',
                            'price': 'unit_price', 'prix': 'unit_price', 'prix unitaire': 'unit_price',
                            'cost': 'cost_price', 'coût': 'cost_price', 'pamp': 'cost_price',
                            'supplier': 'supplier_name', 'fournisseur': 'supplier_name'
                        }
                        df.columns = [str(col).lower().strip() for col in df.columns]
                        df.rename(columns={k:v for k,v in column_mapping.items() if k in df.columns}, inplace=True)
                        
                        processed_count = 0
                        
                        for _, row in df.iterrows():
                            try:
                                # Helper
                                def get(col, default=None): return row[col] if col in row and pd.notna(row[col]) else default
                                
                                sku = get('sku')
                                name = get('name')
                                if not sku and not name: continue
                                sku = str(sku) if sku else f"GEN-{hash(name)}"
                                
                                # Category
                                cat_name = str(get('category', 'General'))
                                cat = db.query(models.Category).filter_by(name=cat_name, tenant_id=user.tenant_id).first()
                                if not cat:
                                    cat = models.Category(name=cat_name, tenant_id=user.tenant_id)
                                    db.add(cat)
                                    db.flush()
                                    
                                # Supplier
                                sup_name = get('supplier_name')
                                sup_id = None
                                if sup_name:
                                    sup = db.query(models.Supplier).filter_by(name=str(sup_name), tenant_id=user.tenant_id).first()
                                    if not sup:
                                        sup = models.Supplier(name=str(sup_name), tenant_id=user.tenant_id)
                                        db.add(sup)
                                        db.flush()
                                    sup_id = sup.id
                                    
                                # Product
                                prod = db.query(models.Product).filter_by(sku=sku, tenant_id=user.tenant_id).first()
                                if not prod:
                                    prod = models.Product(
                                        sku=sku,
                                        name=str(name) if name else f"Product {sku}",
                                        category_id=cat.id,
                                        supplier_id=sup_id,
                                        unit_price=float(get('unit_price', 0)),
                                        cost_price=float(get('cost_price', 0)),
                                        tenant_id=user.tenant_id,
                                        data_source_id=ds.id
                                    )
                                    db.add(prod)
                                    db.flush()
                                    
                                # Stock
                                qty = int(get('quantity', 0))
                                if qty > 0:
                                    mv = models.StockMovement(
                                        product_id=prod.id,
                                        movement_type="INBOUND",
                                        quantity=qty,
                                        notes="Initial Import via Streamlit",
                                        user_id=user.id,
                                        tenant_id=user.tenant_id
                                    )
                                    db.add(mv)
                                
                                processed_count += 1
                            except Exception as e:
                                print(f"Skipping row: {e}")
                                
                        db.commit()
                        st.success(f"✅ Importé {processed_count} articles avec succès !")
                        st.session_state.messages.append({"role": "assistant", "content": f"J'ai bien reçu vos données ({processed_count} articles). Je suis prêt à les analyser !"})
                        
                except Exception as e:
                    st.error(f"Erreur d'import: {str(e)}")
                finally:
                    db.close()
            except Exception as e:
                st.error(f"Erreur de connexion: {e}")

# --- MAIN CHAT AREA ---

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "chart" in msg:
            st.plotly_chart(msg["chart"], use_container_width=True)

# Chat Input
if prompt := st.chat_input("Posez une question sur votre stock..."):
    # Add User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate AI Response
    with st.chat_message("assistant"):
        with st.spinner("Analyse en cours..."):
            try:
                # 1. Analyse Intent (NLP)
                # Since analyze_query is async, we need to handle it. 
                # For Streamlit sync nature, we can either use asyncio.run or check if analyze_query can be sync.
                # I recently made it async. Let's force a sync wrapper.
                import asyncio
                
                # Check for existing loop
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                analysis = loop.run_until_complete(nlp_service.analyze_query(prompt))
                
                # 2. Execute Query
                db = get_session()
                user = auth.get_or_create_session_user(db, st.session_state.client_id)
                tenant_id = str(user.tenant_id)
                
                response_text = ""
                chart = None
                
                if analysis.get("intent") == "GENERAL_KNOWLEDGE":
                    response_text = loop.run_until_complete(nlp_service.generate_chat_response(prompt))
                else:
                    result = query_service.execute(db, tenant_id, analysis)
                    response_text = result['text']
                    if result.get("chart"):
                        # Ensure chart data is compatible with Plotly
                        chart_data = result["chart"]
                        # Convert frontend-ready chart struct to Plotly fig
                        # Simple logic: keys as x, values as y
                        chart_type = analysis['entities'].get('graph_type', 'bar')
                        
                        labels = chart_data['labels']
                        values = chart_data['datasets'][0]['data']
                        title = chart_data['datasets'][0]['label']
                        
                        df_chart = pd.DataFrame({'Label': labels, 'Value': values})
                        
                        if chart_type == 'pie':
                            fig = px.pie(df_chart, names='Label', values='Value', title=title)
                        else: # Default bar
                            fig = px.bar(df_chart, x='Label', y='Value', title=title)
                            
                        chart = fig
                
                st.markdown(response_text)
                if chart:
                    st.plotly_chart(chart, use_container_width=True)
                    
                # Save context
                st.session_state.messages.append({"role": "assistant", "content": response_text, "chart": chart if chart else None})
                
                db.close()
                
            except Exception as e:
                st.error(f"Une erreur est survenue: {e}")
