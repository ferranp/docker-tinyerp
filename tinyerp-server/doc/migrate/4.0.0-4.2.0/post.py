##############################################################################
#
# Copyright (c) 2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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

__author__ = 'Gaetan de Menten, <ged@tiny.be>'
__version__ = '0.1.0'

import psycopg
import optparse
import ConfigParser

# -----

parser = optparse.OptionParser(version="Tiny ERP server migration script " + __version__)

parser.add_option("-c", "--config", dest="config", help="specify path to Tiny ERP config file")

group = optparse.OptionGroup(parser, "Database related options")
group.add_option("--db_host", dest="db_host", help="specify the database host") 
group.add_option("--db_port", dest="db_port", help="specify the database port") 
group.add_option("-d", "--database", dest="db_name", help="specify the database name")
group.add_option("-r", "--db_user", dest="db_user", help="specify the database user name")
group.add_option("-w", "--db_password", dest="db_password", help="specify the database password") 
parser.add_option_group(group)

options = optparse.Values()
options.db_name = 'terp' # default value
parser.parse_args(values=options)

if hasattr(options, 'config'):
	configparser = ConfigParser.ConfigParser()
	configparser.read([options.config])
	for name, value in configparser.items('options'):
		if not (hasattr(options, name) and getattr(options, name)):
			if value in ('true', 'True'):
				value = True
			if value in ('false', 'False'):
				value = False
			setattr(options, name, value)

# -----

host = hasattr(options, 'db_host') and "host=%s" % options.db_host or ''
port = hasattr(options, 'db_port') and "port=%s" % options.db_port or ''
name = "dbname=%s" % options.db_name
user = hasattr(options, 'db_user') and "user=%s" % options.db_user or ''
password = hasattr(options, 'db_password') and "password=%s" % options.db_password or ''

db = psycopg.connect('%s %s %s %s %s' % (host, port, name, user, password), serialize=0)
cr = db.cursor()

# ----------------------------- #
# convert date_planned to delay #
# ----------------------------- #

cr.execute('SELECT c.relname FROM pg_class c WHERE c.relname = \'sale_order_line\'')
if cr.fetchall():
	cr.execute("update sale_order_line set delay = pt.sale_delay from product_product as po, product_template as pt where product_id = po.id and po.product_tmpl_id = pt.id")
cr.commit()

# --------------------------------------------------------------------------- #
# move account_invoice.project_id to account_invoice_line.account_analytic_id #
# --------------------------------------------------------------------------- #

cr.execute('SELECT a.attname FROM pg_class c, pg_attribute a WHERE c.relname = \'account_invoice\' AND a.attname = \'project_id\' AND c.oid = a.attrelid')
if cr.fetchall():
	cr.execute("update account_invoice_line set account_analytic_id = ai.project_id from account_invoice as ai where invoice_id = ai.id")
cr.commit()

# ------------------------------------------------------------------------- #
# move purchase_order.project_id to purchase_order_line.account_analytic_id #
# ------------------------------------------------------------------------- #

cr.execute('SELECT a.attname FROM pg_class c, pg_attribute a WHERE c.relname = \'purchase_order\' AND a.attname = \'project_id\' AND c.oid = a.attrelid')
if cr.fetchall():
	cr.execute("update purchase_order_line set account_analytic_id = po.project_id from purchase_order as po where order_id = po.id")
cr.commit()


# --------------- #
# remove old menu #
# --------------- #

cr.execute("delete from ir_ui_menu where (id not in (select parent_id from ir_ui_menu where parent_id is not null)) and (id not in (select res_id from ir_values where model='ir.ui.menu'))")
cr.commit()

# --------------------- #
# set value for menu_id #
# --------------------- #

cr.execute('update res_users set menu_id = action_id')
cr.commit()

# --------------------------------------------------- #
# set reconciled state to valid for account move line #
# --------------------------------------------------- #

cr.execute('SELECT c.relname FROM pg_class c WHERE c.relname = \'account_move_line\'')
if cr.fetchall():
	cr.execute('UPDATE account_move_line set state = \'valid\' WHERE state = \'reconciled\'')
cr.commit()

# ------------ #
# migrate bank #
# ------------ #

cr.execute('SELECT bank_name, swift, id FROM res_partner_bank WHERE bank IS NULL AND (bank_name IS NOT NULL OR swift IS NOT NULL)')
res = cr.dictfetchall()
for line in res:
	cr.execute('SELECT NEXTVAL(\'res_bank_id_seq\')')
	bank_id = cr.fetchone()[0]
	cr.execute('INSERT INTO res_bank (id, name, bic, active) VALUES (%d, %s, %s, True)',
			(bank_id, line['bank_name'], line['swift']))
	cr.execute('UPDATE res_partner_bank SET bank = %d WHERE id = %d',
			(bank_id, line['id']))
cr.commit()

cr.close()
