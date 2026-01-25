import panel as pn
import pandas as pd
import datetime as dt
pn.extension()
import hvplot.pandas
import holoviews as hv
from bokeh.models import HoverTool
from bokeh.models import NumeralTickFormatter

from dca_simulator.data_loader import load_price_data, load_multiple_price_data
from dca_simulator.strategies import (dca_standard, dca_DD, lump_sum, dca_sma_mom, dca_sma_mean_rev, value_averaging)
from dca_simulator.metrics import compute_KeyMetrics





####Widgets####
##text box for ticker
ticker_text = pn.widgets.TextInput(name="Ticker Text", value="AAPL", width=150)
ticker_text.visible = False #we hide it until "Manual Input" mode is selected
stock_selection_title = pn.pane.Markdown("### Select Stocks or Indices by:")

#ticker selection bar
stock_selection_mode = pn.widgets.RadioButtonGroup(options=["Ticker List", "Sector", "Manual Input"], button_type="primary")
stock_selection_mode.value = None #no mode selected at the beginning

def update_stock_selection(event):
    """Update the visibility of ticker selection widgets depending on stock selection mode"""
    mode = event.new

    ticker_list.visible = False
    sector_selector.visible = False
    ticker_text.visible = False

    if mode == "Ticker List":
        ticker_list_selector.options = top15_tickers
        ticker_list_selector.value = [] #no ticker selected at the beginning
        ticker_list.visible = True

    elif mode == "Sector":
        sector_selector.visible = True
        ticker_list.visible = True

    elif mode == "Manual Input":
        ticker_text.visible = True
stock_selection_mode.param.watch(update_stock_selection, 'value')


def get_selected_tickers(): 
    """Get the list of selected tickers based on the stock selection mode"""
    mode = stock_selection_mode.value

    if mode == "Ticker List":
        return ticker_list_selector.value
    
    elif mode == "Sector":
        return ticker_list_selector.value
    
    elif mode == "Manual Input":
        return [ticker_text.value] if ticker_text.value else []
    
    else:
        return []


#Ticker List and Ticker Selection
top15_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'BRK-B', 'META', 'UNH', 'JNJ', 'V', 'WMT', 'JPM', 'PG', 'MA']
ticker_list_selector = pn.widgets.MultiSelect(options = top15_tickers, size=10)
ticker_list = pn.Column(pn.pane.Markdown("### Select Ticker(s)"), ticker_list_selector)
ticker_list.active = []
ticker_list.visible=False #we hide it until "Ticker List" mode is selected

#Sector Selection
sector_tickers = {
                  "Information Technology": ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'ADBE', 'CRM', 'CSCO', 'INTC', 'ORCL', 'AMD', 'TXN', 'ACN', 'IBM', 'NOW', 'ADP'],
                  "Healthcare": ['UNH', 'JNJ', 'PFE', 'MRK', 'ABBV', 'TMO', 'DHR', 'BMY', 'LLY', 'AMGN', 'CVS', 'MDT', 'GILD', 'ZTS', 'CNC'],
                  "Financials": ['BRK-B', 'JPM', 'V', 'MA', 'BAC', 'WFC', 'C', 'GS', 'AXP', 'MS', 'PNC', 'SCHW', 'BK', 'USB', 'TFC'],
                  "Consumer Discretionary": ['AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'SBUX', 'LOW', 'BKNG', 'TJX', 'GM', 'F', 'EBAY', 'ROST', 'ORLY', 'YUM'],
                  "Communication Services": ['META', 'GOOGL', 'NFLX', 'DIS', 'CMCSA', 'T', 'VZ', 'ATVI', 'EA', 'TMUS', 'CHTR', 'FOXA', 'SIRI', 'TTWO', 'IPG'],
                  "Industrials": ['UNP', 'HON', 'UPS', 'BA', 'CAT', 'LMT', 'GE', 'MMM', 'DE', 'RTX', 'FDX', 'ITW', 'EMR', 'DOV', 'CME'],
                  "Consumer Staples": ['PG', 'KO', 'PEP', 'WMT', 'COST', 'MDLZ', 'CL', 'TGT', 'CVS', 'KMB', 'GIS', 'EL', 'ADM', 'SYY', 'HSY'],
                  "Energy": ['XOM', 'CVX', 'COP', 'SLB', 'EOG', 'PSX', 'VLO', 'MPC', 'KMI', 'OXY', 'HES', 'WMB', 'CPT', 'DVN', 'FTI'],
                  "Utilities": ['NEE', 'DUK', 'SO', 'D', 'AEP', 'EXC', 'SRE', 'PEG', 'ES', 'XEL', 'EIX', 'PCG', 'FE', 'PPL', 'AVANGRID'],
                  "Materials": ['LIN', 'APD', 'NEM', 'ECL', 'SHW', 'DD', 'FCX', 'MLM', 'VMC', 'PPG', 'ALB', 'CF', 'MOS', 'CTVA', 'IFF'],
                  "Real Estate": ['AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'SPG', 'DLR', 'AVB', 'EQR', 'VTR', 'WELL', 'O', 'SBAC', 'EXR', 'ESS']
                 }
sector_selector = pn.widgets.Select(name = "Select Sector", options = list(sector_tickers.keys()), value = None, width=200) 
sector_selector.visible = False #we hide it until "Sector" mode is selected


def update_sector_selection(event):
    """Update the ticker selection based on selected sector"""
    sector = event.new
    if sector is None:
        return
    
    tickers = sector_tickers[sector]
    ticker_list_selector.options = tickers
    ticker_list_selector.value = tickers[:] #select all tickers in the sector by default
sector_selector.param.watch(update_sector_selection, "value")






##date picker
start_date = pn.widgets.DatePicker(name="Start Date", value=pd.to_datetime("2010-01-01"))
end_date = pn.widgets.DatePicker(name="End Date", value=dt.date.today())

##sliders for strategy parameters
monthly_contrib = pn.widgets.IntSlider(name="Monthly Contribution ($)", start=50, end=1000, step=50, value=150)
growth_slider = pn.widgets.FloatSlider(name="Desired Monthly Growth rate (SMA)", start=0.001, end=0.01, step=0.001, value=0.006, format="0.000")
sma_period_slider = pn.widgets.IntSlider(name="SMA period", start=10, end=300, step=10, value=90)
DD_treshold_slider = pn.widgets.FloatSlider(name="Double Down Treshold", start=0.05, end=0.6, step=0.05, value=0.15)

growth_slider.visible = False #because we only want them to appear when the relevant strategy is selected
sma_period_slider.visible = False
DD_treshold_slider.visible = False 



##box checker for strategy selection
strategy_selector = pn.widgets.CheckBoxGroup(name="Strategies", 
                                             options=["DCA",  
                                                      "Double Down DCA", 
                                                       "Lump Sum", 
                                                       "Simple Moving Average DCA - Momentum",
                                                       "Simple Moving Average DCA - Mean Reversion",
                                                       "Value Averaging"],
                                                        inline=False)

#info icons
strategy_info = {
    "DCA": "Dollar-Cost Averaging: invest a fixed amount every month regardless of price",
    "Double Down DCA": "Double Down DCA: invest double the amount when the price drops more than a specified treshold",
    "Lump Sum": "Lump Sum: invest the entire amount at the start date",
    "Simple Moving Average DCA - Momentum": "invest only when the price is above the X-day Simple Moving Average, investing in momentum",
    "Simple Moving Average DCA - Mean Reversion": "invest only when the price is below the X-day Simple Moving Average, investing in mean reversion",
    "Value Averaging": "portfolio attempts to grow at a constant rate, investing more when behind target and less when ahead"
}

info_pane = pn.pane.Markdown("", sizing_mode="stretch_width")

##plot variable options
plot_var_options = {
    "Portfolio Value ($)": "portf_value",
    "Total Invested ($)": "invested_total",
    "Accumulated Shares": "shares_total",
    "Profit/Loss ($)": "profit_loss"
}

##dropdown for var plotting
plot_var = pn.widgets.Select(name="Variable to plot",
                             options=list(plot_var_options.keys()),
                             value="Portfolio Value ($)")

##run button
run_button = pn.widgets.Button(name="Run Simulation", button_type="primary")


##labels (used to display several variables such as portf_total, invested_total, etc.)
var_labels = {
    "portf_value": "Portfolio Value ($)",
    "invested_total": "Total Invested ($)",
    "shares_total": "Accumulated Shares",
    "profit_loss": "Profit/Loss ($)"}


##callback for info icons
def update_info(event):
    """Update info pane based on selected strategies"""
    old_set = set(event.old or [])
    new_set = set(event.new or [])

    added = new_set - old_set
    removed = old_set - new_set

    if added:
        strat = added.pop() #to show the newly added strategy info
        info_pane.object = f"**{strat}**: {strategy_info[strat]}"
    elif removed:
        if new_set:
            strat = list(new_set)[-1] #show info of the last remaining strategy
            info_pane.object = f"**{strat}**: {strategy_info[strat]}"
        else:
            info_pane.object = "" #no strategy selected, so we clear the info pane
strategy_selector.param.watch(update_info, 'value')


##updating the visibility of stretegy-specific sliders
def update_visibility_sliders(event):
    """Update visibility of strategy-specific sliders based on selected strategies"""
    strategies = event.new #new list of selected strategies

    monthly_contrib.visible = True 
    growth_slider.visible = False
    sma_period_slider.visible = False
    DD_treshold_slider.visible = False  

    if "Simple Moving Average DCA - Momentum" in strategies or "Simple Moving Average DCA - Mean Reversion" in strategies:
        sma_period_slider.visible = True
    if "Value Averaging" in strategies:
        growth_slider.visible = True
    if "Double Down DCA" in strategies:
        DD_treshold_slider.visible = True
strategy_selector.param.watch(update_visibility_sliders, "value")



####Output####
##preview
preview_pane = pn.pane.HoloViews(None, sizing_mode="stretch_width", height=350)

##plot
plot_pane = pn.pane.HoloViews(None, sizing_mode="stretch_width", height = 350)

##metrics comparison table
metrics_pane = pn.pane.DataFrame(None, sizing_mode="stretch_width")


#Layout
template = pn.template.FastListTemplate(title = "Retail Investment Strategy Backtester",
    sidebar=[stock_selection_title,
             stock_selection_mode,
             sector_selector,
             ticker_list,
             ticker_text, 
             start_date, 
             end_date, 
             monthly_contrib,
             DD_treshold_slider,
             sma_period_slider,
             growth_slider,
             pn.pane.Markdown("### Strategies"), 
             strategy_selector, 
             info_pane,
             pn.pane.Markdown("### Plot Settings"), 
             plot_var, 
             run_button],

    main=[pn.pane.Markdown("## Data Preview"),
          preview_pane,
          pn.pane.Markdown("## Strategy Plot"),
          plot_pane,
          pn.pane.Markdown("## Key Metrics"),
          metrics_pane])

template.servable()



####Simulation func####
def run_simulation(simulation):
    """Run the simulation with the specified parameters from the "Run Simulation" button"""

    selected_tickers = get_selected_tickers()

    selected_strategies = strategy_selector.value
    selected_var = plot_var_options[plot_var.value]
    start = start_date.value
    end = end_date.value
    monthly_c = monthly_contrib.value
    growth = growth_slider.value
    sma_p = sma_period_slider.value
    dd_tresh = DD_treshold_slider.value

    ## Data loading
    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")

    if len(selected_tickers) == 1:
        ticker = selected_tickers[0]
        df = load_price_data(ticker, start_str, end_str)

    else:
        merged = load_multiple_price_data(selected_tickers, start_str, end_str)
        if merged is None or merged.empty:
            raise ValueError("No data found for the selected tickers.")

        df = (
            merged
            .set_index("Date")[["Portfolio"]]
            .rename(columns={"Portfolio": "Close"})
        )



    ##Strategies
    results = {}

    for strat in selected_strategies:
        if strat == "DCA":
            results["DCA"] = dca_standard(df, monthly_c)
        
        elif strat == "Double Down DCA":
            results["Double Down DCA"] = dca_DD(df, monthly_c, dd_tresh)

        elif strat == "Lump Sum":
            results["Lump Sum"] = lump_sum(df, monthly_c)

        elif strat == "Simple Moving Average DCA - Momentum":
            results["SMA Momentum"] = dca_sma_mom(df, monthly_c, sma_p)
        
        elif strat == "Simple Moving Average DCA - Mean Reversion":
            results["SMA Mean Reversion"] = dca_sma_mean_rev(df, monthly_c, sma_p)
        
        elif strat == "Value Averaging":
            results["Value Averaging"] = value_averaging(df, growth, monthly_c)




    ##Plotting
    plots = []



    def format_axis(plot, element):
        """Format y-axis to show $ sign and commas for money variables """
        fmt="$0,0" if selected_var in ["portf_value", "invested_total", "profit_loss"] else "0,0"
        plot.state.yaxis.formatter = NumeralTickFormatter(format=fmt)



    for name, df_result in results.items():
        curve = df_result.hvplot(y=selected_var, 
                                 ylabel=var_labels[selected_var], 
                                 label=name, #legend label
                                 title=f"{var_labels[selected_var]} over Time",
                                 height=350, 
                                 responsive=True).opts(hooks=[format_axis]) #format y-axis to financial notation
        plots.append(curve)

    interact_plot = plots[0]
    for curve in plots[1:]:
        interact_plot *= curve #add the curves on top of each other

    plot_pane.object = interact_plot



    ##Key Metrics table
    metrics_list = []

    for name, df_result in results.items():
        try:
            metrics = compute_KeyMetrics(df_result)
            metrics["Strategy"] = name
            metrics_list.append(metrics)
        except Exception as e:
            print(f'Error computing metrics for {name}: {e}')

    
    metrics_df = pd.DataFrame(metrics_list).set_index("Strategy")
    metrics_pane.object = metrics_df



##connecting button with run_simulation
run_button.on_click(run_simulation)
