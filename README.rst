django-pxpay
============

PaymentExpress PxPay Gateway for Django

Installation:
-------------

``pip install django-pxpay``
or
``easy_install django-pxpay``

Usage:
------

You'll need to add a few items in your ``settings.py``: ``PXPAY_USERID``,
``PXPAY_KEY`` and, optionally, ``PXPAY_CURRENCY``.

.. code-block:: python

	from django.shortcuts import redirect, render_to_response
	from django.template.context import RequestContext
	from django.http import Http404
	from pxpay.gateway import Gateway
	
	
	def payment(request, amount):
	    # Create a transaction.
	    txn = Gateway().transaction(
	        TxnType='Purchase',
	        AmountInput='%.2f' % amount,
	        CurrencyInput='AUD',  # Alternatively, can be provided in settings.py
	        MerchantReference='Some reference')
	
	    # Send payment request.
	    response = Gateway().process_transaction(
	        txn,
	        UrlFail=request.build_absolute_uri(reverse('process_payment')),
	        UrlSuccess=request.build_absolute_uri(reverse('process_payment')))
	
	    # Redirect to PaymentExpress hosted payment page.
	    if response.is_valid:
	        return redirect(response.get_data['URI'])
	
	    # Show error.
	    else:
	        return payment_result(request, False, 'Invalid Transaction Request')
	
	
	def process_payment(request):
	    # Proper PaymentExpress request would always have these.
	    if 'result' in request.GET and 'userid' in request.GET:
	
	        # Process PaymentExpress response.
	        process_response = Gateway().process_response(
	            Response=request.GET['result'])
	
	        # Show payment result.
	        return payment_result(
	            request,
	            bool(int(process_response.get_data['Success'])),
	            process_response.get_data['ResponseText'])
	
	    # Rise 404 if no required arguments were passed.
	    raise Http404
	
	
	def payment_result(request, success, msg):
	    return render_to_response(
	        'payment.html',
	        {'success': success, 'msg': msg},
	        context_instance=RequestContext(request))
	

