from django import forms
from django.contrib.auth import get_user_model
from .models import Role, Department, UserRole, RolePermission, Permission

User = get_user_model()


class UserForm(forms.Form):
    user_id = forms.UUIDField(required=False, widget=forms.HiddenInput)
    username = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'input-field'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'input-field'}))
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'input-field'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'input-field'}))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'input-field'}))
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        required=False, widget=forms.Select(attrs={'class': 'input-field'})
    )
    employee_id = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'input-field'}))
    job_title = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'input-field'}))
    password = forms.CharField(max_length=128, required=False, widget=forms.PasswordInput(attrs={'class': 'input-field'}))
    status = forms.ChoiceField(
        choices=[('active', 'Active'), ('inactive', 'Inactive'), ('locked', 'Locked'), ('pending', 'Pending')],
        widget=forms.Select(attrs={'class': 'input-field'})
    )
    role_ids = forms.CharField(required=False, widget=forms.HiddenInput)

    def save(self, user=None):
        data = self.cleaned_data
        user_id = data.get('user_id')
        role_ids_str = data.get('role_ids', '')
        role_ids = [r.strip() for r in role_ids_str.split(',') if r.strip()] if role_ids_str else []

        if user_id:
            target = User.objects.get(id=user_id)
            target.username = data['username']
            target.email = data['email']
            target.first_name = data['first_name']
            target.last_name = data['last_name']
            target.phone = data.get('phone', '')
            target.department = data.get('department')
            target.employee_id = data.get('employee_id', '')
            target.job_title = data.get('job_title', '')
            target.status = data.get('status', 'active')
            if data.get('password'):
                target.set_password(data['password'])
            target.save()
        else:
            target = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data.get('password') or 'changeme123',
                first_name=data['first_name'],
                last_name=data['last_name'],
                phone=data.get('phone', ''),
                department=data.get('department'),
                employee_id=data.get('employee_id', ''),
                job_title=data.get('job_title', ''),
                status=data.get('status', 'active'),
            )

        UserRole.objects.filter(user=target).delete()
        for rid in role_ids:
            try:
                role = Role.objects.get(id=rid)
                UserRole.objects.create(user=target, role=role, assigned_by=user.id if user else None)
            except Role.DoesNotExist:
                pass

        return target


class RoleForm(forms.Form):
    role_id = forms.UUIDField(required=False, widget=forms.HiddenInput)
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'input-field'}))
    code = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'input-field'}))
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'input-field', 'rows': 2}))

    def save(self, user=None):
        data = self.cleaned_data
        role_id = data.get('role_id')
        if role_id:
            role = Role.objects.get(id=role_id)
            role.name = data['name']
            role.code = data['code']
            role.description = data.get('description', '')
            role.save()
        else:
            role = Role.objects.create(
                name=data['name'],
                code=data['code'],
                description=data.get('description', ''),
                created_by=user.id if user else None
            )
        return role


class DepartmentForm(forms.Form):
    dept_id = forms.UUIDField(required=False, widget=forms.HiddenInput)
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'input-field'}))
    code = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'input-field'}))
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'input-field', 'rows': 2}))
    parent_department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        required=False, widget=forms.Select(attrs={'class': 'input-field'})
    )
    is_clinical = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'rounded'}))

    def save(self):
        data = self.cleaned_data
        dept_id = data.get('dept_id')
        if dept_id:
            dept = Department.objects.get(id=dept_id)
            dept.name = data['name']
            dept.code = data['code']
            dept.description = data.get('description', '')
            dept.parent_department = data.get('parent_department')
            dept.is_clinical = data.get('is_clinical', False)
            dept.save()
        else:
            dept = Department.objects.create(
                name=data['name'],
                code=data['code'],
                description=data.get('description', ''),
                parent_department=data.get('parent_department'),
                is_clinical=data.get('is_clinical', False),
            )
        return dept


class ProfileForm(forms.Form):
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'input-field'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'input-field'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'input-field'}))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'input-field'}))

    def save(self, user):
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data.get('phone', '')
        user.save()
        return user


class PasswordChangeForm(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input-field'}))
    new_password = forms.CharField(min_length=8, widget=forms.PasswordInput(attrs={'class': 'input-field'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input-field'}))

    def __init__(self, target_user=None, *args, **kwargs):
        self.target_user = target_user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('new_password') != cleaned.get('confirm_password'):
            raise forms.ValidationError('New passwords do not match')
        if self.target_user and not self.target_user.check_password(cleaned.get('current_password', '')):
            raise forms.ValidationError('Current password is incorrect')
        return cleaned

    def save(self):
        self.target_user.set_password(self.cleaned_data['new_password'])
        self.target_user.save()
        return self.target_user


class UserRoleAssignForm(forms.Form):
    user_id = forms.UUIDField(widget=forms.HiddenInput)
    role_id = forms.UUIDField(widget=forms.HiddenInput)

    def assign(self, assigned_by=None):
        user = User.objects.get(id=self.cleaned_data['user_id'])
        role = Role.objects.get(id=self.cleaned_data['role_id'])
        user_role, created = UserRole.objects.get_or_create(
            user=user, role=role,
            defaults={'assigned_by': assigned_by.id if assigned_by else None}
        )
        return user_role

    def remove(self):
        UserRole.objects.filter(
            user_id=self.cleaned_data['user_id'],
            role_id=self.cleaned_data['role_id']
        ).delete()


class RolePermissionAssignForm(forms.Form):
    role_id = forms.UUIDField(widget=forms.HiddenInput)
    permission_id = forms.UUIDField(widget=forms.HiddenInput)

    def assign(self, granted_by=None):
        role = Role.objects.get(id=self.cleaned_data['role_id'])
        perm = Permission.objects.get(id=self.cleaned_data['permission_id'])
        rp, created = RolePermission.objects.get_or_create(
            role=role, permission=perm,
            defaults={'granted_by': granted_by.id if granted_by else None}
        )
        return rp

    def remove(self):
        RolePermission.objects.filter(
            role_id=self.cleaned_data['role_id'],
            permission_id=self.cleaned_data['permission_id']
        ).delete()


class HospitalSettingForm(forms.Form):
    hospital_name = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'input-field'}))
    short_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'input-field'}))
    tagline = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={'class': 'input-field'}))
    logo = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'input-field'}))
    phone = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'input-field'}))
    email = forms.CharField(max_length=120, required=False, widget=forms.EmailInput(attrs={'class': 'input-field'}))
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'input-field', 'rows': 2}))
    website = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={'class': 'input-field'}))
    registration_fee = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0, widget=forms.NumberInput(attrs={'class': 'input-field', 'step': '0.01'}))
    followup_window_days = forms.IntegerField(min_value=1, max_value=365, widget=forms.NumberInput(attrs={'class': 'input-field'}))

    def save(self, updated_by=None):
        from .models import HospitalSetting
        setting = HospitalSetting.get_settings()
        setting.hospital_name = self.cleaned_data['hospital_name']
        setting.short_name = self.cleaned_data['short_name']
        setting.tagline = self.cleaned_data.get('tagline', '')
        setting.phone = self.cleaned_data.get('phone', '')
        setting.email = self.cleaned_data.get('email', '')
        setting.address = self.cleaned_data.get('address', '')
        setting.website = self.cleaned_data.get('website', '')
        setting.registration_fee = self.cleaned_data.get('registration_fee', 5.00)
        setting.followup_window_days = self.cleaned_data.get('followup_window_days', 30)
        if self.cleaned_data.get('logo'):
            setting.logo = self.cleaned_data['logo']
        if updated_by:
            setting.updated_by = updated_by
        setting.save()
        return setting
