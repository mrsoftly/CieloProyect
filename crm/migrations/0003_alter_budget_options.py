# Generated by Django 5.1.3 on 2025-02-01 03:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0002_budget_cielo_fee_budget_cost_price_budget_sale_fee_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='budget',
            options={'ordering': ['-emission_date'], 'verbose_name': 'Presupuesto', 'verbose_name_plural': 'Presupuestos'},
        ),
    ]
