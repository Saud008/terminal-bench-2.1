pub fn vision_radius(class: &str) -> i32 {
    match class {
        "scout" => 4,
        "infantry" => 2,
        "tower" => 3,
        _ => 1,
    }
}
