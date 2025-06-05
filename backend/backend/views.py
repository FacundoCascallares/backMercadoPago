from rest_framework import viewsets, generics, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import Destinos, Carrito, Nosotros, User, MetodoPago, Profile
from .serializers import (
    DestinosSerializer,
    MetodoPagoSerializer,
    CarritoSerializer,
    NosotrosSerializer,
    ProfileSerializer,
    RegisterSerializer,
    LoginSerializer
)
from django.contrib.auth.models import User
import logging
from rest_framework import serializers

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import mercadopago
import json
import uuid
from django.db import transaction
from django.utils import timezone

# SDK DE MERCADO PAGO
sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

logger = logging.getLogger(__name__)

class MetodoPagoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MetodoPago.objects.all()
    serializer_class = MetodoPagoSerializer

#########################################
# Nosotros
#########################################

class NosotrosViewSet(viewsets.ModelViewSet):
    queryset = Nosotros.objects.all()
    serializer_class = NosotrosSerializer

    def get_permissions(self):
        if self.action == 'list':
            self.permission_classes = [AllowAny]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        logger.debug('Creating a new Nosotros entry')
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        logger.debug(f'Nosotros created successfully: {serializer.data}')
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        logger.debug(f'Updating Nosotros with id: {instance.id_nosotros}')
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        logger.debug(f'Nosotros updated successfully: {serializer.data}')
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        logger.debug(f'Deleting Nosotros with id: {instance.id_nosotros}')
        self.perform_destroy(instance)
        logger.debug('Nosotros deleted successfully')
        return Response(status=status.HTTP_204_NO_CONTENT)

###########################
## Destinos
###########################

class DestinosViewSet(viewsets.ModelViewSet):
    queryset = Destinos.objects.all()
    serializer_class = DestinosSerializer

    def get_permissions(self):
        if self.action == 'list':
            self.permission_classes = [AllowAny]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        logger.debug(f'Updating Destino with id: {instance.id_destino}')
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        logger.debug(f'Destino updated successfully: {serializer.data}')
        return Response(serializer.data)

#############################################
####### Carrito
#############################################

class CarritoViewSet(viewsets.ModelViewSet):
    queryset = Carrito.objects.all()
    serializer_class = CarritoSerializer

    @action(detail=True, methods=['put'])
    def actualizar_cantidad(self, request, pk=None):
        try:
            carrito_item = self.get_object()
            nueva_cantidad = request.data.get('cantidad')

            if not nueva_cantidad or int(nueva_cantidad) < 1:
                return Response({'error': 'Cantidad inválida'}, status=status.HTTP_400_BAD_REQUEST)

            carrito_item.cantidad = int(nueva_cantidad)
            carrito_item.save()
            return Response(CarritoSerializer(carrito_item).data)
        except Carrito.DoesNotExist:
            return Response({'error': 'Carrito item not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error al actualizar la cantidad: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def agregar_al_carrito(request):
    try:
        id_destino = request.data.get('id_destino')
        cantidad = request.data.get('cantidad', 1)
        id_metodo_pago = request.data.get('id_metodoPago')


        if not id_destino:
            return Response({'error': 'id_destino es requerido'}, status=status.HTTP_400_BAD_REQUEST)

        destino = Destinos.objects.get(pk=id_destino)

        if id_metodo_pago:
            metodo_pago = MetodoPago.objects.get(pk=id_metodo_pago)
        else:
            metodo_pago = MetodoPago.objects.first()

        carrito_item = Carrito.objects.create(
            user=request.user,
            id_destino=destino,
            id_metodoPago=metodo_pago,
            cantidad=cantidad

        )

        serializer = CarritoSerializer(carrito_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except Destinos.DoesNotExist:
        return Response({'error': 'Destino no encontrado'}, status=status.HTTP_404_NOT_FOUND)
    except MetodoPago.DoesNotExist:
        return Response({'error': 'Método de pago no encontrado'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_carrito(request):
    try:
        carrito_items = Carrito.objects.filter(user=request.user)
        serializer = CarritoSerializer(carrito_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def eliminar_item_carrito(request, id):
    try:
        carrito_item = Carrito.objects.get(pk=id, user=request.user)
        carrito_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Carrito.DoesNotExist:
        return Response({'error': 'Ítem del carrito no encontrado'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
def actualizar_fecha_salida(request, id):
    try:
        carrito_item = Carrito.objects.get(pk=id)
    except Carrito.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    data = request.data
    fecha_salida = data.get('fecha_salida')
    if fecha_salida:
        carrito_item.fecha_salida = fecha_salida
        carrito_item.save()
        return Response(status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Fecha de salida no proporcionada"})

#################################
### Dashboard
#################################

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_compras(request):
    compras = Carrito.objects.filter(user=request.user)
    serializer = CarritoSerializer(compras, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_perfil_usuario(request):
    try:
        profile = Profile.objects.get(user=request.user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Profile.DoesNotExist:
        return Response({'error': 'Perfil no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

##############################################

@api_view(['POST'])
def checkout(request):
    try:
        carrito_items = Carrito.objects.filter(user=request.user)
        metodo_pago = MetodoPago.objects.get(id_metodoPago=request.data['metodo_pago'])

        if not carrito_items.exists():
            return Response({'error': 'El carrito está vacío.'}, status=status.HTTP_400_BAD_REQUEST)

        for item in carrito_items:
            item.estado = 'comprado'
            item.save()

        return Response({'message': 'Compra realizada con éxito.'}, status=status.HTTP_200_OK)
    except MetodoPago.DoesNotExist:
        return Response({'error': 'Método de pago no válido.'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def token_refresh(request):
    serializer = TokenRefreshView().get_serializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return Response(serializer.validated_data, status=status.HTTP_200_OK)

# Perfiles de Usuario

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def profile_api_view(request):
    if request.method == 'GET':
        profiles = Profile.objects.all()
        profiles_serializer = ProfileSerializer(profiles, many=True)
        return Response(profiles_serializer.data, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        profile_serializer = ProfileSerializer(data=request.data)
        if profile_serializer.is_valid():
            profile_serializer.save()
            return Response(profile_serializer.data, status=status.HTTP_201_CREATED)
        return Response(profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_usuario_autenticado(request):
    try:
        profile = Profile.objects.get(user=request.user)
        profile_serializer = ProfileSerializer(profile)
        return Response(profile_serializer.data, status=status.HTTP_200_OK)
    except Profile.DoesNotExist:
        return Response({'error': 'Perfil no encontrado'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def profile_detail_api_view(request, pk=None):
    profile = Profile.objects.filter(id=pk).first()
    if profile:
        if request.method == 'GET':
            profile_serializer = ProfileSerializer(profile)
            return Response(profile_serializer.data, status=status.HTTP_200_OK)
        elif request.method == 'PUT':
            profile_serializer = ProfileSerializer(profile, data=request.data)
            if profile_serializer.is_valid():
                profile_serializer.save()
                return Response(profile_serializer.data, status=status.HTTP_200_OK)
            return Response(profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'DELETE':
            profile.delete()
            return Response({'message': 'Perfil eliminado correctamente'}, status=status.HTTP_200_OK)
    return Response({'message': 'No se ha encontrado un perfil con estos datos'}, status=status.HTTP_404_NOT_FOUND)

# Nuevo endpoint para actualización parcial del perfil
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def actualizar_perfil_parcial(request):
    try:
        profile = Profile.objects.get(user=request.user)
        # Solo permitimos actualizar estos campos específicos
        campos_permitidos = {'telephone', 'dni', 'address'}
        data = {k: v for k, v in request.data.items() if k in campos_permitidos}

        if not data:
            return Response(
                {'error': 'No se proporcionaron campos válidos para actualizar. Campos permitidos: telephone, dni, address'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ProfileSerializer(profile, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Profile.DoesNotExist:
        return Response({'error': 'Perfil no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error al actualizar perfil: {str(e)}")
        return Response(
            {'error': 'Ocurrió un error al actualizar el perfil'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            register_serializer = self.get_serializer(data=request.data)
            register_serializer.is_valid(raise_exception=True)
            user = register_serializer.save()

            # La señal post_save se encargará de crear el perfil automáticamente

            # Autenticar al usuario recién creado
            login_data = {
                'email': request.data['email'],
                'password': request.data['password']
            }
            login_serializer = LoginSerializer(data=login_data)
            login_serializer.is_valid(raise_exception=True)
            user = login_serializer.validated_data['user']

            refresh = RefreshToken.for_user(user)

            # Obtener el perfil creado por la señal
            profile = Profile.objects.get(user=user)

            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': ProfileSerializer(profile).data
            }, status=status.HTTP_201_CREATED)

        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
# your_app/views.py

@csrf_exempt
def create_preference(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cart_items_payload = data.get('items', [])
            user_id = data.get('user_id')

            logger.info(f"create_preference: Datos recibidos: {data}")
            logger.info(f"create_preference: Ítems recibidos: {cart_items_payload}")

            if not cart_items_payload:
                logger.error("create_preference: No items in cart payload.")
                return JsonResponse({'error': 'No items in cart'}, status=400)

            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                logger.error(f"create_preference: User with ID {user_id} not found.")
                return JsonResponse({'error': 'User not found'}, status=404)

            items_mp = []
            external_reference = f"order-{user.id}-{uuid.uuid4()}"
            
            payer_email = user.email if user.email else "test_user@example.com" # Ajusta a un email de prueba de MP si el usuario no tiene

            with transaction.atomic():
                for item_payload in cart_items_payload:
                    destino_id = item_payload.get('id_destino')
                    cantidad_comprada = item_payload.get('cantidadComprada')
                    
                    # Validación básica del payload
                    if not destino_id or not isinstance(cantidad_comprada, int) or cantidad_comprada <= 0:
                        logger.warning(f"Ítem inválido o incompleto en payload, se ignorará: {item_payload}. Faltan id_destino o cantidadComprada.")
                        continue 

                    try:
                        # Obtener el objeto Destino primero (asegurando que exista)
                        destino = Destinos.objects.get(pk=destino_id)
                    except Destinos.DoesNotExist:
                        logger.warning(f"Destino con ID {destino_id} no encontrado en la DB para item_payload: {item_payload}. Se ignorará.")
                        continue 

                    try:
                        # Buscar el item del carrito existente para este usuario y destino
                        # que aún esté en estado 'cart_active'
                        carrito_item_db = Carrito.objects.get(
                            user=user,
                            id_destino=destino, # ¡Usamos el objeto Destino aquí!
                            estado_pago='cart_active'
                        )
                        
                        # Actualiza la cantidad y el estado/referencia
                        carrito_item_db.cantidad = cantidad_comprada
                        carrito_item_db.estado_pago = 'in_process'
                        carrito_item_db.mercadopago_external_reference = external_reference
                        # Asegúrate de que Carrito.clean() o Carrito.save() no generen validación para id_metodoPago si no se actualiza
                        carrito_item_db.save()
                        logger.info(f"Carrito ID {carrito_item_db.id_compra} para destino {destino_id} actualizado a 'in_process'.")

                        items_mp.append({
                            # MP recomienda el 'id' del producto, puedes usar el ID del destino
                            "id": str(destino.pk), 
                            "title": item_payload.get('nombre_Destino', destino.nombre_Destino), # Prioriza payload, fallback a DB
                            # ¡CORREGIDO AQUÍ! Se cambió 'destino.descripcion_Destino' por 'destino.descripcion'
                            "description": item_payload.get('descripcion', destino.descripcion), # Prioriza payload, fallback a DB
                            "quantity": cantidad_comprada,
                            "currency_id": "ARS", # Asegúrate que esta sea tu moneda
                            "unit_price": float(item_payload.get('precio_Destino', destino.precio_Destino)), # Prioriza payload, fallback a DB
                            "picture_url": item_payload.get('image', '') # Usar la URL de imagen del payload
                        })
                    except Carrito.DoesNotExist:
                        logger.warning(f"Item de carrito para user {user_id} y destino {destino_id} no encontrado en estado 'cart_active'. Se ignorará.")
                        continue # Si no existe el Carrito activo, no hay nada que procesar para este intento
                    except Exception as e: # Captura cualquier otro error durante el procesamiento del ítem del carrito
                        logger.error(f"Error inesperado al procesar el ítem del carrito para destino {destino_id} (user {user_id}): {e}", exc_info=True)
                        continue


                if not items_mp:
                    logger.warning("create_preference: Después de procesar todos los ítems del payload, 'items_mp' está vacío. No hay ítems válidos para Mercado Pago.")
                    return JsonResponse({'error': 'No valid items to process for payment.'}, status=400)


                notification_url = f"{settings.BACKEND_BASE_URL}/api/mercadopago/notifications/"
                
                preference_data = {
                    "items": items_mp,
                    "payer": {
                        "email": payer_email,
                    },
                    "back_urls": {
                        "success": f"{settings.BACKEND_BASE_URL}/api/mercadopago/feedback/?status=success",
                        "failure": f"{settings.BACKEND_BASE_URL}/api/mercadopago/feedback/?status=failure",
                        "pending": f"{settings.BACKEND_BASE_URL}/api/mercadopago/feedback/?status=pending"
                    },
                    "auto_return": "approved", # Cambiado a "approved" para ser más amplio en las redirecciones
                    "notification_url": notification_url,
                    "external_reference": external_reference, 
                    "binary_mode": False, # Asegura que recibas todas las notificaciones
                    "metadata": { 
                        "user_id": user.id,
                    }
                }

                logger.info(f"create_preference: Enviando a Mercado Pago preferencia: {json.dumps(preference_data, indent=2)}") # Log la preferencia antes de enviar

                preference_response = sdk.preference().create(preference_data)
                
                # Modificado para un chequeo más robusto de la respuesta
                # Mercado Pago puede devolver 'status' como string o int
                mp_status = preference_response.get("status")
                mp_response = preference_response.get("response")

                if mp_status in [200, 201] and mp_response:
                    preference = mp_response
                    logger.info(f"Preferencia de Mercado Pago creada exitosamente. ID: {preference['id']}")

                    # Guarda el preference_id de Mercado Pago en los ítems del carrito
                    Carrito.objects.filter(mercadopago_external_reference=external_reference, user=user)\
                        .update(mercadopago_preference_id=preference['id'])

                    return JsonResponse({
                        'init_point': preference['init_point'],
                        'preference_id': preference['id'],
                        'external_reference': external_reference 
                    })
                else:
                    # SI FALLA: Esto es lo CLAVE. Imprime la respuesta COMPLETA de MP.
                    full_mp_error_details = preference_response
                    logger.error(f"Error al crear la preferencia de Mercado Pago. Detalles completos de MP: {full_mp_error_details}")
                    
                    # Revertimos el estado de los ítems si falla la creación de la preferencia en MP
                    Carrito.objects.filter(mercadopago_external_reference=external_reference, user=user)\
                        .update(estado_pago='cart_active', mercadopago_external_reference=None, mercadopago_preference_id=None)
                    
                    # Devuelve los detalles completos a Postman para facilitar la depuración
                    return JsonResponse({
                        'error': 'Error creating preference in Mercado Pago',
                        'mercadopago_details': full_mp_error_details
                    }, status=400)

        except json.JSONDecodeError:
            logger.error("create_preference: Invalid JSON received.", exc_info=True)
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            # Este es un catch-all para errores inesperados antes o después de la interacción con MP
            logger.error(f"Error inesperado en create_preference: {str(e)}", exc_info=True)
            return JsonResponse({'error': 'Internal server error: ' + str(e)}, status=500)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def mercadopago_notifications(request):
    """
    Esta vista maneja las notificaciones (webhooks) de Mercado Pago.
    Cuando un pago cambia de estado, Mercado Pago envía una notificación aquí.
    """
    if request.method == 'GET':
        # Mercado Pago hace una petición GET para validar el webhook
        return JsonResponse({'status': 'ok'})
    elif request.method == 'POST':
        try:
            notification_data = json.loads(request.body)
            topic = notification_data.get('topic')
            resource_id = notification_data.get('id') # ID del recurso (pago o merchant_order)
            
            logger.info(f"Notificación de Mercado Pago recibida: Topic={topic}, Resource ID={resource_id}")

            if topic == 'payment':
                # Obtener detalles completos del pago desde la API de Mercado Pago
                payment_info_response = sdk.payment().get(resource_id)
                if payment_info_response["status"] != 200:
                    logger.error(f"Error al obtener detalles del pago {resource_id} desde MP: {payment_info_response.get('message')}")
                    # Aunque haya un error al obtener detalles, responder 200 para que MP no reintente
                    return JsonResponse({'error': 'Error fetching payment details from MP'}, status=200) 

                payment_data = payment_info_response['response']
                payment_status = payment_data['status'] # 'approved', 'rejected', 'pending', etc.
                payment_id = payment_data['id']
                # La referencia externa que enviamos cuando creamos la preferencia
                external_reference = payment_data.get('external_reference')
                amount = payment_data['transaction_amount']

                logger.info(f"Pago ID: {payment_id}, Estado: {payment_status}, Referencia Externa: {external_reference}, Monto: {amount}")

                # --- Lógica CRÍTICA: Actualizar el estado de tu Carrito en la DB ---
                if external_reference:
                    try:
                        # Buscar todos los ítems del carrito asociados a esta referencia externa
                        # que se crearon cuando se generó la preferencia
                        carrito_items_to_update = Carrito.objects.filter(
                            mercadopago_external_reference=external_reference,
                            # Puedes añadir más filtros, como que el estado anterior fuera 'in_process'
                            # o que el usuario sea el correcto si no lo pusiste en la external_reference
                            # user__id=user_id_extraido_de_external_reference
                        )

                        if not carrito_items_to_update.exists():
                            logger.warning(f"No se encontraron ítems de carrito con external_reference: {external_reference}")
                            # Aunque no se encuentren, respondemos 200 para que MP no reintente
                            return JsonResponse({'status': 'no matching cart items found'}, status=200)

                        # Actualizar el estado de todos los ítems encontrados
                        # Usamos update() para eficiencia en lote
                        update_fields = {
                            'estado_pago': payment_status, # Actualiza al estado que MP nos envía
                            'mercadopago_payment_id': payment_id,
                            'fecha_pago_actualizacion': timezone.now()
                        }
                        
                        if payment_status == 'approved':
                            update_fields['fecha_compra'] = timezone.now()
                            # Si es aprobado, y quieres eliminar los ítems del carrito activo del usuario,
                            # podrías crear un nuevo modelo 'Orden' y mover los datos ahí, y luego eliminar
                            # estos ítems del carrito. Pero esto va más allá de esta iteración.
                            
                        elif payment_status == 'rejected' or payment_status == 'cancelled':
                            # Si el pago falla o es cancelado, puedes considerar "liberar" los ítems del carrito
                            # para una nueva compra, o simplemente dejarlos con el estado de rechazo.
                            # update_fields['mercadopago_external_reference'] = None # Opcional: para reusar el carrito
                            # update_fields['mercadopago_preference_id'] = None # Opcional: para reusar el carrito
                            pass # Ya se actualizó el estado a 'rejected' o 'cancelled'


                        carrito_items_to_update.update(**update_fields)
                        logger.info(f"Actualizados {carrito_items_to_update.count()} ítems de carrito para external_reference {external_reference} a estado: {payment_status}")
                        
                        # Aquí puedes añadir más lógica de negocio, como:
                        # - Enviar un email de confirmación
                        # - Actualizar stock de productos
                        # - Crear una factura
                        # - Mover ítems a un historial de pedidos final si el modelo Carrito es temporal

                    except Exception as db_e:
                        logger.error(f"Error al actualizar la base de datos para external_reference {external_reference}: {db_e}", exc_info=True)
                        # No retornar error (4xx/5xx) aquí, MP necesita 200 OK para no reintentar
                        return JsonResponse({'status': 'internal db error, but notification received'}, status=200)
                else:
                    logger.warning(f"Notificación de Mercado Pago recibida sin external_reference. Payment ID: {payment_id}")

                return JsonResponse({'status': 'notification processed'}, status=200)

            elif topic == 'merchant_order':
                # Las notificaciones de merchant_order consolidan varios pagos de una orden.
                # Puedes obtener detalles de la orden de pago:
                # merchant_order_info_response = sdk.merchant_orders().get(resource_id)
                # merchant_order_data = merchant_order_info_response['response']
                # logger.info(f"Merchant Order ID: {merchant_order_data['id']}, Estado: {merchant_order_data['status']}")
                # Aquí también deberías actualizar el estado de tu pedido si es necesario
                return JsonResponse({'status': 'merchant_order notification processed'}, status=200)
            else:
                logger.info(f"Notificación de Mercado Pago con topic desconocido: {topic}")
                return JsonResponse({'status': 'unknown topic'}, status=200)

        except json.JSONDecodeError:
            logger.error('Invalid JSON in Mercado Pago notification request.', exc_info=True)
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error procesando notificación de Mercado Pago: {e}", exc_info=True)
            return JsonResponse({'error': 'Internal server error: ' + str(e)}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def mercadopago_success(request):
    """
    Vista de retorno para pagos exitosos.
    El usuario es redirigido aquí después de un pago aprobado.
    Puedes mostrar un mensaje de éxito o redirigir a una página de confirmación.
    """
    payment_id = request.GET.get('payment_id')
    status = request.GET.get('status')
    preference_id = request.GET.get('preference_id')
    # Puedes usar estos parámetros para mostrar un mensaje al usuario
    return JsonResponse({'message': 'Payment successful!', 'payment_id': payment_id, 'status': status, 'preference_id': preference_id})

def mercadopago_failure(request):
    """
    Vista de retorno para pagos fallidos.
    """
    payment_id = request.GET.get('payment_id')
    status = request.GET.get('status')
    preference_id = request.GET.get('preference_id')
    return JsonResponse({'message': 'Payment failed.', 'payment_id': payment_id, 'status': status, 'preference_id': preference_id}, status=400)

def mercadopago_pending(request):
    """
    Vista de retorno para pagos pendientes.
    """
    payment_id = request.GET.get('payment_id')
    status = request.GET.get('status')
    preference_id = request.GET.get('preference_id')
    return JsonResponse({'message': 'Payment pending.', 'payment_id': payment_id, 'status': status, 'preference_id': preference_id})
