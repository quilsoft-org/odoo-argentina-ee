# -*- coding: utf-8 -*-

{
    "name": "Argentinian Electronic Invoicing CAEA",
    'version': '1.7',
    'category': 'Accounting/Localizations/EDI',
    'sequence': 14,
    'author': 'Quilsoft',

    'summary': """Habilita la gestion de CAEA en las facturas""",

    'description': """
        Habilita la gestion de CAEA en las facturas
    """,

    'website': "http://www.Quilsoft.com",

    'depends': ['l10n_ar_edi'],

    'data': [
        'views/afipws_caea.xml',
        'views/account_journal.xml',
        'views/account_move_view.xml',
        'wizards/l10n_ar_afipws_dummy.xml',
        'views/res_config_settings.xml',
        'views/asset.xml',
    ],
    'qweb': [
        'static/src/xml/systray_afip_caea.xml',
    ],

}
