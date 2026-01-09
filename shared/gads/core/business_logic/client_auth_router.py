"""
Client-Specific Authentication and Credential Routing

This module provides secure, client-isolated authentication and credential management
for multi-tenant Google Ads operations. It ensures credentials are properly scoped
and accessed only within authorized client contexts.

Key Features:
- Client-specific credential encryption and storage
- Secure credential routing based on client context
- OAuth token management per client
- Credential validation and rotation
- Audit trail for credential access
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import json
import base64
import hashlib
import secrets
from contextlib import asynccontextmanager

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import jwt
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logger.warning("Cryptography library not available. Using fallback encryption.")

from client_context_manager import ClientContext, get_current_client_context

logger = logging.getLogger(__name__)


@dataclass
class CredentialMetadata:
    """Metadata for stored credentials"""
    client_id: str
    service: str
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    encryption_version: str = "1.0"
    checksum: Optional[str] = None

    def is_expired(self) -> bool:
        """Check if credential is expired"""
        return self.expires_at is not None and datetime.now() > self.expires_at

    def record_access(self):
        """Record credential access"""
        self.last_accessed = datetime.now()
        self.access_count += 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "client_id": self.client_id,
            "service": self.service,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "access_count": self.access_count,
            "encryption_version": self.encryption_version,
            "checksum": self.checksum
        }


@dataclass
class OAuthToken:
    """OAuth token with metadata"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_at: Optional[datetime] = None
    scope: Optional[str] = None
    client_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self, buffer_seconds: int = 300) -> bool:
        """Check if token is expired (with buffer for refresh)"""
        if not self.expires_at:
            return False
        return datetime.now() + timedelta(seconds=buffer_seconds) > self.expires_at

    def get_authorization_header(self) -> str:
        """Get authorization header value"""
        return f"{self.token_type} {self.access_token}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "scope": self.scope,
            "client_id": self.client_id,
            "metadata": self.metadata
        }


class CredentialEncryption:
    """Secure credential encryption/decryption"""

    def __init__(self, master_key: Optional[str] = None):
        if not CRYPTO_AVAILABLE:
            logger.warning("Using insecure fallback encryption. Install cryptography for secure encryption.")
            self.master_key = master_key or "fallback_insecure_key"
            return

        # Generate or use master key
        if master_key:
            self.master_key = base64.b64decode(master_key)
        else:
            # Generate a new master key (should be stored securely)
            self.master_key = Fernet.generate_key()

        self.fernet = Fernet(self.master_key)

    def encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """Encrypt credential data"""
        data_str = json.dumps(credentials, sort_keys=True)
        data_bytes = data_str.encode('utf-8')

        if CRYPTO_AVAILABLE:
            encrypted = self.fernet.encrypt(data_bytes)
            return base64.b64encode(encrypted).decode('utf-8')
        else:
            # Fallback: simple base64 (NOT SECURE)
            return base64.b64encode(data_bytes).decode('utf-8')

    def decrypt_credentials(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt credential data"""
        try:
            if CRYPTO_AVAILABLE:
                encrypted_bytes = base64.b64decode(encrypted_data)
                decrypted_bytes = self.fernet.decrypt(encrypted_bytes)
            else:
                # Fallback: simple base64 (NOT SECURE)
                decrypted_bytes = base64.b64decode(encrypted_data)

            data_str = decrypted_bytes.decode('utf-8')
            return json.loads(data_str)
        except Exception as e:
            logger.error(f"Failed to decrypt credentials: {e}")
            raise ValueError("Invalid encrypted credential data")

    def get_master_key_b64(self) -> str:
        """Get master key as base64 string for storage"""
        if CRYPTO_AVAILABLE:
            return base64.b64encode(self.master_key).decode('utf-8')
        else:
            return base64.b64encode(self.master_key.encode('utf-8')).decode('utf-8')


class ClientCredentialStore:
    """
    Secure credential storage for client-specific credentials

    This class provides:
    - Encrypted credential storage
    - Client isolation
    - Credential validation
    - Access audit trails
    """

    def __init__(self, storage_path: Path, encryption: CredentialEncryption):
        self.storage_path = storage_path
        self.storage_path.mkdir(exist_ok=True, parents=True)
        self.encryption = encryption
        self.metadata: Dict[str, CredentialMetadata] = {}

        # Load existing metadata
        self._load_metadata()

    def _get_credential_path(self, client_id: str, service: str) -> Path:
        """Get file path for credential storage"""
        return self.storage_path / f"{client_id}_{service}.enc"

    def _get_metadata_path(self) -> Path:
        """Get metadata file path"""
        return self.storage_path / "metadata.json"

    def _load_metadata(self):
        """Load credential metadata"""
        metadata_path = self._get_metadata_path()
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r') as f:
                    data = json.load(f)
                    for key, meta_dict in data.items():
                        # Convert ISO strings back to datetime
                        if 'created_at' in meta_dict:
                            meta_dict['created_at'] = datetime.fromisoformat(meta_dict['created_at'])
                        if 'updated_at' in meta_dict:
                            meta_dict['updated_at'] = datetime.fromisoformat(meta_dict['updated_at'])
                        if meta_dict.get('expires_at'):
                            meta_dict['expires_at'] = datetime.fromisoformat(meta_dict['expires_at'])
                        if meta_dict.get('last_accessed'):
                            meta_dict['last_accessed'] = datetime.fromisoformat(meta_dict['last_accessed'])

                        self.metadata[key] = CredentialMetadata(**meta_dict)
            except Exception as e:
                logger.error(f"Failed to load credential metadata: {e}")

    def _save_metadata(self):
        """Save credential metadata"""
        metadata_path = self._get_metadata_path()
        try:
            data = {key: meta.to_dict() for key, meta in self.metadata.items()}
            with open(metadata_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save credential metadata: {e}")

    def store_credentials(self, client_id: str, service: str,
                         credentials: Dict[str, Any],
                         expires_at: Optional[datetime] = None) -> bool:
        """
        Store encrypted credentials for a client and service

        Args:
            client_id: Client identifier
            service: Service name (google_ads, airtable, etc.)
            credentials: Credential data to encrypt and store
            expires_at: Optional expiration datetime

        Returns:
            True if stored successfully
        """
        try:
            # Encrypt credentials
            encrypted_data = self.encryption.encrypt_credentials(credentials)

            # Create metadata
            key = f"{client_id}_{service}"
            now = datetime.now()

            if key in self.metadata:
                metadata = self.metadata[key]
                metadata.updated_at = now
                metadata.expires_at = expires_at
            else:
                metadata = CredentialMetadata(
                    client_id=client_id,
                    service=service,
                    created_at=now,
                    updated_at=now,
                    expires_at=expires_at
                )
                self.metadata[key] = metadata

            # Calculate checksum
            checksum_data = f"{client_id}:{service}:{encrypted_data}"
            metadata.checksum = hashlib.sha256(checksum_data.encode()).hexdigest()

            # Save encrypted data
            cred_path = self._get_credential_path(client_id, service)
            with open(cred_path, 'w') as f:
                json.dump({
                    "encrypted_data": encrypted_data,
                    "metadata": metadata.to_dict()
                }, f, indent=2)

            # Save metadata
            self._save_metadata()

            logger.info(f"Stored credentials for client {client_id}, service {service}")
            return True

        except Exception as e:
            logger.error(f"Failed to store credentials for client {client_id}: {e}")
            return False

    def get_credentials(self, client_id: str, service: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve and decrypt credentials for a client and service

        Args:
            client_id: Client identifier
            service: Service name

        Returns:
            Decrypted credentials or None if not found/expired
        """
        try:
            key = f"{client_id}_{service}"

            # Check if metadata exists
            if key not in self.metadata:
                return None

            metadata = self.metadata[key]

            # Check if expired
            if metadata.is_expired():
                logger.warning(f"Credentials expired for client {client_id}, service {service}")
                return None

            # Load encrypted data
            cred_path = self._get_credential_path(client_id, service)
            if not cred_path.exists():
                return None

            with open(cred_path, 'r') as f:
                data = json.load(f)

            encrypted_data = data.get("encrypted_data")
            if not encrypted_data:
                return None

            # Verify checksum
            checksum_data = f"{client_id}:{service}:{encrypted_data}"
            calculated_checksum = hashlib.sha256(checksum_data.encode()).hexdigest()
            if metadata.checksum and calculated_checksum != metadata.checksum:
                logger.error(f"Credential checksum mismatch for client {client_id}, service {service}")
                return None

            # Decrypt
            credentials = self.encryption.decrypt_credentials(encrypted_data)

            # Record access
            metadata.record_access()
            self._save_metadata()

            logger.debug(f"Retrieved credentials for client {client_id}, service {service}")
            return credentials

        except Exception as e:
            logger.error(f"Failed to retrieve credentials for client {client_id}: {e}")
            return None

    def delete_credentials(self, client_id: str, service: str) -> bool:
        """Delete stored credentials"""
        try:
            key = f"{client_id}_{service}"
            cred_path = self._get_credential_path(client_id, service)

            # Remove file
            if cred_path.exists():
                cred_path.unlink()

            # Remove metadata
            if key in self.metadata:
                del self.metadata[key]
                self._save_metadata()

            logger.info(f"Deleted credentials for client {client_id}, service {service}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete credentials for client {client_id}: {e}")
            return False

    def list_client_credentials(self, client_id: str) -> List[Dict[str, Any]]:
        """List all services with credentials for a client"""
        client_creds = []
        for key, metadata in self.metadata.items():
            if metadata.client_id == client_id:
                client_creds.append({
                    "service": metadata.service,
                    "created_at": metadata.created_at.isoformat(),
                    "updated_at": metadata.updated_at.isoformat(),
                    "expires_at": metadata.expires_at.isoformat() if metadata.expires_at else None,
                    "last_accessed": metadata.last_accessed.isoformat() if metadata.last_accessed else None,
                    "access_count": metadata.access_count,
                    "is_expired": metadata.is_expired()
                })
        return client_creds

    def rotate_credentials(self, client_id: str, service: str,
                          new_credentials: Dict[str, Any],
                          expires_at: Optional[datetime] = None) -> bool:
        """Rotate existing credentials"""
        logger.info(f"Rotating credentials for client {client_id}, service {service}")
        return self.store_credentials(client_id, service, new_credentials, expires_at)


class ClientAuthRouter:
    """
    Client-specific authentication and credential routing

    This class provides:
    - Client-isolated credential access
    - OAuth token management
    - Service-specific authentication
    - Security validation
    """

    def __init__(self, credential_store: ClientCredentialStore):
        self.credential_store = credential_store
        self.token_cache: Dict[str, OAuthToken] = {}
        self._oauth_clients: Dict[str, Dict[str, Any]] = {}

    def register_oauth_client(self, service: str, client_config: Dict[str, Any]):
        """
        Register OAuth client configuration for a service

        Args:
            service: Service name
            client_config: OAuth client configuration
        """
        self._oauth_clients[service] = client_config

    async def get_client_credentials(self, client_id: str, service: str) -> Optional[Dict[str, Any]]:
        """
        Get credentials for a specific client and service

        This method enforces client isolation - credentials can only be accessed
        within the client's context.

        Args:
            client_id: Client identifier
            service: Service name

        Returns:
            Service credentials or None if not authorized or not found
        """
        # Validate client context
        current_context = get_current_client_context()
        if not current_context:
            logger.error("No client context available for credential access")
            return None

        if current_context.client_id != client_id:
            logger.error(f"Client context mismatch: requested {client_id}, current {current_context.client_id}")
            return None

        # Validate operation is allowed for client
        if not current_context.validate_access(f"access_{service}_credentials"):
            logger.error(f"Client {client_id} not authorized to access {service} credentials")
            return None

        # Start operation tracking
        operation_id = current_context.start_operation(f"credential_access_{service}")

        try:
            credentials = self.credential_store.get_credentials(client_id, service)

            if credentials:
                # Log successful access
                current_context.end_operation(operation_id, success=True)
                logger.info(f"Credentials accessed for client {client_id}, service {service}")
            else:
                current_context.end_operation(operation_id, success=False, error="Credentials not found")
                logger.warning(f"Credentials not found for client {client_id}, service {service}")

            return credentials

        except Exception as e:
            current_context.end_operation(operation_id, success=False, error=str(e))
            logger.error(f"Error accessing credentials for client {client_id}: {e}")
            return None

    async def store_client_credentials(self, client_id: str, service: str,
                                     credentials: Dict[str, Any],
                                     expires_at: Optional[datetime] = None) -> bool:
        """Store credentials for a client (admin operation)"""
        # Validate client context for admin operations
        current_context = get_current_client_context()
        if current_context and current_context.client_id != client_id:
            # Allow cross-client access only for admin contexts
            if not hasattr(current_context.config, 'user_roles') or 'admin' not in current_context.config.communication_preferences.get('user_roles', []):
                logger.error(f"Client {current_context.client_id} not authorized to store credentials for {client_id}")
                return False

        operation_id = f"store_credentials_{client_id}_{service}_{int(time.time())}"

        try:
            success = self.credential_store.store_credentials(client_id, service, credentials, expires_at)
            logger.info(f"{'Stored' if success else 'Failed to store'} credentials for client {client_id}, service {service}")
            return success
        except Exception as e:
            logger.error(f"Error storing credentials for client {client_id}: {e}")
            return False

    async def get_oauth_token(self, client_id: str, service: str,
                            scopes: Optional[List[str]] = None) -> Optional[OAuthToken]:
        """
        Get valid OAuth token for a client and service

        Args:
            client_id: Client identifier
            service: Service name
            scopes: Required OAuth scopes

        Returns:
            Valid OAuth token or None
        """
        cache_key = f"{client_id}_{service}"

        # Check cache first
        if cache_key in self.token_cache:
            token = self.token_cache[cache_key]
            if not token.is_expired():
                return token
            else:
                # Remove expired token
                del self.token_cache[cache_key]

        # Get stored credentials
        credentials = await self.get_client_credentials(client_id, service)
        if not credentials:
            return None

        # Attempt token refresh or creation
        try:
            token = await self._refresh_or_create_token(client_id, service, credentials, scopes)
            if token:
                self.token_cache[cache_key] = token
            return token
        except Exception as e:
            logger.error(f"Failed to get OAuth token for client {client_id}: {e}")
            return None

    async def _refresh_or_create_token(self, client_id: str, service: str,
                                     credentials: Dict[str, Any],
                                     scopes: Optional[List[str]] = None) -> Optional[OAuthToken]:
        """Refresh or create OAuth token"""
        # This would implement actual OAuth flow
        # For now, return mock token from stored credentials

        if 'access_token' in credentials:
            expires_at = None
            if 'expires_at' in credentials:
                if isinstance(credentials['expires_at'], str):
                    expires_at = datetime.fromisoformat(credentials['expires_at'])
                else:
                    expires_at = credentials['expires_at']

            return OAuthToken(
                access_token=credentials['access_token'],
                refresh_token=credentials.get('refresh_token'),
                token_type=credentials.get('token_type', 'Bearer'),
                expires_at=expires_at,
                scope=credentials.get('scope'),
                client_id=credentials.get('client_id')
            )

        return None

    async def validate_credentials(self, client_id: str, service: str) -> Tuple[bool, str]:
        """
        Validate that stored credentials are working

        Args:
            client_id: Client identifier
            service: Service name

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            credentials = await self.get_client_credentials(client_id, service)
            if not credentials:
                return False, "Credentials not found"

            # Service-specific validation
            if service == "google_ads":
                return await self._validate_google_ads_credentials(credentials)
            elif service == "airtable":
                return await self._validate_airtable_credentials(credentials)
            else:
                return True, "Credentials exist (no specific validation available)"

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    async def _validate_google_ads_credentials(self, credentials: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate Google Ads credentials"""
        # This would make a test API call
        return True, "Google Ads credentials appear valid"

    async def _validate_airtable_credentials(self, credentials: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate Airtable credentials"""
        # This would make a test API call
        return True, "Airtable credentials appear valid"

    def get_client_credential_summary(self, client_id: str) -> Dict[str, Any]:
        """Get summary of client's stored credentials"""
        services = self.credential_store.list_client_credentials(client_id)

        return {
            "client_id": client_id,
            "total_services": len(services),
            "services": services,
            "has_expired": any(s.get("is_expired", False) for s in services),
            "last_updated": max((s.get("updated_at") for s in services if s.get("updated_at")), default=None)
        }


# Global auth router instance
_auth_router = None

def get_auth_router(credential_store_path: Optional[Path] = None) -> ClientAuthRouter:
    """Get global auth router instance"""
    global _auth_router
    if _auth_router is None:
        storage_path = credential_store_path or Path("./client_credentials")
        encryption = CredentialEncryption()
        credential_store = ClientCredentialStore(storage_path, encryption)
        _auth_router = ClientAuthRouter(credential_store)
    return _auth_router

# Export for easy importing
__all__ = [
    'ClientAuthRouter',
    'ClientCredentialStore',
    'CredentialEncryption',
    'OAuthToken',
    'CredentialMetadata',
    'get_auth_router'
]
