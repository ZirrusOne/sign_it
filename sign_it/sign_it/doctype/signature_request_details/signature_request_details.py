# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document
from frappe.utils import add_to_date,nowdate
from frappe.utils import random_string
from sign_it.api.utils import send_email


class SignatureRequestDetails(Document):
	def before_insert(self):
		self.signature_url = random_string(20)
		self.expiry_date = add_to_date(nowdate(), days=7)

	def after_insert(self):
		send_email(self.name)

