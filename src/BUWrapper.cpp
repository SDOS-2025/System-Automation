#include <Python.h>
#include <bits/stdc++.h>
#include <iostream>
using namespace std;

class BUWrapper{
    private:
        string template1;
        string template2;

    public:
    BUWrapper(){
        //set env
        template1 = R"(
from langchain_openai import ChatOpenAI
from browser_use import Agent
import asyncio
import sys
from dotenv import load_dotenv
load_dotenv()

async def main():
    task = )";
            
        template2 = R"(    
    agent = Agent(
        task=task,
        llm=ChatOpenAI(model="gpt-4o"),
    )
    result = await agent.run()
    print(result)

asyncio.run(main())
        )";   

    }

    void setAPI(string apiKey){
        setenv("OPENAI_API_KEY", apiKey.c_str(), 1);
    }

    void execute(string input){
        string pythonCode = template1 + "\"" + input + "\"" + template2;
        
        Py_Initialize();
        PyRun_SimpleString(pythonCode.c_str());
        Py_Finalize();
        return;
    }

};