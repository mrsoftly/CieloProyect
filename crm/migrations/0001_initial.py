# Generated by Django 5.1.3 on 2024-12-05 22:03

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(help_text='Nombre del cliente', max_length=60, verbose_name='Nombre')),
                ('paternal_last_name', models.CharField(help_text='Primer apellido', max_length=60, verbose_name='Apellido paterno')),
                ('maternal_last_name', models.CharField(help_text='Segundo apellido', max_length=60, verbose_name='Apellido materno')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='Correo electrónico')),
                ('phone_number', models.CharField(help_text='Número de teléfono con código de área', max_length=15, verbose_name='Número de teléfono')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Última actualización')),
            ],
            options={
                'verbose_name': 'Cliente',
                'verbose_name_plural': 'Clientes',
                'ordering': ['first_name', 'paternal_last_name'],
            },
        ),
        migrations.CreateModel(
            name='Budget',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('emission_date', models.DateField()),
                ('itinerary', models.CharField(max_length=50)),
                ('cod_airline', models.CharField(max_length=50)),
                ('reserv_system', models.CharField(max_length=50)),
                ('beeper', models.CharField(max_length=50)),
                ('base_price', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ('emisor_cost', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ('sale_price', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ('special_services', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ('vendor', models.CharField(max_length=50)),
                ('provider', models.CharField(max_length=50)),
                ('state', models.CharField(choices=[('pendiente', 'Pendiente'), ('aceptado', 'Aceptado'), ('rechazado', 'Rechazado')], default='pendiente', max_length=10)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crm.client')),
            ],
        ),
        migrations.CreateModel(
            name='closedSales',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vendor', models.CharField(max_length=50)),
                ('sales_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('fee_sale', models.DecimalField(decimal_places=2, max_digits=10)),
                ('fee_cielo', models.DecimalField(decimal_places=2, max_digits=10)),
                ('fee_vendor', models.DecimalField(decimal_places=2, max_digits=10)),
                ('paid', models.CharField(max_length=20)),
                ('date_sale', models.DateTimeField(auto_now_add=True)),
                ('budget', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='venta', to='crm.budget')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crm.client')),
            ],
        ),
    ]
