# -*- coding: utf-8 -*-
{
    "name": "CMO :: Project Extension",
    "summary": "",
    "version": "1.0",
    "category": "Project",
    "description": """

* Additional fields for project master

    """,
    "website": "http://ecosoft.co.th",
    "author": "Kitti U., Phongyanon Y.",
    "license": "AGPL-3",
    "depends": [
        'project',
        'account_auto_fy_sequence',
    ],
    "data": [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/cmo_project_sequence.xml',
        'data/project_data.xml',
        'wizard/close_reason_view.xml',
        'wizard/hold_reason_view.xml',
        'views/project_view.xml',
        'views/master_data_view.xml',
        'views/customer_view.xml',
        'views/account_view.xml',
    ],
    "application": False,
    "installable": True,
}
