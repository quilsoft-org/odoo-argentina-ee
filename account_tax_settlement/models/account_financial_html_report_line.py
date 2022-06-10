from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
import ast

class FormulaLine(object):
    def __init__(self, obj, currency_table, financial_report, type='balance', linesDict=None):
        if linesDict is None:
            linesDict = {}
        fields = dict((fn, 0.0) for fn in ['debit', 'credit', 'balance'])
        if type == 'balance':
            fields = obj._get_balance(linesDict, currency_table, financial_report)[0]
            linesDict[obj.code] = self
        elif type in ['sum', 'sum_if_pos', 'sum_if_neg']:
            if type == 'sum_if_neg':
                obj = obj.with_context(sum_if_neg=True)
            if type == 'sum_if_pos':
                obj = obj.with_context(sum_if_pos=True)
            if obj._name == 'account.financial.html.report.line':
                fields = obj._get_sum(currency_table, financial_report)
                self.amount_residual = fields['amount_residual']
            elif obj._name == 'account.move.line':
                self.amount_residual = 0.0
                field_names = ['debit', 'credit', 'balance', 'amount_residual']
                res = obj.env['account.financial.html.report.line']._compute_line(currency_table, financial_report)
                for field in field_names:
                    fields[field] = res[field]
                self.amount_residual = fields['amount_residual']
        elif type == 'not_computed':
            for field in fields:
                fields[field] = obj.get(field, 0)
            self.amount_residual = obj.get('amount_residual', 0)
        elif type == 'null':
            self.amount_residual = 0.0
        self.balance = fields['balance']
        self.credit = fields['credit']
        self.debit = fields['debit']

class FormulaContext(dict):
    def __init__(self, reportLineObj, linesDict, currency_table, financial_report, curObj=None, only_sum=False, *data):
        self.reportLineObj = reportLineObj
        self.curObj = curObj
        self.linesDict = linesDict
        self.currency_table = currency_table
        self.only_sum = only_sum
        self.financial_report = financial_report
        return super(FormulaContext, self).__init__(data)

    def __getitem__(self, item):
        formula_items = ['sum', 'sum_if_pos', 'sum_if_neg']
        if item in set(__builtins__.keys()) - set(formula_items):
            return super(FormulaContext, self).__getitem__(item)

        if self.only_sum and item not in formula_items:
            return FormulaLine(self.curObj, self.currency_table, self.financial_report, type='null')
        if self.get(item):
            return super(FormulaContext, self).__getitem__(item)
        if self.linesDict.get(item):
            return self.linesDict[item]
        if item == 'sum':
            res = FormulaLine(self.curObj, self.currency_table, self.financial_report, type='sum')
            self['sum'] = res
            return res
        if item == 'sum_if_pos':
            res = FormulaLine(self.curObj, self.currency_table, self.financial_report, type='sum_if_pos')
            self['sum_if_pos'] = res
            return res
        if item == 'sum_if_neg':
            res = FormulaLine(self.curObj, self.currency_table, self.financial_report, type='sum_if_neg')
            self['sum_if_neg'] = res
            return res
        if item == 'NDays':
            d1 = fields.Date.from_string(self.curObj.env.context['date_from'])
            d2 = fields.Date.from_string(self.curObj.env.context['date_to'])
            res = (d2 - d1).days
            self['NDays'] = res
            return res
        if item == 'count_rows':
            return self.curObj._get_rows_count()
        if item == 'from_context':
            return self.curObj._get_value_from_context()
        line_id = self.reportLineObj.search([('code', '=', item)], limit=1)
        if line_id:
            date_from, date_to, strict_range = line_id._compute_date_range()
            res = FormulaLine(line_id.with_context(strict_range=strict_range, date_from=date_from, date_to=date_to), self.currency_table, self.financial_report, linesDict=self.linesDict)
            self.linesDict[item] = res
            return res
        return super(FormulaContext, self).__getitem__(item)


class AccountFinancialReport(models.Model):
    _inherit = "account.financial.html.report"

    def create_tax_settlement_entry(self, journal):
        """
        Funcion que crea asiento de liquidación a partir de información del
        reporte y devuelve browse del asiento generado
        * from_report_id
        * force_context
        * context: periods_number, cash_basis, date_filter_cmp, date_filter,
        date_to, date_from, hierarchy_3, company_ids, date_to_cmp,
        date_from_cmp, all_entries
        * search_disable_custom_filters
        * from_report_model
        * active_id
        """
        self.ensure_one()

        # obtenemos lineas de este reporte que tengan revert (sin importar
        # dominio o no porque en realidad puede estar seteado en linea padre
        # sin dominio)
        revert_lines = self.line_ids.search([
            ('id', 'child_of', self.line_ids.ids),
            ('settlement_type', '=', 'revert'),
        ])

        # obtenemos todas las lineas hijas de las que obtuvimos que tengan
        # dominio (esto es para evitar tener que
        # configurar revert en cada linea hija)
        revert_lines = self.line_ids.search([
            ('id', 'child_of', revert_lines.ids),
            ('domain', '!=', False),
            ('settlement_type', 'in', ['revert', False])
        ])

        move_lines = self.env['account.move.line']
        # TODO podriamos en vez de usar el report_move_lines_action para
        # obtener domain, usar directamente el "_compute_line" o el "_get_sum"
        # pero deberiamos luego cambiar la logica del grouped move lines
        # o en realidad estariamos repidiento casi dos veces lo mismo
        domains = []
        for line in revert_lines:
            domains.append(line.report_move_lines_action()['domain'])
        domain = expression.OR(domains)

        lines_vals = journal._get_tax_settlement_entry_lines_vals(domain)

        # agregamos otrs lineas ẗipo "new line"
        new_lines = self.line_ids.search([
            ('id', 'child_of', self.line_ids.ids),
            ('settlement_type', 'in', ['new_line', 'new_line_negative'])])

        # pasamos por contexto lo que viene adentro del contetxo como contexto
        # porque asi lo interpreta _get_balance (en vez aparentemente
        # report_move_lines_action busca dentro del contexto)
        new_lines = new_lines.with_context(
            new_lines._context.get('context'))
        for new_line in new_lines:
            account = self.env['account.account'].search([
                ('company_id', '=', journal.company_id.id),
                ('tag_ids', '=', new_line.settement_account_tag_id.id)],
                limit=1)
            if not account:
                raise ValidationError(_(
                    'No account found with tag "%s" (id: %s) for company "%s".'
                    ' Check report and accounts configuration.') % (
                    new_line.settement_account_tag_id.name,
                    new_line.settement_account_tag_id.id,
                    journal.company_id.name))
            balance = sum(
                [x['balance'] for x in new_line._get_balance(
                    {}, {}, self, field_names=['balance'])])
            if journal.company_id.currency_id.is_zero(balance):
                continue
            balance = new_line.settlement_type == 'new_line' \
                and balance or balance * -1.0
            lines_vals.append({
                'name': self.name,
                'debit': balance < 0.0 and -balance,
                'credit': balance >= 0.0 and balance,
                'account_id': account.id,
            })

        vals = journal._get_tax_settlement_entry_vals(lines_vals)
        move = self.env['account.move'].with_context(
            allow_no_partner=True).create(vals)

        if self._context.get('tax_settlement_link', True):
            move_lines.write({'tax_settlement_move_id': move.id})
        return move


class AccountFinancialReportLine(models.Model):
    _inherit = "account.financial.html.report.line"

    settlement_type = fields.Selection([
        ('new_line', 'New Journal Item'),
        ('new_line_negative', 'New Journal Item (negative)'),
        ('revert', 'Revert Journal Item'),
    ], help="If you choose:\n"
        "* New Journal Item: a new journal item with selected account will be "
        "created\n"
        "* New Journal Item (negative): a new journal item with selected "
        "account will be created (amount * -1)"
        "* Revert Journal Item: a line reverting this line will be created",
    )
    settement_account_tag_id = fields.Many2one(
        'account.account.tag',
        domain=[('applicability', '=', 'accounts')],
        context={'default_applicability': 'accounts'},
        string='Etiquetas de Cuenta',
        help='Si se eligió "Nuevo Apunte Contable", para la nueva línea, '
        'Se va a buscar una cuenta con esta etiqueta de cuenta',
    )

    def report_move_lines_action(self):
        domain = ast.literal_eval(self.domain)
        if 'date_from' in self.env.context.get('context', {}):
            if self.env.context['context'].get('date_from'):
                domain = expression.AND([domain, [('date', '>=', self.env.context['context']['date_from'])]])
            if self.env.context['context'].get('date_to'):
                domain = expression.AND([domain, [('date', '<=', self.env.context['context']['date_to'])]])
            if self.env.context['context'].get('state', 'all') == 'posted':
                domain = expression.AND([domain, [('move_id.state', '=', 'posted')]])
            if self.env.context['context'].get('company_ids'):
                domain = expression.AND([domain, [('company_id', 'in', self.env.context['context']['company_ids'])]])
        return {'type': 'ir.actions.act_window',
                'name': 'Journal Items (%s)' % self.name,
                'res_model': 'account.move.line',
                'view_mode': 'tree,form',
                'domain': domain,
                }

    def _get_balance(self, linesDict, currency_table, financial_report, field_names=None):
        results = []

        if not field_names:
            field_names = ['debit', 'credit', 'balance']

        for rec in self:
            res = dict((fn, 0.0) for fn in field_names)
            c = FormulaContext(self.env['account.financial.html.report.line'],
                    linesDict, currency_table, financial_report, rec)
            if rec.formulas:
                for f in rec.formulas.split(';'):
                    [field, formula] = f.split('+')
                    field = field.strip()
                    if field in field_names:
                        try:
                            res[field] = safe_eval(formula, c, nocopy=True)
                        except ValueError as err:
                            if 'division by zero' in err.args[0]:
                                res[field] = 0
                            else:
                                raise err
            results.append(res)
        return results