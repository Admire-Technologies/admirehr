"""
Core models for the HRMS application.
"""

import uuid
from django.db import models


class BaseModel(models.Model):
    """
    Abstract base model with common fields for all models.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Company(BaseModel):
    """
    Company model for multi-tenant support.
    """
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    settings = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Companies"
        ordering = ['name']

    def __str__(self):
        return self.name


class TenantAwareModel(BaseModel):
    """
    Abstract model that includes company for multi-tenant support.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    class Meta:
        abstract = True