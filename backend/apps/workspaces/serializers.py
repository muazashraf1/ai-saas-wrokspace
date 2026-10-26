from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import Workspace, WorkspaceMember

User = get_user_model()


class WorkspaceMemberUserSerializer(serializers.ModelSerializer):
    """Minimal user representation for membership listings."""
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name']


class WorkspaceMemberSerializer(serializers.ModelSerializer):
    """Serializer representing a workspace member with nested user info."""
    user = WorkspaceMemberUserSerializer(read_only=True)

    class Meta:
        model = WorkspaceMember
        fields = ['id', 'workspace', 'user', 'role', 'created_at']
        read_only_fields = ['id', 'workspace', 'created_at']


class WorkspaceSerializer(serializers.ModelSerializer):
    """Serializer for displaying workspaces."""
    owner = WorkspaceMemberUserSerializer(read_only=True)
    current_user_role = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Workspace
        fields = ['id', 'name', 'owner', 'plan', 'created_at', 'current_user_role', 'member_count']
        read_only_fields = ['id', 'owner', 'created_at', 'current_user_role', 'member_count']

    def get_current_user_role(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        membership = obj.memberships.filter(user=request.user).first()
        return membership.role if membership else None

    def get_member_count(self, obj):
        return obj.memberships.count()


class WorkspaceCreateSerializer(serializers.ModelSerializer):
    """
    Serializer to create a workspace.
    Atomically creates the Workspace and assigns the creator as 'owner' in workspace_members.
    """
    class Meta:
        model = Workspace
        fields = ['id', 'name', 'plan']
        read_only_fields = ['id']

    def create(self, validated_data):
        user = self.context['request'].user
        with transaction.atomic():
            workspace = Workspace.objects.create(
                owner=user,
                **validated_data
            )
            # Creator automatically becomes the workspace owner member
            WorkspaceMember.objects.create(
                workspace=workspace,
                user=user,
                role='owner'
            )
        return workspace


class AddMemberSerializer(serializers.Serializer):
    """
    Serializer to invite/add a member to a workspace by email.
    As per Section 2.3: 'invite by email as a simple record, no real email needed'.
    """
    email = serializers.EmailField(required=True)
    role = serializers.ChoiceField(
        choices=[('admin', 'Admin'), ('member', 'Member')],
        default='member'
    )

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist on the platform.")
        return user

    def validate(self, attrs):
        workspace = self.context['workspace']
        user = attrs['email']  # resolved User instance from validate_email

        if WorkspaceMember.objects.filter(workspace=workspace, user=user).exists():
            raise serializers.ValidationError({"email": "This user is already a member of this workspace."})

        attrs['user_instance'] = user
        return attrs

    def create(self, validated_data):
        workspace = self.context['workspace']
        user = validated_data['user_instance']
        role = validated_data.get('role', 'member')

        return WorkspaceMember.objects.create(
            workspace=workspace,
            user=user,
            role=role
        )
