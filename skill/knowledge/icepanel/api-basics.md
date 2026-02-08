# IcePanel API Basics

**Learned from**: https://developer.icepanel.io/introduction/getting-started

## Base URL & Auth

```
Base: https://api.icepanel.io/v1
Header: Authorization: ApiKey <key>
   or:  X-API-Key: <key>
```

## Rate Limits

- GET/HEAD: 2,400/min
- POST/PUT/PATCH/DELETE: 60/min

## Common Patterns

- All write endpoints use `latest` as versionId: `/landscapes/{id}/versions/latest/...`
- Get root object first to create top-level objects: `GET ...model/objects?filter[type]=root`
- Use the root object's `id` as `parentId` for top-level systems
- Upsert (PUT) = create-or-update by ID
- All responses wrap data in a key: `{ modelObject: {...} }`, `{ diagram: {...} }`
