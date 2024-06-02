from django.shortcuts import render, get_object_or_404, redirect
from .models import Stock, Dividend, IndustryHold, StockHold, JuridicalData
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
import plotly.graph_objs as go
from django.contrib.auth import authenticate, login, logout
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


def introduce(request):
    return render(request, 'introduce.html')

def stock_list(request):
    stock_list = Stock.objects.all().order_by('-date', 'stock_code')
    
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

    industry_holds = IndustryHold.objects.filter(stock_code=stock_code)
    industry_holders = [industry.industry_holder for industry in industry_holds]
    industry_percentages = [industry.percentage for industry in industry_holds]

    trace3 = go.Pie(labels=industry_holders, values=industry_percentages)
    layout_industry = go.Layout(title=f'{stock_code}行業比重')
    figure_industry = go.Figure(data=[trace3], layout=layout_industry)
    plot_industry_hold = figure_industry.to_html(full_html=False)


    stock_holds = StockHold.objects.filter(stock_code=stock_code)
    #stock_holders = [stock_hold.stock_holder for stock_hold in stock_holds]
    #percentages = [stock_hold.percentage for stock_hold in stock_holds]

    #trace4 = go.Pie(labels=stock_holders, values=percentages)
    #layout_stock = go.Layout(title=f'Stock Holds for {stock_code}')
    #figure_stock = go.Figure(data=[trace4], layout=layout_stock)
    #plot_stock_hold = figure_stock.to_html(full_html=False)

    return render(request, 'stock_holder.html', {'stock': stock, 'stock_code': stock_code, 'industry_holds': industry_holds, 
                                                 'plot_industry_hold': plot_industry_hold, 'stock_holds': stock_holds})

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
            return HttpResponseRedirect(reverse('stock_detail', kwargs={'stock_code': keyword}))
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