from django.conf import settings
from django.db import models
from uuid import uuid4


TXN_TYPE_CHOICES = [(s, s) for s in ['Purchase', 'Auth', 'Complete']]
CURRENCY_CHOICES = [('AUD', "Australian Dollar"),
                    ('BND', "Brunei Dollar"),
                    ('CAD', "Canadian Dollar"),
                    ('CHF', "Switzerland Franc"),
                    ('EUR', "Euro"),
                    ('FJD', "Fiji Dollar"),
                    ('FRF', "French Franc"),
                    ('GBP', "United Kingdom Pound"),
                    ('HKD', "Hong Kong Dollar"),
                    ('INR', "Indian Rupee"),
                    ('JPY', "Japanese Yen"),
                    ('KWD', "Kuwait Dinar"),
                    ('MYR', "Malaysian Ringgit"),
                    ('NZD', "New Zealand  Dollar"),
                    ('PGK', "Papua New Guinean Kina"),
                    ('SBD', "Solomon Islander Dollar"),
                    ('SGD', "Singapore Dollar"),
                    ('THB', "Thai Baht"),
                    ('TOP', "Tongan Pa'anga"),
                    ('USD', "United States Dollar"),
                    ('VUV', "Vanuatu Vatu"),
                    ('WST', "Samoan Tala"),
                    ('ZAR', "South African Rand")]
STATE_CHOICES = [(s, s) for s in ['Init', 'GenerateRequest', 'RequestSent',
                                  'ProcessResponse', 'Complete']]


class Transaction(models.Model):

    # Model field names match API fields.
    TxnId = models.CharField(max_length=16, editable=False, primary_key=True)
    TxnType = models.CharField(max_length=8, choices=TXN_TYPE_CHOICES)
    MerchantReference = models.CharField(max_length=64, null=True, blank=True)
    TxnData1 = models.CharField(max_length=32, null=True, blank=True)
    TxnData2 = models.CharField(max_length=32, null=True, blank=True)
    TxnData3 = models.CharField(max_length=32, null=True, blank=True)
    AmountInput = models.DecimalField(decimal_places=2, max_digits=12)
    AmountSettlement = models.DecimalField(decimal_places=2, max_digits=12,
                                           null=True, blank=True)
    CurrencyInput = models.CharField(max_length=4, choices=CURRENCY_CHOICES)
    CurrencySettlement = models.CharField(max_length=4,
                                          choices=CURRENCY_CHOICES,
                                          null=True, blank=True)
    EnableAddBillCard = models.IntegerField(null=True, blank=True)
    BillingId = models.CharField(max_length=32, null=True, blank=True)
    DpsBillingId = models.CharField(max_length=16, null=True, blank=True)
    Opt = models.CharField(max_length=64, null=True, blank=True)
    AuthCode = models.CharField(max_length=22, null=True, blank=True)
    DpsTxnRef = models.CharField(max_length=16, null=True, blank=True)
    Success = models.IntegerField(null=True, blank=True)
    ResponseText = models.TextField(max_length=32, null=True, blank=True)
    Response = models.TextField(null=True, blank=True)
    ClientInfo = models.CharField(max_length=15, null=True, blank=True)
    # No info on max_length given in the documentation.
    TxnMac = models.TextField(null=True, blank=True)
    # Service fields.
    created = models.DateTimeField(auto_now_add=True)
    state = models.CharField(max_length=15, choices=STATE_CHOICES,
                             default='Init')
    complete = models.BooleanField(default=False)

    def __init__(self, *args, **kwargs):
        # If no txn_id provided generate a new one.
        if not kwargs.get('TxnId'):
            kwargs['TxnId'] = self._generate_unique_txnid()
        # Currency code must be provided
        # either within transaction or in settings.py.
        if not kwargs.get('CurrencyInput'):
            try:
                kwargs['CurrencyInput'] = getattr(settings, 'PXPAY_CURRENCY')
            except AttributeError:
                raise KeyError('No currency set. Please provide CurrencyInput \
                               or specify PXPAY_CURRENCY in settings')
        return super(Transaction, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return '%s' % self.TxnId

    def _generate_unique_txnid(self):
        TxnId = str(uuid4())[:15].replace('-', '')
        while self._base_manager.filter(TxnId=TxnId).exists():
            TxnId = str(uuid4())[:15].replace('-', '')
        return TxnId

    class Meta:

        ordering = ('-created', )
