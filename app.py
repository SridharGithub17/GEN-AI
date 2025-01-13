import streamlit as st
from llm import ollama_use
from SQLUtility import execute
import lineagequeries
import Configs
import requests

def main():
    st.set_page_config(layout="wide")
    st.sidebar.image('td_logo.png')

    st.title("TD-Bank POC")
    with st.sidebar:
        "[Graph Database]("+Configs.Graph_URL+")"
        llm_responsecode=CheckNetworkConnectivity(Configs.llm_URL)
        if(llm_responsecode is not None and llm_responsecode.status_code==200):
            "LLM is Online"
        else:
            "LLM is Offline"
            
        graphurl_responsecode=CheckNetworkConnectivity(Configs.Graph_URL)
        if(graphurl_responsecode is not None and graphurl_responsecode.status_code==200):
            "GRAPHDB is Online"
        else:
            "GRAPHDB is Offline"
   
    input_text = st.chat_input("enter your prompt")
    print('Prompt entered :'+str(input_text))
    
    if input_text is not None:
        st.markdown('************************************************')
        Counter=1
        st.markdown('**Prompt** :'+input_text)
        llm_object=ollama_use()
        llm_output=llm_object.call_llm(input_text)
    
        st.markdown(llm_output)
        #df=execution(llm_output)
        #st.write(df)

    
def CheckNetworkConnectivity(URL):

    try:
        print('Checking URL - '+URL)
        response = requests.get(URL)
        if response.status_code==200:
            print("URL is Online.")
        else:
            print(f"Response code : {response.status_code}")
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
        print(f"Failure - Unable to establish connection: {e}.")
        response=None
    except Exception as e:
        print(f"Failure - Unknown error occurred: {e}.")
        response=None
    return response

if __name__ == "__main__":
    main()