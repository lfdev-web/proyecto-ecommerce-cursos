from rest_framework import serializers
from .models import MembershipPlan, UserMembership, MembershipPayment


class MembershipPlanSerializer(serializers.ModelSerializer):
    tier_name = serializers.CharField(source='tier.name', read_only=True)
    tier_rank = serializers.IntegerField(source='tier.rank', read_only=True)
    audience_name = serializers.CharField(source='audience.name', read_only=True)

    class Meta:
        model = MembershipPlan
        fields = (
            'id', 'name', 'description', 'billing_cycle', 'price',
            'discount_pct', 'member_discount_pct', 'courses_limit',
            'audience', 'audience_name', 'tier', 'tier_name', 'tier_rank',
            'course_slots', 'instructor_commission_pct',
        )


class MembershipPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipPayment
        fields = ('id', 'amount', 'card_last4', 'paid_at', 'transaction_reference', 'is_successful')
        read_only_fields = fields


class UserMembershipSerializer(serializers.ModelSerializer):
    plan = MembershipPlanSerializer(read_only=True)
    is_currently_active = serializers.BooleanField(read_only=True)
    payments = MembershipPaymentSerializer(many=True, read_only=True)

    class Meta:
        model = UserMembership
        fields = (
            'id', 'plan', 'audience', 'status', 'is_currently_active',
            'started_at', 'expires_at', 'auto_renew', 'payments'
        )


class SubscribeSerializer(serializers.Serializer):
    """
    Datos necesarios para suscribirse a un plan.
    La tarjeta se valida con el Algoritmo de Luhn antes de procesar.
    CRÍTICO PCI-DSS: El número de tarjeta NUNCA se persiste en BD.
    Solo se almacenan los últimos 4 dígitos para referencia del usuario.
    """
    plan_id = serializers.IntegerField()
    # El card_number se usa solo en memoria para validación Luhn — nunca se guarda
    card_number = serializers.CharField(
        max_length=19,
        write_only=True,
        help_text="Número de tarjeta para validación Luhn (no se almacena)"
    )

    def validate_plan_id(self, value):
        try:
            plan = MembershipPlan.objects.get(id=value, is_active=True)
        except MembershipPlan.DoesNotExist:
            raise serializers.ValidationError("Plan de membresía no encontrado o inactivo.")
        return value

    def validate_card_number(self, value):
        from apps.orders.utils.luhn import is_valid_luhn
        if not is_valid_luhn(value):
            raise serializers.ValidationError(
                "Número de tarjeta inválido. Por favor verifica los datos."
            )
        return value
