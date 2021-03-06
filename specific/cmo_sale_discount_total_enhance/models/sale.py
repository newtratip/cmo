# -*- coding: utf-8 -*-

from openerp import api, fields, models
import openerp.addons.decimal_precision as dp


class sale_order(models.Model):
    _inherit = 'sale.order'

    amount_untaxed = fields.Float(
        store=False,
    )
    amount_tax = fields.Float(
        store=False,
    )
    amount_total = fields.Float(
        store=False,
    )
    amount_discount = fields.Float(
        store=False,
    )
    amount_before_discount = fields.Float(
        string='Subtotal Amount',
        readonly=True,
        compute='_amount_all',
        digits_compute=dp.get_precision('Account'),
        track_visibility='always',
    )

    @api.model
    def calculate_discount(self, vals):
        discount = 0
        if ('discount_rate' in vals) and ('order_line' in vals):
            res = vals['sale_order_record']
            if vals['discount_type'] == 'percent':
                discount = vals['discount_rate']
            else:
                amount = sum(res.order_line.mapped(
                    lambda r: r.product_uom_qty * r.price_unit)
                )
                total = amount if amount != 0 else 1 # prevent devison by zero
                discount_rate = vals['discount_rate']
                if discount_rate != 0:
                    discount = (discount_rate / total) * 100.0
                else:
                    discount = discount_rate
            for line in res.order_line:
                line.write({'discount': discount})

    @api.model
    def create(self, vals):
        res = super(sale_order, self).create(vals)
        vals['sale_order_record'] = res
        res.calculate_discount(vals)
        res._amount_all()
        return res

    @api.multi
    def write(self, vals):
        res = super(sale_order, self).write(vals)
        for order in self:
            if ('discount_rate' in vals) and ('order_line' in vals):
                if 'discount_type' not in vals:
                    vals['discount_type'] = order.discount_type
                if 'discount_rate' not in vals:
                    vals['discount_rate'] = order.discount_rate
                vals['sale_order_record'] = order
                order.calculate_discount(vals)
                order._amount_all()
        return res

    @api.multi
    @api.depends('order_line.price_subtotal')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = 0.0
            amount_discount = amount_before_discount = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += self._amount_line_tax(line=line)
                amount_discount += (line.product_uom_qty *
                                    line.price_unit *
                                    line.discount) / 100
                amount_before_discount += (line.product_uom_qty *
                                           line.price_unit)
            order.amount_untaxed = cur.round(amount_untaxed)
            order.amount_tax = cur.round(amount_tax)
            order.amount_discount = cur.round(amount_discount)
            order.amount_total = amount_untaxed + amount_tax
            order.amount_before_discount = amount_before_discount

    @api.multi
    @api.onchange('discount_type', 'discount_rate', 'order_line')
    def supply_rate(self):
        for order in self:
            if order.discount_type == 'percent':
                for line in order.order_line:
                    line.discount = order.discount_rate
            else:
                amount = sum(order.order_line.mapped(
                            lambda r: r.product_uom_qty * r.price_unit)
                        )
                total = amount if amount != 0 else 1 # prevent devison by zero
                if order.discount_rate != 0:
                    discount = (order.discount_rate / total) * 100.0
                else:
                    discount = order.discount_rate
                for line in order.order_line:
                    line.discount = discount
        self._amount_all()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    price_subtotal_no_disco = fields.Float(
        string='Sub Total',
        compute='_compute_price_subtotal_no_disco',
    )

    @api.multi
    @api.depends('price_unit', 'product_uom_qty')
    def _compute_price_subtotal_no_disco(self):
        for line in self:
            line.price_subtotal_no_disco = line.price_unit * line.product_uom_qty
