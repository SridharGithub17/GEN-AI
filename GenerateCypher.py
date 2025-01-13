# from langchain_openai import ChatOpenAI
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph
from langchain.prompts import PromptTemplate
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_community.llms import Ollama
from neo4j import GraphDatabase
from ConnectPostGres import connect_pg
import Configs
from neo4j import GraphDatabase
from ConnectPostGres import connect_pg
import pandas as pd
import numpy as np
from langchain_community.graphs import Neo4jGraph
from langchain_groq import ChatGroq
from langchain.chains import GraphCypherQAChain


#Dynanamic fewshot prompting
from langchain_community.vectorstores import Neo4jVector
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_community.embeddings import HuggingFaceEmbeddings

# from google.colab import userdata
from torch import __version__; from packaging.version import Version as V
xformers = "xformers==0.0.27" if V(__version__) < V("2.4.0") else "xformers"


# Connect to Neo4j
# neo4j_driver = GraphDatabase.driver(
#     uri=Configs.Neo4JS_DB_Url,  # Your Neo4j bolt address
#     auth=(Configs.NEO4JS_DB_User, Configs.NEO4JS_DB_Password)
# )
# session= neo4j_driver.session()

#Below way of connecting to neo4j uses APOC plugin
graph = Neo4jGraph(url=Configs.Neo4JS_DB_Url,username=Configs.NEO4JS_DB_User,password=Configs.NEO4JS_DB_Password,sanitize=True,enhanced_schema=True)

# graph.refresh_schema()
# print(graph.schema)

questions = ["List of all CSA Nodes",
             "Show me all transactions?",
             "Show me top to bottom lineage for transaction reference number of 009400040000000001490049152024038631",
             "Show me top to bottom lineage for transaction reference number of 0094000400000000435487971520240091",
             "Show me all transactions with transaction amount greater than $100"
]

CYPHER_GENERATION_TEMPLATE = """
You are an expert Neo4j Developer translating user questions into Cypher to answer questions about all transactions and corresponding lineage.
Convert the user's question based on the schema.

Schema: {schema}
Question: {question}
"""


cypher_generation_prompt = PromptTemplate(
    template=CYPHER_GENERATION_TEMPLATE,
    input_variables=["schema", "question"],
)


# llm = Ollama(model="mistral-nemo:latest", base_url=Configs.llm_URL,temperature=0.2)

llm= Ollama(model="openhermes:latest", base_url=Configs.llm_URL, temperature=0)

examples= [
    {
        "question": "show KDE1 to stitch relation for account 1108742?",
        "query": "MATCH (n:KDE1 {tran_acct1_tmp: '1108742'})-[:Extr_from_kde1_to_stich]->(p:STITCH) RETURN p LIMIT 25",
    },
    {
        "question": "show all the csa nodes ?",
        "query": "MATCH (p:CSA ) RETURN p",
    },
    {
        "question": "show all transactions above transaction amount 50 ?",
        "query": "MATCH (p:CSA ) where p.txn_amt > 50 RETURN p",
    }
]

# cypher_chain.invoke({"query": "Show me top to bottom lineage for transaction reference number of 0094000400000000441021077020241503"})

example_prompt = PromptTemplate.from_template(
    "User input: {question}\nCypher query: {query}"
)

prompt = FewShotPromptTemplate(
    examples=examples[:2],
    example_prompt=example_prompt,
    prefix="You are a Neo4j expert. Given an input question, create a syntactically correct Cypher query to run.\n\nHere is the schema information\n{schema}.\n\n Below are a number of examples of questions and their corresponding Cypher queries. Don't add any preambles, just return the correct cypher query",
    suffix="User input: {question}\nCypher query: ",
    input_variables=["question", "schema"],
)

cypher_chain = GraphCypherQAChain.from_llm(
    llm,
    graph=graph,
    cypher_prompt=cypher_generation_prompt,
    verbose=True,
    allow_dangerous_requests=True
    )

chain_with_few_shot = GraphCypherQAChain.from_llm( llm,
    graph=graph,
    cypher_prompt=cypher_generation_prompt,
    verbose=True,
    allow_dangerous_requests=True
    )


for q in questions:
    print("\n", q)
    try:
        result = chain_with_few_shot.invoke(q)['result']
        print(result)
    except:
        pass


#Dynanamic fewshot prompting

# example_selector = SemanticSimilarityExampleSelector.from_examples(
#     examples,
#     HuggingFaceEmbeddings(),
#     Neo4jVector,
#     graph=graph,
#     k=3,
#     input_keys=["question"],
# )

# example_selector.select_examples({"question": "show all transactions on fic_mis_dt = '28-May-24'?"})

# dynamic_prompt = FewShotPromptTemplate(
#     example_selector=example_selector, #previous: examples = examples[:3]
#     example_prompt=example_prompt,
#     prefix="You are a Neo4j expert. Given an input question, create a syntactically correct Cypher query to run.\n\nHere is the schema information\n{schema}.\n\nBelow are a number of examples of questions and their corresponding Cypher queries. Don't add any preambles, just return the correct cypher query",
#     suffix="User input: {question}\nCypher query: ",
#     input_variables=["question", "schema"],
# )

# print(dynamic_prompt.format(question="Where do Michael work?", schema= graph.schema))
# chain_with_dynamic_few_shot = GraphCypherQAChain.from_llm(graph=graph,
#                                                           cypher_llm=llm,
#                                                           qa_llm=llm,
#                                                           cypher_prompt=dynamic_prompt, # don't forget to change this into the dynamic_prompt
#                                                           verbose=True,
#                                                           validate_cypher = True,
#                                                           use_function_response=True
#                                                           )

# for q in questions:
#     print("\n", q)
#     try:
#         result = chain_with_dynamic_few_shot.invoke(q)['result']
#         print(result)
#     except:
#         pass