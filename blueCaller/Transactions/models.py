from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class TransactionMain(models.Model):
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_idx = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=50)
    payment_method = models.CharField(max_length=50)
    payment_type = models.CharField(max_length=50)
    fee_for = models.CharField(max_length=50)
    plan_id = models.IntegerField()
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_transactions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"

    def __str__(self):
        return f"{self.transaction_idx} - {self.user.email}" 