from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator  # Import MaxValueValidator
from django.contrib.auth.models import User  # Import User
from decimal import Decimal 
import logging
logger = logging.getLogger(__name__)

class Client(models.Model):
    first_name = models.CharField(max_length=60, verbose_name="Nombre", help_text="Nombre del cliente")
    paternal_last_name = models.CharField(max_length=60, verbose_name="Apellido paterno", help_text="Primer apellido")
    maternal_last_name = models.CharField(max_length=60, verbose_name="Apellido materno", help_text="Segundo apellido")
    email = models.EmailField(unique=True, verbose_name="Correo electrónico")
    phone_number = models.CharField(
        max_length=15,
        verbose_name="Número de teléfono",
        help_text="Número de teléfono con código de área"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["first_name", "paternal_last_name"]

    def __str__(self):
        return f"{self.first_name} {self.paternal_last_name} {self.maternal_last_name}"


class Budget(models.Model):
    STATE = [
        ('pendiente', 'Pendiente'),
        ('aceptado', 'Aceptado'),
        ('rechazado', 'Rechazado'),
    ]

    emission_date = models.DateField()
    client = models.ForeignKey('Client', on_delete=models.CASCADE)
    itinerary = models.CharField(max_length=200)  
    cod_airline = models.CharField(max_length=200)  
    reserv_system = models.CharField(max_length=200)  
    beeper = models.CharField(max_length=200)  
    base_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(99999999.99)])
    emisor_cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(99999999.99)])
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(99999999.99)])
    special_services = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    vendor = models.ForeignKey(User, on_delete=models.CASCADE)
    provider = models.CharField(max_length=200)
    state = models.CharField(max_length=10, choices=STATE, default='pendiente')

    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cielo_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    vendor_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def calculate_cost_price(self):
        return (self.base_price or 0) + (self.emisor_cost or 0)

    def calculate_sale_fee(self):
        return (self.sale_price or 0) - self.calculate_cost_price() + (self.special_services or 0)

    def calculate_cielo_fee(self):
        sale_fee = self.calculate_sale_fee()
        return sale_fee - (Decimal(sale_fee) * Decimal('0.13')) if sale_fee else 0

    def calculate_vendor_fee(self):
        return self.calculate_sale_fee() - self.calculate_cielo_fee()

    def save(self, *args, **kwargs):
        try:
            creating_closed_sale = False
            
            if self.pk:
                old_budget = Budget.objects.get(pk=self.pk)
                if old_budget.state != "aceptado" and self.state == "aceptado":
                    creating_closed_sale = True

            self.cost_price = self.calculate_cost_price()
            self.sale_fee = self.calculate_sale_fee()
            self.cielo_fee = self.calculate_cielo_fee()
            self.vendor_fee = self.calculate_vendor_fee()

            super().save(*args, **kwargs)

            if creating_closed_sale:
                closed_sale, created = closedSales.objects.get_or_create(
                    budget=self,
                    defaults={
                        'client': self.client,
                        'vendor': self.vendor,
                        'sales_price': self.sale_price,
                        'fee_sale': self.sale_fee,
                        'fee_cielo': self.cielo_fee,
                        'fee_vendor': self.vendor_fee,
                        'paid': "Pendiente"
                    }
                )
                if not created:
                    logger.info(f"ClosedSale ya existía para el presupuesto {self.pk}, actualizando datos...")
                    closed_sale.client = self.client
                    closed_sale.vendor = self.vendor
                    closed_sale.sales_price = self.sale_price
                    closed_sale.fee_sale = self.sale_fee
                    closed_sale.fee_cielo = self.cielo_fee
                    closed_sale.fee_vendor = self.vendor_fee
                    closed_sale.save()

        except Exception as e:
            logger.error(f"Error al guardar el presupuesto o crear la venta cerrada: {e}")
            raise

class closedSales(models.Model):
    budget = models.OneToOneField('Budget', on_delete=models.CASCADE, related_name='venta')
    client = models.ForeignKey('Client', on_delete=models.CASCADE)
    vendor = models.ForeignKey(User, on_delete=models.CASCADE)
    sales_price = models.DecimalField(max_digits=10, decimal_places=2)
    fee_sale = models.DecimalField(max_digits=10, decimal_places=2)
    fee_cielo = models.DecimalField(max_digits=10, decimal_places=2)
    fee_vendor = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.CharField(max_length=20)
    date_sale = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Venta de {self.client} - {self.date_sale}"