from django.shortcuts import render, redirect
from .models import Stock
from chartjs.views.lines import BaseLineChartView
from django.views.generic import TemplateView

def introduce(request):
    return render(request, 'introduce.html')

def stock_list(request):
    stock_list = Stock.objects.all().order_by('-date', 'stock_code')[:155]
    return render(request, 'stock_list.html', {'stock_list': stock_list})



class LineChartJSONView(BaseLineChartView):
    def get_labels(self):
        return ["Date 1", "Date 2", "Date 3", "Date 4", "Date 5", "Date 6", "Date 7"]

    def get_data(self):
        stock_data = Stock.objects.filter(stock_code=self.kwargs['stock_code'])[:7]
        close_prices = [stock.close_price for stock in stock_data]
        return [close_prices]

def stock_detail(request, stock_code):
    stock = Stock.objects.filter(stock_code=stock_code).first()
    line_chart = LineChartJSONView()
    line_chart.kwargs = {'stock_code': stock_code}
    return render(request, 'stock_detail.html', {'stock': stock, 'line_chart': line_chart})