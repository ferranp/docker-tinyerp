{
	"name" : "Project Management",
	"version": "1.0",
	"author" : "Tiny",
	"website" : "http://tinyerp.com/module_project.html",
	"category" : "Generic Modules/Projects & Services",
	"depends" : ["product", "account", 'mrp', 'sale', 'base'],
	"description": "Project management module that track multi-level projects, tasks, works done on tasks, eso. It is able to render planning, order tasks, eso.",
	"init_xml" : [],
	"demo_xml" : ["project_demo.xml"],
	"update_xml": ["project_data.xml", "project_wizard.xml", "project_view.xml", "project_report.xml", "project_workflow.xml"],
	"active": False,
	"installable": True
}
