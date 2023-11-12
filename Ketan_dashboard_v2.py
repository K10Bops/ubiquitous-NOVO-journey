#==============================================================================
# Initiating
#==============================================================================

# Libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import yfinance as yf
import streamlit as  st
import requests as req
import redditwarp.SYNC
import time
import urllib

from plotly.subplots import make_subplots
from datetime import datetime, timedelta

st.set_option('deprecation.showPyplotGlobalUse', False )
st.set_page_config(layout='wide')
#==============================================================================
# HOT FIX FOR YFINANCE .INFO METHOD
# Ref: https://github.com/ranaroussi/yfinance/issues/1729
#==============================================================================



class YFinance:
    user_agent_key = "User-Agent"
    user_agent_value = ("Mozilla/5.0 (Windows NT 6.1; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/58.0.3029.110 Safari/537.36")
    
    def __init__(self, ticker):
        self.yahoo_ticker = ticker

    def __str__(self):
        return self.yahoo_ticker

    def _get_yahoo_cookie(self):
        cookie = None

        headers = {self.user_agent_key: self.user_agent_value}
        response = req.get("https://fc.yahoo.com",
                                headers=headers,
                                allow_redirects=True)

        if not response.cookies:
            raise Exception("Failed to obtain Yahoo auth cookie.")

        cookie = list(response.cookies)[0]

        return cookie

    def _get_yahoo_crumb(self, cookie):
        crumb = None

        headers = {self.user_agent_key: self.user_agent_value}

        crumb_response = req.get(
            "https://query1.finance.yahoo.com/v1/test/getcrumb",
            headers=headers,
            cookies={cookie.name: cookie.value},
            allow_redirects=True,
        )
        crumb = crumb_response.text

        if crumb is None:
            raise Exception("Failed to retrieve Yahoo crumb.")

        return crumb

    @property
    def info(self):
        # Yahoo modules doc informations :
        # https://cryptocointracker.com/yahoo-finance/yahoo-finance-api
        cookie = self._get_yahoo_cookie()
        crumb = self._get_yahoo_crumb(cookie)
        info = {}
        ret = {}

        headers = {self.user_agent_key: self.user_agent_value}

        yahoo_modules = ("assetProfile,"  # longBusinessSummary
                         "summaryDetail,"
                         "financialData,"
                         "indexTrend,"
                         "defaultKeyStatistics")

        url = ("https://query1.finance.yahoo.com/v10/finance/"
               f"quoteSummary/{self.yahoo_ticker}"
               f"?modules={urllib.parse.quote_plus(yahoo_modules)}"
               f"&ssl=true&crumb={urllib.parse.quote_plus(crumb)}")

        info_response = req.get(url,
                                     headers=headers,
                                     cookies={cookie.name: cookie.value},
                                     allow_redirects=True)

        info = info_response.json()
        info = info['quoteSummary']['result'][0]

        for mainKeys in info.keys():
            for key in info[mainKeys].keys():
                if isinstance(info[mainKeys][key], dict):
                    try:
                        ret[key] = info[mainKeys][key]['raw']
                    except (KeyError, TypeError):
                        pass
                else:
                    ret[key] = info[mainKeys][key]

        return ret
#==============================================================================

ticker_list = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]['Symbol']      
#ticker_key = "unique_ticker_key"  # Unique key for the ticker selectbox , key=ticker_key
ticker = st.sidebar.selectbox("Choose Your Stock", ticker_list)

def render_header():
    
    """
    This function render the header of the dashboard with the following items:
        - Title
        - Dashboard description
        - 3 selection boxes to select: Ticker, Start Date, End Date
    """
    
    # Add dashboard title and description
    st.title("Ketan's FINANCIAL DASHBOARD")
    col1, col2 = st.columns([1,5])
    
    # Add the selection boxes
    col1, col2, col3 = st.columns(3)  # Create 3 columns

def GetStockData(ticker, start_date, end_date):
    stock_df = yf.Ticker(ticker).history(start=start_date, end=end_date)
    stock_df.reset_index(inplace=True)  # Drop the indexes
    stock_df['Date'] = stock_df['Date'].dt.date  # Convert date-time to date
    return stock_df


st.sidebar.write('Yahoo Brands Features™')
st.sidebar.markdown('---')  # Add a horizontal line for separation


start_date = datetime.today().date() - timedelta(days=30)
end_date = datetime.today().date()
click = st.sidebar.button("Refresh")
if click:
    yf.Ticker(ticker).history(period='1d')
    GetStockData(ticker, start_date, end_date)
    st.warning("Stock data refreshed successfully!")
       

def render_tab1():
    """
    This function render the Tab 1 - Company Profile of the dashboard.
    """
    
    # Adding Columns
    col1, col2 = st.columns([6, 4])
    col3, col4, col5 = st.columns([6, 1, 1])
    
    
    # Function to get company information
    @st.cache_data
    def get_company_info(ticker):
        return YFinance(ticker).info
    start_date = datetime.today().date() - timedelta(days=30) #default dates
    end_date = datetime.today().date() #default dates
    info = get_company_info(ticker)
    stock_price = GetStockData(ticker, start_date, end_date)
    
# =============================================================================
    with col1:
        # Add a check box to show/hide data
        col2a, col2b = st.columns([0.5,2])
        with col2a:
            dropdown = st.selectbox('Chart Type',('Line', 'Candlestick', 'Areachart'))
        with col2b:
            time_range = st.radio("Select Time Range", ["1M","3M", "6M", "YTD", "1Y", "3Y", "5Y", "Max"], index=0, key="time_range",horizontal=True )
        # the time intervals is fixed at 1 Day
        show_data_table = st.checkbox("Show data table")
    
         # Determine the start and end dates based on the selected time range
        if time_range == "1M":
            start_date = datetime.today().date() - timedelta(days=30)
        elif time_range == "3M":
            start_date = datetime.today().date() - timedelta(days=90)
        elif time_range == "6M":
            start_date = datetime.today().date() - timedelta(days=180)
        elif time_range == "YTD":
            start_date = datetime(datetime.today().year, 1, 1).date()
        elif time_range == "1Y":
            start_date = datetime.today().date() - timedelta(days=365)
        elif time_range == "3Y":
            start_date = datetime.today().date() - timedelta(days=1095)
        elif time_range == "5Y":
            start_date = datetime.today().date() - timedelta(days=1825)
        else:
            start_date = stock_price['Date'].min().date() if 'stock_price' in locals() or 'stock_price' in globals() else datetime.today().date() - timedelta(days=30)
    
        if ticker != '':
            stock_price = GetStockData(ticker, start_date, end_date)
            if dropdown == "Line":
                st.write('**Line Chart of** ' + ticker)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=stock_price['Date'], y=stock_price['Close'], mode='lines', name='Stock Price', line=dict(color='Violet')))
                fig.update_layout(title='Stock Price Line Chart', xaxis_title='Date', yaxis_title='Close Price', width = 200)
                st.plotly_chart(fig, use_container_width=True)   
            elif dropdown == "Candlestick":
                st.write('**Candlestick Chart**')       
                fig = go.Figure(data=[go.Candlestick(
                x=stock_price['Date'],
                open=stock_price['Open'],
                high=stock_price['High'],
                low=stock_price['Low'],
                close=stock_price['Close'])])
                st.plotly_chart(fig, use_container_width=True)
            elif dropdown == "Areachart":
                st.write('**Area Chart of** ' + ticker)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=stock_price['Date'], y=stock_price['Close'], fill='tozeroy', mode='none', name='Stock Price'))
                fig.update_layout(title='Stock Price Area Chart', xaxis_title='Date', yaxis_title='Close Price', width = 200)
                st.plotly_chart(fig, use_container_width=True)

        if show_data_table:
            st.write('**Stock price data**')
            st.dataframe(stock_price, hide_index=True, use_container_width=True)
# =============================================================================

    with col2:
        st.write('**1.Key Statistics:**')
        col2a, col2b = st.columns(2)
        with col2a:

            company_stats1 = {}  # Dictionary
            # Manual assignment of key-value pairs
            company_stats1['Previous Close'] = info['previousClose']
            company_stats1['Open'] = info['open']
            company_stats1['Bid'] = info['bid']
            company_stats1['Ask'] = info['ask']
            company_stats1['Volume'] = info['volume']
            company_stats1['Average Daily Volume'] = info['averageDailyVolume10Day']
            company_stats1["Day's Range"] = f"{info['regularMarketDayLow']} - {info['regularMarketDayHigh']}"
            company_stats1["52 Week Range"] = f"{info['fiftyTwoWeekLow']} - {info['fiftyTwoWeekHigh']}"
                         
        #Removed the for loop and manually assigned the key value pairs,
        
        with col2b:
            
            company_stats2 = {}  # Dictionary
            # Manual assignment of key-value pairs
            company_stats2['Market Cap'] = info['marketCap']
            company_stats2['Beta (5Y Monthly)'] = info['beta']
            company_stats2['PE Ratio'] = info['pegRatio'] 
            company_stats2['PE Ratio'] = f"{info['bid']//info['trailingEps']}"
            company_stats2['EPS(TTM)'] = info['trailingEps'] 
        
        
        # for key in info_keys:
            # company_stats[info_keys[key]] = info[key]
    
        # Display the dataframes
        df1 = pd.DataFrame({'Value': pd.Series(company_stats1)})
        col2a.dataframe(df1)
        
        df2 = pd.DataFrame({'Value': pd.Series(company_stats2)})
        col2b.dataframe(df2)
        
    col3, col4 = st.columns(2)
    with col3:    
    # Show the major shareholders information
        show_major_shareholders(ticker)
    with col4:
        # Get the company information
        # Extract the first 200 words of the business summary
        limited_summary = ' '.join(info['longBusinessSummary'].split()[:200])
        
        # Display company information in Streamlit app
        st.title(f"Company Information for {ticker}")
        # st.write(f"**Company Name:** {info['LongName']}")
        st.write(f"**Industry:** {info['industry']}")
        st.write(f"**Sector:** {info['sector']}")
        
        # Show the limited business summary using Markdown + HTML
        st.write('**1. Business Summary:**')
        st.markdown('<div style="text-align: justify;">' + \
                    limited_summary + \
                    '</div><br>',
                    unsafe_allow_html=True)
        
        # Add a link for more information
        st.markdown('[Find more information on Wikipedia](https://en.wikipedia.org/)',
                    unsafe_allow_html=True)

def show_major_shareholders(ticker):
    
    # Get major shareholders information
    major_shareholders = yf.Ticker(ticker).get_institutional_holders()
    
    # Convert "Date Reported" column to string and remove timestamp
    major_shareholders['Date Reported'] = major_shareholders['Date Reported'].astype(str).str.split(' ').str[0]
    
    # Display the major shareholders information
    st.header("Major Shareholders")
    st.dataframe(major_shareholders)


        
#==============================================================================
# Tab 2
#==============================================================================
def render_tab2():
    """
    This function render the Tab 2 - Chart of the dashboard.
    """
    # Add table to show stock data
    @st.cache_data
    def GetStockData(ticker, start_date, end_date):
        stock_df = yf.Ticker(ticker).history(start=start_date, end=end_date)
        stock_df.reset_index(inplace=True)  # Drop the indexes
        stock_df['Date'] = stock_df['Date'].dt.date  # Convert date-time to date
        return stock_df
    start_date = datetime.today().date() - timedelta(days=30) #default dates
    end_date = datetime.today().date() #default dates

    stock_price = GetStockData(ticker, start_date, end_date)
    # st.sidebar.date_input("Start date", 
    # st.sidebar.date_input("End date", 
        # Add a check box to show/hide data
    col2a, col2b = st.columns([0.5,2])
    with col2a:
        dropdown = st.selectbox('Chart Type',('Line', 'Candlestick'), key='tab2chart')
    with col2b:
        time_range = st.radio("Select Time Range", [ "Date Range", "1M","3M", "6M", "YTD", "1Y", "3Y", "5Y", "Max"], index=3, key="tab2line",horizontal=True )
    # the time intervals is fixed at 1 Day
    show_data_table = st.checkbox("Show data table", key='checkboxtab2')
    if show_data_table:
        st.write('**Stock price data**')
        st.dataframe(stock_price, hide_index=True, use_container_width=True)

     # Determine the start and end dates based on the selected time range
    start_date = datetime.today().date() - timedelta(days=30) #default dates
    end_date = datetime.today().date()
    if time_range == "Date Range":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start date", format = "YYYY-MM-DD", value = datetime.today().date() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End date", format = "YYYY-MM-DD", value="today")
    elif time_range == "1M":
        start_date = datetime.today().date() - timedelta(days=30)
    elif time_range == "3M":
        start_date = datetime.today().date() - timedelta(days=90)
    elif time_range == "6M":
        start_date = datetime.today().date() - timedelta(days=180)
    elif time_range == "YTD":
        start_date = datetime(datetime.today().year, 1, 1).date()
    elif time_range == "1Y":
        start_date = datetime.today().date() - timedelta(days=365)
    elif time_range == "3Y":
        start_date = datetime.today().date() - timedelta(days=1095)
    elif time_range == "5Y":
        start_date = datetime.today().date() - timedelta(days=1825)
    else:
        start_date = stock_price['Date'].min() if 'stock_price' in locals() or 'stock_price' in globals() else datetime.today().date() - timedelta(days=30)

    if ticker != '':
        stock_price = GetStockData(ticker, start_date, end_date)
        if dropdown == "Line":
            st.write('**Stock Price Line Chart of** ' + ticker)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=stock_price['Date'], y=stock_price['Close'], mode='lines', name='Stock Price', line=dict(color='Violet')))
            fig.update_layout(title='', xaxis_title='Date', yaxis_title='Close Price', width = 200)
            sma_50 = stock_price['Close'].rolling(window=50).mean()
            fig.add_trace(go.Scatter(x=stock_price['Date'], y=sma_50, mode='lines', name='50-day SMA', line=dict(color='Orange')))
            st.plotly_chart(fig, use_container_width=True)   
        elif dropdown == "Candlestick":
            st.write('**Stock Price Candlestick Chart of** ' + ticker)       
            fig = go.Figure(data=[go.Candlestick(
            x=stock_price['Date'],
            open=stock_price['Open'],
            high=stock_price['High'],
            low=stock_price['Low'],
            close=stock_price['Close'])])
            st.plotly_chart(fig, use_container_width=True)


#==============================================================================
# Tab 3
#==============================================================================



def render_tab3():
    
    """
    This function render the Tab 3 - Chart of the dashboard.
    """
    col3a, col3b = st.columns(2)
    
    with col3a:
    
        # Dropdown for financial statements
        statement_Drop = st.selectbox('Select a Financial Statement', ['Income Statement', 'Balance Sheet', 'Cash Flow'])
    
    with col3b:
        # Dropdown for period selection
        period_type = st.selectbox('Select a Period', ['Annual', 'Quarterly'])
    
    
    
    # Fetch and display the selected financial statement
    if statement_Drop == 'Income Statement':
        if period_type == 'Annual':
            statement_data = yf.Ticker(ticker).income_stmt
        else:
            statement_data = yf.Ticker(ticker).quarterly_income_stmt
    elif statement_Drop == 'Balance Sheet':
        if period_type == 'Annual':
            statement_data = yf.Ticker(ticker).balance_sheet
        else:
            statement_data = yf.Ticker(ticker).quarterly_balance_sheet
    else:
        if period_type == 'Annual':
            statement_data = yf.Ticker(ticker).cashflow
        else:
            statement_data = yf.Ticker(ticker).quarterly_cashflow
    # Convert datetime column names to strings and remove timestamp
    statement_data.columns = statement_data.columns.astype(str).str.split(' ').str[0]
    
    st.dataframe(statement_data)
    
            
#==============================================================================
# Tab 4 monte_carlo_simulation
#==============================================================================

def render_tab4():

    def monte_carlo_simulation(closing_prices, num_simulations, num_days):
        log_returns = np.log(1 + closing_prices.pct_change()).dropna()
        last_price = closing_prices[-1]
        simulations = np.zeros((num_days, num_simulations))
        simulations[0] = last_price
    
        for t in range(1, num_days):
            drift = log_returns.mean()
            volatility = log_returns.std()
            daily_returns = np.exp(drift + volatility * np.random.randn(num_simulations))
            simulations[t] = simulations[t-1] * daily_returns

        return simulations
            
    st.header('Monte Carlo Simulation for ' + ticker + ' Stock Closing Price', divider='red')
    
    # User inputs
    
    num_simulations = st.selectbox('Number of Simulations', [200, 500, 1000])
    num_days = st.selectbox('Time Horizon (in days)', [30, 60, 90])
    
    # Fetch stock data
    stock_data = yf.download(ticker)
    closing_prices = stock_data['Close']
    
    # Perform Monte Carlo simulation
    simulated_prices = monte_carlo_simulation(closing_prices, num_simulations, num_days)
    
    # Calculate Value at Risk (VaR)
    sorted_simulations = np.sort(simulated_prices[-1])
    var_nine5 = sorted_simulations[int(0.05 * num_simulations)]
    
    # Plotting the simulation results
    st.subheader('Simulation Results')
    for i in range(num_simulations):
        plt.plot(simulated_prices[:, i])
    plt.xlabel('Time')
    plt.ylabel('Price')
    st.pyplot(plt.show())
  
    
  
#==============================================================================
# Tab 5
#==============================================================================

def render_tab5():
    def calculate_fire_number(monthly_expenses, annual_expenses, annual_savings, withdrawal_rate):
        monthly_savings = annual_savings / 12
        fire_number = (annual_expenses / withdrawal_rate) * 100
        months_to_fire = fire_number / monthly_savings
        return fire_number, months_to_fire

    def create_dual_axis_chart(years_to_fire, portfolio_values, withdrawal_rates):
        fig = go.Figure()

        # Add portfolio value trace
        fig.add_trace(go.Scatter(x=years_to_fire, y=portfolio_values, mode='lines', name='Portfolio Value', yaxis='y', line = dict(color='rgba(229, 12, 124, 0.9)') ))

        # Add withdrawal rate trace
        fig.add_trace(go.Scatter(x=years_to_fire, y=withdrawal_rates, mode='lines', name='Withdrawal Rate', yaxis='y2'))

        # Update layout for dual y-axes
        fig.update_layout(
            xaxis=dict(title='Years to Retirement'),
            yaxis=dict(title='Portfolio Value', side='left', showgrid=False, tickformat='$,.1s'),  # Format ticks as dollars with SI prefix
            yaxis2=dict(title='Withdrawal Rate (%)', overlaying='y', side='right', showgrid=False),
            legend=dict(x=0, y=1)
        )

        return fig

    st.subheader("Financial Independence Retirement Calculator & Latest News")

    # User inputs
    monthly_expenses = st.number_input("Monthly Expenses ($)", min_value=1, value=3000)
    annual_expenses = monthly_expenses * 12

    annual_savings = st.number_input("Annual Savings ($)", min_value=0, value=20000)

    withdrawal_rate = st.slider("Withdrawal Rate (%)", min_value=1, max_value=10, value=4, step=1)

    if st.button("Calculate FIRE Number"):
        fire_number, months_to_fire = calculate_fire_number(monthly_expenses, annual_expenses, annual_savings, withdrawal_rate / 100)

        st.success(f"Your FIRE Number: ${fire_number:.2f}")
        st.success(f"Time to Financial Independence: {months_to_fire:.2f} months")

        # Generate example data for the chart
        years_to_fire_example = [i for i in range(int(months_to_fire / 12) + 1)]

       # Calculate portfolio_values_example iteratively
        portfolio_values_example = []
        for i in years_to_fire_example:
            value = annual_savings / 12  
            for _ in range(12 * i):
                value += (annual_savings / 12) * (1 + (withdrawal_rate / 100))
            portfolio_values_example.append(value)


        withdrawal_rates_example = [withdrawal_rate] * len(years_to_fire_example)

        # Create dual y-axis chart
        chart= create_dual_axis_chart(years_to_fire_example, portfolio_values_example, withdrawal_rates_example)
        
        
        # Change mode to 'lines+markers' for both traces
        chart.data[0].mode = 'lines+markers'
        chart.data[1].mode = 'lines+markers'

        # Display the chart
        with st.spinner('Progress to Financial Freedom...'):
            time.sleep(5)
    
        st.plotly_chart(chart)
    
        st.success('Done!')
        
        
        
    st.divider()
 #--------------Part 1----------------------------------------------         
    col1, col2 = st.columns(2)
    client = redditwarp.SYNC.Client()
    
    # Display the first 5 submissions on the r/Fire subreddit.
    fire_submissions = client.p.subreddit.pull.hot('Fire', amount=5)
    fire_list = list(fire_submissions)
    
    fire_data = {
        'Subreddit': [f"r/{subm.subreddit.name}" for subm in fire_list],
        'Upvotes': [subm.score for subm in fire_list],
        'Title': [subm.title for subm in fire_list],
    }
    with col1:
        fire_df = pd.DataFrame(fire_data)
    
        # Display the table for r/Fire subreddit
        st.subheader("Fire News : Reddit")
        st.dataframe(fire_df, hide_index=True)
    
    # Display the first 5 submissions on the r/WorldNews subreddit.
    worldnews_submissions = client.p.subreddit.pull.hot('WorldNews', amount=5)
    worldnews_list = list(worldnews_submissions)
    
    worldnews_data = {
        'Subreddit': [f"r/{subm.subreddit.name}" for subm in worldnews_list],
        'Upvotes': [subm.score for subm in worldnews_list],
        'Title': [subm.title for subm in worldnews_list],
    }
    with col2:
        worldnews_df = pd.DataFrame(worldnews_data)
    
        # Display the table for r/WorldNews subreddit
        st.subheader("Worldnews : Reddit")
        st.dataframe(worldnews_df, hide_index=True)
    
    
    #ADD HORIZONTAL sliding news
    
# CSS for styling
css = """
<style>
.marquee {
    white-space: nowrap;
    overflow: hidden;
    box-sizing: border-box;
    animation: marquee 10s linear infinite;
}

@keyframes marquee {
    0%   { transform: translate(100%, 0); }
    100% { transform: translate(-100%, 0); }
}
</style>
"""

# Add CSS to the Streamlit app
st.markdown(css, unsafe_allow_html=True)

# News content
news_content = ["All Rights Resrved by Yahoo Brands Features"]

# Join news items with a space
news_text = " ".join(news_content)

# Display the marquee
st.markdown(f'<div class="marquee">{news_text}</div>', unsafe_allow_html=True)

#==============================================================================
# Main body
#==============================================================================




# Render the header
render_header()

# render_sidebar()

# Render the tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Summary", "Chart", "Financials", "Monte Carlo simulation", "Goal to FIRE"])
with tab1:
    render_tab1()
with tab2:
    render_tab2()
with tab3:
    render_tab3()
with tab4:
    render_tab4()
with tab5:
    render_tab5()
    
    
    
# # Customize the dashboard with CSS
# st.markdown(
#     """
#     <style>
#         .stApp {
#             background: #F0F8FF;
#             text: #000000;
#         }
#     </style>
#     """,
#     unsafe_allow_html=True,
# )

cola, colb, colc = st.columns(3,gap="medium")
with colb:  
    st.sidebar.image('yahoo_finance.png', width=100)   
    
    
###############################################################################
# END
###############################################################################
    




