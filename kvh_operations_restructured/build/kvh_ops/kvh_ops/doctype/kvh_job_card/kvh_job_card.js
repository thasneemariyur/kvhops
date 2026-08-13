frappe.ui.form.on('KVH Job Card', {
    refresh: function(frm) {
        // Add stage progression buttons
        if (!frm.is_new() && !frm.doc.docstatus) {
            frm.add_custom_button(__('Update Factory Stage'), function() {
                show_stage_update_dialog(frm);
            }, __('Actions'));

            frm.add_custom_button(__('View Stage History'), function() {
                frappe.route_options = { job_card: frm.doc.name };
                frappe.set_route('List', 'KVH Stage Event');
            }, __('Actions'));
        }

        // Color-code factory stage field
        color_stage_badge(frm);

        // Show rework button for factory supervisor
        if (frappe.user.has_role(['KVH Factory Supervisor', 'KVH Production Head', 'KVH Production Manager', 'KVH Admin'])) {
            frm.add_custom_button(__('Log Rework'), function() {
                show_rework_dialog(frm);
            }, __('Actions'));
        }
    },

    factory_stage: function(frm) {
        frm.set_value('stage_updated_at', frappe.datetime.now_datetime());
        frm.set_value('stage_updated_by', frappe.session.user);
    },

    design_status: function(frm) {
        if (frm.doc.design_status === 'Completed' && !frm.doc.design_completed_at) {
            frm.set_value('design_completed_at', frappe.datetime.now_datetime());
        }
    }
});

function color_stage_badge(frm) {
    const stage_colors = {
        'Pending': '#94a3b8',
        'CNC': '#6366f1',
        'Fabrication': '#3b82f6',
        'Surface Finishing': '#06b6d4',
        'Primer Coating': '#10b981',
        'Powder Coating': '#f59e0b',
        'PU Foam Filling': '#f97316',
        'Accessories': '#ec4899',
        'Packing': '#8b5cf6',
        'Installation': '#0ea5e9',
        'Ready': '#22c55e',
        'Dispatched': '#64748b'
    };

    const stage = frm.doc.factory_stage;
    if (stage && stage_colors[stage]) {
        frm.set_indicator_formatter('factory_stage',
            function(doc) { return 'blue'; }
        );
    }
}

function show_stage_update_dialog(frm) {
    const stages = [
        'Pending', 'CNC', 'Fabrication', 'Surface Finishing', 'Primer Coating',
        'Powder Coating', 'PU Foam Filling', 'Accessories', 'Packing',
        'Installation', 'Ready', 'Dispatched'
    ];

    const d = new frappe.ui.Dialog({
        title: __('Update Factory Stage'),
        fields: [
            {
                label: __('New Stage'),
                fieldname: 'new_stage',
                fieldtype: 'Select',
                options: stages.join('\n'),
                default: frm.doc.factory_stage,
                reqd: 1
            },
            {
                label: __('Notes'),
                fieldname: 'notes',
                fieldtype: 'Small Text'
            }
        ],
        primary_action_label: __('Update Stage'),
        primary_action: function(values) {
            frm.set_value('factory_stage', values.new_stage);
            if (values.notes) {
                frm.set_value('notes', (frm.doc.notes || '') + '\n' + values.notes);
            }
            frm.save().then(() => {
                d.hide();
                frappe.show_alert({message: __('Stage updated to: ') + values.new_stage, indicator: 'green'});
            });
        }
    });
    d.show();
}

function show_rework_dialog(frm) {
    const d = new frappe.ui.Dialog({
        title: __('Log Rework'),
        fields: [
            {
                label: __('Rework Reason'),
                fieldname: 'reason',
                fieldtype: 'Select',
                options: [
                    'Wrong measurement',
                    'Surface defect',
                    'Damaged in transit',
                    'Customer change',
                    'Quality rejection'
                ].join('\n'),
                reqd: 1
            },
            {
                label: __('Stage'),
                fieldname: 'stage',
                fieldtype: 'Data',
                default: frm.doc.factory_stage
            },
            {
                label: __('Description'),
                fieldname: 'description',
                fieldtype: 'Small Text',
                reqd: 1
            }
        ],
        primary_action_label: __('Log Rework'),
        primary_action: function(values) {
            frappe.call({
                method: 'frappe.client.insert',
                args: {
                    doc: {
                        doctype: 'KVH Rework',
                        job_card: frm.doc.name,
                        sales_order: frm.doc.sales_order,
                        reason: values.reason,
                        stage: values.stage,
                        description: values.description,
                        status: 'Open'
                    }
                },
                callback: function(r) {
                    if (r.message) {
                        d.hide();
                        frappe.show_alert({
                            message: __('Rework logged: ') + r.message.name,
                            indicator: 'orange'
                        });
                    }
                }
            });
        }
    });
    d.show();
}
