import json
import ollama
import asyncio
import streamlit as st
import yfinance as yf
import pandas as pd
from rich import print
import MySQLdb
import json
from dotenv import load_dotenv
import os

# Simulates an API call to get flight times
# FUNCTION : get flight times with limited and simulated data
def get_flight_times(departure: str, arrival: str) -> str:
  flights = {
    'NYC-LAX': {'departure': '08:00 AM', 'arrival': '11:30 AM', 'duration': '5h 30m'},
    'LAX-NYC': {'departure': '02:00 PM', 'arrival': '10:30 PM', 'duration': '5h 30m'},
    'LHR-JFK': {'departure': '10:00 AM', 'arrival': '01:00 PM', 'duration': '8h 00m'},
    'JFK-LHR': {'departure': '09:00 PM', 'arrival': '09:00 AM', 'duration': '7h 00m'},
    'CDG-DXB': {'departure': '11:00 AM', 'arrival': '08:00 PM', 'duration': '6h 00m'},
    'DXB-CDG': {'departure': '03:00 AM', 'arrival': '07:30 AM', 'duration': '7h 30m'},
  }

  key = f'{departure}-{arrival}'.upper()
  print(f" INSIDE the FUNCTION : Json {json.dumps(flights.get(key, {'error': 'Flight not found'}))}")
  return json.dumps(flights.get(key, {'error': 'Flight not found'}))


#FUNCTION : Get Stock data from yFinance 
def get_stock_price(stock_symbol:str)->str:
   try:
    stock_data = yf.Ticker(stock_symbol)
    df = stock_data.history(period="1d")
    # Get the current stock price
    current_price = df['Close'].values[0]
    # Print the current stock price in JSON format
    print(json.dumps({"symbol": stock_symbol, "price":round(current_price,2)}))
    return json.dumps({"symbol": stock_symbol, "price":round(current_price,2)})
   except Exception as ex:
     return json.dumps({'error': 'Stock Symbol '+stock_symbol+' NOT FOUND '})


#FUNCTION : To get data from MySQLDB's employees table
def get_emp_details(firstname:str,lastname:str)->str:
   # Load environment variables from .env file
   load_dotenv()
   try:
        # Open database connection
        db = MySQLdb.connect(
            os.getenv("DB_HOST"),
            os.getenv("DB_USER"),
            os.getenv("DB_PASSWORD"),
            os.getenv("DB_NAME")
        )
        # Prepare a cursor object using cursor() method
        cursor = db.cursor()
        # Prepare SQL query
        sql = "SELECT * FROM employees WHERE first_name = %s AND last_name = %s"

        # Execute the SQL command
        cursor.execute(sql, (firstname, lastname))

        # Fetch one record
        record = cursor.fetchone()

        if record:
            # Convert the record to a dictionary
            record_dict = {
                "emp_no": record[0],
                "birth_date": str(record[1]),
                "first_name": record[2],
                "last_name": record[3],
                "gender": record[4],
                "hire_date": str(record[5])
            }
            # Convert the dictionary to a JSON string
            json_record = json.dumps(record_dict)
            print(json_record)
            return str(json_record)
        else:
            print(json.dumps({"message": "Record not found"}))
            return str(json.dumps({"message": "Record not found"}))

   except MySQLdb.Error as e:
        print(json.dumps({"error": str(e)}))

   finally:
        # Disconnect from server
        if db.open:
            db.close()

# Function to Call and run the model
async def run(model: str,inputQuery:str):
  #Initialize the async client
  client = ollama.AsyncClient()
  messages = [{'role': 'user', 'content': inputQuery}]
  
  #Send the query and FUNCTION description to the MODEL
  response = await client.chat(
    model=model,
    messages=messages,
    tools=[
      {
        'type': 'function',
        'function': {
          'name': 'get_flight_times',
          'description': 'Get the flight times between two cities',
          'parameters': {
            'type': 'object',
            'properties': {
              'departure': {
                'type': 'string',
                'description': 'The departure city (airport code)',
              },
              'arrival': {
                'type': 'string',
                'description': 'The arrival city (airport code)',
              },
            },
            'required': ['departure', 'arrival'],
          },
        },
      },
      {
        'type': 'function',
        'function': {
          'name': 'get_stock_price',
          'description': 'Get Current Stock price',
          'parameters': {
            'type': 'object',
            'properties': {
              'stock_symbol': {
                'type': 'string',
                'description': 'Stock Symbol to find the price',
              },
            },
            'required': ['stock_symbol'],
          },
        },
      },
      {
        'type': 'function',
        'function': {
          'name': 'get_emp_details',
          'description': 'Get Employee details',
          'parameters': {
            'type': 'object',
            'properties': {
              'firstname': {
                'type': 'string',
                'description': 'Firstname of the employee',
              },
              'lastname': {
                'type': 'string',
                'description': 'Lastname of the employee',
              },
            },
            'required': ['firstname','lastname'],
          },
        },
      },
    ],
  )

  # Add the model's response to the conversation history
  messages.append(response['message'])

  # Check if the model decided to use the provided function
  if not response['message'].get('tool_calls'):
    print("The model didn't use the function. Its response was:")
    print(response['message']['content'])
    #return response['message']['content']
    messages.append(response['message'])
    return

  # Process function calls made by the model
  if response['message'].get('tool_calls'):
    #function/tool mapping
    available_functions = {
      'get_flight_times': get_flight_times,
      'get_stock_price': get_stock_price,
      'get_emp_details': get_emp_details,
    }
    for tool in response['message']['tool_calls']:
      #function_to_call = available_functions[tool['function']['name']]
      #function_response = function_to_call(tool['function']['arguments']['departure'], tool['function']['arguments']['arrival'])
      function_to_call = available_functions[tool["function"]["name"]]
      print(f"function to call: {function_to_call}")

      if function_to_call == get_flight_times:
          function_response = function_to_call(
              tool["function"]["arguments"]["departure"],
              tool["function"]["arguments"]["arrival"],
          )
          print(f"function response: {function_response}")

      elif function_to_call == get_stock_price:
          function_response = function_to_call(
              tool["function"]["arguments"]["stock_symbol"],
          )
          print(f"function response: {function_response}")
      elif function_to_call == get_emp_details:
          function_response = function_to_call(
              tool["function"]["arguments"]["firstname"],
              tool["function"]["arguments"]["lastname"],
          )
          print(f"function response: {function_response}")

      # Add function response to the conversation
      messages.append(
        {
          'role': 'tool',
          'content': function_response,
        }
      )

  # Get final response from the model
  final_response = await client.chat(model=model, messages=messages)
  print(final_response['message']['content'])
  st.write(final_response['message']['content'])
#end of run function


#Main Streamlit UI
st.header("Ollama Tools execution (function calling)")
st.write("""
         You can ask Questions on your functions such as below
         \n What is the flight time from New York (NYC) to Los Angeles (LAX)?
         \n What is the current Stock price of AAPL?
         \n Get employee details of Georgi Facello?
         """)
input_query = st.text_input("Type your Query?")
if st.button("Gemerate"):
    if input_query:
        with st.spinner("Generating response...."):
            #Run the async function
            #asyncio.run(run('llama3.1',input_query))
            asyncio.run(run('mistral',input_query))
            
