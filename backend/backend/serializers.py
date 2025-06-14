from rest_framework import serializers
from accounts.models import Destinos, MetodoPago, Nosotros, Carrito, Profile
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

class DestinosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destinos
        fields = '__all__'

class MetodoPagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetodoPago
        fields = '__all__'

class CarritoSerializer(serializers.ModelSerializer):
    id_destino = serializers.PrimaryKeyRelatedField(queryset=Destinos.objects.all())
    user = serializers.ReadOnlyField(source='user.id')
    id_metodoPago = MetodoPagoSerializer()
    nombre_destino = serializers.SerializerMethodField()  # Nuevo campo para el nombre del destino
    
    class Meta:
        model = Carrito
        fields = [
            'id_compra',
            'id_destino',
            'nombre_destino',  # Añadido el nuevo campo
            'user',
            'id_metodoPago',
            'cantidad',
            'fecha_creacion',
            'total'  # Asegúrate de incluir todos los campos que necesitas
        ]
    
    def get_nombre_destino(self, obj):
        return obj.id_destino.nombre_Destino if obj.id_destino else None

class NosotrosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nosotros
        fields = '__all__'

class RegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password', 'password2']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
        }
    
    def validate(self, attrs):
        email = attrs.get('email')
        
        # Verificar si el email ya está registrado
        if User.objects.filter(username=email).exists():
            raise serializers.ValidationError({"email": "Este correo electrónico ya está registrado."})
            
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})
        return attrs

    def create(self, validated_data):
        email = validated_data['email']
        
        # Verificar nuevamente por si acaso
        if User.objects.filter(username=email).exists():
            raise serializers.ValidationError({"email": "Este correo electrónico ya está registrado."})
            
        validated_data.pop('password2')
        user = User(
            username=email,  # Usar el correo electrónico como nombre de usuario
            email=email,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField() # El usuario ingresa su email aquí
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        # *** ¡CAMBIO CRÍTICO AQUÍ! ***
        # Pasamos el 'email' que el usuario ingresó como si fuera el 'username'
        # porque así es como lo guardamos en el RegisterSerializer.
        user = authenticate(request=self.context.get('request'), username=email, password=password)
        
        if not user:
            # Si el usuario no se puede autenticar, las credenciales son inválidas
            raise serializers.ValidationError('Credenciales inválidas')
        
        # Opcional pero recomendado: Asegúrate de que el usuario esté activo
        if not user.is_active:
            raise serializers.ValidationError('Cuenta inactiva.')

        attrs['user'] = user
        return attrs
    

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'
        extra_kwargs = {
            'user': {'read_only': True}
        }
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['email'] = instance.user.email
        representation['first_name'] = instance.user.first_name
        representation['last_name'] = instance.user.last_name
        return representation