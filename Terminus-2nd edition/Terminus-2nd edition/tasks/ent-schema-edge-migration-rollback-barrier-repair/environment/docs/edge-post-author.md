# post_author edge

Edge name: post_author. From posts.author_id to users.id.

Legacy column user_ref stores ent string refs as u:USER_ID. Backfill must parse the u: prefix, not only bare numeric strings.

After migration, every posts row must have author_id NOT NULL with a matching users.id. Orphan author_id values fail ent_post_validate and the final migrate up orphan gate.

The bundled catalog codegen_seed is bundled-edge-v3 at target_version 3.
