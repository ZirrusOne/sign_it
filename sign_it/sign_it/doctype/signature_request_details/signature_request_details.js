frappe.ui.form.on("Signature Request Details", {
    refresh(frm) {
        if (!frm.is_new() && frm.doc.is_signed == 0) {
            // Send Email button

            // Get Webform Link button
            frm.add_custom_button('Get Form Link', () => {
                const webformLink = `${window.location.origin}/signature-request-details/new?encrypt=${cur_frm.doc.signature_url}`;
                // Display the Webform link using frappe.msgprint
                frappe.msgprint(webformLink);
            });


            frm.add_custom_button('Send Email', () => {
                frappe.call({
                    method: "sign_it.api.utils.send_email",
                    args: {
                        "docname": frm.doc.name
                    },
                    callback: function (r) {
                        if (!r.exc && r.message) {
                            frappe.msgprint('Sent Successfully');                            
                        } else {
                            frappe.msgprint(__('Unable to fetch details.'));
                        }
                    }
                });
            });

        }
    }
});
