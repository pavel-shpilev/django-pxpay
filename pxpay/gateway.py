from django.conf import settings
from pxpay.models import CURRENCY_CHOICES, TXN_TYPE_CHOICES
from xml.dom.minidom import parseString, Document
import re
import requests

# Methods

AUTH = 'Auth'
COMPLETE = 'Complete'
PURCHASE = 'Purchase'
REFUND = 'Refund'
VALIDATE = 'Validate'

UNABLE_TO_FULFILL_TRANSACTION = 'Unable to fulfill transaction'


class Request(object):
	"""
	Represents a GenerateRequest request.
	First request to PaymentExpress of two.
	"""
	root_element='GenerateRequest'
	
	def __init__(self, userid, passkey, currency, txn_type, kwargs):
		self.data = {}
		self.required_keys = [
			'userid',
			'passkey',
			'amount',
			'currency',
			'txn_type',
			'url_fail',
			'url_success',
		]
		self.field_map = {
			'userid': 'PxPayUserId',
			'passkey': 'PxPayKey',
			'amount': 'AmountInput',
			'billing_id': 'BillingId',
			'currency': 'CurrencyInput',
			'email': 'EmailAddress',
			'enable_add_bill_card': 'EnableAddBillCard',
			'merchant_ref': 'MerchantReference',
			'txn_data1': 'TxnData1',
			'txn_data2': 'TxnData2',
			'txn_data3': 'TxnData3',
			'txn_type': 'TxnType',
			'txn_id': 'TxnId',
			'url_fail': 'UrlFail',
			'url_success': 'UrlSuccess',
			'opt': 'Opt',
		}
		self.set_auth(userid, passkey)
		self.set_element('currency', currency)
		self.set_element('txn_type', txn_type)
		for element in kwargs:
			self.set_element(element, kwargs[element])

	@property
	def request_xml(self):
		doc = Document()
		root = doc.createElement(self.root_element)
		doc.appendChild(root)
		for key, value in self.data.items():
			field = self.field_map.get(key)
			self._create_element(doc, root, field, value)
		return doc.toxml()

	def set_auth(self, userid, passkey):
		self.set_element('userid', userid)
		self.set_element('passkey', passkey)

	def set_element(self, name, value):
		self.data[name] = value

	def _create_element(self, doc, parent, tag, value=None, attributes=None):
		ele = doc.createElement(tag)
		parent.appendChild(ele)
		if value:
			text = doc.createTextNode(str(value))
			ele.appendChild(text)
		if attributes:
			[ele.setAttribute(k, v) for k, v in attributes.items()]
		return ele

	def __unicode__(self):
		return self.request_xml

	def __str__(self):
		return self.__unicode__()


class Response_Request(Request):
	"""
	A ProcessResponse Request. The second of two.
	How weird is that class name?
	"""
	root_element='ProcessResponse'
	
	def __init__(self, userid, passkey, response):
		self.data = {}
		self.required_keys = [
			'userid',
			'passkey',
			'response',
		]
		self.field_map = {
			'userid': 'PxPayUserId',
			'passkey': 'PxPayKey',
			'response': 'Response',
		}
		self.set_auth(userid, passkey)
		self.set_element('response', response)


class Response(object):
	"""
	Encapsulate a PxPay response.
	"""
	def __init__(self, request_xml, response_xml):
		self.request_xml = request_xml
		self.response_xml = response_xml
		self.response_parsed = self._extract_data(self.response_xml)

	def _extract_data(self, response_xml):
		if response_xml == '' \
			or response_xml == '<?xml version="1.0" ?>' \
			or response_xml is None:
			return None
		return parseString(response_xml)
	
	@property
	def get_data(self):
		if self.is_valid:
			data = {}
			for el in self.response_parsed.firstChild.childNodes:
				data[el.nodeName] = self._get_element_val(el)
			return data
		return None

	def _get_element_val(self, el):
		if el.firstChild:
			return el.firstChild.data
		return None

	@property
	def is_valid(self):
		ele = self.response_parsed.firstChild
		if ele is None or ele.attributes is None:
			return False
		return int(ele.attributes.get('valid').value) == 1


class Gateway(object):
	"""
	Transport class and entry point.
	"""
	def __init__(self):
		self.pxpay_url = self._get_settings('PXPAY_URL')
		self.userid = self._get_settings('PXPAY_USERID')
		self.passkey = self._get_settings('PXPAY_KEY')
		self.currency = self._get_settings('PXPAY_CURRENCY')

	def _get_settings(self, name):
		return getattr(settings, name, Exception("Please specify %s in settings." % name))

	def _fetch_response(self, request):
		self._check_kwargs(request.data, request.required_keys)
		response = requests.post(self.pxpay_url, request.request_xml)
		return Response(request.request_xml, response.text)

	def _check_kwargs(self, kwargs, required_keys):
		for key in required_keys:
			if key not in kwargs:
				raise ValueError('You must provide a "%s" argument' % key)

		for key in kwargs:
			value = kwargs[key]
			if key == 'currency' and value not in [k[0] for k in CURRENCY_CHOICES]:
				raise ValueError('Currency code must be a 3 character code')
			if key == 'amount' and value == 0:
				raise ValueError('Amount must be non-zero')
			if key in ('card_issue_date', 'card_expiry') \
				and value is not None \
				and not re.match(r'^(0[1-9]|1[012])([0-9]{2})$', value):
				raise ValueError('%s must be in format mmyy' % key)

	def _get_request(self, txn_type, kwargs, required_keys):
		self._check_kwargs(kwargs, required_keys)
		request = Request(self.userid, self.passkey, self.currency, txn_type, kwargs)
		for key in required_keys:
			request.set_element(key, kwargs.get(key))
		return request

	def authorise(self, **kwargs):
		"""
		Authorizes a transaction.
		Must be completed within 7 days using the "Complete" TxnType
		"""
		request = self._get_request(AUTH, kwargs, [
			'card_holder', 'card_number', 'cvc2', 'amount',
		])
		return self._fetch_request_response(request)

	def complete(self, **kwargs):
		"""
		Completes (settles) a pre-approved Auth Transaction.
		The DpsTxnRef value returned by the original approved Auth transaction
		must be supplied.
		"""
		request = self._get_request(COMPLETE, kwargs, ['dps_txn_ref', ])
		return self._fetch_request_response(request)

	def purchase(self, **kwargs):
		"""
		Purchase - Funds are transferred immediately.
		"""
		if kwargs.get('dps_billing_id') is None:
			return self._purchase_on_new_card(**kwargs)
		return self._purchase_on_existing_card(**kwargs)

	def _purchase_on_new_card(self, **kwargs):
		request = self._get_request(PURCHASE, kwargs, [
			'merchant_ref', 'url_fail', 'url_success'
		])
		return self._fetch_response(request)

	def _purchase_on_existing_card(self, **kwargs):
		request = self._get_request(PURCHASE, kwargs, ['dps_billing_id'])
		return self._fetch_response(request)

	def process_response(self, **kwargs):
		"""
		Post-processing transaction validation.
		"""
		self._check_kwargs(kwargs, ['result'])
		request = Response_Request(self.userid, self.passkey, kwargs.get('result'))
		return self._fetch_response(request)

	def validate(self, **kwargs):
		"""
		Validation Transaction.
		Effects a $1.00 Auth to validate card details including expiry date.
		Often utilised with the EnableAddBillCard property set to 1 to
		automatically add to Billing Database if the transaction is approved.
		"""
		request = self._get_request(AUTH, kwargs, [
			'card_holder', 'card_number', 'cvc2', 'card_expiry',
		])
		return self._fetch_request_response(request)

	def refund(self, **kwargs):
		"""
		Refund - Funds transferred immediately.
		Must be enabled as a special option.
		"""
		request = self._get_request(REFUND, kwargs, [
			'dps_txn_ref', 'merchant_ref',
		])
		return self._fetch_request_response(request)
