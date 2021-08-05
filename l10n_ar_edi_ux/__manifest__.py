##############################################################################
#
#    Copyright (C) 2015  ADHOC SA  (http://www.adhoc.com.ar)
#    All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Argentinian Electronic Invoicing UX',
    'version': "14.0.1.0.0",
    'category': 'Localization/Argentina',
    'sequence': 14,
    'author': 'ADHOC SA, QUILSOFT',
    'website': 'www.quilsoft.com',
    'license': 'AGPL-3',
    'summary': '',
    'depends': [
        'l10n_ar_ux',
        'l10n_ar_edi',
    ],
    'external_dependencies': {
        'python': ['zeep'],
    },
    'data': [
        'wizards/res_config_settings_view.xml',
        'wizards/res_partner_update_from_padron_wizard_view.xml',
        'wizards/account_payment_group_invoice_wizard_view.xml',
        'views/res_partner_view.xml',
        'views/account_move_view.xml',
        'views/account_journal_view.xml',
    ],
    'demo': [
        'demo/res_partner_demo.xml',
    ],
    'installable': True,
    'auto_install': True,
    'application': False,
    'post_init_hook': 'post_init_hook',
}
