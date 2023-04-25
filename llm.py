
from langchain import PromptTemplate, OpenAI, LLMChain
from langchain.memory import ConversationBufferWindowMemory
import re

class ShoppingLLM:

    def __init__(self):
        template = """You are a friendly, conversational retail shopping assistant AI. Your goal is to show the shopper whats available, help them 
        find what they want, and answer any questions. It's ok if you dont know the answer.

        In order to satisfy the goal of showing the shopper what's available, you will first need to collect some information. The information that
        you need to collect from the shopper before assisting them is the following:
        - short description of the product, for example, red nike tennis shoes
        - store name, for example, nike
        - category of products in that store, for example, shoes

        Once you think you have collected the product description, store name, and category from the shopper, you should make the 
        following exact statement contained within the | characters replacing product description, store, and category with the 
        product description, store, and category you think you collected, but say nothing else when you make this statement as it will be used as input for the system:

        |product description, store, category|


        Use the following pieces of context to answer the users question. 
        If you dont know the answer, just say that you dont know, dont try to make up an answer.

        Context:
        {history}
        Human shopper: {human_input}
        Assistant:"""

        shopping_assistant_memory_prompt = PromptTemplate(
            input_variables=["history", "human_input"], 
            template=template
        )

        self.chatgpt_chain = LLMChain(
            llm=OpenAI(temperature=0), 
            prompt=shopping_assistant_memory_prompt, 
            verbose=True, 
            memory=ConversationBufferWindowMemory(k=5),
        )

    def get_output(self, user_input):
        output = self.chatgpt_chain.predict(human_input=user_input)
        return (
            output.split("|")[0],
            self._extract_store_and_category(output)
        )

    #TODO handle condition where only product or store or category or none provided 
    def _extract_store_and_category(self, input_str):
        result = {
            "product": None,
            "store": None,
            "category": None
        }

        start = input_str.find('|')
        end = input_str.find('|', start + 1)
        
        if start == -1 or end == -1:
            return result
        
        inner_str = input_str[start + 1:end].strip()
        s1, s2, s3 = [s.strip() for s in inner_str.split(',')]
        
        return {
            "product": s1.lower(),
            "store": s2.lower(),
            "category": s3.lower()
        }