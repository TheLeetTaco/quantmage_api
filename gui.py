import plotly.graph_objects as go
from qm_dataclass import Spell
import streamlit as st
import json

class SpellAnalyzer:
    def __init__(self):
        self.setup_page()
        self.spell_files = st.sidebar.file_uploader("Upload Spell JSONs", type="json", accept_multiple_files=True)
        self.spells = []
        if self.spell_files:
            self.spells = [self.load_spell(file) for file in self.spell_files]
            st.title("Quantmage Spell Analysis")
            self.display_calculations()
        
    def setup_page(self):
        # Set the page layout to wide
        st.set_page_config(layout="wide")
        # Inject custom CSS for background color
        st.markdown(
            """
            <style>
            .reportview-container .main .block-container{
                background-color: #1f1f1f;
                color: white;
            }
            .sidebar .sidebar-content {
                background-color: #333333;
                color: white;
            }
            .css-1d391kg {
                background-color: #333333;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

    @st.cache_data
    def load_spell(_self, file):
        data = json.load(file)
        return Spell.from_json(data)
    
    def display_metrics(self, spell):
        st.write(f"### Spell Name: {spell.name}")
        st.write(f"Assets: {', '.join(spell.assets)}")

    def plot_data(self, dates, data_dict, title, ylabel):
        fig = go.Figure()
        
        # Add traces for each line in the data dictionary
        for name, data in data_dict.items():
            temp_dates = dates[-len(data):]
            fig.add_trace(go.Scatter(
                x=temp_dates, y=data, mode='lines', name=name,
                hoverinfo='x+y', 
                hovertemplate=f'{name}: '+'%{y:.2f}<extra></extra>',
                hoverlabel=dict(namelength=-1)
            ))

        # Update layout to include spike lines and auto-range
        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title=ylabel,
            hovermode='x unified',
            spikedistance=1000,
            xaxis=dict(
                spikemode='across',
                spikethickness=1,
                spikecolor='#000000',
                spikesnap='cursor',
                rangeslider=dict(visible=True),
                type='date',
                autorange=True
            ),
            yaxis=dict(
                spikemode='across',
                spikethickness=1,
                spikecolor='#000000',
                spikesnap='cursor',
                autorange=True
            ),
            showlegend=True,
            legend=dict(
                x=1,
                y=1,
                traceorder='normal',
                font=dict(
                    family='sans-serif',
                    size=12,
                    color='white'
                ),
                bgcolor='rgba(0,0,0,0)',
                bordercolor='rgba(0,0,0,0)'
            ),
            template='plotly_dark',
            plot_bgcolor='#1f1f1f',
            paper_bgcolor='#1f1f1f'
        )

        st.plotly_chart(fig, use_container_width=True)
    
    def display_calculations(self):
        """Method used to display the calculations from the Spell Dataclass
        """
        for spell in self.spells:
            self.display_metrics(spell)

        metric_options = ["All", 
                          "Cumulative Return", 
                          "Annual Return", 
                          "Daily Win Rate", 
                          "Max Drawdown", 
                          "Volatility", 
                          "Sharpe Ratio", 
                          "Sortino Ratio"]
        selected_metric = st.sidebar.selectbox("Select Metric", metric_options, index=0)
        window_size = st.sidebar.number_input("Window Size (days)", min_value=7, value=30, step=1)
        
        def plot_it(metric):
            """Helper function to create plots of metrics

            Args:
                metric (_type_): _description_
            """
            metrics_dict = {}
            for spell in self.spells:
                metrics = spell.calculate_all_metrics(window_size)
                metrics_dict[spell.name] = metrics[metric]
                
            if metrics_dict:
                st.write(f"### {metric}")
                self.plot_data(self.spells[0].formatted_dates[-self.spells[0].number_of_days:], metrics_dict, metric, metric)

        if selected_metric == "All":
            for metric in metric_options[1:]:
                plot_it(metric)
        else:
            plot_it(selected_metric)

# Initialize and run the SpellAnalyzer
if __name__ == '__main__':
    SpellAnalyzer()
