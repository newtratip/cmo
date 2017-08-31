# -*- coding: utf-8 -*-
import datetime
from string import ascii_uppercase

from openerp import fields, models, api, _
from openerp.exceptions import ValidationError

class SaleCovenantDescription(models.Model):
    _name = 'sale.covenant.description'

    name = fields.Char(
        string='Name',
        required=True,
    )
    description = fields.Text(
        string='Description',
        translate=True,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        copy=False,
    )

    @api.multi
    @api.constrains('active')
    def _constrains_active(self):
        for rec in self:
            active_cov = rec.env['sale.covenant.description'].\
                search([('active', '=', True), ])
            if len(active_cov) > 1:
                raise ValidationError(_('Must be only 1 active covenant!'))

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'Name must be unique!'),
    ]


class SaleLayoutCategory(models.Model):
    _inherit = 'sale_layout.category'

    management_fee = fields.Boolean(
        string='Management Fee',
        default=False,
    )


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    project_related_id = fields.Many2one(
        'project.project',
        string='Project',
        states={'done': [('readonly', True)]},
        required=True,
    )
    # TODO: project_number field may be not used because project_related_id show project_number
    # project_number = fields.Char(
    #     string='Project Code',
    #     related='project_related_id.project_number',
    #     readonly=True,
    #     compute='_compute_project_number',
    #     copy=False,
    # )
    event_date_description = fields.Char(
        string='Event Date',
        size=250,
        states={'done': [('readonly', True)]},
        required=True,
    )
    venue_description = fields.Char(
        string='Venue',
        size=250,
        states={'done': [('readonly', True)]},
        required=True,
    )
    amount_before_management_fee = fields.Float(
        string="Before Management Fee",
        compute='_compute_before_management_fee',
    )
    payment_term_description = fields.Text(
        string='Payment Term',
        states={'done': [('readonly', True)]},
    )
    covenant_description = fields.Text(
        string='Covenant',
        translate=True,
        default=lambda self: self._default_covenant(),
        states={'done': [('readonly', True)]},
    )
    quote_ref_id = fields.Many2one(
        'sale.order',
        string='Ref.Quotation',
        states={'done': [('readonly', True)]},
        domain=[
            '&', ('order_type', 'like', 'quotation'),
            ('state', 'not like', 'cancel'),
        ],
    )
    approval_id = fields.Many2one(
        'res.users',
        string='Approval',
        states={'done': [('readonly', True)]},
    )
    margin_percentage = fields.Float(
        string='Margin Percentage (%)',
        readonly=True,
        compute='_compute_margin_percentage',
    )

    @api.model
    def create(self, vals):
        ctx = self._context.copy()
        current_date = fields.Date.context_today(self)
        fiscalyear_id = self.env['account.fiscalyear'].find(dt=current_date)
        ctx["fiscalyear_id"] = fiscalyear_id
        if (vals.get('order_type', False) or
            self._context.get('order_type', False)) == 'quotation' \
                and vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence']\
                .with_context(ctx).get('cmo.quotation')
        elif (vals.get('order_type', False) or
            self._context.get('order_type', False)) == 'sale_order' \
                and vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence']\
                .with_context(ctx).get('cmo.sale_order')
        new_order = super(SaleOrder, self).create(vals)
        return new_order

    @api.multi
    @api.depends('amount_before_management_fee')
    def _compute_before_management_fee(self):
        total = sum(self.order_line.filtered(
            lambda r: r.order_lines_group == 'before'
            ).mapped('price_unit'))
        self.amount_before_management_fee = total

    @api.multi
    @api.onchange('project_related_id')
    def _onchange_project_number(self):
        for project in self:
            Project = self.env['project.project']\
                .browse(project.project_related_id.id)
            project.project_id = Project.analytic_account_id.id
    #         project.project_number = Project.project_number
    #
    # @api.multi
    # @api.depends('project_number', 'project_related_id')
    # def _compute_project_number(self):
    #     for quote in self:
    #         parent_project = self.env['project.project']\
    #             .browse(quote.project_related_id.id)
    #         quote.project_id = parent_project.analytic_account_id.id
    #         quote.project_number = parent_project.project_number

    @api.model
    def _default_covenant(self):
        Description = self.env['sale.covenant.description']
        covenants = Description.search([('active', '=', True), ])
        return covenants and covenants[0].description or False

    @api.multi
    @api.constrains('order_line')
    def _constrains_order_line(self):
        for rec in self:
            if not self.order_line:
                raise ValidationError(_('Must have at least 1 order line!'))
            else:
                for line in self.order_line:
                    if ((line.price_unit <= 0) or (line.product_uom_qty <= 0))\
                            and (line.order_lines_group == 'before'):
                        raise ValidationError(
                            _('Unit Price and Quantity in order \
                            line must more than zero !')
                        )

    @api.multi
    def _get_amount_by_custom_group(self, custom_group):
        self.ensure_one()
        lines = self.order_line.filtered(
            lambda r:
            (r.order_lines_group == 'before') and
            (r.sale_layout_custom_group_id.id == custom_group.id)
        )
        return sum(lines.mapped('price_subtotal'))

    @api.multi
    def _compute_margin_percentage(self):
        for order in self:
            if order.amount_untaxed != 0.0:
                order.margin_percentage = order.margin * 100 /\
                    order.amount_untaxed


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    order_lines_group = fields.Selection(
        [('before','Before Management Fee'),
         ('manage_fee','Management and Operation Fee'),
        ],
        string='Group',
        default='before',
        required=True,
    )
    sale_layout_custom_group_id = fields.Many2one(
        'sale_layout.custom_group',
        string='Custom Group (no use)',
    )
    sale_layout_custom_group = fields.Char(
        string='Custom Group',
    )
    sale_order_line_margin = fields.Float(
        string='Margin',
        compute='_compute_sale_order_line_margin',
        readonly=True,
    )
    so_line_percent_margin = fields.Float(
        string='Percentage',
        compute='_compute_sale_order_line_margin',
    )
    # section_code = fields.Selection(
    #     [('A', 'A'),
    #      ('B', 'B'),
    #      ('C', 'C'),
    #      ('D', 'D'),
    #      ('E', 'E'),
    #      ('F', 'F'), ],
    #     string='Section Code',
    #     # required=True,
    # )
    # section_code = fields.Char(
    #     compute='_compute_section_code',
    #     string='Section Code',
    # )
    product_id = fields.Many2one(
        'product.product',
        required=True,
    )

    @api.multi
    def action_cal_management_fee(self):
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.cal.manage.fee',
            'src_model': 'sale.order',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': {'order_line_id': self.id, 'view_id': 'view_sale_management_fee',}
        }

    @api.multi
    @api.depends('price_unit', 'purchase_price', 'product_uom_qty',)
    def _compute_sale_order_line_margin(self):
        for line in self:
            margin = (line.price_unit - line.purchase_price) * \
                line.product_uom_qty
            line.sale_order_line_margin = margin
            line.so_line_percent_margin = \
                (line.price_unit - line.purchase_price) * 100.0 / \
                (line.price_unit or 1.0)

    @api.onchange('order_lines_group')
    def _onchange_order_lines_group(self):
        res = {}
        if self.order_lines_group == 'before':
            res['domain'] = {
                'sale_layout_cat_id': [
                    ('management_fee', '=', False),
                ]
            }
        elif self.order_lines_group == 'manage_fee':
            res['domain'] = {
                'sale_layout_cat_id': [
                    ('management_fee', '=', True),
                ]
            }
        self.sale_layout_custom_group = None
        self.sale_layout_cat_id = False
        self.product_id = False
        self.product_uom_qty = 1
        self.price_unit = 0
        self.purchase_price = 0
        return res

    @api.onchange('sale_layout_cat_id')
    def _onchange_sale_layout_cat(self):  # section
        res = {}
        if self.order_lines_group == 'before':
            res['domain'] = {
                'product_id': [
                    ('sale_ok', '=', True),
                    ('sale_layout_cat_id', '=', self.sale_layout_cat_id.id),
                ]
            }
        elif self.order_lines_group == 'manage_fee':
            res['domain'] = {
                'product_id': [
                    ('sale_ok', '=', True),
                    ('sale_layout_cat_id', '=', self.sale_layout_cat_id.id),
                ]
            }
        self.product_id = False
        self.product_uom_qty = 1
        self.price_unit = 0
        self.purchase_price = 0
        return res

    @api.model
    def _gen_ascii_seq(self, num, seq=''):
        leng = len(ascii_uppercase)
        digit = num / leng
        if digit == 0:
            seq = seq + ascii_uppercase[num]
            return seq
        else:
            seq = seq + ascii_uppercase[(digit % leng) - 1]
            num = num - (digit * leng)
            return self._gen_ascii_seq(num, seq)

    # @api.multi
    # def _compute_section_code(self):
    #     for order_line in self:
    #         print('>>>>>>>>>>>>', order_line)


class SaleLayoutCustomGroup(models.Model):
    _name = 'sale_layout.custom_group'

    name = fields.Char(
        string='Name',
        required=True,
    )

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'Name must be unique!'),
    ]
