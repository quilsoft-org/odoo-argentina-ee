# -*- encoding: utf-8 -*-
{
    'name': "Reporte de Libro Diario Contable",
    'version': "14.0.2.0.1",
    'author': "ADHOC SA, QUILSOFT",
    'website': "www.adhoc.com.ar",
    'category': "Localisation/Accounting",
    'license': "AGPL-3",
    'depends': [
        "account_reports",
        "report_xlsx",
    ],
    'data': [
        'wizard/account_journal_book_report_views.xml',
        "report/account_journal_book_report_xlsx.xml",
        'report/account_journal_book_report.xml',
        'report/report_account_journal_book.xml',
        'security/ir.model.access.csv',
        'views/account_views.xml',
        'views/account_journal_book_group_views.xml',
    ],
    'installable': True,
}
