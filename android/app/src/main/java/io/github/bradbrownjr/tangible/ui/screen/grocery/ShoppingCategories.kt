package io.github.bradbrownjr.tangible.ui.screen.grocery

import androidx.annotation.StringRes
import io.github.bradbrownjr.tangible.R

internal data class ShoppingCategoryPreset(val slug: String, @StringRes val labelRes: Int)

/** All grocery category presets, alphabetised by English label. Custom is handled separately. */
internal val SHOPPING_CATEGORY_PRESETS: List<ShoppingCategoryPreset> = listOf(
    ShoppingCategoryPreset("alcohol",             R.string.cat_alcohol),
    ShoppingCategoryPreset("bakery",              R.string.cat_bakery),
    ShoppingCategoryPreset("beverages",           R.string.cat_beverages),
    ShoppingCategoryPreset("bread",               R.string.cat_bread),
    ShoppingCategoryPreset("breakfast-cereal",    R.string.cat_breakfast_cereal),
    ShoppingCategoryPreset("canned-pantry",       R.string.cat_canned_pantry),
    ShoppingCategoryPreset("cleaning-household",  R.string.cat_cleaning_household),
    ShoppingCategoryPreset("condiments-spices",   R.string.cat_condiments_spices),
    ShoppingCategoryPreset("dairy-eggs",          R.string.cat_dairy_eggs),
    ShoppingCategoryPreset("deli",                R.string.cat_deli),
    ShoppingCategoryPreset("frozen",              R.string.cat_frozen),
    ShoppingCategoryPreset("health-beauty",       R.string.cat_health_beauty),
    ShoppingCategoryPreset("meat-seafood",        R.string.cat_meat_seafood),
    ShoppingCategoryPreset("pasta-grains",        R.string.cat_pasta_grains),
    ShoppingCategoryPreset("pet-supplies",        R.string.cat_pet_supplies),
    ShoppingCategoryPreset("produce",             R.string.cat_produce),
    ShoppingCategoryPreset("snacks",              R.string.cat_snacks),
)

internal val PRESET_SLUGS: Set<String> = SHOPPING_CATEGORY_PRESETS.map { it.slug }.toSet()
