# -*- coding: utf-8 -*-

{
    'name': "CMO :: Human Resource Extension",
    'summary': "",
    'author': "Phongyanon Y.",
    'website': "http://ecosoft.co.th",
    'category': 'Tools',
    "version": "1.0",
    'depends': [
        'hr_expense_auto_invoice',
        'hr_expense_advance_clearing',
        'l10n_th_doctype_expense',
    ],
    'data': [
        'views/hr_view.xml',
        'workflow/cmo_hr_workflow.xml'
    ],
    'demo': [
    ],
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
