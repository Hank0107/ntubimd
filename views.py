from django.shortcuts import render, get_object_or_404, redirect
from .models import Stock, Dividend, Funds_Holding, JuridicalData, Etf_Performance, Stock_Performance, Ratio, FundsInfo, FundsNetWorth,Risk
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
import plotly.graph_objs as go
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import RegisterForm, Forgot_password_Form, ResetPasswordForm
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import PasswordResetConfirmView
import requests
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import pandas as pd
import json
from decimal import Decimal
from prophet import Prophet
import numpy as np
from django.db.models import OuterRef, Subquery, Value, CharField
import re

def introduce(request):
    return render(request, 'introduce.html')

def stock_list(request):
    latest_date = Stock.objects.latest('date').date
    stock_list = Stock.objects.filter(date=latest_date).order_by('stock_code')
    
    items_per_page = 20
    paginator = Paginator(stock_list, items_per_page)
    
    page = request.GET.get('page', 1)
    
    try:
        stock_list = paginator.page(page)
    except PageNotAnInteger:
        stock_list = paginator.page(1)
    except EmptyPage:
        stock_list = paginator.page(paginator.num_pages)
    
    return render(request, 'stock_list.html', {'stock_list': stock_list})

def stock_detail(request, stock_code):
    stock = Stock.objects.filter(stock_code=stock_code).order_by('-date').first()
    yesterday_stock = Stock.objects.filter(stock_code=stock_code).order_by('-date')[1]
    
    return render(request, 'realtime_data.html', {'stock': stock, 'stock_code': stock_code, 'yesterday_stock': yesterday_stock})



def serialize_decimal(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def technical_analysis(request, stock_code):
    timeframe = request.GET.get('timeframe', 'daily')
    
    stock_data = Stock.objects.filter(stock_code=stock_code).order_by('date')
    
    if stock_data.exists():
        df = pd.DataFrame(list(stock_data.values()))
        df['date'] = pd.to_datetime(df['date'])

        if timeframe == 'weekly':
            df['week'] = df['date'].dt.to_period('W').apply(lambda r: r.end_time)
            df = df.groupby('week').agg({
                'date': 'last',
                'open_price': 'first',
                'high_price': 'max',
                'low_price': 'min',
                'close_price': 'last',
                'total_volume': 'sum'
            }).reset_index(drop=True)
        elif timeframe == 'monthly':
            df['month'] = df['date'].dt.to_period('M').apply(lambda r: r.end_time)
            df = df.groupby('month').agg({
                'date': 'last',
                'open_price': 'first',
                'high_price': 'max',
                'low_price': 'min',
                'close_price': 'last',
                'total_volume': 'sum'
            }).reset_index(drop=True)
        else:
            df = df.sort_values('date')

        # Convert DataFrame to JSON
        df['date'] = df['date'].dt.strftime('%Y-%m-%d')  # Convert datetime to string
        chart_data = df.to_dict(orient='records')

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse(chart_data, safe=False, json_dumps_params={'default': serialize_decimal})

        return render(request, 'technical_analysis.html', {
            'stock': stock_data.first(),
            'stock_code': stock_code,
            'chart_data': json.dumps(chart_data, default=serialize_decimal)
        })
    else:
        return render(request, 'technical_analysis.html', {'stock_code': stock_code})



def stock_dividend(request, stock_code):
    stock = Stock.objects.filter(stock_code=stock_code).order_by('-date').first()

    dividends = Dividend.objects.filter(stock_code=stock_code)
    distribution_dates = []
    cash_dividends = []
    stock_dividends = []

    for dividend in dividends:
        if dividend.Distribution_Date:
            distribution_dates.append(dividend.Distribution_Date)
            cash_dividends.append(dividend.Cash_Dividend)
            stock_dividends.append(dividend.stock_Dividend)

    trace1 = go.Bar(x=distribution_dates, y=cash_dividends, name='現金股利')
    trace2 = go.Bar(x=distribution_dates, y=stock_dividends, name='股票股利')
    layout = go.Layout(title=f'{stock_code}歷年股利分配', xaxis=dict(title='發放年份'), yaxis=dict(title='股利'))
    figure = go.Figure(data=[trace1, trace2], layout=layout)
    plot_stock_dividend = figure.to_html(full_html=False)

    return render(request, 'stock_dividend.html', {'stock': stock, 'stock_code': stock_code, 'dividends': dividends, 'plot_stock_dividend': plot_stock_dividend})

def stock_holder(request, stock_code):
    stock = Stock.objects.filter(stock_code=stock_code).order_by('-date').first()
    industry_holds = Funds_Holding.objects.filter(fund_code=stock_code).order_by('-industry_ratio')

    # 使用字典過濾重複的行業類型
    unique_industries = {}
    for hold in industry_holds:
        industry_ratio = hold.industry_ratio
        if hold.industry_type not in unique_industries:
            unique_industries[hold.industry_type] = industry_ratio

    industry_type = list(unique_industries.keys())
    industry_ratio = list(unique_industries.values())

    trace3 = go.Bar(x=industry_type,y=industry_ratio,text=industry_ratio)
    layout_industry = go.Layout(title=f'{stock_code} 行業比重')
    figure_industry = go.Figure(data=[trace3], layout=layout_industry)
    plot_industry_hold = figure_industry.to_html(full_html=False)

    # 取得股票持有資料並按股票比重排序
    stock_holds = Funds_Holding.objects.filter(fund_code=stock_code).order_by('-stock_ratio')
    # stock_holders = [stock_hold.stock_holder for stock_hold in stock_holds]
    # percentages = [stock_hold.stock_ratio for stock_hold in stock_holds]

    # trace4 = go.Pie(labels=stock_holders, values=percentages)
    # layout_stock = go.Layout(title=f'Stock Holds for {stock_code}')
    # figure_stock = go.Figure(data=[trace4], layout=layout_stock)
    # plot_stock_hold = figure_stock.to_html(full_html=False)

    return render(request, 'stock_holder.html', {
        'stock': stock,
        'stock_code': stock_code,
        'plot_industry_hold': plot_industry_hold,
        'unique_industries':unique_industries,
        'stock_holds': stock_holds,
    })

def proxy_get_stock_info(request, stock_code):
    stock = Stock.objects.filter(stock_code=stock_code).first()
    if stock:
        target_url = f'https://tw.stock.yahoo.com/_td-stock/api/resource/FinanceChartService.ApacLibraCharts;autoRefresh=1715224690029;symbols=%5B%22{stock_code}.TW%22%5D;type=tick?bkt=&device=desktop&ecma=modern&feature=enableGAMAds%2CenableGAMEdgeToEdge%2CenableEvPlayer&intl=tw&lang=zh-Hant-TW&partner=none&prid=1lvf1qtj3og0r&region=TW&site=finance&tz=Asia%2FTaipei&ver=1.4.102&returnMeta=true'
        
        try:
            response = requests.get(target_url)
            return JsonResponse(response.json())
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Missing stock_code parameter'}, status=400)




def stock_search(request):
    keyword = request.GET.get('keyword', '')
    if keyword:
        if keyword.isdigit():
            stock = Stock.objects.filter(stock_code=keyword).first()
            if stock:
                return HttpResponseRedirect(reverse('stock_detail', kwargs={'stock_code': stock.stock_code}))
            else:
                return HttpResponseRedirect(reverse('empty_page'))
        else:
            stocks = Stock.objects.filter(stock_name__icontains=keyword) | Stock.objects.filter(stock_code__icontains=keyword)
            if stocks.exists():
                stock = stocks.first()
                return HttpResponseRedirect(reverse('stock_detail', kwargs={'stock_code': stock.stock_code}))
            else:
                return HttpResponseRedirect(reverse('empty_page'))

    return HttpResponseRedirect(reverse('empty_page'))


def empty_page(request):
    return render(request, 'empty_page.html')

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            if User.objects.filter(email=email).exists():
                messages.error(request, '此信箱已註冊，請使用其他信箱')
            else:
                form.save()
                return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('introduce')
        else:
            messages.error(request, '帳號或密碼錯誤')
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    return redirect('introduce')

def forgot_password(request):
    if request.method == 'POST':
        form = Forgot_password_Form(request.POST)
        if form.is_valid():
            form.save(request=request)
            messages.success(request, '重設密碼的電子郵件已傳送，請檢查您的電子郵件')
            return redirect('login')
    else:
        form = Forgot_password_Form()
    return render(request, 'forgot_password.html', {'form': form})

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = ResetPasswordForm
    template_name = 'reset_password.html'
    success_url = '/login/'

def reset_password(request):
    return auth_views.CustomPasswordResetConfirmView.as_view(
        template_name='reset_password.html',
        form_class = CustomPasswordResetConfirmView,
        success_url='/login/',
        post_reset_login=True,
        extra_context={'post_reset_login': True}
    )(request)

def juridical_data(request, stock_code):
    stock = Stock.objects.filter(stock_code=stock_code).order_by('-date').first()
    juridical_datas = JuridicalData.objects.filter(stock_code=stock_code).order_by('-date')

    for data in juridical_datas:
        data.foreign_investors_buy_lots = round(data.foreign_investors_buy / 1000)
        data.foreign_investors_sell_lots = round(data.foreign_investors_sell / 1000)
        data.foreign_investors_diff_lots = round(data.foreign_investors_diff / 1000)
        data.foreign_self_buy_lots = round(data.foreign_self_buy / 1000)
        data.foreign_self_sell_lots = round(data.foreign_self_sell / 1000)
        data.foreign_self_diff_lots = round(data.foreign_self_diff / 1000)
        data.investment_trust_buy_lots = round(data.investment_trust_buy / 1000)
        data.investment_trust_sell_lots = round(data.investment_trust_sell / 1000)
        data.investment_trust_diff_lots = round(data.investment_trust_diff / 1000)
        data.dealer_total_diff_lots = round(data.dealer_total_diff / 1000)
        data.dealer_self_buy_lots = round(data.dealer_self_buy / 1000)
        data.dealer_self_sell_lots = round(data.dealer_self_sell / 1000)
        data.dealer_self_diff_lots = round(data.dealer_self_diff / 1000)
        data.dealer_hedge_buy_lots = round(data.dealer_hedge_buy / 1000)
        data.dealer_hedge_sell_lots = round(data.dealer_hedge_sell / 1000)
        data.dealer_hedge_diff_lots = round(data.dealer_hedge_diff / 1000)
        data.total_diff_lots = round(data.total_diff / 1000)

    dates = []
    foreign_diff_lots = []
    investment_diff_lots = []
    dealer_diff_lots = []

    for datas in juridical_datas:
        dates.append(datas.date.strftime('%Y-%m-%d'))
        foreign_diff_lots.append(round(datas.foreign_investors_diff / 1000))
        investment_diff_lots.append(round(datas.investment_trust_diff / 1000))
        dealer_diff_lots.append(round(datas.dealer_total_diff / 1000))
    
    chart_data = {
        'dates': dates,
        'foreign_diff_lots': foreign_diff_lots,
        'investment_diff_lots': investment_diff_lots,
        'dealer_diff_lots': dealer_diff_lots,
    }
    return render(request, 'stock_juridicalperson.html', {'stock': stock, 'stock_code': stock_code, 
                                                          'juridical_datas': juridical_datas, 'chart_data': json.dumps(chart_data)})


def calculate_rsi(data, window=14):
    """計算相對強弱指標（RSI）"""
    delta = data['y'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(data):
    """計算 MACD 指標"""
    exp1 = data['y'].astype(float).ewm(span=12, adjust=False).mean()
    exp2 = data['y'].astype(float).ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

def calculate_bollinger_bands(data, window=20):
    """計算布林帶"""
    rolling_mean = data['y'].astype(float).rolling(window=window).mean()
    rolling_std = data['y'].astype(float).rolling(window=window).std()
    upper_band = rolling_mean + (rolling_std * 2)  # 上帶
    lower_band = rolling_mean - (rolling_std * 2)  # 下帶
    return upper_band, lower_band

def calculate_stochastic(data, window=14):
    """計算隨機指標"""
    lowest_low = data['y'].astype(float).rolling(window=window).min()
    highest_high = data['y'].astype(float).rolling(window=window).max()
    stochastic = 100 * ((data['y'].astype(float) - lowest_low) / (highest_high - lowest_low))
    return stochastic

def calculate_atr(data, window=14):
    """計算平均真實範圍 (ATR)"""
    high_low = data['high_price'].astype(float) - data['low_price'].astype(float)  # 當前高低範圍
    high_prev_close = np.abs(data['high_price'].astype(float) - data['y'].astype(float).shift())  # 當前高與前收盤的差
    low_prev_close = np.abs(data['low_price'].astype(float) - data['y'].astype(float).shift())  # 當前低與前收盤的差
    tr = pd.concat([high_low, high_prev_close, low_prev_close], axis=1).max(axis=1)  # 真實範圍
    atr = tr.rolling(window=window).mean()  # 計算ATR
    return atr

def stock_prediction(request, stock_code):
    # 獲取股票數據
    stock_data = Stock.objects.filter(stock_code=stock_code).order_by('date').values('date', 'close_price', 'high_price', 'low_price')
    df = pd.DataFrame(list(stock_data))

    # 確保 'date' 是 datetime 格式
    df['date'] = pd.to_datetime(df['date'])
    df.rename(columns={'date': 'ds', 'close_price': 'y'}, inplace=True)

    # 將 'y' 列轉換為 float
    df['y'] = df['y'].astype(float)

    # 計算技術指標
    df['ma5'] = df['y'].rolling(window=5).mean()
    df['ma10'] = df['y'].rolling(window=10).mean()
    df['ma20'] = df['y'].rolling(window=20).mean()
    df['ma60'] = df['y'].rolling(window=60).mean()
    df['ma120'] = df['y'].rolling(window=120).mean()
    df['ma240'] = df['y'].rolling(window=240).mean()
    df['rsi'] = calculate_rsi(df)
    df['macd'], df['signal'] = calculate_macd(df)
    df['upper_band'], df['lower_band'] = calculate_bollinger_bands(df)
    df['stochastic'] = calculate_stochastic(df)
    df['atr'] = calculate_atr(df)

    # 處理 NaN 值
    df.fillna(method='bfill', inplace=True)
    df.fillna(method='ffill', inplace=True)

    # 訓練模型並生成預測
    model = Prophet(changepoint_prior_scale=0.1, daily_seasonality=True)
    model.add_regressor('ma5')
    model.add_regressor('ma10')
    model.add_regressor('ma20')
    model.add_regressor('ma60')
    model.add_regressor('ma120')
    model.add_regressor('ma240')
    model.add_regressor('rsi')
    model.add_regressor('macd')
    model.add_regressor('signal')
    model.add_regressor('upper_band')
    model.add_regressor('lower_band')
    model.add_regressor('stochastic')
    model.add_regressor('atr')

    model.fit(df)

    # 生成未來30天的預測
    future = model.make_future_dataframe(periods=7)
    future['ma5'] = df['ma5'].iloc[-1]
    future['ma10'] = df['ma10'].iloc[-1]
    future['ma20'] = df['ma20'].iloc[-1]
    future['ma60'] = df['ma60'].iloc[-1]
    future['ma120'] = df['ma120'].iloc[-1]
    future['ma240'] = df['ma240'].iloc[-1]
    future['rsi'] = df['rsi'].iloc[-1]
    future['macd'] = df['macd'].iloc[-1]
    future['signal'] = df['signal'].iloc[-1]
    future['upper_band'] = df['upper_band'].iloc[-1]
    future['lower_band'] = df['lower_band'].iloc[-1]
    future['stochastic'] = df['stochastic'].iloc[-1]
    future['atr'] = df['atr'].iloc[-1]

    forecast = model.predict(future)

    # 獲取預測數據
    future_predictions = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']][-7:]

    # 對預測值進行後處理
    future_predictions['yhat'] = future_predictions['yhat'].rolling(window=3).mean()
    future_predictions['yhat_lower'] = future_predictions['yhat_lower'].rolling(window=3).mean()
    future_predictions['yhat_upper'] = future_predictions['yhat_upper'].rolling(window=3).mean()

    # 將日期轉換為字符串格式
    future_predictions['ds'] = future_predictions['ds'].dt.strftime('%Y-%m-%d')

    # 準備上下文，包含實際價格和日期
    context = {
        'predictions': future_predictions['yhat'].dropna().tolist(),
        'yhat_lower': future_predictions['yhat_lower'].dropna().tolist(),
        'yhat_upper': future_predictions['yhat_upper'].dropna().tolist(),
        'dates': future_predictions['ds'].tolist(),
        'actual_prices': df['y'].tolist()[-60:],  # 最近30天的實際價格
        'historical_dates': df['ds'].dt.strftime('%Y-%m-%d').tolist()[-60:],  # 最近30天的日期
        'stock_code': stock_code
    }

    return render(request, 'stock_prediction.html', context)


def recommend_data(request):
    performances = Etf_Performance.objects.all()

    data = []
    for performance in performances:
        stock_code = performance.fund_code
        stock = Stock.objects.filter(stock_code=stock_code).order_by('-date').first()
        holdings = Funds_Holding.objects.filter(fund_code=stock_code).order_by('-stock_ratio')[:10]
        
        holding_data = []
        for holding in holdings:
            holding_stock_code = holding.stock_code
            stock_performance = Stock_Performance.objects.filter(stock_code=holding_stock_code)
            ratios = Ratio.objects.filter(stock_code=holding_stock_code)
            holding_data.append({
                'holding': holding,
                'stock_performance': stock_performance,
                'ratios':ratios,
            })

        average_performance = round(performance.average_performance * 100, 2)

        data.append({
            'performance': performance,
            'stock': stock,
            'holdings_data': holding_data,
            'round_average_performance': average_performance,
        })
    
    return render(request, 'recommend_data.html', {'data': data})


def stock_info(request, stock_code):
    info = FundsInfo.objects.filter(fund_code=stock_code)
    
    return render(request, 'stock_info.html', {'info': info, 'stock_code': stock_code})

def funds_rank(request):
    # 獲取當前用戶的 username
    current_user = request.user.username

    # 根據 username 從 RISK 表中獲取 image
    try:
        risk_image = Risk.objects.get(username=current_user).image  # 假設 RISK 表有 username 欄位
    except Risk.DoesNotExist:
        risk_image = None


    print(risk_image)
    # 定義標準差範圍
    risk_data = {
        "http://127.0.0.1:8000/static/images/conservative.png": (0, 3),
        "http://127.0.0.1:8000/static/images/stable.png": (4, 5),
        "http://127.0.0.1:8000/static/images/balanced.png": (6, 10),
        "http://127.0.0.1:8000/static/images/growth.png": (11, 15),
        "http://127.0.0.1:8000/static/images/aggressive.png": (16, 100)
    }

    net_worth = FundsNetWorth.objects.filter(fund_code=OuterRef('fund_code')).order_by('-ytd_net_worth')
    
    info = FundsInfo.objects.annotate(
        close_price=Subquery(net_worth.values('close_price')[:1]),
        net_worth=Subquery(net_worth.values('net_worth')[:1]),
        dp_percent=Subquery(net_worth.values('dp_percent')[:1]),
        ytd_net_worth=Subquery(net_worth.values('ytd_net_worth')[:1]),
        first_management_fee=Value('N/A', output_field=CharField()),  # 預設值
        first_custody_fee=Value('N/A', output_field=CharField())  # 預設值
    )
    
    # 提取管理費用和保管費用
    for item in info:
        management_fee_match = re.search(r'(\d+\.\d+%)', item.managementFee)
        item.first_management_fee = management_fee_match.group(1) if management_fee_match else 'N/A'
        
        custody_fee_match = re.search(r'(\d+\.\d+%)', item.custodyFee)
        item.first_custody_fee = custody_fee_match.group(1) if custody_fee_match else 'N/A'

    # 計算每個基金的標準差
    for item in info:
        stock_entries = Stock.objects.filter(stock_code=item.fund_code).values_list('close_price', flat=True)
        
        if stock_entries:
            close_price_std = np.std(stock_entries)
            item.close_price_std = round(close_price_std, 2)  # 保留兩位小數
        else:
            item.close_price_std = None  # 沒有數據的情況

    # 將符合當前用戶風險類型的基金分開
    matching_funds = []
    non_matching_funds = []

    if risk_image:
        # 獲取風險類型的標準差範圍
        std_range = risk_data.get(risk_image, (float('-inf'), float('inf')))

        for item in info:
            if item.close_price_std is not None:  # 排除沒有標準差的基金
                close_price_std = item.close_price_std
                min_std, max_std = std_range

                # 檢查標準差是否在範圍內
                if min_std <= close_price_std <= max_std:
                    matching_funds.append(item)
                else:
                    non_matching_funds.append(item)
            else:
                non_matching_funds.append(item)
    else:
        non_matching_funds = list(info)

    return render(request, 'funds_rank.html', {
        'matching_funds': matching_funds,
        'non_matching_funds': non_matching_funds,
    })




@login_required(login_url='login') 
def Intelligent(request):
    return render(request, 'Intelligent.html')





# view.py
from django.views.decorators.csrf import csrf_exempt
import yfinance as yf
import plotly.graph_objs as go
from django.contrib import messages

def Intelligent3(request):
    latest_date = Stock.objects.latest('date').date

    if latest_date:
        stocks = Stock.objects.filter(date=latest_date).values_list('stock_code', flat=True)
        etf_list = [f"{stock_code}.TW" for stock_code in stocks]
    else:
        etf_list = []

    return render(request, 'Intelligent3.html', {'etf_list': etf_list})




import os
import plotly.io as pio
from django.conf import settings

@csrf_exempt
def calculate_portfolio(request):
    if request.method == 'POST':
        selected_etfs = request.POST.getlist('etfs')
        if not selected_etfs:
            messages.warning(request, "請至少選擇一個ETF。")
            return redirect('Intelligent3')

        # 下載ETF數據
        try:
            Close = yf.download(selected_etfs, start="2018-01-01", end="2024-08-01")['Adj Close']
            if Close.empty:
                messages.error(request, "無法下載所選ETF的數據。")
                return redirect('Intelligent3')
        except Exception as e:
            messages.error(request, f"下載數據時出錯: {e}")
            return redirect('Intelligent3')

        # 計算共變異數矩陣
        cov_matrix = Close.pct_change().apply(lambda x: np.log(1 + x)).cov()

        # 計算預期報酬率
        expected_return = Close.resample('Y').last()[:-1].pct_change().mean()

        # 計算標準差
        standard_dev = Close.pct_change().apply(lambda x: np.log(1 + x)).std().apply(lambda x: x * np.sqrt(250))

        # 計算夏普比率
        risk_free_rate = 0.01  # 設定無風險利率
        sharpe_ratio = (expected_return - risk_free_rate) / standard_dev

        # 整理成表格
        return_dev_matrix = pd.concat([expected_return, standard_dev, sharpe_ratio], axis=1)
        return_dev_matrix.columns = ['預期報酬率', '標準差', '夏普比率']
        return_dev_matrix = return_dev_matrix.round(4)  # 將所有值取到小數點後四位


        # 計算投資組合報酬與風險
        port_ret = []
        port_dev = []
        port_sharpe = []
        port_weights = []
        assets_nums = len(selected_etfs)
        port_nums = 2000

        for _ in range(port_nums):
            weights = np.random.random(assets_nums)
            weights /= np.sum(weights)
            port_weights.append(weights)
            returns = np.dot(weights, expected_return)
            var = np.dot(weights.T, np.dot(cov_matrix, weights))
            ann_sd = np.sqrt(var) * np.sqrt(250)
            sharpe = (returns - risk_free_rate) / ann_sd
            port_ret.append(returns)
            port_dev.append(ann_sd)
            port_sharpe.append(sharpe)

        data = {'報酬率': port_ret, '標準差': port_dev, '夏普比率': port_sharpe}
        for counter, symbol in enumerate(selected_etfs):
            data[symbol + ' 權重'] = [w[counter] for w in port_weights]

        portfolios = pd.DataFrame(data)

        # 繪製效率前緣
        scatter = go.Scatter(
            x=portfolios['標準差'],
            y=portfolios['報酬率'],
            mode='markers',
            marker=dict(
                size=5,
                color=portfolios['夏普比率'],
                colorscale='YlGnBu',
                showscale=True,
                colorbar=dict(title='夏普比率')
            )
        )

        layout = go.Layout(
            title='效率前緣',
            xaxis=dict(title='標準差'),
            yaxis=dict(title='預期報酬率'),
            hovermode='closest'
        )

        fig = go.Figure(data=[scatter], layout=layout)

        # 將圖表匯出為靜態圖片並保存
        img_dir = os.path.join(settings.BASE_DIR, 'data', 'static', 'images')
        if not os.path.exists(img_dir):
            os.makedirs(img_dir)

        efficient_frontier_path = os.path.join(img_dir, 'efficient_frontier.png')
        pio.write_image(fig, efficient_frontier_path)

        # 找出最佳投資組合並繪製圓餅圖
        best_portfolio = portfolios.loc[portfolios['夏普比率'].idxmax()]
        weights = [best_portfolio[f'{symbol} 權重'] for symbol in selected_etfs]
        labels = selected_etfs

        pie = go.Pie(labels=labels, values=weights, hole=.3)
        pie_layout = go.Layout(title='最佳投資組合的權重分配')
        pie_fig = go.Figure(data=[pie], layout=pie_layout)

        pie_chart_path = os.path.join(img_dir, 'pie_chart.png')
        pio.write_image(pie_fig, pie_chart_path)

        # 將數據轉換為字串顯示
        eff_front_set = portfolios.nlargest(100, '夏普比率')[['報酬率', '標準差'] + [f'{symbol} 權重' for symbol in selected_etfs]]
        
        return render(request, 'Intelligent3.html', {
            'etf_list': selected_etfs,
            'return_dev_matrix': return_dev_matrix,
            'eff_front_set': eff_front_set,
            'efficient_frontier_image': 'images/efficient_frontier.png',
            'pie_chart_image': 'images/pie_chart.png',
            'has_calculated': True
        })
    else:
        return render(request, 'Intelligent3.html', {
            'has_calculated': False
        })





from django.shortcuts import render
from .models import NewsData,News_search_key,Ppt_search_key,News_search_key1
from django.http import JsonResponse,HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from urllib.parse import unquote
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import UserNews
import json

def Intelligent2(request):
    # 从数据库中获取所有新闻数据
    news = NewsData.objects.all()
    news_search_key = News_search_key.objects.all()
    news_search_key1 = News_search_key1.objects.all()
    ppt_search_key = Ppt_search_key.objects.all()
    news_list1 = news.order_by('-url_frequency')
    news_list2 = news.order_by('-pub_date')
    news_list3 = news.order_by('-sentiment')
    news_list4 = news.order_by('sentiment')
    news_list5 = news_search_key.order_by('-positive')
    news_list51 = news_search_key1.order_by('-positive')
    news_list6 = news_search_key.order_by('-negative')
    news_list61 = news_search_key1.order_by('-negative')
    news_list7 = ppt_search_key.order_by('-positive')
    news_list8 = ppt_search_key.order_by('-negative')
    news_theme1 = news.filter(title__contains="ETF").order_by('-pub_date')[:3]
    news_theme2 = news.filter(title__contains="台積電").order_by('-pub_date')[:3]
    news_theme3 = news.filter(title__contains="鴻海").order_by('-pub_date')[:3]
    news_theme4 = news.filter(title__contains="Yahoo奇摩").order_by('-pub_date')[:3]
    news_theme5 = news.filter(title__contains="財經").order_by('-pub_date')[:3]
    news_theme6 = news.filter(title__contains="0050").order_by('-pub_date')[:3]

    # 从数据库中按 sentiment 字段降序获取新闻数据
    news_list = NewsData.objects.order_by('-sentiment')[:10]  # 获取所有新闻并按情绪得分排序

    # 检查用户是否已认证
    if request.user.is_authenticated:
        user = request.user.username
        try:
            user_news = UserNews.objects.get(username=user)
            themes = [user_news.theme1, user_news.theme2, user_news.theme3, user_news.theme4, user_news.theme5, user_news.theme6]
            themes = [theme for theme in themes if theme]  # 过滤掉空的主题
            news_by_theme = {theme: NewsData.objects.filter(title__contains=theme).order_by('-pub_date') for theme in themes}
            theme_count = len(themes)  # 计算主题数量
        except UserNews.DoesNotExist:
            news_by_theme = {}
            theme_count = 0
    else:
        news_by_theme = {}
        theme_count = 0

    # 将新闻数据传递到模板中进行显示
    context = {
        'news_by_theme': news_by_theme,
        'theme_count': theme_count,
        'news': news,
        'news_list1': news_list1,
        'news_list2': news_list2,
        'news_list3': news_list3,
        'news_list4': news_list4,
        'news_list5': news_list5,
        'news_list51': news_list51,
        'news_list6': news_list6,
        'news_list61': news_list61,
        'news_list7': news_list7,
        'news_list8': news_list8,
        'news_theme1': news_theme1,
        'news_theme2': news_theme2,
        'news_theme3': news_theme3,
        'news_theme4': news_theme4,
        'news_theme5': news_theme5,
        'news_theme6': news_theme6,
        'news_list': news_list
    }
    return render(request, 'Intelligent2.html', context)


def Intelligent4(request):
    # 从数据库中获取所有新闻数据
    news = NewsData.objects.all()
    news_search_key = News_search_key.objects.all()
    ppt_search_key = Ppt_search_key.objects.all()
    news_list1 = news.order_by('-url_frequency')
    news_list2 = news.order_by('-pub_date')
    news_list3 = news.order_by('-sentiment')
    news_list4 = news.order_by('sentiment')
    news_list5 = news_search_key.order_by('-positive')
    news_list6 = news_search_key.order_by('-negative')
    news_list7 = ppt_search_key.order_by('-positive')
    news_list8 = ppt_search_key.order_by('-negative')
    news_theme1 = news.filter(title__contains="ETF").order_by('-pub_date')[:3]
    news_theme2 = news.filter(title__contains="台積電").order_by('-pub_date')[:3]
    news_theme3 = news.filter(title__contains="鴻海").order_by('-pub_date')[:3]
    news_theme4 = news.filter(title__contains="Yahoo奇摩").order_by('-pub_date')[:3]
    news_theme5 = news.filter(title__contains="財經").order_by('-pub_date')[:3]
    news_theme6 = news.filter(title__contains="0050").order_by('-pub_date')[:3]

    # 从数据库中按 sentiment 字段降序获取新闻数据
    news_list = NewsData.objects.order_by('-sentiment')[:10]  # 获取所有新闻并按情绪得分排序

    # 检查用户是否已认证
    if request.user.is_authenticated:
        user = request.user.username
        try:
            user_news = UserNews.objects.get(username=user)
            themes = [user_news.theme1, user_news.theme2, user_news.theme3, user_news.theme4, user_news.theme5, user_news.theme6]
            themes = [theme for theme in themes if theme]  # 过滤掉空的主题
            news_by_theme = {theme: NewsData.objects.filter(title__contains=theme).order_by('-pub_date') for theme in themes}
            theme_count = len(themes)  # 计算主题数量
        except UserNews.DoesNotExist:
            news_by_theme = {}
            theme_count = 0
    else:
        news_by_theme = {}
        theme_count = 0

    # 從資料庫中獲取 search_key 欄位的所有資料
    search_keys = Ppt_search_key.objects.values_list('search_key', flat=True)

    # 將所有 search_key 連接成一個字串並拆分
    keywords = ' '.join(search_keys).split(',')

    # 将新闻数据传递到模板中进行显示
    context = {
        'news_by_theme': news_by_theme,
        'theme_count': theme_count,
        'news': news,
        'news_list1': news_list1,
        'news_list2': news_list2,
        'news_list3': news_list3,
        'news_list4': news_list4,
        'news_list5': news_list5,
        'news_list6': news_list6,
        'news_list7': news_list7,
        'news_list8': news_list8,
        'news_theme1': news_theme1,
        'news_theme2': news_theme2,
        'news_theme3': news_theme3,
        'news_theme4': news_theme4,
        'news_theme5': news_theme5,
        'news_theme6': news_theme6,
        'news_list': news_list,
        'keywords': keywords
    }
    return render(request, 'Intelligent4.html', context)

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .models import Risk
import json

# 處理表單提交並儲存數據
@csrf_exempt
def save_risk_assessment(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            try:
                # 獲取POST請求中的數據
                data = json.loads(request.body.decode('utf-8'))
                username = request.user.username
                print(f"收到的數據: {data}")  # 調試輸出

                # 提取答案和圖片數據
                a1 = data.get('investmentTiming1')
                a2 = data.get('investmentTiming2')
                a3 = data.get('investmentTiming3')
                a4 = data.get('investmentTiming4')
                a5 = data.get('investmentTiming5')
                a6 = data.get('investmentTiming6')
                a7 = data.get('investmentTiming7')
                result_image = data.get('resultImage')  # 結果圖片的 Base64 編碼
                
                print(f"username: {username}, a1: {a1}, a2: {a2}, a3: {a3}, a4: {a4}, a5: {a5}, a6: {a6}, a7: {a7}, image: {result_image}")

                # 儲存或更新數據到 Risk 表
                risk, created = Risk.objects.update_or_create(
                    user=request.user,
                    defaults={
                        'username': request.user.username,  # 存入 username
                        'a1': a1,
                        'a2': a2,
                        'a3': a3,
                        'a4': a4,
                        'a5': a5,
                        'a6': a6,
                        'a7': a7,
                        'image': result_image
                    }
                )
                print(f"資料庫更新成功, created: {created}")  # 調試輸出

                return JsonResponse({'status': 'success', 'message': 'Risk assessment saved successfully'})

            except Exception as e:
                print(f"發生錯誤: {e}")  # 調試輸出
                return JsonResponse({'status': 'fail', 'error': str(e)}, status=400)
        else:
            return JsonResponse({'status': 'fail', 'error': 'User not authenticated'}, status=400)
    return JsonResponse({'status': 'fail', 'error': 'Invalid request method'}, status=400)











# 創建模型
generation_config = {
    "temperature": 0.4,
    "top_p": 0.85,
    "top_k": 50,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

with open('training_data.json', 'r', encoding='utf-8') as f:
    history_data = json.load(f)


chat_session = model.start_chat(history=history_data)

@xframe_options_sameorigin
def ai_chat(request):
    if request.method == 'POST':
        user_message = request.POST.get('message', '').strip()
        if not user_message:
            return JsonResponse({'error': 'Message cannot be empty.'}, status=400)
        
        response = chat_session.send_message(user_message)
        ai_response = response.text
        ai_response_filtered = ai_response.replace('*', '')

        return JsonResponse({'response': ai_response_filtered})
    
    return render(request, 'article_board/chat.html')

