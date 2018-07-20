# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#    Copyright (C) 2017-2018 CodUP (<http://codup.com>).
#
##############################################################################

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    google_maps_api_key = fields.Char('Google Maps API Key')

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].set_param
        set_param('google_maps_api_key', (self.google_maps_api_key or '').strip())

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(
            google_maps_api_key=get_param('google_maps_api_key', default=''),
        )
        return res
