##############################################################################
#
# Copyright (c) 2005 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: _date_compute.py 1005 2005-07-25 08:41:42Z nicoe $
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

from mx import DateTime

import time
import pooler

#
# TODO: improve sequences code
#
def _compute_tasks(cr, uid, task_list, date_begin):
	sequences = []
	users = {}
	tasks = {}
	last_date = date_begin
	for task in task_list:
		# TODO: reorder ! with dependencies
		if not task.planned_hours:
			continue
		if task.state in ('open','progress') and task.user_id:

			# Find the starting date of the task
			if task.user_id.id in users:
				date_start = users[task.user_id.id]
			else:
				date_start = date_begin
			if task.start_sequence:
				sequences.sort()
				for (seq,dt) in sequences:
					if seq<task.sequence:
						date_start = max(dt,date_start)
					else:
						break

			if task.date_start:
				task_date_start = DateTime.strptime(task.date_start, '%Y-%m-%d %H:%M:%S')
				if DateTime.cmp(date_start, task_date_start) < 0:
					date_start = task_date_start


			# Compute the closing date of the task
			tasks[task.id] = []
			res = pooler.get_pool(cr.dbname).get('hr.timesheet.group').interval_get(cr, uid, task.project_id.timesheet_id.id, date_start, task.planned_hours)
			for (d1,d2) in res:
				tasks[task.id].append((d1, d2, task.name, task.user_id.login))
			date_close = tasks[task.id][-1][1]

			# Store result
			users[task.user_id.id] = date_close
			sequences.append((task.sequence, date_close))
			if date_close>last_date:
				last_date=date_close
	return tasks, last_date

def _compute_project(cr, uid, project, date_begin):
	tasks, last_date = _compute_tasks(cr, uid, project.tasks, date_begin)
	for proj in project.child_id:
		d0 = DateTime.strptime(proj.date_start,'%Y-%m-%d')
		if d0 > last_date:
			last_date = d0
		t2, l2 = _compute_project(cr, uid, proj, last_date)
		tasks.update(t2)
		last_date = l2
	return tasks, last_date

def _project_compute(cr, uid, project_id):
	project = pooler.get_pool(cr.dbname).get('project.project').browse(cr, uid, project_id)
	if project.date_start:
		date_begin = DateTime.strptime(project.date_start, '%Y-%m-%d')
	else:
		date_begin = DateTime.now()
	tasks, last_date = _compute_project(cr, uid, project, date_begin)
	return tasks, last_date

