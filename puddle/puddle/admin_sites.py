from __future__ import annotations

from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.admin import UserAdmin
from django.db import models
from django.db.models import Count, Sum
from django.http import HttpRequest
from django.template.response import TemplateResponse
from django.urls import path

from carts.models import Cart
from goods.models import Categories, Products
from notifications.models import NotificationLog, Subscription
from orders.models import Order, OrderItem
from users.models import User


class BaseRoleAdminSite(AdminSite):
    index_template = "custom_admin/admin/index.html"
    site_url = "/"

    custom_css_path: str | None = None

    def each_context(self, request: HttpRequest):
        context = super().each_context(request)
        context["custom_css"] = self.custom_css_path
        return context

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("dashboard/", self.admin_view(self.dashboard_view), name="dashboard"),
            path("health/", self.admin_view(self.health_view), name="health"),
        ]
        return custom_urls + urls

    def dashboard_view(self, request: HttpRequest):
        context = {
            **self.each_context(request),
            "title": "Dashboard",
            "stats": {
                "products": Products.objects.count(),
                "categories": Categories.objects.count(),
                "orders": Order.objects.count(),
                "order_items": OrderItem.objects.count(),
                "carts": Cart.objects.count(),
                "subscriptions": Subscription.objects.count(),
            },
            "sales": (OrderItem.objects.aggregate(total=Sum("price")) or {}).get("total"),
            "recent_orders": (
                Order.objects.select_related("user")
                .order_by("-created_timestamp")
                .only("id", "created_timestamp", "status", "is_paid", "user")[:10]
            ),
            "top_products": (
                Products.objects.annotate(sales_count=Count("orderitem"))
                .order_by("-sales_count")
                .only("id", "name")[:10]
            ),
        }
        return TemplateResponse(request, "custom_admin/admin/dashboard.html", context)

    def health_view(self, request: HttpRequest):
        try:
            Products.objects.only("id").exists()
            db_ok = True
        except Exception:
            db_ok = False

        context = {
            **self.each_context(request),
            "title": "Health",
            "db_ok": db_ok,
        }
        return TemplateResponse(request, "custom_admin/admin/health.html", context)


class StaffAdminSite(BaseRoleAdminSite):
    site_header = "Staff Admin"
    site_title = "Staff Admin"
    index_title = "Content"
    custom_css_path = "custom_admin/css/staff_admin.css"

    def has_permission(self, request: HttpRequest):
        user = request.user
        if not (user.is_active and user.is_staff):
            return False
        if user.is_superuser:
            return True
        return user.groups.filter(name="ContentEditor").exists()


class OpsAdminSite(BaseRoleAdminSite):
    site_header = "Ops Admin"
    site_title = "Ops Admin"
    index_title = "Operations"
    custom_css_path = "custom_admin/css/ops_admin.css"

    def has_permission(self, request: HttpRequest):
        user = request.user
        if not (user.is_active and user.is_staff):
            return False
        if user.is_superuser:
            return True
        return user.groups.filter(name__in=["Support", "Manager"]).exists()


staff_admin_site = StaffAdminSite(name="staff_admin")
ops_admin_site = OpsAdminSite(name="ops_admin")


class OrderItemInlineReadOnly(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    show_change_link = True
    fields = ("order", "quantity", "price", "created_timestamp")
    readonly_fields = fields


@admin.register(Products, site=staff_admin_site)
class StaffProductAdmin(admin.ModelAdmin):
    change_form_template = "custom_admin/admin/change_form.html"
    list_display = ("display_id", "name", "final_price", "discount", "quantity", "category")
    list_filter = ("category", "discount")
    search_fields = ("name", "description")
    ordering = ("id",)
    list_select_related = ("category",)
    list_editable = ("discount", "quantity")
    inlines = (OrderItemInlineReadOnly,)

    formfield_overrides = {
        models.TextField: {"widget": admin.widgets.AdminTextareaWidget(attrs={"rows": 6})},
    }

    @admin.display(description="Final price")
    def final_price(self, obj: Products):
        return obj.sell_price()

    @admin.action(description="Set discount to 0%")
    def set_discount_zero(self, request: HttpRequest, queryset):
        queryset.update(discount=0)

    actions = ("set_discount_zero",)

    def get_readonly_fields(self, request: HttpRequest, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        user = request.user
        if user.is_superuser:
            return readonly
        if user.groups.filter(name="ContentEditor").exists():
            readonly.extend(["price", "discount", "quantity", "category", "name", "slug"])
        return readonly


@admin.register(Categories, site=staff_admin_site)
class StaffCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("product", "name", "price", "quantity")
    readonly_fields = ("name", "price")


@admin.action(description="Mark selected orders as paid")
def mark_orders_paid(modeladmin: admin.ModelAdmin, request: HttpRequest, queryset):
    queryset.update(is_paid=True)


# @admin.register(Order, site=ops_admin_site)
# class OpsOrderAdmin(admin.ModelAdmin):
#     change_form_template = "custom_admin/admin/change_form.html"
#     list_display = ("id", "user", "created_timestamp", "status", "is_paid")
#     list_filter = ("status", "is_paid", "created_timestamp")
#     search_fields = ("user__username", "phone_number", "id")
#     date_hierarchy = "created_timestamp"
#     autocomplete_fields = ("user",)
#     inlines = (OrderItemInline,)
#     actions = (mark_orders_paid,)

#     formfield_overrides = {
#         models.TextField: {"widget": admin.widgets.AdminTextareaWidget(attrs={"rows": 4})},
#     }

#     def get_queryset(self, request: HttpRequest):
#         qs = super().get_queryset(request)
#         qs = qs.select_related("user")
#         user = request.user
#         if user.is_superuser:
#             return qs
#         if user.groups.filter(name="Support").exists():
#             return qs.filter(is_paid=False)
#         return qs

#     def get_readonly_fields(self, request: HttpRequest, obj=None):
#         readonly = list(super().get_readonly_fields(request, obj))
#         user = request.user
#         if user.is_superuser:
#             return readonly
#         if user.groups.filter(name="Support").exists():
#             readonly.extend(["user", "phone_number", "requires_delivery", "delivery_address", "payment_on_get"])
#         return readonly


# @admin.register(OrderItem, site=ops_admin_site)
# class OpsOrderItemAdmin(admin.ModelAdmin):
#     list_display = ("order", "product", "name", "price", "quantity", "created_timestamp")
#     list_filter = ("created_timestamp",)
#     search_fields = ("name", "order__id", "product__name")
#     autocomplete_fields = ("order", "product")

#     def get_queryset(self, request: HttpRequest):
#         qs = super().get_queryset(request)
#         return qs.select_related("order", "product")


# @admin.register(Cart, site=ops_admin_site)
# class OpsCartAdmin(admin.ModelAdmin):
#     list_display = ("id", "user", "product", "quantity", "session_key", "created_timestamp")
#     list_filter = ("created_timestamp",)
#     search_fields = ("user__username", "product__name", "session_key")
#     autocomplete_fields = ("user", "product")

#     def get_queryset(self, request: HttpRequest):
#         qs = super().get_queryset(request)
#         return qs.select_related("user", "product")


class SubscriptionInline(admin.StackedInline):
    model = Subscription
    extra = 0
    can_delete = False


@admin.register(User, site=ops_admin_site)
class OpsUserAdmin(UserAdmin):
    list_display = ("username", "email", "email_verified", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active", "email_verified", "groups")
    search_fields = ("username", "email")
    inlines = (SubscriptionInline,)


@admin.register(Subscription, site=ops_admin_site)
class OpsSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "is_subscribed")
    list_filter = ("is_subscribed",)
    search_fields = ("user__username", "user__email")
    autocomplete_fields = ("user",)


@admin.register(NotificationLog, site=ops_admin_site)
class OpsNotificationLogAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "sent_at")
    list_filter = ("status", "sent_at")
    search_fields = ("user__username", "message")
    autocomplete_fields = ("user",)
