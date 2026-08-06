from django.contrib import admin
from .models import (
    MembershipPlan, UserMembership, MembershipPayment,
    PlanAudience, PlanTier,
)


@admin.register(PlanAudience)
class PlanAudienceAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'description')


@admin.register(PlanTier)
class PlanTierAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'rank', 'description')
    ordering = ('rank',)


@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'audience', 'tier', 'price', 'member_discount_pct',
        'course_slots', 'instructor_commission_pct', 'is_active',
    )
    list_filter = ('audience', 'tier', 'billing_cycle', 'is_active')
    ordering = ('audience', 'tier__rank')


class MembershipPaymentInline(admin.TabularInline):
    model = MembershipPayment
    extra = 0
    readonly_fields = ('amount', 'card_last4', 'paid_at', 'transaction_reference', 'is_successful')


@admin.register(UserMembership)
class UserMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'audience', 'plan', 'status', 'is_currently_active', 'expires_at', 'auto_renew')
    list_filter = ('audience', 'status')
    readonly_fields = ('started_at', 'cancelled_at')
    inlines = [MembershipPaymentInline]


@admin.register(MembershipPayment)
class MembershipPaymentAdmin(admin.ModelAdmin):
    list_display = ('membership', 'amount', 'card_last4', 'is_successful', 'paid_at')
    list_filter = ('is_successful',)
    readonly_fields = ('paid_at',)
