# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#    Copyright (C) 2014-2016 CodUP (<http://codup.com>).
#
##############################################################################

{
    'name': 'Cron',
    'version': '2.0',
    'category': 'Extra Tools',
    'summary': 'WSGI cron control',
    'description': """
WSGI cron control
-----------------
User interface for manually start cron.
Usefull if you use WSGI deployment.
    """,
    'author': 'CodUP',
    'website': 'http://codup.com',
    'depends': [],
    'demo': [],
    'data': [
        'wizard/start_cron_view.xml',
        'cron_view.xml',
    ],
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: