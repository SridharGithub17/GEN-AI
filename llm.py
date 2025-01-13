import datetime
import lineagequeries
from schema import schema_td
# from langchain_community.llms import Bedrock
import regex as re
import Configs
from langchain.tools import tool
from langchain_core.tools import StructuredTool
from langchain.agents.agent_types import AgentType
from langchain_community.llms import Ollama
import SQLUtility
from langchain.agents.initialize import initialize_agent
from few_shot_test import construct_few_shot_prompt


class ollama_use:
     
    def __init__(self):
        # Initialization of the Strings
        self.tools = [
    
        StructuredTool.from_function(
            func=lineagequeries.get_the_results,
            name="get_the_results",
            #description=r'Read the prompt to get values from prompt. The prompt has Ordertype , transaction amount, \
            #  transaction date and transaction account ID. Ordertype can be either top to bottom or Bottom to Top Lineage. \
            #Top to Bottom Lineage has a value of 1 and Bottom to Top Lineage has a value of 2. \
            #do not give any explanation and any other quotations before or after the query. Return one single python dictionary with the parsed values'
            #description="Calculate the Lineage of data records from database given their Order type , transaction amount, transaction date and transaction account. Order type can be either Top to Bottom Lineage or Bottom to Top Lineage. Top to Bottom Lineage has a value of 2 and Bottom to Top Lineage has a value of 1"
            description="Calculate the Lineage of data records from database given their transaction reference number (txn_ref_no).\
              Order can be either Top to Bottom Lineage or Bottom to Top Lineage. Top to Bottom has a value of 2 and \
              Bottom to Top has a value of 1."
        )
         ]

        self.DBTool=[
        StructuredTool.from_function(
            func=lineagequeries.look_for_records,
            name="look_for_records",
            description="""You are an expert in converting English questions to POSTGRESQL query!
                                Below is the data base schema:{}
                since i am querying it in my local system and it is in my "DEMO2" for every 
                query before you have to add this just like below example

                question: give me src1 file table containing burger king
                SELECT * FROM "DEMO2"."SRC1_DATA" 
                do not give any explanation and any other quotations before or after the query. 
                Use LIKE wildcard when asked to look for records
                 """.format(schema_td())
        )
        ]



    def sql_prompt(schemaa_td,input_text):

        prompt=[""" You are an expert in converting English questions to POSTGRESQL query!
                                Below is the data base schema:{}
                this is the question regarding the schema: {}

                since i am querying it in my local system and it is in my "DEMO2" for every 
                query before you have to add this just like below example

                question: give me src1 file table containing burger king

                SELECT * FROM "DEMO2"."SRC1_DATA"

                do not give any explainations and any other quotations before or after the query. 
                Return just the SQL query which can be run on a database server.
                Use LIKE wildcard when asked to look for records
                
                 """.format(schemaa_td,input_text)]
        return prompt
    
    def sql_prompt_Few_Shot_Prompt(self,schemaa_td):
        prompt=""" You are an expert in converting English questions to POSTGRESQL query!
                                Below is the data base schema:{}

                since i am querying it in my local system and it is in my "DEMO2" for every 
                query before you have to add this just like below examples
                 """.format(schemaa_td)
        return prompt
    
    def lineage_query(input_text):
        print('inside lineage_query '+input_text)

        prompt=[""" You are an expert in Natural language processing. You are given text in english and you are expected to parse the input and derive Order type , 
                Transaction Amount , Transaction Date .  transaction account.
                 Order type can be either Top to Bottom Lineage or Bottom to Top Lineage.
                 Top to Bottom Lineage has a value of 1 and Bottom to Top Lineage has a value of 2.
                You will return the values in a Python Disctionary. Do not give explainations nor thoughts
                this is the question regarding the value parse: {}

                
                query before you have to add this just like below example
                question: give me Top to Bottom Lineage for Transaction Amount 10000 , Transaction Date 9 Feb 2024 for Account ID 99

              

                """.format(input_text)]
        return prompt

    def validation_prompt(input_text):
        prompt=[""" You are an expert in generating postgres sql queries given the schema, 

            This is the schema:{}

            This is the question based upon the schema:{}


            Just return pure sql code without any explanation and  quotations, donot even add any extra words before or after since i am  directly running this output directly 
            .
            """.format(schema_td(),input_text)]
        return prompt
    

    def validation_question(input_text):
        llm = Ollama(model="mistral-nemo:latest", base_url=Configs.llm_URL,temperature=0.2)
        valid_prompt=ollama_use.validation_prompt(input_text)
        a=llm.invoke(valid_prompt)
        b=list(a)
        print(b)
        for i in b[1:]:
            if i.lower()=='y':
                try:
                    a=ollama_use.call_llm(input_text)
                    return a
                except Exception as e:
                    return e             
            else:
                a=ollama_use.call_llm(input_text)
                return a
                
    def call_llm(self,input_text):
        print("Beginning of Lineage:"+str(datetime.datetime.now()))
        llm1 = Ollama(model="mistral-nemo:latest", base_url=Configs.llm_URL,temperature=0)
        if 'lineage' in input_text.lower():
            agent = initialize_agent(
             self.tools, 
             llm1, 
             agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION, 
             verbose=True
         )
            print('Invoking lineage_query')
             #a=ollama_use.lineage_query(input_text)
            result = agent.run(input_text)
            print(result)
            print("Completed: "+str(datetime.datetime.now()))
            return ''
        else:
            llm1 = Ollama(model="mistral-nemo:latest", base_url=Configs.llm_URL,temperature=0)
            
            print('Invoking sql_prompt agent')
        #     agent = initialize_agent(
        #     self.DBTool, 
        #     llm1, 
        #     agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION, 
        #     verbose=False
        # )
        #     result = agent.run({'input':input_text})
        #     print(result)
            construced_prompt = self.sql_prompt_Few_Shot_Prompt(schema_td()) 
            construced_prompt += construct_few_shot_prompt(input_text)
          
            print(construced_prompt)
            #a=ollama_use.sql_prompt(schema_td(),input_text)
            output=llm1.invoke(construced_prompt)
            print('Query returned by Model',output)
            response = SQLUtility.execute(output,None)
            lineagequeries.print_response(response,'Query Generated : \n '+output)            
            return ''

        #cleaned_query = re.sub(r"^[\s/*'\"\\]+|[\s/*'\"\\]+$", "", output)
        #print('this is cleaned query',cleaned_query)
        #execution(output)
       
    def openhermes(input_text):
        llm = Ollama(model="openhermes:latest", base_url=Configs.llm_URL)
        construced_prompt=construct_few_shot_prompt(input_text)
        print(construced_prompt)

        a=ollama_use.sql_prompt(construced_prompt)
        output=llm.invoke(a)
        print('this is query',output)
        cleaned_query = re.sub(r"^[\s/*'\"\\]+|[\s/*'\"\\]+$", "", output)
        print('this is cleaned query',cleaned_query)
        SQLUtility.execute(output)
        return output

    #b='select all rows from SRC1_FILE'
    #ollama_use.openhermes(b)
# ollama_use.calling_llm(b)


