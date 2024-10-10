import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-sign",
    description="Meta package for oca-sign Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-maintenance_sign_oca>=16.0dev,<16.1dev',
        'odoo-addon-project_task_sign_oca>=16.0dev,<16.1dev',
        'odoo-addon-sign_oca>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
