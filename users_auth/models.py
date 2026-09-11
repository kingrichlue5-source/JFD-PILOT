import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class SyncStatus(models.TextChoices):
    LOCAL = 'local', 'Local'
    SYNCED = 'synced', 'Synced'


class UserStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'
    LOCKED = 'locked', 'Locked'
    PENDING = 'pending', 'Pending'


class Department(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    parent_department = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sub_departments')
    head_of_department = models.UUIDField(null=True, blank=True)
    is_clinical = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'departments'
        managed = True

    def __str__(self):
        return f"{self.code} - {self.name}"


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError('Username is required')
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    employee_id = models.CharField(max_length=50, blank=True, null=True)
    job_title = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=10, choices=UserStatus.choices, default=UserStatus.ACTIVE)
    last_login = models.DateTimeField(blank=True, null=True)
    password_changed_at = models.DateTimeField(auto_now_add=True)
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(blank=True, null=True)
    mfa_enabled = models.BooleanField(default=False)
    mfa_secret = models.CharField(max_length=255, blank=True, null=True)
    profile_photo_url = models.CharField(max_length=500, blank=True, null=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    class Meta:
        db_table = 'users'
        managed = True

    def __str__(self):
        return f"{self.username} - {self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    is_system_role = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'roles'
        managed = True

    def __str__(self):
        return self.name


class Permission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'permissions'
        managed = True

    def __str__(self):
        return self.name


class UserRole(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_roles')
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.UUIDField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'user_roles'
        managed = True
        unique_together = ('user', 'role')

    def __str__(self):
        return f"{self.user.username} - {self.role.name}"


class RolePermission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='role_permissions')
    granted_at = models.DateTimeField(auto_now_add=True)
    granted_by = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'role_permissions'
        managed = True
        unique_together = ('role', 'permission')

    def __str__(self):
        return f"{self.role.name} - {self.permission.name}"


class UserSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_token = models.CharField(max_length=255, unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'user_sessions'
        managed = True

    def __str__(self):
        return f"{self.user.username} - {self.session_token[:20]}..."


class HospitalSetting(models.Model):
    """Singleton-style settings: hospital branding, contact details, and logo."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital_name = models.CharField(max_length=200, default='Jackson F. Doe Memorial Regional Referral Hospital')
    short_name = models.CharField(max_length=100, default='JFD Hospital')
    tagline = models.CharField(max_length=200, blank=True, null=True, default='Hospital Management Information System')
    logo = models.ImageField(upload_to='hospital/', blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(max_length=120, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    website = models.CharField(max_length=200, blank=True, null=True, default='https://jfdhospital.com/')
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=5.00, help_text='Registration fee charged to patients at registration')
    followup_window_days = models.IntegerField(default=30, help_text='Number of days before/after scheduled date considered inside follow-up window')
    updated_by = models.CharField(max_length=100, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hospital_settings'
        managed = True

    def __str__(self):
        return self.hospital_name

    @classmethod
    def get_settings(cls):
        setting = cls.objects.first()
        if setting is None:
            setting = cls.objects.create(tagline='Hospital Management Information System')
        return setting
