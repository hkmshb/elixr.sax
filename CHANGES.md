# Changes

## 0.5.1
- Updated models having parent-child relationships to define cascade operation
  as delete when parent object gets deleted.
- Introduced EntityWithDeletedMixin and updated models to derive from it so that
  they have the deleted field.
- Added API functions implementing business logic for CRUD operations for models

## 0.5
- Added OrganizationType model and extended Organization

## 0.4
- Used UUIDs for all foreign key relationships
- Upgraded elixr.base to version 0.4

## 0.3
- Production release.

## 0.0
- Initial version.
