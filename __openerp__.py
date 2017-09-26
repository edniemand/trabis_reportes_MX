# -*- coding: utf-8 -*-
{
    'name': 'Reportes contables MX Trabis',
    'version': '1.1',
    'summary': 'Modulo agrega funcionalidades extras a los reportes contables de Argil.',
    'category': 'Trabis',
    'description': """
    Reportes:
    -Balance General
    -Estado de Resultados
    """,
    'author': 'Samuel Martinez',
    'website': 'http://www.trabis.com.mx',
    'depends': ['base','account','argil_mx_accounting_reports_consol'],
    'data': [
        'security/ir.model.access.csv',
        'balance_general_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: