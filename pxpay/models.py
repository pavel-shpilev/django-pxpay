from django.conf import settings
from django.db import models
from uuid import uuid4

TXN_TYPE_CHOICES = [(s, s) for s in ['Purchase', 'Auth', 'Complete']]
CURRENCY_CHOICES = [
	('AUD', "Australian Dollar"),		('BND', "Brunei Dollar"),			('CAD', "Canadian Dollar"),
	('CHF', "Switzerland Franc"),		('EUR', "Euro"),					('FJD', "Fiji Dollar"),
	('FRF', "French Franc"),			('GBP', "United Kingdom Pound"),	('HKD', "Hong Kong Dollar"),
	('INR', "Indian Rupee"),			('JPY', "Japanese Yen"),			('KWD', "Kuwait Dinar"),
	('MYR', "Malaysian Ringgit"),		('NZD', "New Zealand  Dollar"),		('PGK', "Papua New Guinean Kina"),
	('SBD', "Solomon Islander Dollar"),	('SGD', "Singapore Dollar"),		('THB', "Thai Baht"),
	('TOP', "Tongan Pa'anga"),			('USD', "United States Dollar"),	('VUV', "Vanuatu Vatu"),
	('WST', "Samoan Tala"),				('ZAR', "South African Rand")]


class Transaction(models.Model):
	txn_id = models.CharField(max_length=16, editable=False, default=str(uuid4()).replace('-', ''))
	txn_type = models.CharField(max_length=8, choices=TXN_TYPE_CHOICES)
	merchant_ref = models.CharField(max_length=64, null=True, blank=True)
	txn_data1 = models.CharField(max_length=32, null=True, blank=True)
	txn_data2 = models.CharField(max_length=32, null=True, blank=True)
	txn_data3 = models.CharField(max_length=32, null=True, blank=True)
	amount = models.DecimalField(decimal_places=2, max_digits=12)
	currency = models.CharField(max_length=4, choices=CURRENCY_CHOICES)
	add_bill_card = models.IntegerField(null=True, blank=True)
	billing_id = models.CharField(max_length=32, null=True, blank=True)
	dps_billing_id = models.CharField(max_length=16, null=True, blank=True)
	opt = models.CharField(max_length=64, null=True, blank=True)
	auth_code = models.CharField(max_length=22, null=True, blank=True)
	dps_txn_ref = models.CharField(max_length=16, null=True, blank=True)
	success = models.IntegerField(null=True, blank=True)
	response_text = models.CharField(max_length=32, null=True, blank=True)
	client_info = models.CharField(max_length=15, null=True, blank=True)
	txn_mac = models.TextField(null=True, blank=True) # No info on max_length in the documentation
	created = models.DateTimeField(auto_now_add=True)

	def __init__(self, *args, **kwargs):
		if 'currency' not in kwargs:
			try:
				currency = getattr(settings, 'PXPAY_CURRENCY')
			except AttributeError:
				raise KeyError("No currency set. Please provide currency or specify PXPAY_CURRENCY in settings")
			return super(Transaction, self).__init__(currency=currency, *args, **kwargs)
		return super(Transaction, self).__init__(*args, **kwargs)

	def __unicode__(self):
		return '%s' % self.txn_id

	class Meta:
		ordering = ('-created',)