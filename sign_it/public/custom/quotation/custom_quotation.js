frappe.ui.form.on('Quotation', {
    refresh(frm) {
        if (!frm.is_new()) {
            // Add the custom button to trigger the signature check
            frm.add_custom_button('Send Signature Request', function () {

                // Call the API to check if a signed Signature Request exists
                frappe.call({
                    method: 'sign_it.api.utils.check_signed_signature_request',
                    args: {
                        doctype: frm.doc.doctype,
                        docname: frm.doc.name
                    },
                    freeze: true, // Freezes the UI while the request is being processed
                    freeze_message: __('Checking signature status...'), // Message during freeze
                    callback: function (r) {
                        if (r.message.exists) {
                            // If a signed request exists, display the signature details
                            const signatureDetails = r.message.details;

                            // Show a message with signature details
                            frappe.msgprint({
                                title: __('Signature Details'),
                                indicator: 'blue',
                                message: `
                                <p>${__('Signature already added.')}</p>
                                <p><b>${__('Signed Date:')}</b> ${signatureDetails.signed_date || __('N/A')}</p>
                                <p><b>${__('Signed By:')}</b> ${signatureDetails.signed_by || __('N/A')}</p>
                                <p><b>${__('Signature:')}</b> <img src="${signatureDetails.signature || ''}" alt="Signature" style="max-width: 100%;"></p>
                            `
                            });
                        } else {
                            // If no signed request exists, show the email dialog
                            let email_dialog = new frappe.ui.Dialog({
                                title: 'Emails',
                                fields: [
                                    {
                                        fieldname: 'signature_template',
                                        fieldtype: 'Link',
                                        label: 'Signature Template',
                                        options: 'Signature Template',
                                        reqd: 1,
                                        get_query() {
                                            return {
                                                filters: {
                                                    reference_doctype: frm.doc.doctype
                                                }
                                            };
                                        }
                                    },
                                    {
                                        fieldname: 'email_table',
                                        fieldtype: 'Table',
                                        label: 'Emails',
                                        cannot_add_rows: false, // Allow adding new rows
                                        in_place_edit: false, // Prevent editing in place
                                        fields: [
                                            {
                                                fieldname: 'email',
                                                fieldtype: 'Data',
                                                label: 'Email',
                                                reqd: 1,
                                                in_list_view: 1,
                                                options: 'Email',
                                            }
                                        ]
                                    }
                                ],
                                primary_action_label: 'Submit',
                                primary_action(values) {
                                    if (validate_emails(values.email_table)) {

                                        // Call the backend method to create or get the signature request
                                        frappe.call({
                                            method: 'sign_it.api.utils.get_or_create_signature_request',
                                            args: {
                                                doctype: frm.doc.doctype,
                                                docname: frm.doc.name,
                                                signature_template: values.signature_template,
                                                email_list: values.email_table
                                            },
                                            freeze: true, // Freezes the UI
                                            freeze_message: __('Processing your request...'),
                                            callback: function (r) {
                                                if (r.message) {
                                                    frappe.show_alert({
                                                        message: __(r.message.text),
                                                        indicator: 'green'
                                                    });
                                                    email_dialog.hide();
                                                }
                                            }
                                        });
                                    }
                                }
                            });

                            email_dialog.show();
                        }
                    },
                    error: function () {
                        frappe.msgprint({
                            title: __('Error'),
                            indicator: 'red',
                            message: __('Unable to check the signature status. Please try again.')
                        });
                    }
                });
            });

        }

    }
});

// Function to validate emails and show toast notifications for invalid ones
function validate_emails(email_table) {
    let is_valid = true;
    $.each(email_table, function (i, row) {
        if (!frappe.utils.validate_type(row.email, "email")) {
            is_valid = false;
            frappe.msgprint({
                title: __('Invalid Email'),
                indicator: 'red',
                message: __('The email <b>{0}</b> is invalid.', [row.email])
            });
        }
    });
    return is_valid;
}
