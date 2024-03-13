from decimal import Decimal
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import JSONField


class TimeStampedModel(models.Model):
    """ TimeStamped Abstract Model """

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class InductionMotor(TimeStampedModel):
    """ Induction Motor Test Report """

    ACTIVE = "ACTIVE"
    DELETE = "DELETE"

    REPORT_STATUS = (
        (ACTIVE, "Active"),
        (DELETE, "DELETED"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="induction_motor")
    serial_number = models.CharField(max_length=20)
    customer_name = models.CharField(max_length=100)
    sales_order_number = models.CharField(max_length=20)
    director_cerad = models.CharField(max_length=50, default='')
    lab_instructor = models.CharField(max_length=50, default='')
    # 1- Motor Identification
    tag = models.CharField(max_length=50, blank=True, null=True)
    material = models.CharField(max_length=50, blank=True, null=True)
    frame = models.CharField(max_length=50, blank=True, null=True)
    mounting = models.CharField(max_length=50, blank=True, null=True)
    drawing = models.CharField(max_length=50, blank=True, null=True)
    enclosure = models.CharField(max_length=50, blank=True, null=True)
    altitude_M = models.PositiveIntegerField(blank=True, null=True)
    duty_cycle = models.CharField(max_length=50, blank=True, null=True)
    design = models.CharField(max_length=50, blank=True, null=True)
    insulation_class = models.CharField(max_length=50, blank=True, null=True)
    temperature_rise_K = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    ambient_temperature_C = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    service_factor = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    voltage = models.PositiveIntegerField(blank=True, null=True)
    current = models.PositiveIntegerField(blank=True, null=True)
    power = models.PositiveIntegerField(blank=True, null=True)
    frequency = models.PositiveIntegerField(blank=True, null=True)
    speed = models.PositiveIntegerField(blank=True, null=True)
    p_f = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    efficiency = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    status = models.CharField(max_length=7, choices=REPORT_STATUS, default=ACTIVE, blank=True)
    report_link = models.CharField(max_length=50, null=True, blank=True)
    remarks = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.serial_number


class PerformanceTest(models.Model):
    """ Represents a performance test for an InductionMotor """

    PERFORMANCE_TEST_CHOICES = (
        ('electric_resistance_test', 'Electric Resistance Test'),
        ('temperature_rise_test', 'Temperature Rise Test'),
        ('performance_determination_test', 'Performance Determination Test'),
        ('no_load_test', 'No Load Test'),
        ('withstand_voltage_ac_test', 'Withstand Voltage AC Test'),
        ('insulation_resistance_test', 'Insulation Resistance Test'),
        ('lock_rotor_test', 'Lock Rotor Test')
    )

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    NOT_FOUND = "NOT_FOUND"

    STATUS_CHOICES = (
        (PENDING, "Pending"),
        (COMPLETED, "Completed"),
        (NOT_FOUND, "Not Found"),
    )

    motor = models.ForeignKey(InductionMotor, on_delete=models.CASCADE, related_name="performance_tests")
    test_type = models.CharField(max_length=50, choices=PERFORMANCE_TEST_CHOICES)
    routine = models.BooleanField(null=True)
    type = models.BooleanField(null=True)
    special = models.BooleanField(null=True)
    page_number = models.IntegerField(default=1)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    def __str__(self):
        return f'{self.motor.serial_number} - {self.test_type}'


class ElectricResistanceTest(TimeStampedModel):
    """ 3.1. Electric Resistance Test Report"""

    induction_motor = models.OneToOneField(InductionMotor, on_delete=models.CASCADE,
                                           related_name="electric_resistance_test")
    resistance_ohm_1 = models.DecimalField(
        max_digits=5, decimal_places=3, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    resistance_ohm_2 = models.DecimalField(
        max_digits=5, decimal_places=3, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    resistance_ohm_3 = models.DecimalField(
        max_digits=5, decimal_places=3, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    ambient_temperature_C = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    unbalance_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )


class TemperatureRiseTest(TimeStampedModel):
    """ 3.2. Temperature Rise - Nominal Condition - Direct Test Report """

    induction_motor = models.OneToOneField(InductionMotor, on_delete=models.CASCADE,
                                           related_name="temperature_rise_test")
    voltage = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    winding = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    frequency = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    de_bearing = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    nde_bearing = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )


class PerformanceDeterminationTest(TimeStampedModel):
    """  3.3. Performance Determination Test Report """

    induction_motor = models.OneToOneField(InductionMotor, on_delete=models.CASCADE,
                                           related_name="performance_determination_test")
    voltage = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    frequency = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    nominal_t = models.DecimalField(
        max_digits=7, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    is_current_date = models.BooleanField(default=False, verbose_name="Use current date")
    test_date = models.DateField(null=True, blank=True, verbose_name="Test Date")
    table_name = models.CharField(max_length=20, null=True, blank=True)
    report_date = models.DateField(null=True, blank=True)
    mdb_data = JSONField(null=True, blank=True)


class PerformanceTestParameters(models.Model):
    performance_determination_test = models.ForeignKey(PerformanceDeterminationTest, on_delete=models.CASCADE,
                                                       related_name="parameters")
    load = models.PositiveSmallIntegerField(blank=True, null=True)
    current = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)
    slip = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)
    speed = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)
    efficiency = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)
    cos = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)


class NoLoadTest(TimeStampedModel):
    """ 3.4. No Load Test Report """

    CLOCKWISE = "CLOCKWISE"
    ANTI_CLOCKWISE = "ANTI_CLOCKWISE"

    DIRECTION_CHOICES = (
        (CLOCKWISE, "Clockwise"),
        (ANTI_CLOCKWISE, "Anti Clockwise"),
    )

    induction_motor = models.OneToOneField(InductionMotor, on_delete=models.CASCADE, related_name="no_load_test")
    voltage = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    current = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    power = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    frequency = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    speed = models.DecimalField(
        max_digits=7, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    direction_of_rotation = models.CharField(max_length=20, choices=DIRECTION_CHOICES, blank=True, null=True)
    report_date = models.CharField(max_length=20, null=True, blank=True)
    mdb_data = JSONField(null=True, blank=True)
    _report_date = models.DateField(null=True, blank=True)


class WithstandVoltageACTest(TimeStampedModel):
    """ 3.5. Withstand Voltage AC Test Report """

    induction_motor = models.OneToOneField(InductionMotor, on_delete=models.CASCADE,
                                           related_name="withstand_voltage_ac_test")
    description = models.CharField(max_length=50, blank=True, null=True)
    voltage_kv = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    time_in_seconds = models.PositiveIntegerField(blank=True, null=True)


class InsulationResistanceTest(TimeStampedModel):
    """ 3.6. Insulation Resistance Test Report """

    induction_motor = models.OneToOneField(InductionMotor, on_delete=models.CASCADE,
                                           related_name="insulation_resistance_test")
    description = models.CharField(max_length=50, blank=True, null=True)
    voltage = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    insulation_resistance = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    time_in_seconds = models.PositiveIntegerField(blank=True, null=True)
    ambient_temperature_C = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    humidity_percentage = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )


class LockRotorTest(TimeStampedModel):
    """ 3.7. Lock Rotor Test Report """

    induction_motor = models.OneToOneField(InductionMotor, on_delete=models.CASCADE, related_name="lock_rotor_test")
    vibration = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    noise = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    temperature = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    speed = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    voltage = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    current = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    power = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))]
    )
    report_date = models.CharField(max_length=20, null=True, blank=True)
    mdb_data = JSONField(null=True, blank=True)
    _report_date = models.DateField(null=True, blank=True)


class Configuration(models.Model):
    no_load_test = models.CharField(max_length=100)
    performance_determination = models.CharField(max_length=100)
    lock_rotor_test = models.CharField(max_length=100)
