# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document
from collections import namedtuple
from frappe.utils import add_to_date, cast, nowdate, validate_email_address,getdate
import frappe.utils
from frappe.utils.safe_exec import get_safe_globals
from frappe.utils import random_string

class SignatureRequestDetails(Document):
	def before_insert(self):
		self.signature_url = random_string(20)
		self.expiry_date = add_to_date(nowdate(), days=7)

	def after_insert(self):
		send_email(self.name)



@frappe.whitelist()
def get_context(doc):
	Frappe = namedtuple("frappe", ["utils"])
	return {
		"doc": doc,
		"nowdate": nowdate,
		"frappe": Frappe(utils=get_safe_globals().get("frappe").get("utils")),
	}



@frappe.whitelist(allow_guest=True)	
def get_document(signature_url):
	signature_url =  frappe.db.get_value("Signature Request Details", {"signature_url": signature_url}, "name")
	if not signature_url:
		return frappe.throw("Signature Request Details not found")

	sign_doc = frappe.get_doc("Signature Request Details", signature_url)  
 
	if sign_doc.is_signed :
		return frappe.throw("Signature already added.")
	if sign_doc.expiry_date < getdate():
		return frappe.throw("Signature Request Details expired.")

 
	doc = frappe.get_doc(sign_doc.document_type, sign_doc.docname)

	context = get_context(doc)
	template = sign_doc.document


	return frappe.render_template(template, context)



@frappe.whitelist(allow_guest=True)
def get_signature(signature_url):
	signature_url =  frappe.db.get_value("Signature Request Details", {"signature_url": signature_url}, "name")
	if not signature_url:
		return frappe.throw("Signature Request Details not found")

	signedBy =  frappe.form_dict.signedBy
	signedDate =  frappe.form_dict.signedDate
	signatureData =  frappe.form_dict.signatureData
		
	sign_doc = frappe.get_doc("Signature Request Details", signature_url)
	if sign_doc.is_signed:
		return frappe.throw("Signature already added.")

	if sign_doc.expiry_date < getdate():
		return frappe.throw("Signature Request Details expired.")

	allowed_emails = [row.email for row in sign_doc.signature_request_email]
	if signedBy not in allowed_emails:
		frappe.throw(f"Email '{signedBy}' is not authorized to sign this document.")



	sign_doc.signed_by = signedBy
	sign_doc.signed_date = frappe.utils.getdate(signedDate)
	sign_doc.signature = signatureData
	sign_doc.is_signed = 1
	sign_doc.save(ignore_permissions=True)
	frappe.db.commit()
	frappe.msgprint("Signature added successfully.")

	return sign_doc
 

@frappe.whitelist()
def send_email(docname):
	doc = frappe.get_doc("Signature Request Details", docname)
	subject = f"Signature Request for {doc.document_type} {doc.docname}"
	context = {'doc':doc}
	message = frappe.render_template("sign_it/templates/emails/signature_request.html",context)
	for row in doc.signature_request_email:
		frappe.sendmail(recipients=row.email, subject=subject, content=message)
		frappe.db.commit()
