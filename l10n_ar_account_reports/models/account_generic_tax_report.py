# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models
from odoo.tools.translate import _
from collections import defaultdict
from odoo.exceptions import UserError
from itertools import chain


class generic_tax_report(models.AbstractModel):
    _inherit = 'account.generic.tax.report'

    def _get_lines_by_tax(self, options, line_id, taxes):
        def get_name_from_record(record):
            format = '%(name)s - %(company)s' if options.get('multi_company') else '%(name)s'
            params = {'company': record.company_id.name}
            if record._name == 'account.tax':
                if record.amount_type == 'group':
                    params['name'] = record.name
                else:
                    params['name'] = '%s (%s)' % (record.name, record.amount)
            elif record._name == 'account.account':
                params['name'] = record.display_name
            return format % params

        def get_vals_from_tax_and_add(tax, *total_lines):
            net_vals = [period['net'] * sign for period in tax['periods']]
            tax_vals = [
                sum(vals['amount'] for vals in tax['obj'].compute_all(period['net'], handle_price_include=False)['taxes']) * sign
                if group_by else
                (period['tax'] * sign)
                for period in tax['periods']
            ]
            if group_by and tax['obj'].amount_type == 'group':
                raise UserError(_('Tax report groupped by account is not available for taxes of type Group'))
            all_vals = list(chain.from_iterable(zip(net_vals, tax_vals)))
            show = any(bool(n) for n in all_vals)

            if show:
                for total in total_lines:
                    if total:
                        for i, v in enumerate(all_vals):
                            total['columns'][i]['no_format'] += v

            return all_vals, show

        group_by = options.get('group_by')
        lines = []
        # INICIO CAMBIO
        # types = ['sale', 'purchase']
        types = ['sale', 'purchase', 'customer', 'supplier']
        # FIN CAMBIO
        accounts = self.env['account.account']
        groups = dict((tp, defaultdict(lambda: {})) for tp in types)
        for tax_account in taxes.values():
            for account_id, tax in tax_account.items():
                # 'none' taxes are skipped.
                if tax['obj'].type_tax_use == 'none':
                    continue

                if tax['obj'].amount_type == 'group':
                    # Group of taxes without child are skipped.
                    if not tax['obj'].children_tax_ids:
                        continue

                    # - If at least one children is 'none', show the group of taxes.
                    # - If all children are different of 'none', only show the children.
                    tax['children'] = []
                    tax['show'] = False
                    for child in tax['obj'].children_tax_ids:
                        if child.type_tax_use != 'none':
                            continue

                        tax['show'] = True
                        for i, period_vals in enumerate(taxes[child.id][0]['periods']):
                            tax['periods'][i]['tax'] += period_vals['tax']
                account = self.env['account.account'].browse(account_id)
                accounts += account
                if group_by == 'tax_account':
                    groups[tax['obj'].type_tax_use][tax['obj']][account] = tax
                else:
                    groups[tax['obj'].type_tax_use][account][tax['obj']] = tax

        accounts.mapped('display_name')  # prefetch values

        period_number = len(options['comparison'].get('periods'))
        for tp in types:
            if not any(tax.get('show') for group in groups[tp].values() for tax in group.values()):
                continue
            sign = tp == 'sale' and -1 or 1
            type_line = {
                'id': tp,
                'name': self._get_type_tax_use_string(tp),
                'unfoldable': False,
                'columns': [{'no_format': 0} for k in range(0, 2 * (period_number + 1))],
                'level': 1,
            }
            lines.append(type_line)
            for header_level_1, group_level_1 in groups[tp].items():
                header_level_1_line = False
                if header_level_1:
                    header_level_1_line = {
                        'id': header_level_1.id,
                        'name': get_name_from_record(header_level_1),
                        'unfoldable': False,
                        'columns': [{'no_format': 0} for k in range(0, 2 * (period_number + 1))],
                        'level': 2,
                        'caret_options': header_level_1._name
                    }
                    lines.append(header_level_1_line)
                for header_level_2, group_level_2 in sorted(group_level_1.items(), key=lambda g: g[1]['obj'].sequence):
                    if group_level_2['show']:
                        all_vals, show = get_vals_from_tax_and_add(group_level_2, type_line, header_level_1_line)
                        if show:
                            lines.append({
                                'id': header_level_2.id,
                                'name': get_name_from_record(header_level_2),
                                'unfoldable': False,
                                'columns': [{'no_format': v, 'style': 'white-space:nowrap;'} for v in all_vals],
                                'level': 4,
                                'caret_options': header_level_2._name,
                            })
                        for child in group_level_2.get('children', []):
                            all_vals, show = get_vals_from_tax_and_add(child, type_line, header_level_1_line)
                            if show:
                                lines.append({
                                    'id': child['obj'].id,
                                    'name': '   ' + get_name_from_record(child['obj']),
                                    'unfoldable': False,
                                    'columns': [{'no_format': v, 'style': 'white-space:nowrap;'} for v in all_vals],
                                    'level': 4,
                                    'caret_options': 'account.tax',
                                })
                if lines[-1] == header_level_1_line:
                    del lines[-1]  # No children so we remove the total line
            if lines[-1] == type_line:
                del lines[-1]  # No children so we remove the total line
        for line in lines:
            for column in line['columns']:
                column['name'] = self.format_value(column['no_format'])
        return lines
