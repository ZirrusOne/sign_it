// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Signature Request Details", {
    refresh(frm) {
        if (!frm.is_new() && frm.doc.is_signed == 0 ) {
            frm.add_custom_button('Send Email', () => {
                frappe.call({
                    method: "sign_it.sign_it.doctype.signature_request_details.signature_request_details.send_email",
                    args: {
                        "docname": frm.doc.name
                    },
                    callback: function (r) {
                        if (!r.exc && r.message) {
                            frappe.msgprint('Sent Successfully')                            
                        } else {
                            frappe.msgprint(__('Unable to fetch details.'));
                        }
                    }
                });
            });
        }
    }
});
