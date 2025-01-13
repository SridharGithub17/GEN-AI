import os
import json
import pandas as pd
from neo4j import GraphDatabase
import plotly.graph_objects as go
import networkx as nx
import Configs

# Neo4j Connection Details
NEO4J_URI = Configs.Neo4JS_DB_Url
NEO4J_USERNAME = Configs.NEO4JS_DB_User
NEO4J_PASSWORD = Configs.NEO4JS_DB_Password
NEO4J_DATABASE = Configs.NEO4JS_DB_Name

# Set environment variables for Neo4j
os.environ["NEO4J_URI"] = NEO4J_URI
os.environ["NEO4J_USERNAME"] = NEO4J_USERNAME
os.environ["NEO4J_PASSWORD"] = NEO4J_PASSWORD
os.environ["NEO4J_DATABASE"] = NEO4J_DATABASE

# Function to filter node properties based on criteria
def filter_properties(node_data, required_amt=64001, required_dt="15-Dec-2024"):
 
    matching_records = []  # List to hold all matching records
    try:
 
        return node_data  # Return all matching records
    except json.JSONDecodeError:
        return []  # Handle cases where the data is not valid JSON

# Function to draw the graph with dynamic positions
def draw_graph(G):
    #print('=================')
    edge_x = []
    edge_y = []
    edge_text = []

    # Create edge traces
    for edge in G.edges():
        x0, y0 = G.nodes[edge[0]]['pos']
        x1, y1 = G.nodes[edge[1]]['pos']
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)  # Line break
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

        edge_text.append(G.edges[edge].get('label', ''))

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='text',
        text=edge_text,
        mode='lines'
    )

    node_x = []
    node_y = []
    node_text = []
    node_hovertext = []  # List for hover text

    # Create node traces
    for node in G.nodes():
        
        x, y = G.nodes[node]['pos']
       
        node_x.append(x)
        node_y.append(y)
        node_text.append(G.nodes[node].get('label', ''))

        # Get node data for filtering
        node_data = G.nodes[node].get('data', '')
        # print(G.nodes[node])
        # print(node)
      
       
        # Filter properties based on tran_amt and tran_dt
        matching_records = filter_properties(node_data)
      

        
        # Format hover text to show all matching records
        if len(matching_records)>0:
           
            hover_info = "".join(
                f"Transaction Amount: {matching_records.get('TRAN_AMT', 'N/A')}<br>"
                 f"Transaction Date: {matching_records.get('TRAN_DT', 'N/A')}<br>"
                 #f"Other Info: {json.dumps({k: v for k, v in matching_records.items() if k not in ['TRAN_AMT', 'TRAN_DT']}, indent=2)}"
                 
            )
        else:
            hover_info = "No matching records"
        

        node_hovertext.append(hover_info)

    node_trace = go.Scatter(
        x=node_x, 
        y=node_y,
        mode='markers+text',
        text=node_text,
        hoverinfo='text',
        hovertext=node_hovertext,
        marker=dict(
            showscale=True,
            colorscale='YlGnBu',
            size=10,
            color=[],
            line_width=2)
    )

    # Create the figure
    fig = go.Figure(data=[edge_trace, node_trace],
                     layout=go.Layout(
                        title='Graph Visualization',
                        titlefont_size=16,
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=0, l=0, r=0, t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )
    return fig

# Function to show graph in Streamlit
def get_graph_in_streamlit(default_cypher):
    # Create a Neo4j session
    print('Inside get_graph_in_streamlit')
    driver = GraphDatabase.driver(
        uri=os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
    )
    session = driver.session()


    # Fetch the graph data
    result = session.run(default_cypher)
 
    # Create a NetworkX graph
    Gr = nx.Graph()

    # Add nodes and edges from Neo4j
    for record in result:
        A = record['A']
        B = record['B']
        C = record['C']
        D = record['D']
        E = record['E']
        F = record['F']
        G = record['G']
        H = record['H']
        I = record['I']
        J = record['J']
        K = record['K']
        
 

        # Add nodes with properties (using lowercase names)
        Gr.add_node(A['name'].lower(), label=A['name'], data=A._properties)
        Gr.add_node(B['name'].lower(), label=B['name'], data=B._properties)
        Gr.add_node(C['name'].lower(), label=C['name'], data=C._properties)
        Gr.add_node(D['name'].lower(), label=D['name'], data=D._properties)
        Gr.add_node(E['name'].lower(), label=E['name'], data=E._properties)
        Gr.add_node(F['name'].lower(), label=F['name'], data=F._properties)
        Gr.add_node(G['name'].lower(), label=G['name'], data=G._properties)
        Gr.add_node(H['name'].lower(), label=H['name'], data=H._properties)
        Gr.add_node(I['name'].lower(), label=I['name'], data=I._properties)
        Gr.add_node(J['name'].lower(), label=J['name'], data=J._properties)
        Gr.add_node(K['name'].lower(), label=K['name'], data=K._properties)


        Gr.add_edge(B['name'].lower(), C['name'].lower())
        Gr.add_edge(B['name'].lower(), A['name'].lower())
        Gr.add_edge(D['name'].lower(), C['name'].lower())
        Gr.add_edge(F['name'].lower(), D['name'].lower())
        Gr.add_edge(I['name'].lower(), F['name'].lower())
        Gr.add_edge(E['name'].lower(), C['name'].lower())
        Gr.add_edge(G['name'].lower(), E['name'].lower())
        Gr.add_edge(J['name'].lower(), G['name'].lower())
        Gr.add_edge(E['name'].lower(), C['name'].lower())
        Gr.add_edge(H['name'].lower(), E['name'].lower())
        Gr.add_edge(H['name'].lower(), K['name'].lower())

        

    session.close()  # Close the session

    # Define specific positions for the nodes (all keys are now lowercase)
    pos = {

    "src1_file": (0, 0),              # Now at the bottom  
    "src2_file1": (2, 0),              # Now at the bottom
    "src2_file2": (4, 0),             # Now at the bottom
    "src1_staging_data": (0, 1),      # Moves up
    "stg_src1_kde": (0, 2),           # Moves up
    "src2_staging_data1": (2, 1),     # Moves up
    "src2_staging_data2": (4, 1),     # Moves up
    "stg_src2_kde": (3, 2),           # Moves up
    "stg_src1_stitched": (2, 3),      # Moves up
    "stg_acct_txns": (2, 4),          # Now at the top
    "fin_acct_txns": (2, 5),          # Now at the top

}

    # Assign positions to nodes using lowercase names
    for node in Gr.nodes():
        print(f"Assigning position for node: {node}")  # Debugging: Print node names
        Gr.nodes[node]['pos'] = pos.get(node, (0, 0))  # Default to (0, 0) if not specified

    fig = draw_graph(Gr)  # Draw the graph with dynamic positions
    return fig
    #st.plotly_chart(fig)  # Show the graph in Streamlit
 
