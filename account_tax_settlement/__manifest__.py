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
    'name': 'Tax Settlement',
    'version': '14.0.1.0.0',
    'category': 'Accounting',
    'sequence': 14,
    'summary': '',
    'author': 'ADHOC SA, QUILSOFT',
    'website': 'www.quilsoft.com',
    'license': 'AGPL-3',
    'images': [
    ],
    'depends': [
        # por ahora agregamos esta dep para permitir vincular a reportes
        'account_reports',
        # dependencia porque llevamos a pagos y tmb porque usamos el boton
        # en apuntes contables para abrir documento relacionado
        'account_payment_group',
    ],
    'data': [
        'wizards/account_tax_settlement_wizard_view.xml',
        'wizards/get_dates_wizard_view.xml',
        'wizards/download_files_wizard.xml',
        'views/account_move_line_view.xml',
        'views/account_move_view.xml',
        'views/account_journal_view.xml',
        'views/account_journal_dashboard_view.xml',
        'views/account_financial_html_report_line_view.xml',
    ],
    'demo': [
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': True,
    'application': False,
}
