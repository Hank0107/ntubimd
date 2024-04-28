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

