# services/visualization.py
import json
import plotly.graph_objects as go
import plotly.utils

class VisualizationService:
    def create_bar_chart(self, data: list, x_key: str, y_key: str, title: str, x_label: str, y_label: str):
        """Génère la config JSON pour un Bar Chart"""
        x_values = [item[x_key] for item in data]
        y_values = [item[y_key] for item in data]

        fig = go.Figure(data=[
            go.Bar(name=y_label, x=x_values, y=y_values, marker_color='#2563eb') 
        ])

        fig.update_layout(
            title=title,
            xaxis_title=x_label,
            yaxis_title=y_label,
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Inter, sans-serif")
        )

        return json.loads(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder))

    def create_pie_chart(self, data: list, labels_key: str, values_key: str, title: str):
        """Génère la config JSON pour un Pie Chart"""
        labels = [item[labels_key] for item in data]
        values = [item[values_key] for item in data]

        fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
        
        fig.update_layout(title=title)
        
        return json.loads(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder))

viz_service = VisualizationService()