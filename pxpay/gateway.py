from django.conf import settings
from pxpay.models import CURRENCY_CHOICES, TXN_TYPE_CHOICES, Transaction
from xml.dom.minidom import parseString, Document
import re
import requests


class Request(object):
    """
    Represents a GenerateRequest request.
    First request to PaymentExpress of two.
    """

    ROOT_ELEMENT = 'GenerateRequest'
    REQUEST_FILEDS = [
        'TxnId',
        'TxnType',
        'MerchantReference',
        'TxnData1',
        'TxnData2',
        'TxnData3',
        'AmountInput',
        'CurrencyInput',
        'EnableAddBillCard',
        'BillingId',
        'Opt',
        'UrlFail',
        'UrlSuccess']

    def __init__(self, userid, passkey, txn, kwargs):
        txn.state = 'GenerateRequest'
        txn.save()
        self.data = {}
        self.set_auth(userid, passkey)
        for element in txn._meta.get_all_field_names():
            if element in self.REQUEST_FILEDS:
                self.set_element(element, getattr(txn, element, None))
        for element in kwargs:
            if element in self.REQUEST_FILEDS:
                self.set_element(element, kwargs[element])

    @property
    def request_xml(self):
        doc = Document()
        root = doc.createElement(self.ROOT_ELEMENT)
        doc.appendChild(root)
        for key, value in self.data.items():
            self._create_element(doc, root, key, value=value)
        return doc.toxml()

    def set_auth(self, userid, passkey):
        self.set_element('PxPayUserId', userid)
        self.set_element('PxPayKey', passkey)

    def set_element(self, name, value):
        self.data[name] = value

    def _create_element(self, doc, parent, tag, value=None, attributes=None):
        element = doc.createElement(tag)
        parent.appendChild(element)
        if value:
            text = doc.createTextNode(str(value))
            element.appendChild(text)
        if attributes:
            [element.setAttribute(k, v) for k, v in attributes.items()]
        return element

    def __unicode__(self):
        return self.request_xml


class ProcessResponse(Request):
    """
    A ProcessResponse Request. The second subsequent request.
    """

    ROOT_ELEMENT = 'ProcessResponse'

    def __init__(self, userid, passkey, kwargs):
        self.data = {}
        self.set_auth(userid, passkey)
        self.set_element('Response', kwargs.get('Response'))


class Response(object):
    """
    Encapsulate a PxPay response.
    """

    RESPONSE_FILEDS = [
        'AmountSettlement',
        'AuthCode',
        'DpsTxnRef',
        'Success',
        'ResponseText',
        'DpsBillingId',
        'CurrencySettlement',
        'ClientInfo',
        'TxnMac',
        'BillingId']

    def __init__(self, request_xml, response_xml, txn=None):
        self.request_xml = request_xml
        self.response_xml = response_xml
        self.response_parsed = self._extract_data(self.response_xml)
        if not txn:
            try:
                txn = Transaction.objects.get(TxnId=self.get_data['TxnId'])
            except:
                txn = None
        if txn is not None:
            for element in self.response_parsed.firstChild.childNodes:
                if element.nodeName in self.RESPONSE_FILEDS:
                    val = self._get_element_val(element)
                    if val is not None and val != '':
                        setattr(txn, element.nodeName, val)
            txn.save()

    def _extract_data(self, response_xml):
        if (response_xml == '' or
            response_xml == '<?xml version="1.0" ?>' or
            response_xml is None):
            return None
        return parseString(response_xml)

    @property
    def get_data(self):
        if self.is_valid:
            data = {}
            for element in self.response_parsed.firstChild.childNodes:
                data[element.nodeName] = self._get_element_val(element)
            return data
        return None

    def _get_element_val(self, element):
        if element.firstChild:
            return element.firstChild.data
        return None

    @property
    def is_valid(self):
        element = self.response_parsed.firstChild
        if element is None or element.attributes is None:
            return False
        return int(element.attributes.get('valid').value) == 1


class Gateway(object):
    """
    Transport class and the entry point.
    """

    def __init__(self, **kwargs):
        self.pxpay_url = 'https://sec2.paymentexpress.com/pxpay/pxaccess.aspx'
        try:
            self.userid = kwargs.get('PXPAY_USERID',
                                     getattr(settings, 'PXPAY_USERID'))
        except AttributeError:
            raise KeyError('No PXPAY_USERID set. Please provide PXPAY_USERID \
                           as an argument or specify it in settings')
        try:
            self.passkey = kwargs.get('PXPAY_KEY',
                                      getattr(settings, 'PXPAY_KEY'))
        except AttributeError:
            raise KeyError('No PXPAY_KEY set. Please provide PXPAY_KEY as an \
                           argument or specify it in settings')

    def _fetch_response(self, request, txn=None):
        response = requests.post(self.pxpay_url, request.request_xml,
                                 verify=False)
        return Response(request.request_xml, response.text, txn=txn)

    def transaction(self, **kwargs):
        if kwargs.get('TxnId'):
            txn = Transaction.objects.get(TxnId__exact=kwargs.get('TxnId'))
        else:
            return Transaction.objects.create(**kwargs)
        # Generate a new transaction if attributes had changed
        # before the transaction was completed.
        if not txn.complete:
            for key, value in kwargs.iteritems():
                if key != 'TxnId' and getattr(txn, key) != value:
                    del kwargs['TxnId']
                    txn = Transaction.objects.create(**kwargs)
                    break
        txn.save()
        return txn

    def process_transaction(self, txn, **kwargs):
        """
        Sends payment request
        """
        request = Request(self.userid, self.passkey, txn, kwargs)
        response = self._fetch_response(request, txn=txn)
        txn.state = 'RequestSent'
        txn.save()
        return response

    def process_response(self, **kwargs):
        """
        Post-processing transaction validation.
        """
        request = ProcessResponse(self.userid, self.passkey, kwargs)
        response = self._fetch_response(request)
        txn = Transaction.objects.get(TxnId=response.get_data['TxnId'])
        txn.state = 'Complete'
        txn.complete = True
        txn.save()
        return response
