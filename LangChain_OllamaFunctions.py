from yahoo_fin import stock_info
import json
from langchain_experimental.llms.ollama_functions import OllamaFunctions
from langchain_core.runnables import RunnableLambda
from datetime import datetime
import requests
import json
import sys
import yfinance as yf

company_name = input("""
                     Enter the Company Name to get the stock price:
                     """)
try:
    model=OllamaFunctions(model="l3custom", format="json")
else:
    model=OllamaFunction(model="llama3.1:latest", format="jason")
model = model.bind_tools(
    tools = [
        { 
            "name": "get_stock_price",
            "description": "Get the current price of the given stock",
            "parameters": {
                "type": "object",
                "properties": {
                    "stock_ticker": {
                        "type": "string",
                        "description": "The stock ticker to pass into the function"
                    }
                },
                "required": ["stock_ticker"]
            }
        },
        {
            "name": "create_meeting",
            "description": "Schedule a meeting for the user with the specified details",
            "parameters": {
                "type": "object",
                "properties": {
                    "attendee": {
                        "type": "string",
                        "description": "The person to schedule the meeting with"
                    },
                    "time": {
                        "type": "datetime",
                        "description": "The date and time of the meeting"
                    }
                },
                "required": [
                    "attendee",
                    "time"
                ]
            },
        },
    ],

)

def get_stock_price(stock_ticker: str) -> float:
    current_price = stock_info.get_live_price(stock_ticker)
    print("The current price is ", "$", round(current_price, 2))

def create_meeting(attendee, time):
    time = datetime.strptime(time, "%Y-%m-%dT%H:%M:%S")
    print(f"Scheduled a meeting with {attendee} on {time}")
functions = {
    "get_stock_price": get_stock_price,
    "create_meeting": create_meeting,
}
response = requests.post("http://localhost:11434/api/chat", json=payload)
company_info = json.loads(response.json()["message"]["content"])

def invoke_and_run(model, invoke_arg):
    result = model.invoke(invoke_arg)
    if result:
        function_call = result.additional_kwargs['function_call']
        print(function_call)
        function_name = function_call['name']
        arguments = json.loads(function_call['arguments'])
        function = functions[function_name]
        if function_name == 'get_stock_price':
            runnable = RunnableLambda(function)
            stock_ticker = arguments['stock_ticker']
            if isinstance(stock_ticker, str):
                runnable.invoke(stock_ticker)
            else:
                runnable.map().invoke(stock_ticker)
         else:
            if 'time' in arguments:
                if isinstance(arguments['time'], dict):
                    try:
                        if isinstance(arguments['time'], dict) and '$date' in arguments['time']:
                            arguments['time'] = arguments['time']['$date']
                        else:
                            arguments['time'] = arguments['time']['time']
                    except KeyError:
                        raise ValueError("The 'time' dictionary does not have a key named 'time' or '$date'")
                elif not isinstance(arguments['time'], str):
                    raise ValueError("The 'time' value must be a string")
            function(**arguments)
schema = {
    "company" : {
           "type": "string",
            "description": "Name of the company"
        },
    "ticker": {
        "type":"string",
        "description": "Ticker symbol of the company"
    }
}

payload = {
    "model": ""llama3.1:latest",
    "messages": [
        {
            "role": "system",
            "content": f"You are a helpful AI assistant. The user will enter a company name and the assistant will return the ticker symbol and current stock price of the company. Output in JSON using the schema defined here: {json.dumps(schema)}."
        },
        # add some training
        {"role": "user", "content": "Apple"},
        {"role": "assistant", "content": json.dumps({"company": "Apple", "ticker": "AAPL"})},  # Example static data
        # fire the zero shot
        {"role": "user", "content": company_name}
    ],
    "format": "json",
    "stream": False
}

# Fetch the current stock price using yfinance
ticker_symbol = company_info['ticker']
stock = yf.Ticker(ticker_symbol)
hist = stock.history(period="1d")
stock_price = hist['Close'].iloc[-1]


print(f"The current stock price of {company_info['company']} ({ticker_symbol}) is USD {stock_price}.")
invoke_and_run(model, "analyse the current stock price of company provided?")
invoke_and_run(model, f"Today is {datetime.now()}. Schedule a meeting at 3:00PM tomorrow and prepare presentation material regarding the company stock price")


--------------------------------------------------------


