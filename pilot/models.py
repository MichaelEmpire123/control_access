from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.


class User(AbstractUser):
    ROLE_CHOICES = (
        ('Admin', 'Администратор'),
        ('Contractor', 'Подрядчик'),
        ('Manager', 'Менеджер'),
        ('Security', 'Охранник КПП'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='Contractor',
    )

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'user'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Contractor(models.Model):
    STATUS_ACCREDITATION_CHOICES = (
        ('Accreditate', 'Аккредитован'),
        ('Noaccreditate', 'Неаккредитован'),
    )

    inn = models.IntegerField(max_length=12)
    name = models.CharField(max_length=120)
    status_accreditation = models.CharField(
        max_length=20,
        choices=STATUS_ACCREDITATION_CHOICES,
        default='Noaccreditate',
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'contractor'
        verbose_name = 'Подрядчик'
        verbose_name_plural = 'Подрядчики'


class ComplianceDocument(models.Model):
    TYPE_CHOICES = (
        ('Insurance', 'Страхование'),
        ('Registry', 'СРО'),
    )

    id_contractor = models.ForeignKey(Contractor, on_delete=models.CASCADE)
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
    )
    release_date = models.DateField()
    expiration_date = models.DateField()
    file = models.FileField(upload_to='compliance_documents')

    def __str__(self):
        return f"{self.get_type_display()} - {self.id_contractor.name}"  # Исправлено

    class Meta:
        db_table = 'compliance_document'
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'


class ContractorEmployee(models.Model):
    id_contractor = models.ForeignKey(Contractor, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120)
    passport = models.CharField(max_length=11)

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.name}".strip()  # Исправлено (был кортеж)

    class Meta:
        db_table = 'contractor_employee'
        verbose_name = 'Сотрудник подрядчика'
        verbose_name_plural = 'Сотрудники подрядчиков'


class AccessPass(models.Model):
    STATUS_CHOICES = (
        ('active', 'Активен'),
        ('passive', 'Неактивен'),
    )
    TYPE_CHOICES = (
        ('permanent', 'Постоянный'),
        ('temporary', 'Временный'),
        ('one_time', 'Разовый'),
    )

    id_employee = models.ForeignKey(ContractorEmployee, on_delete=models.CASCADE)
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='temporary',
    )
    zona_access = models.CharField(max_length=120)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
    )

    def __str__(self):
        return f"{self.type} - {self.zona_access} - {self.status}"

    class Meta:
        db_table = 'access_pass'
        verbose_name = 'Пропуск'
        verbose_name_plural = 'Пропуска'


class Blacklist(models.Model):
    TYPE_CHOICES = (
        ('Yurlico', 'Юрлицо'),  # Contractor (компания)
        ('Fizlico', 'Физлицо'),  # ContractorEmployee (сотрудник)
    )

    # Для юрлица - это ID Contractor, для физлица - ID ContractorEmployee
    entity_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name='Тип сущности'
    )
    entity_id = models.CharField(
        max_length=36,
        verbose_name='ID сущности',
        help_text='ID Contractor (юрлицо) или ID ContractorEmployee (физлицо)'
    )
    reason = models.TextField(verbose_name='Причина')
    date = models.DateField(auto_now_add=True, verbose_name='Дата внесения')
    added_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Добавил'
    )

    def __str__(self):
        return f"{self.get_entity_type_display()} (ID: {self.entity_id}) - {self.reason[:30]}"

    class Meta:
        db_table = 'blacklist'
        verbose_name = 'Запись черного списка'
        verbose_name_plural = 'Черный список'
        unique_together = ['entity_type', 'entity_id']


