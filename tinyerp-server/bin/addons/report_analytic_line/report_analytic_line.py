##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: sale.py 1005 2005-07-25 08:41:42Z nicoe $
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from osv import fields,osv

class report_account_analytic_line_to_invoice(osv.osv):
    _name = "report.account.analytic.line.to.invoice"
    _description = "Analytic lines to invoice report"
    _auto = False
    _columns = {
        'name': fields.date('Month', readonly=True),
        'product_id':fields.many2one('product.product', 'Product', readonly=True),
        'account_id':fields.many2one('account.analytic.account', 'Analytic account', readonly=True),
        'product_uom_id':fields.many2one('product.uom', 'UoM', readonly=True),
        'unit_amount': fields.float('Units', readonly=True),
        'sale_price': fields.float('Sale price', readonly=True),
        'amount': fields.float('Amount', readonly=True),
    }
    _order = 'name desc, product_id asc, account_id asc'

    def init(self, cr):
        cr.execute("""
            CREATE OR REPLACE VIEW report_account_analytic_line_to_invoice AS (
                SELECT
                    DISTINCT(SUBSTRING(l.date for 7))||'-'||'01' AS name,
                    MIN(l.id) AS id,
                    l.product_id,
                    l.account_id,
                    SUM(l.amount) AS amount,
                    SUM(l.unit_amount*t.list_price) AS sale_price,
                    SUM(l.unit_amount) AS unit_amount,
                    l.product_uom_id
                FROM
                    account_analytic_line l
                left join
                    product_product p on (l.product_id=p.id)
                left join
                    product_template t on (p.product_tmpl_id=t.id)
                WHERE
                    (invoice_id IS NULL) and (to_invoice IS NOT NULL)
                GROUP BY
                    SUBSTRING(date for 7), product_id, product_uom_id, account_id
            )
        """)
report_account_analytic_line_to_invoice()
