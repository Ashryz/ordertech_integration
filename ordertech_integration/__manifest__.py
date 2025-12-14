# -*- coding: utf-8 -*-
{
    'name': "OrderTech Integration",

    'summary': """ """,

    'description': """ """,

    'author': "Tarek Ashry",

    'version': '18.0.1.0',

    'depends': [
        'base',
        'base_geolocalize',
        'point_of_sale',

    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ordertech_configration.xml',
        'views/ordertech_config_view.xml',
        'views/ordertech_restaurant_view.xml',
        'views/ordertech_branch_view.xml',
        'views/ordertech_customer_view.xml',
        'views/ordertech_menu_view.xml',
        'views/ordertech_addons_group_view.xml',
        'views/res_company_view.xml',
        'views/res_partner_view.xml',
    ],
    'post_init_hook': 'post_init_generate_api_key',
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
}