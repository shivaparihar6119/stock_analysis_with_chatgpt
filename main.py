import openai
import json
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd
import yfinance as yf

openai.api_key = open('API_KEY', 'r').read()


def get_stock_price(ticker, window='1y'):
    return str(yf.Ticker(ticker).history(period=window).iloc[-1].Close)


def cal_sma(ticker, window):
    data = yf.Ticker(ticker).history(period='1y').Close
    return str(data.rolling(window=window).mean().iloc[-1])


def cal_ema(ticker, window):
    data = yf.Ticker(ticker).history(period='1y').Close
    return str(data.ewm(span=window, adjust=False).mean().iloc[-1])


def cal_rsi(ticker, window):
    df = yf.Ticker(ticker).history(period='1y')

    # Calculate daily price changes
    df['Price Change'] = df['Close'].diff()

    # Calculate gain and loss for each day
    df['Gain'] = df['Price Change'].apply(lambda x: x if x > 0 else 0)
    df['Loss'] = df['Price Change'].apply(lambda x: abs(x) if x < 0 else 0)

    # Calculate average gain and average loss over the RSI period
    df['Avg Gain'] = df['Gain'].rolling(window=window).mean()
    df['Avg Loss'] = df['Loss'].rolling(window=window).mean()

    # Calculate RS (Relative Strength)
    df['RS'] = df['Avg Gain'] / df['Avg Loss']

    # Calculate RSI using the RS
    df['RSI'] = 100 - (100 / (1 + df['RS']))

    return str(df['RSI'].dropna())


def cal_MACD(ticker):
    data = yf.Ticker(ticker).history(period='1y').Close
    ema_long = data.ewm(span=26, adjust=False).mean()
    ema_short = data.ewm(span=12, adjust=False).mean()
    MAC_D = ema_short - ema_long

    signal = MAC_D.ewm(span=9, adjust=False).mean()
    MAC_D_histogram = MAC_D - signal

    return f'{MAC_D[-1]},{signal[-1]},{MAC_D_histogram[-1]}'


def plot_sp(ticker, start_date, end_date):
    data = yf.Ticker(ticker).history(start=start_date, end=end_date)
    plt.figure(figsize=(10, 5))
    plt.plot(data.index, data.Close)
    plt.title(f'{ticker} Stock Price from {start_date} to {end_date}')
    plt.xlabel('Date')
    plt.ylabel('Stock Price')
    plt.grid(True)
    plt.savefig('stock.png')
    plt.close()


functions = [
    {
        'name': 'get_stock_price',
        'description': 'Gets the latest stock price of a company through given ticker symbol',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'stock ticker symbol for the given company in the input(for example AAPL fox Apple)'
                },
                'window': {
                    'type': 'integer',
                    'description': 'The time to consider for calculating Stock price.'
                }
            },
            'required': ['ticker']

        },

    },
    {
        'name': 'cal_sma',
        'description': 'Calculates the Simple Moving Average (SMA) for a given ticker symbol for company and period',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'stock ticker symbol for the given company in the input(for'
                                   'example AAPL for Apple).'
                },
                'window': {
                    'type': 'integer',
                    'description': 'The time to consider for calculating SMA.'
                }
            },
            'required': ['ticker', 'window']
        },
    },
    {
        'name': 'cal_ema',
        'description': 'Calculates the Exponential Moving Average (EMA) for a given ticker symbol '
                       'for company and a window',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'stock ticker symbol for the given company in the input(for'
                                   'example AAPL for Apple).'
                },
                'window': {
                    'type': 'integer',
                    'description': 'The time to consider for calculating EMA.'
                }
            },
            'required': ['ticker', 'window']
        },
    },
    {
        'name': 'cal_rsi',
        'description': 'Calculates the Relative Strength Index for a given ticker symbol '
                       'for company and a window',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'stock ticker symbol for the given company in the input(for'
                                   'example AAPL for Apple).'
                },
                'window': {
                    'type': 'integer',
                    'description': 'The time for RSI period.'
                }
            },
            'required': ['ticker', 'window']
        },
    },
    {
        'name': 'cal_MACD',
        'description': 'Calculates the MACD for a given ticker symbol and a short window and a long window.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'stock ticker symbol for the given company in the input(for'
                                   'example AAPL for Apple).'
                }
            },
            'required': ['ticker']
        },
    },
    {
        'name': 'plot_sp',
        'description': 'PLot the stock price for a given ticker of a company over the last year.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'stock ticker symbol for the given company in the input(for'
                                   'example AAPL for Apple).'
                },
                'start_date': {
                    'type': 'string',
                    'description': 'start date for retrieving stock data'
                },
                'end_date': {
                    'type': 'string',
                    'description': 'end date for retrieving stock data'
                }
            },
            'required': ['ticker', 'start_date', 'end_date']
        },
    },
]

available_functions = {
    'get_stock_price': get_stock_price,
    'cal_sma': cal_sma,
    'cal_ema': cal_ema,
    'cal_rsi': cal_rsi,
    'cal_MACD': cal_MACD,
    'plot_sp': plot_sp
}

if 'messages' not in st.session_state:
    st.session_state['messages'] = []

st.title('Stock Analysis Chatbot Assistant')

user_input = st.text_input('Your Input:')

if user_input:
    try:
        st.session_state['messages'].append({'role': 'user', 'content': f'{user_input}'})

        respond = openai.ChatCompletion.create(
            model='gpt-3.5-turbo-0613',
            messages=st.session_state['messages'],
            functions=functions,
            function_call='auto'
        )

        response_message = respond['choices'][0]['message']

        if response_message.get('function_call'):
            function_name = response_message['function_call']['name']
            function_args = json.loads(response_message['function_call']['arguments'])

            if function_name in ['cal_MACD']:
                args_dict = {'ticker': function_args.get('ticker')}
            elif function_name in ['cal_sma', 'cal_ema', 'get_stock_price', 'cal_rsi']:
                args_dict = {'ticker': function_args.get('ticker'), 'window': function_args.get('window')}
            elif function_name in ['plot_sp']:
                args_dict = {'ticker': function_args.get('ticker'), 'start_date': function_args.get('start_date'),
                             'end_date': function_args.get('end_date')}
            function_to_call = available_functions[function_name]
            function_response = function_to_call(**args_dict)

            if (function_name == 'plot_sp'):
                st.image('stock.png')
            else:
                st.session_state['messages'].append(response_message)
                st.session_state['messages'].append({
                    'role': 'function',
                    'name': function_name,
                    'content': function_response
                })
                second_response = openai.ChatCompletion.create(
                    model='gpt-3.5-turbo-0613',
                    messages=st.session_state['messages']
                )
                st.write(second_response['choices'][0]['message']['content'])
                st.session_state['messages'].append(
                    {'role': 'assistant',
                     'content': second_response['choices'][0]['message']['content']
                     })

        else:
            st.write(response_message['content'])
            st.session_state['messages'].append(
                {
                    'role': 'assistant',
                    'content': response_message['content']
                }
            )
    except Exception as e:
        raise e
