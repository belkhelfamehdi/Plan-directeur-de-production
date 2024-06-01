from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class MPS(models.Model):
    _name = 'mps'
    _description = 'Master Production Schedule'

    bom_id = fields.Many2one('mrp.bom', string="Nomenclature")
    display_name = fields.Char(string="Nom d'affichage", readonly=True)
    forecast_ids = fields.One2many('mps.forecasted.qty', 'mps_id', string="Quantité prévue à la date")
    forecast_target_qty = fields.Float(string="Stock de sécurité")
    max_to_replenish_qty = fields.Float(string="Maximum à réapprovisionner", default=1000)
    min_to_replenish_qty = fields.Float(string="Minimum à réapprovisionner")
    product_id = fields.Many2one('product.product', string="Produit")
    product_tmpl_id = fields.Many2one('product.template', string="Modèle de produit")
    product_uom_id = fields.Many2one('uom.uom', string="Unité de mesure du produit")
    warehouse_id = fields.Many2one('stock.warehouse', string="Entrepôt")

    @api.constrains('product_tmpl_id')
    def _check_unique_product_tmpl_id(self):
        for record in self:
            if record.product_tmpl_id:
                existing_record = self.search([
                    ('id', '!=', record.id),
                    ('product_tmpl_id', '=', record.product_tmpl_id.id),
                ])
                if existing_record:
                    raise ValidationError("Ce produit existe déja!")

    @api.model
    def save(self, vals):
        return {'type': 'ir.actions.act_window_close'}

    def action_delete(self):
        for rec in self:
            rec.unlink()

    def generate_periods(self):
        config_param = self.env['ir.config_parameter'].sudo()
        time_range = config_param.get_param('my_module.time_range', default='monthly')
        num_columns = int(config_param.get_param('my_module.num_columns', default=2))
        
        start_date = datetime.now()
        periods = []

        for i in range(num_columns):
            if time_range == 'daily':
                period_start = start_date + timedelta(days=i)
                period_end = period_start + timedelta(days=1) - timedelta(seconds=1)
                period_str = period_start.strftime("%B %d").capitalize()
            elif time_range == 'weekly':
                week_start = start_date + timedelta(weeks=i)
                week_end = week_start + timedelta(days=6)
                period_str = f"Week {week_start.isocalendar()[1]} ({week_start.day}-{week_end.day}/{week_start.strftime('%b')})"
                period_start = week_start
                period_end = week_end
            elif time_range == 'monthly':
                period_start = start_date + timedelta(days=30*i)
                period_end = period_start + timedelta(days=29)
                period_str = period_start.strftime("%b. %Y").capitalize()
            else:
                raise ValidationError("Invalid time range configuration!")

            periods.append({
                'period_str': period_str,
                'period_start': period_start,
                'period_end': period_end,
            })
        
        return periods