# scripts/seed_db.py
import sys
import os
import random
from datetime import datetime, timedelta

# Ajouter le dossier parent au path pour pouvoir importer les modules backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database import get_session, get_engine, Base
import models
import hashing

# Initialisation de la session
db = get_session()

def seed():
    print("🌱 Début du peuplement de la base de données...")

    # 1. Créer le Tenant
    tenant = db.query(models.Tenant).filter_by(company_name="Demo Corp").first()
    if not tenant:
        tenant = models.Tenant(company_name="Demo Corp", subscription_tier=models.SubscriptionTier.PROFESSIONAL)
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        print(f"✅ Tenant créé : {tenant.company_name}")
    else:
        print(f"ℹ️ Tenant existant : {tenant.company_name}")

    # 2. Créer l'Utilisateur Admin
    admin_email = "admin@demo.com"
    user = db.query(models.User).filter_by(email=admin_email).first()
    if not user:
        user = models.User(
            email=admin_email,
            password_hash=hashing.Hash.bcrypt("admin123"),
            full_name="Admin Demo",
            role=models.UserRole.ADMIN,
            tenant_id=tenant.id
        )
        db.add(user)
        db.commit()
        print(f"✅ Utilisateur créé : {admin_email} (mdp: admin123)")

    # 3. Créer les Catégories
    categories_data = ["Électronique", "Mobilier", "Vêtements", "Jouets", "Alimentation"]
    categories = {}
    for cat_name in categories_data:
        cat = db.query(models.Category).filter_by(name=cat_name, tenant_id=tenant.id).first()
        if not cat:
            cat = models.Category(name=cat_name, tenant_id=tenant.id)
            db.add(cat)
            db.commit()
            db.refresh(cat)
        categories[cat_name] = cat
    print(f"✅ {len(categories)} Catégories créées")

    # 4. Créer les Entrepôts
    warehouses_data = [("PAR", "Entrepôt Paris"), ("LYO", "Entrepôt Lyon")]
    warehouses = []
    for code, name in warehouses_data:
        wh = db.query(models.Warehouse).filter_by(code=code, tenant_id=tenant.id).first()
        if not wh:
            wh = models.Warehouse(code=code, name=name, address=f"ZI {name}", tenant_id=tenant.id)
            db.add(wh)
            db.commit()
            db.refresh(wh)
        warehouses.append(wh)
    print(f"✅ {len(warehouses)} Entrepôts créés")

    # 5. Créer les Fournisseurs
    suppliers_data = ["TechGlobal", "FurniHome", "FashionWholesale"]
    suppliers = []
    for sup_name in suppliers_data:
        sup = db.query(models.Supplier).filter_by(name=sup_name, tenant_id=tenant.id).first()
        if not sup:
            sup = models.Supplier(name=sup_name, code=sup_name[:3].upper(), tenant_id=tenant.id)
            db.add(sup)
            db.commit()
            db.refresh(sup)
        suppliers.append(sup)
    print(f"✅ {len(suppliers)} Fournisseurs créés")

    # 6. Créer des Produits
    products = []
    existing_products_count = db.query(models.Product).filter_by(tenant_id=tenant.id).count()
    if existing_products_count < 50:
        print("📦 Création de 50 produits...")
        for i in range(50):
            cat_name = random.choice(list(categories.keys()))
            sku = f"{cat_name[:3].upper()}-{1000+i}"
            price = random.uniform(10.0, 500.0)

            prod = models.Product(
                tenant_id=tenant.id,
                sku=sku,
                name=f"Produit {cat_name} {i+1}",
                description=f"Description superbe pour {cat_name} {i+1}",
                category_id=categories[cat_name].id,
                supplier_id=random.choice(suppliers).id,
                unit_price=round(price, 2),
                cost_price=round(price * 0.6, 2),
                reorder_point=random.randint(5, 20),
                reorder_quantity=random.randint(20, 100),
                lead_time_days=random.randint(3, 14)
            )
            db.add(prod)
            products.append(prod)
        db.commit()
        print(f"✅ {len(products)} Produits ajoutés")
    else:
        products = db.query(models.Product).filter_by(tenant_id=tenant.id).all()
        print("ℹ️ Produits déjà existants")

    # 7. Simuler des Mouvements de Stock (Historique)
    movements_count = db.query(models.StockMovement).filter_by(tenant_id=tenant.id).count()
    if movements_count < 200:
        print("🚚 Simulation de 200 mouvements de stock...")
        for _ in range(200):
            prod = random.choice(products)
            wh = random.choice(warehouses)

            # Type de mouvement aléatoire (plus d'entrées au début, plus de sorties ensuite)
            is_in = random.choice([True, False])
            m_type = "IN" if is_in else "OUT"
            qty = random.randint(1, 20)

            # Date aléatoire dans les 90 derniers jours
            days_ago = random.randint(0, 90)
            move_date = datetime.now() - timedelta(days=days_ago)

            movement = models.StockMovement(
                tenant_id=tenant.id,
                product_id=prod.id,
                warehouse_id=wh.id,
                movement_type=m_type,
                quantity=qty if is_in else -qty, # Négatif pour les sorties
                unit_cost=prod.cost_price,
                timestamp=move_date,
                user_id=user.id,
                notes="Simulation auto"
            )
            db.add(movement)
        db.commit()
        print("✅ Mouvements de stock simulés")
    else:
        print("ℹ️ Mouvements déjà existants")

    print("🌱 Peuplement terminé avec succès !")

if __name__ == "__main__":
    try:
        seed()
    except Exception as e:
        print(f"❌ Erreur : {e}")
    finally:
        db.close()
