from sqlalchemy.orm import Session
from sqlalchemy import func, case, text, literal_column
from typing import Dict, Any
import models

class QueryService:
    def execute(self, db: Session, tenant_id: str, nlp_result: dict) -> Dict[str, Any]:
        """
        Transforme l'intention NLP en requête SQLAlchemy complexe.
        """
        intent = nlp_result.get("intent")
        entities = nlp_result.get("entities", {})
        
        print(f"   [QueryService] Processing Intent: {intent} | Entities: {entities}")

        if intent == "LIST_PRODUCTS":
            return self._handle_list_products(db, tenant_id, entities)

        elif intent == "GET_STATS":
            return self._handle_get_stats(db, tenant_id, entities)

        elif intent == "SEARCH_PRODUCT":
            product_name = entities.get("product_name", "")
            return self._handle_search_product(db, tenant_id, product_name, entities)
            
        elif intent == "LIST_SUPPLIERS":
            return self._handle_list_suppliers(db, tenant_id, entities)
            
        elif intent == "SUPPLIER_STATS":
            return self._handle_supplier_stats(db, tenant_id)
            
        elif intent == "PLOT_CHART":
            return self._handle_plot_chart(db, tenant_id, entities)

        elif intent == "unknown":
            return {"text": "Je n'ai pas bien compris votre demande. Essayez de reformuler (ex: 'Produits en rupture', 'Statistiques')."}

        return {"text": f"Je comprends l'intention '{intent}', mais je ne sais pas encore la traiter."}

    def _get_stock_query(self, db: Session, tenant_id: str):
        """
        Helper: Crée une requête de base qui calcule le stock actuel pour chaque produit.
        Stock = Somme(quantity) dans la table StockMovement.
        """
        stock_subquery = (
            db.query(
                models.StockMovement.product_id,
                func.sum(models.StockMovement.quantity).label("current_stock")
            )
            .filter(models.StockMovement.tenant_id == tenant_id)
            .group_by(models.StockMovement.product_id)
            .subquery()
        )

        query = (
            db.query(
                models.Product,
                models.Category.name.label("category_name"),
                models.Supplier.name.label("supplier_name"),
                func.coalesce(stock_subquery.c.current_stock, 0).label("stock_level")
            )
            .join(models.Category, models.Category.id == models.Product.category_id)
            .outerjoin(models.Supplier, models.Supplier.id == models.Product.supplier_id)
            .outerjoin(stock_subquery, models.Product.id == stock_subquery.c.product_id)
            .filter(models.Product.tenant_id == tenant_id)
        )
        return query

    def _handle_list_products(self, db: Session, tenant_id: str, entities: dict) -> str:
        query = self._get_stock_query(db, tenant_id)
        
        category_filter = entities.get("category")
        if category_filter:
            query = query.filter(models.Category.name.ilike(f"%{category_filter}%"))
            
        supplier_filter = entities.get("supplier_name")
        if supplier_filter:
            query = query.filter(models.Supplier.name.ilike(f"%{supplier_filter}%"))

        status_filter = entities.get("filter_status")
        
        # Sorting
        sort_field = entities.get("sort_field")
        sort_order = entities.get("sort_order")
        
        if sort_field == "price":
            if sort_order == "DESC":
                query = query.order_by(models.Product.unit_price.desc())
            else:
                query = query.order_by(models.Product.unit_price.asc())
        elif sort_field == "quantity":
             if sort_order == "DESC":
                query = query.order_by(text("stock_level DESC"))
             else:
                query = query.order_by(text("stock_level ASC"))
        
        filtered_results = []
        
        all_results = query.limit(50).all() 

        for product, cat_name, supplier_name, stock in all_results:
            include = True
            
            if status_filter == "OUT_OF_STOCK":
                if stock > 0: include = False
            elif status_filter == "LOW_STOCK":
                threshold = product.reorder_point if product.reorder_point else 5
                if stock > threshold: include = False
            elif status_filter == "ACTIVE":
                if stock <= 0: include = False
            
            if include:
                filtered_results.append((product, cat_name, supplier_name, stock))

        if not filtered_results:
            msg = "Aucun produit trouvé"
            if category_filter: msg += f" dans la catégorie '{category_filter}'"
            if status_filter == "OUT_OF_STOCK": msg += " en rupture de stock"
            return {"text": msg + "."}

        response = f"Voici les produits trouvés ({len(filtered_results)}) :\n"
        for prod, cat, supp, stock in filtered_results[:10]:
            icon = "🔴" if stock <= 0 else "🟠" if stock < 10 else "🟢"
            supp_str = f" | Fournisseur: {supp}" if supp else ""
            response += f"{icon} **{prod.name}** ({cat})\n   Stock : {int(stock)} | Prix : {prod.unit_price}€{supp_str}\n"
        
        if len(filtered_results) > 10:
            response += f"... et {len(filtered_results) - 10} autres."
            
        return {"text": response}

    def _handle_get_stats(self, db: Session, tenant_id: str, entities: dict = {}) -> Dict[str, Any]:
        stat_type = entities.get("stat_type") # global, by_category, by_product, margin
        
        if stat_type == "by_product" or stat_type == "margin":
            # Margin Analysis
            products = db.query(models.Product).filter(
                models.Product.tenant_id == tenant_id,
                models.Product.unit_price.isnot(None),
                models.Product.cost_price.isnot(None)
            ).all()
            
            if not products:
                return {"text": "Impossible de calculer les marges : prix de vente ou coût de revient manquants pour les produits."}
                
            margins = []
            for p in products:
                margin = float(p.unit_price) - float(p.cost_price)
                if p.unit_price > 0:
                    margin_percent = (margin / float(p.unit_price)) * 100
                else:
                    margin_percent = 0
                margins.append({
                    "name": p.name,
                    "margin": margin,
                    "margin_percent": margin_percent,
                    "price": float(p.unit_price),
                    "cost": float(p.cost_price)
                })
            
            # Sort by margin desc
            margins.sort(key=lambda x: x["margin"], reverse=True)
            top_5 = margins[:5]
            avg_margin = sum(m["margin"] for m in margins) / len(margins)
            
            chart_data = [{"product": m["name"], "margin": m["margin"]} for m in top_5]
            
            from services.visualization import viz_service 
            chart_config = viz_service.create_bar_chart(
                data=chart_data,
                x_key="product",
                y_key="margin",
                title="Top 5 Produits par Marge (Unit)",
                x_label="Produit",
                y_label="Marge (€)"
            )
            
            response = f"**Analyse de Marge** :\nMarge moyenne par produit : {avg_margin:.2f}€.\n\nTop 5 produits les plus rentables :\n"
            for m in top_5:
                response += f"- {m['name']} : Marge {m['margin']:.2f}€ ({m['margin_percent']:.1f}%)\n"
                
            return {
                "text": response,
                "chart": chart_config
            }

        # Default Global Stats
        product_count = db.query(models.Product).filter_by(tenant_id=tenant_id).count()
        stats_by_category = (
            db.query(models.Category.name, func.count(models.Product.id).label("count"))
            .join(models.Product, models.Product.category_id == models.Category.id)
            .filter(models.Category.tenant_id == tenant_id)
            .group_by(models.Category.name)
            .all()
        )
        
        chart_data = [{"category": name, "count": count} for name, count in stats_by_category]

        from services.visualization import viz_service 
        chart_config = viz_service.create_bar_chart(
            data=chart_data,
            x_key="category",
            y_key="count",
            title="Nombre de produits par Catégorie",
            x_label="Catégorie",
            y_label="Nombre de produits"
        )

        return {
            "text": f" **Statistiques Globales** : Nous avons {product_count} produits répartis dans {len(chart_data)} catégories.",
            "chart": chart_config
        }

    def _handle_search_product(self, db: Session, tenant_id: str, search_term: str, entities: dict) -> Dict[str, Any]:
        query = self._get_stock_query(db, tenant_id)
        
        # Superlative handling (e.g., "le plus cher", "le plus disponible")
        sort_field = entities.get("sort_field")
        sort_order = entities.get("sort_order")
        
        # If the user asks for "le produit le plus cher", the search_term might be "produit" or "le plus cher"
        # If we have a sort_order, it's likely a superlative query, so we should ignore the search term 
        # unless it looks like a specific product name. Simple heuristic: if sort_order is set, prioritize sort.
        if sort_order:
             # Use literal_column to refer to the label "stock_level" from the SELECT clause
             order_clause = None
             if sort_field == "price":
                 order_clause = models.Product.unit_price.desc() if sort_order == "DESC" else models.Product.unit_price.asc()
             elif sort_field == "quantity":
                 order_clause = literal_column("stock_level").desc() if sort_order == "DESC" else literal_column("stock_level").asc()
             
             if order_clause is not None:
                 results = query.order_by(order_clause).limit(1).all()
                 if results:
                     prod, cat, supp, stock = results[0]
                     supp_str = f" (Fournisseur: {supp})" if supp else ""
                     price_str = f", Prix: {prod.unit_price}€" if prod.unit_price else ""
                     return {"text": f"Le produit le { 'plus' if sort_order == 'DESC' else 'moins' } { 'cher' if sort_field == 'price' else 'disponible' } est **{prod.name}** ({cat}){supp_str}.\nStock: {int(stock)}{price_str}"}
                 else:
                     return {"text": "Aucun produit trouvé."}
        
        if not search_term:
            return {"text": "Quel produit cherchez-vous ?"}
            
        # Tiered Search Logic: Exact > StartsWith > Contains
        # 1. Exact Match
        results = query.filter(models.Product.name.ilike(search_term)).all()
        
        # 2. Starts With (if no exact)
        if not results:
             results = query.filter(models.Product.name.ilike(f"{search_term}%")).all()
             
        # 3. Contains (if still nothing)
        if not results:
             results = query.filter(models.Product.name.ilike(f"%{search_term}%")).limit(10).all()

        if not results:
            return {"text": f"Je n'ai pas trouvé de produit correspondant à '{search_term}'."}

        response = f"Résultats pour '{search_term}' :\n"
        for prod, cat, supp, stock in results[:10]: # Limit display
            supp_str = f" via {supp}" if supp else ""
            response += f"{'🟢' if stock > 10 else '🔴'} **{prod.name}** ({cat}){supp_str} : {int(stock)} en stock\n"
            
        if len(results) > 10:
            response += f"... et {len(results) - 10} autres."
            
        return {"text": response}

    def _handle_list_suppliers(self, db: Session, tenant_id: str, entities: dict) -> Dict[str, Any]:
        category_filter = entities.get("category")
        
        query = db.query(models.Supplier).filter(models.Supplier.tenant_id == tenant_id)
        
        if category_filter:
            # Find suppliers who have products in this category
            query = (
                query.join(models.Product, models.Product.supplier_id == models.Supplier.id)
                .join(models.Category, models.Category.id == models.Product.category_id)
                .filter(models.Category.name.ilike(f"%{category_filter}%"))
                .distinct()
            )
            
        suppliers = query.limit(20).all()
        
        if not suppliers:
            msg = "Aucun fournisseur trouvé"
            if category_filter: msg += f" pour la catégorie '{category_filter}'"
            return {"text": msg + "."}
            
        response = f"Voici les fournisseurs trouvés ({len(suppliers)})"
        if category_filter: response += f" pour '{category_filter}'"
        response += " :\n"
        
        for s in suppliers:
             response += f"- **{s.name}**\n"
             
        return {"text": response}

    def _handle_supplier_stats(self, db: Session, tenant_id: str) -> Dict[str, Any]:
        # Top 10 suppliers by product count
        stats = (
            db.query(models.Supplier.name, func.count(models.Product.id).label("count"))
            .join(models.Product, models.Product.supplier_id == models.Supplier.id)
            .filter(models.Supplier.tenant_id == tenant_id)
            .group_by(models.Supplier.name)
            .order_by(func.count(models.Product.id).desc())
            .limit(10)
            .all()
        )
        
        if not stats:
             return {"text": "Pas assez de données pour les statistiques fournisseurs."}
             
        chart_data = [{"supplier": name, "count": count} for name, count in stats]
        
        from services.visualization import viz_service 
        chart_config = viz_service.create_bar_chart(
            data=chart_data,
            x_key="supplier",
            y_key="count",
            title="Top Fournisseurs (nombre de produits)",
            x_label="Fournisseur",
            y_label="Nombre de produits"
        )
        
        top_supplier = stats[0][0] if stats else "N/A"
        return {
            "text": f"Voici les fournisseurs avec le plus de produits. Le top est **{top_supplier}**.",
            "chart": chart_config
        }

    def _handle_plot_chart(self, db: Session, tenant_id: str, entities: dict) -> Dict[str, Any]:
        stat_type = entities.get("stat_type")
        graph_type = entities.get("graph_type")
        
        # Intelligent Defaulting
        if not stat_type:
            if graph_type == "histogram":
                stat_type = "by_product" # Price distribution usually involves products
            elif graph_type == "pie":
                stat_type = "by_category"
            else:
                stat_type = "by_category" # Fallback if nothing known
        
        from services.visualization import viz_service
        
        if stat_type == "by_category":
             # If user explicitly asked for Pie or no type specified, default to Pie for categories?
             # Or stick to existing get_stats which might return text.
             # Let's enforce a Category Chart.
             
             # Get category distribution
             stats = (
                db.query(models.Category.name, func.count(models.Product.id).label("count"))
                .join(models.Product, models.Product.category_id == models.Category.id)
                .filter(models.Category.tenant_id == tenant_id)
                .group_by(models.Category.name)
                .all()
             )
             chart_data = [{"category": name, "count": count} for name, count in stats]
             
             graph_type = entities.get("graph_type", "pie")
             
             if graph_type == "bar":
                 chart_config = viz_service.create_bar_chart(
                    data=chart_data, x_key="category", y_key="count",
                    title="Répartition par Catégorie", x_label="Catégorie", y_label="Nombre"
                 )
             else:
                 chart_config = viz_service.create_pie_chart(
                    data=chart_data, labels_key="category", values_key="count",
                    title="Répartition du Stock par Catégorie"
                 )
                 
             return {
                 "text": "Voici la répartition du stock par catégorie.",
                 "chart": chart_config
             }

        elif stat_type == "by_supplier":
             return self._handle_supplier_stats(db, tenant_id)
             
        elif stat_type == "by_product":
            # Check if user wants Price Distribution (Histogram)
            # NLP entity 'graph_type': 'histogram' or just heuristic
            graph_type = entities.get("graph_type")
            
            if graph_type == "histogram":
                # Price distribution buckets
                products = db.query(models.Product.unit_price).filter(models.Product.tenant_id == tenant_id).all()
                prices = [p.unit_price for p in products if p.unit_price is not None]
                if not prices: return {"text": "Pas de données de prix."}
                
                # Basic binning
                import math
                min_p, max_p = min(prices), max(prices)
                if min_p == max_p: bins = [min_p]
                else: 
                     # 5 bins
                     step = (max_p - min_p) / 5
                     bins = [min_p + i*step for i in range(6)]
                
                # Count
                hist_data = [{"range": f"{int(bins[i])}-{int(bins[i+1])}€", "count": 0} for i in range(5)]
                for p in prices:
                    for i in range(5):
                        if bins[i] <= p < bins[i+1]:
                            hist_data[i]["count"] += 1
                            break
                        elif i == 4 and p >= bins[4]: # Last bin inclusive
                            hist_data[i]["count"] += 1
                            
                chart_config = viz_service.create_bar_chart(
                    data=hist_data, x_key="range", y_key="count",
                    title="Distribution des Prix", x_label="Plage de prix", y_label="Nombre de produits"
                )
                return {
                    "text": "Voici la distribution des prix de vos produits.",
                    "chart": chart_config
                }
            
            # Default: Bar chart of top products by price/stock
            query = self._get_stock_query(db, tenant_id).limit(20)
            results = query.all()
            
            # Decide what to plot based on sort_field or default to price/stock? 
            # User said "graphique du prix produit" -> implied price
            
            chart_data = []
            for prod, cat, supp, stock in results:
                chart_data.append({
                    "name": prod.name,
                    "price": float(prod.unit_price) if prod.unit_price else 0,
                    "stock": int(stock)
                })
            
            chart_config = viz_service.create_bar_chart(
                data=chart_data,
                x_key="name",
                y_key="price", # Defaulting to price as per user request example
                title="Prix des Produits (Top 20)",
                x_label="Produit",
                y_label="Prix Unitaire (€)"
            )
            
            return {
                "text": "Voici le graphique des prix pour les premiers produits.",
                "chart": chart_config
            }
            
        return {"text": "Je ne peux pas encore générer ce type de graphique."}

query_service = QueryService()