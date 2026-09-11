from rest_framework import serializers
from .models import User, Role, Department, UserRole, Permission


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'code', 'description', 'is_system_role', 'is_active']


class DepartmentSerializer(serializers.ModelSerializer):
    parent_department_name = serializers.CharField(source='parent_department.name', read_only=True, default=None)

    class Meta:
        model = Department
        fields = ['id', 'name', 'code', 'description', 'parent_department', 'parent_department_name',
                  'head_of_department', 'is_clinical', 'is_active']


class UserSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True, default=None)
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone',
                  'department', 'department_name', 'employee_id', 'job_title',
                  'status', 'last_login', 'mfa_enabled', 'roles', 'created_at']
        read_only_fields = ['id', 'last_login', 'created_at']

    def get_roles(self, obj):
        user_roles = UserRole.objects.filter(user=obj, is_active=True).select_related('role')
        return [RoleSerializer(ur.role).data for ur in user_roles]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    role_ids = serializers.ListField(child=serializers.UUIDField(), write_only=True, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name',
                  'phone', 'department', 'employee_id', 'job_title', 'role_ids']

    def create(self, validated_data):
        role_ids = validated_data.pop('role_ids', [])
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        # Assign roles
        for role_id in role_ids:
            try:
                role = Role.objects.get(id=role_id)
                UserRole.objects.create(user=user, role=role)
            except Role.DoesNotExist:
                pass

        return user


class UserProfileSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True, default=None)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone',
                  'department', 'department_name', 'employee_id', 'job_title',
                  'profile_photo_url', 'last_login', 'created_at']
        read_only_fields = ['id', 'username', 'last_login', 'created_at']


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
