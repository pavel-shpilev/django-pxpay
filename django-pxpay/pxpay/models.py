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
	currency = models.CharField(max_length=4, choices=CURRENCY_CHOICES)
	merchant_ref = models.CharField(max_length=64)
	txn_data_1 = models.CharField(max_length=255)
	txn_data_2 = models.CharField(max_length=255)
	txn_data_3 = models.CharField(max_length=255)
	amount = models.DecimalField(decimal_places=2, max_digits=12)
	created = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ('-created',)