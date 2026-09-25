use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ItemDef {
    pub id: String,
    pub stack_max: u32,
    pub stackable: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Ingredient {
    pub item: String,
    pub qty: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Catalyst {
    pub item: String,
    pub qty: u32,
    #[serde(default)]
    pub consumed: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Output {
    pub item: String,
    pub qty: u32,
    #[serde(default = "default_true")]
    pub stackable: bool,
}

fn default_true() -> bool {
    true
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Recipe {
    pub id: String,
    pub inputs: Vec<Ingredient>,
    #[serde(default)]
    pub catalyst: Option<Catalyst>,
    pub output: Output,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RecipeBook {
    pub slot_limit: u32,
    pub items: Vec<ItemDef>,
    pub recipes: Vec<Recipe>,
    #[serde(default)]
    pub substitutes: BTreeMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InventorySlot {
    pub slot: u32,
    pub item: String,
    pub qty: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResolvedIngredient {
    pub item: String,
    pub qty: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OutputPlacement {
    pub item: String,
    pub qty: u32,
    pub target_slot: Option<u32>,
    pub new_slot: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CraftPreview {
    pub recipe_id: String,
    pub batch_qty: u32,
    pub inputs: Vec<ResolvedIngredient>,
    pub catalyst: Option<ResolvedIngredient>,
    pub outputs: Vec<OutputPlacement>,
    pub ok: bool,
    pub reason: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CraftExport {
    pub slot_limit: u32,
    pub slots: Vec<InventorySlot>,
    pub last_craft: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RecipeGraphReport {
    pub recipe_count: u32,
    pub edge_count: u32,
    pub cyclic: bool,
    pub cycles: Vec<Vec<String>>,
}

impl RecipeBook {
    pub fn item_def(&self, item_id: &str) -> Option<&ItemDef> {
        self.items.iter().find(|i| i.id == item_id)
    }

    pub fn recipe(&self, recipe_id: &str) -> Option<&Recipe> {
        self.recipes.iter().find(|r| r.id == recipe_id)
    }

    pub fn producer_of(&self, item_id: &str) -> Option<&Recipe> {
        self.recipes.iter().find(|r| r.output.item == item_id)
    }
}
