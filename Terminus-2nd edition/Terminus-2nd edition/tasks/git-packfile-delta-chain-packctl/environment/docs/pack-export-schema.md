# Export schema

packctl resolve export writes /app/output/pack-object-export.json:

{
  "pack_id": string,
  "objects": [
    {
      "id": string,
      "kind": string,
      "inflated_size": integer,
      "sha1": string (40 hex chars, git object id style),
      "chain_depth": integer
    }
  ],
  "total_inflated_bytes": integer
}

Objects are sorted by id ascending. sha1 is SHA-1 of inflated payload bytes. When TB3_OBJECT_ID_SALT is set, exported id values append the salt string to the catalog id for mutation tests only; sha1 still reflects raw inflated bytes.
