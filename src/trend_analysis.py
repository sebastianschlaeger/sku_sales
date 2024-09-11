import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.tsa.seasonal import seasonal_decompose
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def calculate_trend(data):
    data = data.sort_values('Date')
    data['Days'] = (data['Date'] - data['Date'].min()).dt.days
    
    # Clean the SKU column
    data['SKU'] = data['SKU'].astype(str).str.split('-').str[0]

    # Handle cases where there's not enough data or all x values are identical
    if len(data) < 2 or data['Days'].nunique() == 1:
        return 0

    try:
        long_term_slope, _, _, _, _ = stats.linregress(data['Days'], data['Quantity'])
    except ValueError:
        long_term_slope = 0

    last_30_days = data[data['Date'] >= (data['Date'].max() - pd.Timedelta(days=30))]
    if len(last_30_days) > 1 and last_30_days['Days'].nunique() > 1:
        try:
            short_term_slope, _, _, _, _ = stats.linregress(last_30_days['Days'], last_30_days['Quantity'])
        except ValueError:
            short_term_slope = 0
    else:
        short_term_slope = 0

    overall_trend = 0.7 * long_term_slope + 0.3 * short_term_slope

    return overall_trend

def calculate_seasonality(data):
    data = data.sort_values('Date')
    data = data.set_index('Date')
    
    date_range = pd.date_range(start=data.index.min(), end=data.index.max(), freq='D')
    data = data.reindex(date_range).fillna(0)
    data = data.infer_objects(copy=False)
    
    if len(data) >= 14:
        result = seasonal_decompose(data['Quantity'], model='additive', period=7)
        seasonality = result.seasonal
    else:
        seasonality = pd.Series(0, index=range(7))

    return seasonality

def smooth_data(data, window=14):
    data = data.sort_values('Date')
    data['SmoothQuantity'] = data['Quantity'].rolling(window=window, min_periods=1).mean()
    return data

def create_forecast(data, days=60):
    data = data.sort_values('Date')
    last_date = data['Date'].max()
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=days)

    trend = calculate_trend(data)
    seasonality = calculate_seasonality(data)

    forecast = pd.DataFrame({'Date': future_dates})
    forecast['Trend'] = np.arange(1, len(forecast) + 1) * trend
    forecast['Seasonality'] = [seasonality.iloc[d.dayofweek] for d in forecast['Date']]
    forecast['Forecast'] = forecast['Trend'] + forecast['Seasonality']

    forecast['LowerCI'] = forecast['Forecast'] - 2 * data['Quantity'].std()
    forecast['UpperCI'] = forecast['Forecast'] + 2 * data['Quantity'].std()

    return forecast

def analyze_sku(sku_data):
    try:
        sku_data['Date'] = pd.to_datetime(sku_data['Date'])
        sku_data = sku_data.set_index('Date')
        
        # Clean the SKU column
        sku_data['SKU'] = sku_data['SKU'].astype(str).str.split('-').str[0]
        
        sku_data = sku_data.resample('D').sum().astype('float64')
        
        if len(sku_data) >= 14:  # Ensure we have enough data for decomposition
            result = seasonal_decompose(sku_data['Quantity'], model='additive', period=7)
            seasonality = result.seasonal
            trend = result.trend
        else:
            seasonality = pd.Series(0, index=sku_data.index)
            trend = sku_data['Quantity'].rolling(window=min(7, len(sku_data)), min_periods=1).mean()
        
        overall_trend = calculate_trend(sku_data.reset_index())
        
        # Add smoothed data
        smoothed_data = smooth_data(sku_data.reset_index())
        
        # Create forecast
        forecast = create_forecast(sku_data.reset_index())
        
        return {
            'seasonality': seasonality,
            'trend': trend,
            'overall_trend': overall_trend,
            'smoothed_data': smoothed_data,
            'forecast': forecast
        }
    except Exception as e:
        logger.error(f"Error in analyze_sku: {str(e)}")
        return {
            'seasonality': pd.Series(),
            'trend': pd.Series(),
            'overall_trend': 0,
            'smoothed_data': pd.DataFrame(),
            'forecast': pd.DataFrame()
        }

def analyze_all_skus(all_data):
    results = {}
    for sku in all_data['SKU'].unique():
        sku_data = all_data[all_data['SKU'] == sku].copy()
        if len(sku_data) > 0:
            try:
                result = analyze_sku(sku_data)
                if result is not None:
                    results[sku] = result
            except Exception as e:
                logger.error(f"Error analyzing SKU {sku}: {str(e)}")
    return results