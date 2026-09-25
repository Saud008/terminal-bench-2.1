use craft_core::model::{CraftExport, CraftPreview, InventorySlot, RecipeBook};
use craft_core::{apply_craft, preview_craft};
use rusqlite::{params, Connection};
use std::path::Path;

pub struct InventoryDao<'a> {
    conn: &'a Connection,
}

impl<'a> InventoryDao<'a> {
    pub fn new(conn: &'a Connection) -> Self {
        Self { conn }
    }

    pub fn load_slots(&self) -> Result<Vec<InventorySlot>, String> {
        let mut stmt = self
            .conn
            .prepare("SELECT slot, item, qty FROM slots ORDER BY slot")
            .map_err(|e| e.to_string())?;
        let rows = stmt
            .query_map([], |row| {
                Ok(InventorySlot {
                    slot: row.get::<_, i64>(0)? as u32,
                    item: row.get(1)?,
                    qty: row.get::<_, i64>(2)? as u32,
                })
            })
            .map_err(|e| e.to_string())?;
        rows.collect::<Result<Vec<_>, _>>()
            .map_err(|e| e.to_string())
    }

    pub fn save_slots(&self, slots: &[InventorySlot]) -> Result<(), String> {
        self.conn
            .execute("DELETE FROM slots", [])
            .map_err(|e| e.to_string())?;
        for slot in slots {
            self.conn
                .execute(
                    "INSERT INTO slots (slot, item, qty) VALUES (?1, ?2, ?3)",
                    params![slot.slot, slot.item, slot.qty],
                )
                .map_err(|e| e.to_string())?;
        }
        Ok(())
    }

    pub fn preview(
        &self,
        book: &RecipeBook,
        recipe_id: &str,
        batch_qty: u32,
    ) -> Result<CraftPreview, String> {
        let slots = self.load_slots()?;
        Ok(preview_craft(book, &slots, recipe_id, batch_qty))
    }

    pub fn apply(
        &self,
        book: &RecipeBook,
        recipe_id: &str,
        batch_qty: u32,
    ) -> Result<CraftPreview, String> {
        let snapshot = self.load_slots()?;
        let mut slots = snapshot.clone();

        match apply_craft(book, &mut slots, recipe_id, batch_qty) {
            Ok(result) => {
                self.save_slots(&slots)?;
                self.conn
                    .execute(
                        "INSERT INTO craft_log (recipe_id, batch_qty, committed) VALUES (?1, ?2, 1)",
                        params![recipe_id, batch_qty],
                    )
                    .map_err(|e| e.to_string())?;
                self.conn
                    .execute(
                        "INSERT OR REPLACE INTO meta (key, value) VALUES ('last_craft', ?1)",
                        params![recipe_id],
                    )
                    .map_err(|e| e.to_string())?;
                Ok(result)
            }
            Err(err) => {
                self.save_slots(&snapshot)?;
                Err(err)
            }
        }
    }

    pub fn seed_profile(&self, profile: &[InventorySlot], slot_limit: u32) -> Result<(), String> {
        self.save_slots(profile)?;
        self.conn
            .execute(
                "INSERT OR REPLACE INTO meta (key, value) VALUES ('slot_limit', ?1)",
                params![slot_limit.to_string()],
            )
            .map_err(|e| e.to_string())?;
        Ok(())
    }

    pub fn export(&self, default_slot_limit: u32) -> Result<CraftExport, String> {
        let slot_limit = self
            .conn
            .query_row(
                "SELECT value FROM meta WHERE key = 'slot_limit'",
                [],
                |row| row.get::<_, String>(0),
            )
            .ok()
            .and_then(|v| v.parse().ok())
            .unwrap_or(default_slot_limit);

        let last_craft = self
            .conn
            .query_row(
                "SELECT value FROM meta WHERE key = 'last_craft'",
                [],
                |row| row.get(0),
            )
            .ok();

        Ok(CraftExport {
            slot_limit,
            slots: self.load_slots()?,
            last_craft,
        })
    }
}

pub fn load_recipe_book(path: &Path) -> Result<RecipeBook, String> {
    let raw = std::fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}
