app_name = "kvh_ops"
app_title = "KVH Operations"
app_publisher = "KVH Industries"
app_description = "KVH Industries Operations Management System - migrated from Lovable to ERPNext/Frappe"
app_email = "admin@kvhindustries.com"
app_license = "MIT"
app_version = "1.0.0"

required_apps = ["erpnext", "crm"]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/kvh_ops/css/kvh_ops.css"
# app_include_js = "/assets/kvh_ops/js/kvh_ops.js"

# include js, css files in header of web template
# web_include_css = "/assets/kvh_ops/css/kvh_ops_web.css"
# web_include_js = "/assets/kvh_ops/js/kvh_ops_web.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "kvh_ops/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#     "methods": "kvh_ops.utils.jinja_methods",
#     "filters": "kvh_ops.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "kvh_ops.install.before_install"
after_install = "kvh_ops.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "kvh_ops.uninstall.before_uninstall"
# after_uninstall = "kvh_ops.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "kvh_ops.utils.before_app_install"
# after_app_install = "kvh_ops.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "kvh_ops.utils.before_app_uninstall"
# after_app_uninstall = "kvh_ops.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "kvh_ops.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#     "Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#     "Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#     "ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Sales Order": {
        "validate": "kvh_ops.overrides.sales_order.validate",
        "before_submit": "kvh_ops.overrides.sales_order.before_submit",
        "on_submit": "kvh_ops.overrides.sales_order.on_submit",
        "on_cancel": "kvh_ops.overrides.sales_order.on_cancel",
    },
    "CRM Lead": {
        "before_insert": "kvh_ops.overrides.crm_lead.before_insert",
        "after_insert": "kvh_ops.overrides.crm_lead.after_insert",
        "before_save": "kvh_ops.overrides.crm_lead.before_save",
        "on_update": "kvh_ops.overrides.crm_lead.on_update",
    },
    "Purchase Order": {
        "on_submit": "kvh_ops.overrides.purchase_order.on_submit",
        "on_update_after_submit": "kvh_ops.overrides.purchase_order.on_update_after_submit",
    },
    "Stock Entry": {
        "on_submit": "kvh_ops.overrides.stock_entry.on_submit",
    },
}

# Scheduled Tasks
# ---------------

scheduler_events = {
    "daily": [
        "kvh_ops.tasks.daily.check_overdue_deliveries",
        "kvh_ops.tasks.daily.check_sla_breaches",
        "kvh_ops.tasks.daily.sync_lead_followups",
        "kvh_ops.tasks.daily.check_subscription_renewals",
        "kvh_ops.tasks.daily.expire_edit_requests",
    ],
}

# Testing
# -------

# before_tests = "kvh_ops.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#     "frappe.desk.doctype.event.event.get_permission_query_conditions": "kvh_ops.event.get_permission_query_conditions"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#     "Task": "kvh_ops.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["kvh_ops.utils.before_request"]
# after_request = ["kvh_ops.utils.after_request"]

# Job Events
# ----------
# before_job = ["kvh_ops.utils.before_job"]
# after_job = ["kvh_ops.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
#     {
#         "doctype": "{doctype_1}",
#         "filter_by": "{filter_by}",
#         "redact_fields": ["{field_1}", "{field_2}"],
#         "partial": 1,
#     },
#     {
#         "doctype": "{doctype_2}",
#         "filter_by": "{filter_by}",
#         "partial": 1,
#     },
#     {
#         "doctype": "{doctype_3}",
#         "is_table": True,
#         "redact_fields": ["{field_1}", "{field_2}"],
#     },
# ]

# Authentication and authorization
# ---------------------------------

# auth_hooks = [
#     "kvh_ops.auth.validate"
# ]

# Automatically update this file when field definitions for DocTypes change
# This is very useful during development when you push your changes
# to a repo and someone else pulls
fixtures = [
    {
        "dt": "Role",
        "filters": [
            [
                "name",
                "in",
                [
                    "KVH Admin",
                    "KVH CRE",
                    "KVH Sales Head",
                    "KVH BDM",
                    "KVH Design Team",
                    "KVH Production Head",
                    "KVH Production Manager",
                    "KVH Factory Supervisor",
                    "KVH Store Keeper",
                    "KVH Purchase Officer",
                    "KVH Marketing Head",
                    "KVH Marketing Member",
                    "KVH Operation Manager",
                ],
            ]
        ],
    },
    {
        "dt": "Custom Field",
        "filters": [["module", "=", "KVH Ops"]],
    },
    {
        "dt": "Property Setter",
        "filters": [["module", "=", "KVH Ops"]],
    },
    {
        "dt": "Client Script",
        "filters": [["module", "=", "KVH Ops"]],
    },
    {
        "dt": "Server Script",
        "filters": [["module", "=", "KVH Ops"]],
    },
    {
        "dt": "Notification",
        "filters": [["module", "=", "KVH Ops"]],
    },
]
