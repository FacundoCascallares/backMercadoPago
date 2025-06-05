from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from .views import (
    DestinosViewSet,
    MetodoPagoViewSet,
    NosotrosViewSet,
    CarritoViewSet,
    profile_api_view,
    profile_detail_api_view,
    obtener_usuario_autenticado,
    listar_compras,
    obtener_perfil_usuario,
    checkout,
    LoginView,
    RegisterView,
    token_refresh,
    agregar_al_carrito,
    obtener_carrito,
    eliminar_item_carrito,
    actualizar_fecha_salida,
    actualizar_perfil_parcial,
    create_preference, 
    mercadopago_notifications, 
    mercadopago_success, 
    mercadopago_failure, 
    mercadopago_pending
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = DefaultRouter()
router.register(r'destinos', DestinosViewSet)
router.register(r'nosotros', NosotrosViewSet)
router.register(r'carrito', CarritoViewSet, basename='carrito')
router.register(r'metodos-pago', MetodoPagoViewSet)

# Configuración principal de URLs
urlpatterns = [
    path('admin/', admin.site.urls),
    
    #MERCADO PAGO
    path('api/mercadopago/create_preference/', create_preference, name='create_preference'),
    path('api/mercadopago/notifications/', mercadopago_notifications, name='mercadopago_notifications'),
    path('api/mercadopago/success/', mercadopago_success, name='mercadopago_success'),
    path('api/mercadopago/failure/', mercadopago_failure, name='mercadopago_failure'),
    path('api/mercadopago/pending/', mercadopago_pending, name='mercadopago_pending'),

    # API v1
    path('api/v1/', include([
        # Autenticación
        path('auth/', include([
            path('register/', RegisterView.as_view(), name='register'),
            path('login/', LoginView.as_view(), name='login'),
            path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
            path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
            path('custom-token/refresh/', token_refresh, name='custom_token_refresh'),
        ])),

        # Perfiles
        path('profiles/', include([
            path('', profile_api_view, name='profiles_api'),
            path('<int:pk>/', profile_detail_api_view, name='profiles_detail_api'),
            path('me/update/', actualizar_perfil_parcial, name='actualizar_perfil_parcial'),
            path('me/', obtener_perfil_usuario, name='obtener_perfil'),
        ])),

        # Carrito
        path('cart/', include([
            path('', obtener_carrito, name='obtener_carrito'),
            path('add/', agregar_al_carrito, name='agregar-al-carrito'),
            path('remove/<int:id>/', eliminar_item_carrito, name='eliminar-item-carrito'),
            path('<int:pk>/update-quantity/', CarritoViewSet.as_view({'put': 'actualizar_cantidad'}),
                 name='actualizar_cantidad'),
            path('<int:id>/update-date/', actualizar_fecha_salida, name='actualizar_fecha_salida'),
        ])),

        # Compras
        path('purchases/', listar_compras, name='listar_compras'),
        path('checkout/', checkout, name='checkout'),

        # Usuario actual
        path('user/me/', obtener_usuario_autenticado, name='obtener_usuario_autenticado'),

        # Router principal
        path('', include(router.urls)),
    ])),

    # Accounts (recuperación de contraseña)
    path('api/accounts/', include('accounts.urls')),
]

# Servir archivos multimedia en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)