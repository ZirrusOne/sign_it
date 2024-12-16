import frappe
from frappe.model.document import Document
from collections import namedtuple
from frappe.utils import add_to_date, cast, nowdate, validate_email_address,getdate
import frappe.utils
from frappe.utils.safe_exec import get_safe_globals
from frappe.utils import random_string


@frappe.whitelist()
def get_or_create_signature_request(doctype, docname, signature_template, email_list):
	try:
		email_list = frappe.parse_json(email_list)  # Convert JSON string to Python list
		

		# Check if a signed request already exists
		if frappe.db.exists("Signature Request Details", {"reference_doctype": doctype, "reference_docname": docname, 'is_signed': 1}):
			signature_request = frappe.get_doc("Signature Request Details", {"reference_doctype": doctype, "reference_docname": docname, 'is_signed': 1})
			return {'text': 'Signature already added.', 'doc': signature_request}

		# Check if an unsigned request exists
		elif frappe.db.exists("Signature Request Details", {"reference_doctype": doctype, "reference_docname": docname, 'is_signed': 0}):
			signature_request = frappe.get_doc("Signature Request Details", {"reference_doctype": doctype, "reference_docname": docname, 'is_signed': 0})
			signature_request.signature_template = signature_template

			# Add new emails to the request
			for email in email_list:
				if not frappe.db.exists("Signature Request Email", {'parent': signature_request.name, 'email':  email.get('email')}):
					signature_request.append("signature_request_email",{ 'email':email.get('email')})


			signature_request.save(ignore_permissions=True)
			send_email(signature_request.name)
			frappe.db.commit()
			return {'text': 'Email added successfully.', 'doc': signature_request}

		# Create a new signature request
		else:
			signature_request = frappe.new_doc("Signature Request Details")
			signature_request.reference_doctype = doctype
			signature_request.reference_docname = docname
			signature_request.signature_template = signature_template

			# Add emails to the new request
			for email in email_list:
				signature_request.append("signature_request_email", {
					'email': email.get('email')
				})
    
			signature_request.save(ignore_permissions=True)

			frappe.db.commit()
			return {'text': 'Signature Request sent successfully.', 'doc': signature_request}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Signature Request Error")
		return frappe.throw('An error occurred while processing the request.')




@frappe.whitelist()
def check_signed_signature_request(doctype, docname):
    try:
        # Check if a signed Signature Request Details exists
        signed_request = frappe.db.get_value(
            "Signature Request Details",
            {"reference_doctype": doctype, "reference_docname": docname, "is_signed": 1},
            ["name", "signed_date", "signed_by", "signature"]
        )

        if signed_request:
            return {
                "exists": True,
                "details": {
                    "name": signed_request[0],
                    "signed_date": signed_request[1],
                    "signed_by": signed_request[2],
                    "signature": signed_request[3]
                }
            }
        else:
            return {"exists": False}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Check Signed Signature Request Error")
        frappe.throw(_("An error occurred while checking the signature request."))






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

 
	doc = frappe.get_doc(sign_doc.reference_doctype, sign_doc.reference_docname)
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
	subject = f"Signature Request for {doc.reference_doctype} {doc.reference_docname}"
	context = {'doc':doc}
	message = frappe.render_template("sign_it/templates/emails/signature_request.html",context)
	for row in doc.signature_request_email:
		frappe.sendmail(recipients=row.email, subject=subject, content=message)
		frappe.db.commit()
