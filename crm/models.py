from django.db import models
from django.core.validators import MinValueValidator

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
    
from django.db import models
from django.core.validators import MinValueValidator

class Budget(models.Model):
    STATE = [
        ('pendiente', 'Pendiente'),
        ('aceptado', 'Aceptado'),
        ('rechazado', 'Rechazado'),
    ]

    emission_date = models.DateField()
    client = models.ForeignKey('Client', on_delete=models.CASCADE)
    itinerary = models.CharField(max_length=50)
    cod_airline = models.CharField(max_length=50)
    reserv_system = models.CharField(max_length=50)
    beeper = models.CharField(max_length=50)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    emisor_cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    special_services = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    vendor = models.CharField(max_length=50)
    provider = models.CharField(max_length=50)
    state = models.CharField(max_length=10, choices=STATE, default='pendiente')

    def calculate_cost_price(self):
        base_price = self.base_price if self.base_price is not None else 0
        emisor_cost = self.emisor_cost if self.emisor_cost is not None else 0
        return base_price + emisor_cost

    def calculate_sale_fee(self):
        sale_price = self.sale_price if self.sale_price is not None else 0
        cost_price = self.calculate_cost_price()
        special_services = self.special_services if self.special_services is not None else 0
        return (sale_price - cost_price) + special_services

    # Calcular la tarifa de cielo
    def calculate_cielo_fee(self):
        sale_fee = self.calculate_sale_fee()
        return sale_fee - (sale_fee * 0.13) if sale_fee is not None else 0

    # Calcular la tarifa del vendedor
    def calculate_vendor_fee(self):
        sale_fee = self.calculate_sale_fee()
        cielo_fee = self.calculate_cielo_fee()
        return sale_fee - cielo_fee if sale_fee is not None and cielo_fee is not None else 0

    def save(self, *args, **kwargs):
        # Optional: add any pre-save logic if needed
        super().save(*args, **kwargs)

class closedSales(models.Model):
    budget = models.OneToOneField('Budget', on_delete=models.CASCADE, related_name='venta')
    client = models.ForeignKey('Client', on_delete=models.CASCADE)
    vendor = models.CharField(max_length=50)
    sales_price = models.DecimalField(max_digits=10, decimal_places=2)
    fee_sale = models.DecimalField(max_digits=10, decimal_places=2)
    fee_cielo = models.DecimalField(max_digits=10, decimal_places=2)
    fee_vendor = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.CharField(max_length=20)
    date_sale = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Venta de {self.client} - {self.date_sale}"
