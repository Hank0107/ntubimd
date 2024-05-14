from django.db import models

class Stock(models.Model):
    date = models.DateField(verbose_name="日期")
    stock_code = models.CharField(max_length=10, primary_key=True, verbose_name="證券代號")
    stock_name = models.TextField(verbose_name="證券名稱")
    open_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="開盤價")
    high_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="最高價")
    low_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="最低價")
    close_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="收盤價")
    pos_neg = models.CharField(max_length=1, verbose_name="漲跌(+/-)")
    change_percent = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="漲跌價差")
    total_volume = models.DecimalField(max_digits=15, decimal_places=0, verbose_name="成交股數")
    total_value = models.DecimalField(max_digits=20, decimal_places=2, verbose_name="成交金額")
    class Meta:
        db_table = 'stock_data'

class Dividend(models.Model):
    stock_code = models.CharField(max_length=10, primary_key=True, verbose_name="證券代號")
    stock_name = models.TextField(verbose_name="證券名稱")
    Distribution_Date = models.CharField(max_length=50, verbose_name="發放期間")
    Belong = models.CharField(max_length=255, verbose_name="所屬期間")
    Cash_Dividend = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="現金股利")
    stock_Dividend = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="股票股利")
    Cash_Yield = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="現金殖利率")
    Ex_Date_Close = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="除息日昨收價")
    Ex_Dividend_Date = models.CharField(max_length=50, verbose_name="除息日")
    Ex_Right_Date = models.CharField(max_length=50, verbose_name="除權日")
    Cash_Dividend_Date = models.CharField(max_length=50, verbose_name="現金股利發放日")
    stock_Dividends_Date = models.CharField(max_length=50, verbose_name="股票股利發放日")
    Back_To_Close_Date = models.IntegerField(max_length=10, verbose_name="填息天數")
    class Meta:
        db_table = 'dividend'

class IndustryHold(models.Model):
    stock_code = models.CharField(max_length=10, primary_key=True, verbose_name="證券代號")
    stock_name = models.TextField(verbose_name="證券名稱")
    industry_holder = models.CharField(max_length=50, verbose_name="持股產業")
    percentage = models.CharField(max_length=10, verbose_name="百分比")
    class Meta:
        db_table = 'industry_hold'

class StockHold(models.Model):
    stock_code = models.CharField(max_length=10, primary_key=True, verbose_name="證券代號")
    stock_name = models.TextField(verbose_name="證券名稱")
    stock_holder = models.CharField(max_length=50, verbose_name="持股證券")
    percentage = models.CharField(max_length=10, verbose_name="百分比")
    class Meta:
        db_table = 'stock_hold'