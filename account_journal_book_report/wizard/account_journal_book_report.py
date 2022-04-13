# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################
from odoo import api, fields, models
from dateutil.relativedelta import relativedelta
from io import BytesIO
buffer = BytesIO()


class AccountJournalBookReport(models.TransientModel):
    _inherit = "account.common.report"
    _name = "account.journal.book.report"
    _description = "Journal Book Report"

    # este campo ya existe en la clase oficial, lo recreamos
    # para cambiar la rel
    journal_ids = fields.Many2many(
        'account.journal',
        'account_journal_book_journal_rel',
        'acc_journal_entries_id',
        'journal_id',
        'Journals',
        required=True,
        ondelete='cascade',
    )
    last_entry_number = fields.Integer(
        string='Último número de asiento',
        required=True,
        default=0,
    )
    date_from = fields.Date(
        required=True,
    )
    date_to = fields.Date(
        required=True,
    )

    report_file = fields.Binary('Reporte')
    file_name = fields.Char('File Name')
    report_exported = fields.Boolean('Report File Exportado')

    @api.onchange('company_id')
    def _onchange_company_id(self):
        dates = self.company_id.compute_fiscalyear_dates(
            fields.Date.from_string(fields.Date.today()))
        if dates:
            self.date_from = dates['date_from']
            self.date_to = dates['date_to']


    def _print_report(self,data):
        date_from = fields.Date.from_string(self.date_from)
        date_to = fields.Date.from_string(self.date_to)
        periods = []
        # por mas que el usuario pida fecha distinta al 1 del mes, los move
        # lines ya van a estar filtrados por esa fecha y por simplicidad
        # construimos periodos desde el 1
        dt_from = date_from.replace(day=1)
        while dt_from < date_to:
            dt_to = dt_from + relativedelta(months=1, days=-1)
            periods.append((fields.Date.to_string(dt_from),
                            fields.Date.to_string(dt_to)))
            # este va a se la date from del proximo
            dt_from = dt_to + relativedelta(days=1)
        domain = [('company_id', '=', self.company_id.id)]
        if self.target_move == 'posted':
            domain.append(('state', '=', 'posted'))
        if self.date_from:
            domain.append(('date', '>=', self.date_from))
        if self.date_to:
            domain.append(('date', '<=', self.date_to))
        moves = self.env['account.move'].search(domain)

        data = {
            'last_entry_number': self.last_entry_number,
            'periods': periods,
            'moves': moves.ids
        }
        return self.env.ref('account_journal_book_report.action_account_journal_book_report_xlsx').\
            report_action(self, data=data)


class JournalBookReportXlsx(models.AbstractModel):
    _name = "report.account_journal_book_report.journal_book_report_xslx"
    _description = "Libro Diario"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self,workbook,data,partners):
        report_name = 'JournalReport'
        sheet = workbook.add_worksheet(report_name)
        format_header = workbook.add_format({'bold': True})
        format_date = workbook.add_format({'num_format': 'dd/mm/yy'})
        sheet.write(0, 3, 'Libro Diario',format_header)
        sheet.write(4, 0, 'No',format_header)
        sheet.write(4, 1, 'Fecha',format_header)
        sheet.write(4, 2, 'Descripcion / Cuenta',format_header)
        sheet.write(4, 4, 'Debe',format_header)
        sheet.write(4, 5, 'Haber',format_header)

        moves_ids = data.get('moves')
        last_entry_number = data.get('last_entry_number')
        periods_ids = data.get('periods')
        initial_row = 5
        num = 1 if last_entry_number == 0 else last_entry_number
        for p in periods_ids:
            for move in self.env['account.move'].search([('id', 'in', moves_ids), ('date', '>=', p[0]), ('date', '<=', p[1]), ('journal_id.book_group_id', '=', False)], order='date, id'):
                sheet.write(initial_row, 0, num)
                sheet.write(initial_row, 1, move.date, format_date)
                sheet.write(initial_row, 1, move.date, format_date)
                partner = move.partner_id.name if move.partner_id else ''
                sheet.write(initial_row, 2, move.name + ' - ' + partner)
                for line in move.line_ids.sorted(lambda x: x.credit):
                    initial_row += 1
                    sheet.write(initial_row, 2, line.account_id.code)
                    sheet.write(initial_row, 3, line.account_id.name)
                    sheet.write(initial_row, 4, line.debit)
                    sheet.write(initial_row, 5, line.credit)
                initial_row += 1
                num += 1
            for move_g in self.env['account.move.line'].search([('move_id', 'in', moves_ids), ('date', '>=', p[0]), ('date', '<=', p[1]), ('journal_id.book_group_id', '!=', False)]).mapped('journal_id.book_group_id'):
                sheet.write(initial_row, 0, num)
                sheet.write(initial_row, 1, p[1], format_date)
                sheet.write(initial_row, 2, move_g.name)
                for line_g in self.env['account.move.line'].read_group([('move_id', 'in', moves_ids), ('date', '>=', p[0]), ('date', '<=', p[1]), ('journal_id.book_group_id', '=', move_g.id), ('debit', '>', 0.0)], ['account_id', 'debit', 'credit'], ['account_id'], orderby='debit desc') + self.env['account.move.line'].read_group([('move_id', 'in', moves_ids), ('journal_id.book_group_id', '=', move_g.id), ('credit', '>', 0.0)], ['account_id', 'debit', 'credit'], ['account_id'], orderby='debit desc'):
                    initial_row += 1
                    sheet.write(initial_row, 2, self.env['account.account'].browse(line_g.get('account_id')[0]).code if line_g.get('account_id') else '')
                    sheet.write(initial_row, 3, self.env['account.account'].browse(line_g.get('account_id')[0]).name if line_g.get('account_id') else '')
                    sheet.write(initial_row, 4, line_g.get('debit'))
                    sheet.write(initial_row, 5, line_g.get('credit'))
                initial_row += 1
                num += 1
