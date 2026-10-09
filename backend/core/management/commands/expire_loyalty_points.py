from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from core.models import LoyaltySettings, PointTransaction, Customer


class Command(BaseCommand):
    help = 'Expire loyalty points that have passed their expiry date'

    def handle(self, *args, **options):
        today = timezone.now()
        expired_count = 0
        total_points_expired = 0

        # Find all restaurants with loyalty settings and expiry enabled
        loyalty_settings = LoyaltySettings.objects.filter(
            enabled=True,
            points_expiry_days__isnull=False
        )

        for settings in loyalty_settings:
            restaurant = settings.restaurant

            # Find expired point transactions (earned points that have expired)
            # Only those that haven't been reversed or expired yet
            expired_transactions = PointTransaction.objects.filter(
                restaurant=restaurant,
                transaction_type='EARNED',
                expires_at__lt=today
            ).exclude(
                id__in=PointTransaction.objects.filter(
                    transaction_type__in=['REVERSED', 'EXPIRED']
                ).values_list('related_transaction_id', flat=True)
            ).select_related('customer')

            with transaction.atomic():
                for tx in expired_transactions:
                    # Lock customer for update
                    customer = Customer.objects.select_for_update().get(pk=tx.customer.id)

                    # Check if customer actually has these points available
                    # (they might have been spent or already reversed)
                    if customer.points < tx.points:
                        # Can't expire more points than customer has
                        points_to_expire = customer.points
                    else:
                        points_to_expire = tx.points

                    if points_to_expire <= 0:
                        continue

                    new_balance = customer.points - points_to_expire
                    customer.points = max(0, new_balance)  # Prevent negative balance
                    customer.save()

                    # Create expiry transaction
                    PointTransaction.objects.create(
                        customer=customer,
                        restaurant=restaurant,
                        transaction_type='EXPIRED',
                        points=-points_to_expire,
                        balance_after=customer.points,
                        related_transaction=tx,
                        description=f"Expired {points_to_expire} points from transaction #{tx.id}"
                    )

                    expired_count += 1
                    total_points_expired += points_to_expire

        self.stdout.write(
            self.style.SUCCESS(
                f"Expired {expired_count} point transactions totaling {total_points_expired} points."
            )
        )
